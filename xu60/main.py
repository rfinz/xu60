"""
Hopefully a server spread over not too many files.
"""
import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.endpoints import HTTPEndpoint
from starlette.responses import Response, JSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.config import Config

import pygit2
from pygit2.enums import ObjectType

from xu60.data import cvd, cnd, changeset, SuperRepo

config = Config(env_prefix='XU60_')

REPO_HOME = Path(config("REPO_HOME", default="."))
SRV_HOME = Path(config("SRV_HOME", default=REPO_HOME))
OBJECT_ROUTE = config("OBJECT_ROUTE", default="object")
VERSIONS_ROUTE = config("VERSIONS_ROUTE", default="versions")
META_ROUTE = config("META_ROUTE", default="meta")
MIRRORS = config("MIRRORS", default={})


@asynccontextmanager
async def lifespan(app):
    """
    Lifespan management.
    """
    print('Startup')
    # double cache size and enable caching for objects under 512KB
    pygit2.settings.cache_max_size(512 * 1024**2)
    pygit2.settings.cache_object_limit(ObjectType.BLOB, 512 * 1024)

    app.state.repo = SuperRepo(REPO_HOME) # main repo
    app.state.vd = {} # VERSIONS DIRECTORY
    app.state.od = {} # OBJECT DIRECTORY
    app.state.nd = {} # NAME DIRECTORY
    app.state.cd = {} # CHANGE DIRECTORY
    app.state.mirrors = MIRRORS.copy()

    repo = app.state.repo

    for path, url in app.state.mirrors.items():
        try:
            repo.submodules.add(url, path)
        except ValueError as e:
            print(e)

    for sub in repo.submodules:
        if not sub.path in app.state.mirrors:
            app.state.mirrors[sub.path] = sub.url

    repo.submodules.cache_all()

    yield

    used = pygit2.settings.cached_memory[0]
    total = pygit2.settings.cached_memory[1]
    print(
        'libgit2 cache use: ' \
        f'{used/1024**2:.1f}MB of {total/1024**2:.1f}MB ({used/total*100:.1f}%)'
    )
    repo.free()
    print('Shutdown')


class Metadata(HTTPEndpoint):
    """
    Metadata for the site
    """
    async def noop(self, scope, receive, send):
        """
        No op callable to satisfy the endpoint
        """

    async def get(self, request):
        """
        If a path is present, add flag to scope and re-route,
        otherwise return JSON metadata for the entire repo.
        """
        host = request.headers['host']
        repo = request.app.state.repo
        head = repo.revparse_single('HEAD')
        meta = request.path_params.get('meta_url')
        try:
            origin = repo.remotes["origin"].url
        except KeyError:
            origin = "None"

        if meta:
            scope = dict(self.scope)
            del scope["root_path"]
            del scope["path_params"]
            scope["path"] = "/" + meta
            scope["raw_path"] = str.encode(scope["path"])
            scope["xu60.meta"] = True
            await request.app(scope, self.receive, self.send)
            return self.noop

        return JSONResponse({
            "site": f'{request.url.scheme}://{host}{request.url.path}',
            "origin": origin,
            "head": str(head.id),
            "last_updated": str(datetime.datetime.fromtimestamp(head.commit_time)),
            "content_id": "sha1", #placeholder -- should be calculated from the object database
            "mirrors": request.app.state.mirrors,
            "meta": f"/{META_ROUTE}",
            "object": f"/{OBJECT_ROUTE}",
            "versions": f"/{VERSIONS_ROUTE}"
        })


class Directory(HTTPEndpoint):
    """
    Site directory
    """
    async def get(self, request):
        """
        Send version directory, one entry per blob object in the tree.
        """
        repo = request.app.state.repo
        res = "object,time,name,length,indices\n"

        vd = cvd(repo, request)
        json = []

        for c in reversed(vd):
            for t in vd[c]:
                if self.scope.get("xu60.meta"):
                    t["id"] = str(t["id"])
                    json += [t]
                else:
                    res += f'{t["id"]},{t["time"]},{t["name"]},{t["length"]},{t["indices"]}\n'
        if self.scope.get("xu60.meta"):
            return JSONResponse(json)
        return Response(res, media_type='text/plain')


