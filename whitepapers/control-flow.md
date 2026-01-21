# Control Flow

Basic description of the "business logic" inside **xu60**.

## Anatomy of a URL

```python
r"""\A
(?P<meta>/meta)?                         # is it a "meta" URL
(?P<endpoint>/versions|/object)?         # what endpoint is targeted, if any
(?(endpoint)                             # if an endpoint was targeted
  (?P<resource>(?:/[.\w-]+)+?            # look for resource ID/name
  (?=(?:/\d+|/-){2,3}\Z|\Z))             # lookahead to avoid capturing slice
)?
(?(resource)                             # if asking for a resource
  (?P<slice>                             # check for slice component
  (?:/(?P<start>\d+)/)?                  # check for start index
  (?(start)-|/-)                         # match different "-/" for start/no start
  (?:/(?P<end>\d+))?                     # check for end index
)?|\b)                                   # if no resource, only match empty
\Z"""
```

## Mirroring

:tentative:

Mirrors are specified by a source of Truth and a commit from which to load (mostly to ensure integrity if the deployment ever has to be rebuilt). This looks something like this:

`https://github.com/rfinz/xu60.git@98f6ae10b7c6ad5c7f1e90a76626b4bb0fb0185e`

**xu60** will clone the git repo at the specified commit and fail if the commit does not exist. If an `xu60.txt` resource is found in the root of the repository, **xu60** will "mount" the version names under the domain name listed under the "Site" directive. If no `xu60.txt` is present, the repository is presumed to be under regular version control, and the git repository's name is used instead.
