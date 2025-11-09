"""
Hopefully a single file server.
"""
import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.responses import PlainTextResponse, JSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.config import Config

from pygit2 import Repository
from pygit2.enums import SortMode
from pygit2.enums import ObjectType

config = Config(env_prefix='XU60_')
REPO_HOME = Path(config("REPO_HOME", default="."))
SRV_HOME = Path(config("SRV_HOME", default=REPO_HOME))

@asynccontextmanager
async def lifespan(app):
    """
    Lifespan management.
    """
    print('Startup')
    yield
    print('Shutdown')

def cvd(repo, request):
    """
    Construct Version Directory (CVD)
    """
    prev = {}
    vd = {}

    if str(repo.head.target) in request.app.state.vd:
        # premature optimization type shi -- caching mechanism
        return request.app.state.vd[str(repo.head.target)]

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


class Metadata(HTTPEndpoint):
    """
    Metadata for the site
    """
    async def get(self, request):
        host = request.headers['host']
        repo = Repository(REPO_HOME)
        origin = repo.remotes["origin"].url
        head = repo.revparse_single('HEAD')

        if request.path_params.get('meta_url'):
            return JSONResponse({
                "url":request.path_params['meta_url']
            })

        return JSONResponse({
            "site": f'{request.url.scheme}://{host}{request.url.path}',
            "origin": origin,
            "head": str(head.id),
            "last_updated": str(datetime.datetime.fromtimestamp(head.commit_time))
        })


class Directory(HTTPEndpoint):
    """
    Site tree
    """
    async def get(self, request):
        repo = Repository(REPO_HOME)
        res = "object,time,name,length\n"

        vd = cvd(repo, request)

        for c in reversed(vd):
            for t in vd[c]:
                res += f'{t["id"]},{t["time"]},{t["name"]},{t["length"]}\n'

        return PlainTextResponse(res)


class Object(HTTPEndpoint):
    """
    Get object contents from repo
    """
    async def get(self, request):
        repo = Repository(REPO_HOME)
        oid = request.path_params['object']

        start = request.path_params.get('start', 0)
        end = request.path_params.get('end', -1)

        res = repo.get(oid).data
        return PlainTextResponse(res[start:end])


class Versions(HTTPEndpoint):
    """
    Convert file properties to object form.
    """
    async def get(self, request):
        repo = Repository(REPO_HOME)
        p = request.path_params['path_to_file']
        versions = {}

        vd = cvd(repo, request)

        for c in reversed(vd):
            for t in vd[c]:
                if t["name"] in versions:
                    versions[t["name"]] = versions[t["name"]] + [str(t["id"])]
                else:
                    versions[t["name"]] = [str(t["id"])]

        res = "\n".join(versions.get(p,[])).rstrip()
        return PlainTextResponse(res)


# RESERVED ROUTES: meta, object, versions
routes = [
    Route('/meta', Metadata),
    Mount('/meta', routes=[
        Route('/', Metadata),
        Route('/{meta_url:path}', Metadata),
    ]),

    Route('/object', Directory),
    Mount('/object', routes=[
        Route('/', Directory),
        Route('/{object}', Object),
        Route('/{object}/{start:int}/-', Object),
        Route('/{object}/{start:int}/-/{end:int}', Object),
        Route('/{object}/-/{end:int}', Object),
    ]),
    
    Route('/versions', Directory),
    Mount('/versions', routes=[
        Route('/', Directory),
        Route('/{path_to_file:path}', Versions),
    ]),
    
    Mount('/', app=StaticFiles(directory=SRV_HOME, html=True)),
]

app = Starlette(debug=True, routes=routes, lifespan=lifespan)
app.state.vd = {}
