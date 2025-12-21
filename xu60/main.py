"""
Hopefully a server spread over not too many files.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.config import Config

import pygit2
from pygit2.enums import ObjectType

from xu60.data import SuperRepo
from xu60.endpoints import Metadata, Directory, Versions, Object

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

    # Initialize constants
    app.state.meta_route = META_ROUTE
    app.state.versions_route = VERSIONS_ROUTE
    app.state.object_route = OBJECT_ROUTE

    # Initialize state
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
