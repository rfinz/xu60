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
