"""
Hopefully a single file server.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from pygit2 import Repository
from pygit2.enums import SortMode
from pygit2.enums import ObjectType

REPO_HOME = Path(os.environ.get("HYPERHYPER_REPO_HOME", "."))
SRV_HOME = Path(os.environ.get("HYPERHYPER_SRV_HOME", REPO_HOME))

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

def metadata(request):
    return PlainTextResponse("metadata")

def directory(request):
    """
    Site tree
    """
    repo = Repository(REPO_HOME)
    res = "object,time,name,length\n"

    vd = cvd(repo, request)

    for c in reversed(vd):
        for t in vd[c]:
            res += f'{t["id"]},{t["time"]},{t["name"]},{t["length"]}\n'

    return PlainTextResponse(res)

def obj(request):
    """
    Get object contents from repo
    """
    repo = Repository(REPO_HOME)
    oid = request.path_params['object']

    start = request.path_params.get('start', 0)
    end = request.path_params.get('end', -1)

    res = repo.get(oid).data
    return PlainTextResponse(res[start:end])

def vers(request):
    """
    Convert file properties to object form.
    """
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
    Route('/meta', metadata),
    Route('/meta/', metadata), # kindness is virtue
    Route('/meta/{meta_url:path}', metadata),
    Route('/object', directory),
    Route('/object/', directory), # kindness is virtue
    Route('/object/{object}', obj),
    Route('/object/{object}/{start:int}/-', obj),
    Route('/object/{object}/{start:int}/-/{end:int}', obj),
    Route('/object/{object}/-/{end:int}', obj),
    Route('/versions', directory),
    Route('/versions/', directory), # kindness is virtue
    Route('/versions/{path_to_file:path}', vers),
    Mount('/', app=StaticFiles(directory=SRV_HOME, html=True)),
]

app = Starlette(debug=True, routes=routes, lifespan=lifespan)
app.state.vd = {}
