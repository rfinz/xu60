"""
Hopefully a single file server.
"""
import re
import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.responses import Response, JSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.config import Config

import pygit2
from pygit2 import Repository
from pygit2.enums import SortMode, ObjectType


config = Config(env_prefix='XU60_')

REPO_HOME = Path(config("REPO_HOME", default="."))
SRV_HOME = Path(config("SRV_HOME", default=REPO_HOME))
OBJECT_ROUTE = config("OBJECT_ROUTE", default="object")
VERSIONS_ROUTE = config("VERSIONS_ROUTE", default="versions")
META_ROUTE = config("META_ROUTE", default="meta")

DIFFLINE = re.compile(r"\+(\d+),(\d+) ")

@asynccontextmanager
async def lifespan(app):
    """
    Lifespan management.
    """
    print('Startup')
    # double cache size and enable caching for objects under 512KB
    pygit2.settings.cache_max_size(512 * 1024**2)
    pygit2.settings.cache_object_limit(ObjectType.BLOB, 512 * 1024)

    yield

    print(
        'libgit2 cache use: ' \
        f'{pygit2.settings.cached_memory[0]}B of {pygit2.settings.cached_memory[1]}B'
    )
    print('Shutdown')

def cvd(repo, request):
    """
    Construct Version Directory (CVD)
    """
    if str(repo.head.target) in request.app.state.vd:
        # premature optimization type shi -- caching mechanism
        return request.app.state.vd[str(repo.head.target)]

    prev = {}
    vd = {}

    def construct(tree, commit, name=""):
        names = []
        for e in tree:
            if e.id in prev:
                pass
            else:
                if e.type == ObjectType.BLOB:
                    prev[e.id] = e.name
                    p = f'{name}/{e.name}'[1:]
                    names += [
                        {"id": e.id,
                         "time": commit.commit_time,
                         "name": p,
                         "length": e.size - 1}
                    ]
                if e.type == ObjectType.TREE:
                    names += construct(e, commit, name=f'{name}/{e.name}')

        return names

    for commit in repo.walk(
            repo.head.target,
            SortMode.TOPOLOGICAL | SortMode.TIME | SortMode.REVERSE
    ):
        vd[commit.id] = construct(commit.tree, commit)

    request.app.state.vd[str(repo.head.target)] = vd
    return vd

def cnd(repo, request):
    """
    Construct Name Directory (CND)
    """

    if str(repo.head.target) in request.app.state.nd:
        return request.app.state.nd[str(repo.head.target)]

    nd = {}
    vd = cvd(repo, request)

    for c in reversed(vd):
        for t in vd[c]:
            if t["name"] in nd:
                nd[t["name"]] = nd[t["name"]] + [str(t["id"])]
            else:
                nd[t["name"]] = [str(t["id"])]

    request.app.state.nd[str(repo.head.target)] = nd
    return nd

def cod(repo, request):
    """
    Construct Object Directory (COD)
    """

    if str(repo.head.target) in request.app.state.od:
        return request.app.state.od[str(repo.head.target)]

    od = {}
    vd = cvd(repo, request)

    for c in reversed(vd):
        for t in vd[c]:
            item = {
                "name": t["name"],
                "commit_id": str(c),
                "time": t["time"]
            }
            if t["id"] in od:
                od[t["id"]] = od[t["id"]] + [item]
            else:
                od[t["id"]] = [item]

    request.app.state.od[str(repo.head.target)] = od
    return od

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
        repo = Repository(REPO_HOME)
        origin = repo.remotes["origin"].url
        head = repo.revparse_single('HEAD')
        meta = request.path_params.get('meta_url')

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
            "last_updated": str(datetime.datetime.fromtimestamp(head.commit_time))
        })


class Directory(HTTPEndpoint):
    """
    Site directory
    """
    async def get(self, request):
        """
        Send version directory, one entry per blob object in the tree.
        """
        repo = Repository(REPO_HOME)
        res = "object,time,name,length\n"

        vd = cvd(repo, request)
        json = []

        for c in reversed(vd):
            for t in vd[c]:
                if self.scope.get("xu60.meta"):
                    t["id"] = str(t["id"])
                    json += [t]
                else:
                    res += f'{t["id"]},{t["time"]},{t["name"]},{t["length"]}\n'
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
        repo = Repository(REPO_HOME)
        oid = request.path_params['object']
        obj = repo.get(oid)

        start = request.path_params.get('start', 0)
        end = request.path_params.get('end', obj.size - 1)

        body = obj.data[start:end]

        if self.scope.get("xu60.meta"):
            od = cod(repo, request)
            nd = cnd(repo, request)
            names = od[obj.id]

            versions = [v for n in names for v in nd[n["name"]]]
            i = versions.index(oid)
            changes = []
            if len(versions) > i + 1:
                patch = repo.get(versions[i+1]).diff(obj)
                for h in patch.hunks:
                    m = DIFFLINE.search(h.header)
                    startline = int(m[1]) - 1
                    numlines = int(m[2])

                    lines = obj.data.splitlines(keepends=True)
                    prevbytes = sum(len(l) for l in lines[:startline])
                    changebytes = sum(len(l) for l in lines[startline:startline+numlines])
                    changes += [f"{prevbytes}/-/{prevbytes + changebytes}"]

            return JSONResponse({
                "id": str(obj.id),
                "names": names,
                "body": body.decode('utf-8'),
                "length": obj.size - 1,
                "window": {"start": start, "end": end},
                "changes": changes
            })
        return Response(body, media_type='text/plain')


class Versions(HTTPEndpoint):
    """
    Convert file properties to object form.
    """
    async def get(self, request):
        """
        Send version IDs in reverse order (newest first)
        """
        repo = Repository(REPO_HOME)
        p = request.path_params['path_to_file']

        versions = cnd(repo, request)

        if self.scope.get("xu60.meta"):
            return JSONResponse({
                "name": p,
                "versions": versions.get(p, [])
            })

        res = "\n".join(versions.get(p,[])).rstrip()
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
app.state.vd = {} # VERSIONS DIRECTORY
app.state.od = {} # OBJECT DIRECTORY
app.state.nd = {} # NAME DIRECTORY