class Object(HTTPEndpoint):
    """
    Get object contents from repo
    """
    async def get(self, request):
        """
        Send object contents, with allowable URL pattern for selecting bytes.
        """
        repo = request.app.state.repo
        oid = request.path_params['object']
        try:
            obj = repo.get(oid)
        except ValueError as e:
            raise HTTPException(status_code=404, detail="Not Found") from e

        if not obj or obj.type != ObjectType.BLOB:
            raise HTTPException(status_code=404, detail="Not Found")

        if obj.is_binary:
            body = obj.data
            size = obj.size
        else:
            body = obj.data.decode('utf-8')
            size = len(body)

        start = request.path_params.get('start', 0)
        end = request.path_params.get('end', size)

        body = "" if "nobody" in request.query_params else body[start:end]

        if self.scope.get("xu60.meta"):
            names, previous_version, next_version = changeset(obj, repo, request)

            resp = {
                "id": str(obj.id),
                "names": names,
                "length": size,
                "indices": "bytes" if obj.is_binary else "chars",
                "window": {"start": start, "end": end},
                "previous_version": previous_version,
                "next_version": next_version
            }
            if not obj.is_binary and body:
                resp["body"] = body

            return JSONResponse(resp)
        headers = {
            "Cache-Control": "max-age=3600, stale-while-revalidate=86400, immutable"
        }
        return Response(body, headers=headers, media_type='text/plain')


class Versions(HTTPEndpoint):
    """
    Convert file properties to object form.
    """
    async def get(self, request):
        """
        Send version IDs in reverse order (newest first)
        """
        repo = request.app.state.repo
        p = request.path_params['path_to_file']
        pp = Path(p).parts
        versions = cnd(repo, request)
        start = ""
        end = ""

        if len(pp) > 2 and '-' in pp[-3:]:
            tail = pp[-3:]
            i = tail.index('-')
            if len(pp) == 3 or i == 2 or not tail[0].isdigit():
                p = str(Path(*pp[:-2]))
                if i == 2:
                    start = tail[1]
                else:
                    end = tail[2]
            else:
                start = tail[0]
                end = tail[2]
                p = str(Path(*pp[:-3]))

        try:
            versions = versions[p]
        except KeyError as e:
            raise HTTPException(status_code=404, detail="Not Found") from e

        try:
            if start:
                start = int(start)
                versions = [v for v in versions if v["time"] >= start]
            if end:
                end = int(end)
                versions = [v for v in versions if v["time"] <= end]
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Non-Integer Time Index") from e

        if self.scope.get("xu60.meta"):
            return JSONResponse({
                "name": p,
                "versions": versions
            })

        res = "\n".join([x["id"] for x in versions]).rstrip()
        return Response(res, media_type='text/plain')


# RESERVED ROUTES: meta, object, versions
routes = [
    Route(f'/{META_ROUTE}', Metadata),
    Mount(f'/{META_ROUTE}',
          routes=[
              Route('/', Metadata),
              Route('/{meta_url:path}', Metadata),
          ]
    ),
    Route(f'/{OBJECT_ROUTE}', Directory),
    Mount(f'/{OBJECT_ROUTE}',
          routes=[
              Route('/', Directory),
              Route('/{object}', Object),
              Route('/{object}/{start:int}/-', Object),
              Route('/{object}/{start:int}/-/{end:int}', Object),
              Route('/{object}/-/{end:int}', Object)
        ]
    ),
    Route(f'/{VERSIONS_ROUTE}', Directory),
    Mount(f'/{VERSIONS_ROUTE}',
          routes=[
              Route('/', Directory),
              Route('/{path_to_file:path}', Versions)
          ]
    ),

    Mount('/', app=StaticFiles(directory=SRV_HOME, html=True)),
]

app = Starlette(debug=True, routes=routes, lifespan=lifespan)
