"""
Endpoint logic for default asgi/git implentation of xu60
"""

import datetime
from pathlib import Path

from starlette.exceptions import HTTPException
from starlette.endpoints import HTTPEndpoint
from starlette.responses import Response, JSONResponse
from pygit2.enums import ObjectType

from xu60.data import cvd, cnd, changeset


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
        state = request.app.state
        repo = state.repo
        head = repo.revparse_single('HEAD')
        meta = request.path_params.get('meta_url')
        try:
            origin = repo.remotes["origin"].url
        except KeyError:
            origin = "None"

        try:
            if repo.config.get_int("core.repositoryFormatVersion") > 0:
                content_id = repo.config["extensions.objectFormat"]
            else:
                content_id = "sha1"
        except KeyError:
            content_id = "sha1"

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
            "site": f'{request.url.scheme}://{request.url.netloc}{state.base_url}',
            "origin": origin,
            "head": str(head.id),
            "last_updated": str(datetime.datetime.fromtimestamp(head.commit_time)),
            "content_id": content_id,
            "mirrors": state.mirrors,
            "meta": f"/{state.meta_route}",
            "object": f"/{state.object_route}",
            "versions": f"/{state.versions_route}"
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
