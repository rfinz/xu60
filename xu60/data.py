"""
xu60 functionality related to building and maintaining in-memory
data structures
"""

from pygit2 import Repository
from pygit2.enums import SortMode, ObjectType, DiffOption

def cvd(repo, request):
    """
    Construct Version Directory (CVD)
    """
    if str(repo.head.target) in request.app.state.vd:
        # premature optimization type shi -- caching mechanism
        # make sure to cache a seahorse emoji so you don't have to later
        return request.app.state.vd[str(repo.head.target)]

    prev = {}
    vd = {}

    def construct(tree, commit, prefix="", name=""):
        names = []
        for e in tree:
            p = f'{prefix}{name}/{e.name}'[1:]
            if e.id in prev and p in prev[e.id]:
                pass
            else:
                if e.type == ObjectType.BLOB:
                    names += [
                        {"id": e.id,
                         "time": commit.commit_time,
                         "name": p,
                         "length": e.size if e.is_binary else len(e.data.decode('utf-8')),
                         "message": commit.message,
                         "indices": "bytes" if e.is_binary else "chars"
                         }
                    ]
                    if e.id in prev:
                        prev[e.id] += [p]
                    else:
                        prev[e.id] = [p]
                if e.type == ObjectType.TREE:
                    names += construct(e, commit, prefix=prefix, name=f'{name}/{e.name}')

        return names

    for sub in repo.submodules:
        r = sub.open()
        for commit in r.walk(
                r.head.target,
                SortMode.TOPOLOGICAL | SortMode.TIME | SortMode.REVERSE
        ):
            vd[commit.id] = construct(commit.tree, commit, prefix="/" + sub.path)
        r.free()

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
            item = {
                "id": str(t["id"]),
                "commit_id": str(c),
                "time": t["time"],
                "message": t["message"]
            }
            if t["name"] in nd:
                nd[t["name"]] += [item]
            else:
                nd[t["name"]] = [item]

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
                "time": t["time"],
                "message": t["message"]
            }
            if t["id"] in od:
                od[t["id"]] += [item]
            else:
                od[t["id"]] = [item]

    request.app.state.od[str(repo.head.target)] = od
    return od


def changes(v1, v2):
    """
    Get minimal diff for two text blobs.
    """
    c = []
    patch = v1.diff(
        v2,
        flags=DiffOption.PATIENCE|DiffOption.MINIMAL,
        context_lines=0
    )
    total_off = 0
    
    for h in patch.hunks:
        tlines = [l for l in h.lines if l.origin == '+'] # to lines
        flines = [l for l in h.lines if l.origin == '-'] # from lines
        
        if tlines:
            t_soff = len(v1.data[0:tlines[0].content_offset].decode('utf-8'))
            t_eoff = max([len(v1.data[0:t.content_offset].decode('utf-8')) + len(t.content) for t in tlines])
        else:
            t_soff = t_eoff = len(v1.data[0:flines[0].content_offset].decode('utf-8'))

        if flines:
            f_soff = len(v1.data[0:flines[0].content_offset].decode('utf-8'))
            f_eoff = max([len(v1.data[0:f.content_offset].decode('utf-8')) + len(f.content) for f in flines])
        else:
            f_soff = f_eoff = len(v1.data[0:tlines[0].content_offset].decode('utf-8')) - total_off

        print([(l.origin, l.content_offset, l.content) for l in h.lines], total_off)
        total_off += sum([len(t.content) for t in tlines] + [len(f.content) * -1 for f in flines])
        
        c += [{
            "from": f"{f_soff}/-/{f_eoff}",
            "to": f"{t_soff}/-/{t_eoff}"
        }]

    return c


def changeset(obj, repo, request):
    """
    produce changeset for a give BLOB, repo, and request
    """
    od = cod(repo, request)
    nd = cnd(repo, request)
    names = od[obj.id]

    versions = [v["id"] for n in names for v in nd[n["name"]]]
    i = versions.index(obj.id)
    previous_version = {}
    next_version = {}
    if i > 0:
        next_obj = repo.get(versions[i-1])
        next_version["id"] = str(next_obj.id)
        try:
            next_version["changes"] = \
                request.app.state.cd[f"{obj.id}->{next_obj.id}"]
        except KeyError:
            next_version["changes"] = \
                request.app.state.cd[f"{obj.id}->{next_obj.id}"] = \
                changes(obj, next_obj)

    if len(versions) > i + 1:
        prev_obj = repo.get(versions[i+1])
        previous_version["id"] = str(prev_obj.id)
        try:
            previous_version["changes"] = \
                request.app.state.cd[f"{prev_obj.id}->{obj.id}"]
        except KeyError:
            previous_version["changes"] = \
                request.app.state.cd[f"{prev_obj.id}->{obj.id}"] = \
                changes(prev_obj, obj)

    return names, previous_version, next_version


class SuperRepo(Repository):
    """
    Custom pygit2.Repository class that implements functions to
    facilitate working recursively with git submodules.
    """
    def __init__(self, *args, **kwargs):
        Repository.__init__(self, *args, **kwargs)

    def recurse(self, oid, repo=None):
        """
        utility function to descend into submodules, should return
        first match for an oid
        """
        obj = None
        if repo:
            obj = repo.get(oid)
        else:
            obj = super().get(oid)

        for sub in self.submodules:
            if obj:
                return obj
            r = sub.open()
            obj = self.recurse(oid, repo=r)
            r.free()
        return obj


    def get(self, oid):
        """
        recurse into submodules, if present
        """
        return self.recurse(oid)


    def walk(self, *args, **kwargs):
        return super().walk(*args, **kwargs)
