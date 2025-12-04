from pygit2.enums import SortMode, ObjectType, DiffOption

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
            p = f'{name}/{e.name}'[1:]
            if e.id in prev and p in prev[e.id]:
                pass
            else:
                if e.type == ObjectType.BLOB:
                    names += [
                        {"id": e.id,
                         "time": commit.commit_time,
                         "name": p,
                         "length": e.size}
                    ]
                    if e.id in prev:
                        prev[e.id] += [p]
                    else:
                        prev[e.id] = [p]
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
            item = {
                "id": str(t["id"]),
                "commit_id": str(c),
                "time": t["time"]
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
                "time": t["time"]
            }
            if t["id"] in od:
                od[t["id"]] += [item]
            else:
                od[t["id"]] = [item]

    request.app.state.od[str(repo.head.target)] = od
    return od


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
        next_version["id"] = str(versions[i-1])
    if len(versions) > i + 1:
        previous_version["id"] = str(versions[i+1])
        previous_version["changes"] = []

        patch = repo.get(versions[i+1]).diff(
            obj,
            flags=DiffOption.PATIENCE|DiffOption.MINIMAL,
            context_lines=0
        )

        for h in patch.hunks:
            tlines = [l for l in h.lines if l.origin == '+'] # to lines
            flines = [l for l in h.lines if l.origin == '-'] # from lines

            if tlines:
                t_soff = tlines[0].content_offset
                t_eoff = tlines[-1].content_offset + len(tlines[-1].content)
            else:
                t_soff = t_eoff = h.lines[0].content_offset

            if flines:
                f_soff = flines[0].content_offset
                f_eoff = flines[-1].content_offset + len(flines[-1].content)
            else:
                f_soff = f_eoff = h.lines[0].content_offset

            previous_version["changes"] = previous_version["changes"] + [{
                "from": f"{f_soff}/-/{f_eoff}",
                "to": f"{t_soff}/-/{t_eoff}"
            }]

    return names, previous_version, next_version
