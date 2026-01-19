# xu60
needed now more than ever

**xu60** is a 
- Content-Addressable 
- Hyper Text Transport Protocol 
- Application Programmatic Interface

where hashes and character indexes

define immutable URLs

for re-usable content, (mostly) guaranteed not to rot as a website grows, changes, is edited, or is otherwised enhanced (or regressed)

## scope
1. **xu60** should provide an HTTP server that is simultaneously capable of serving traditional web pages, scripts, and styles alongside whatever content-addressable data an application developer sees fit
2. **xu60** should contain additional functionality for querying document version histories and displaying document metadata such as original paths, edit dates, etc.
3. besides documents, content-addressable document histories, and document/history metadata, **xu60** should remain agnostic to use-case and ship as few features as is plausible
4. **xu60** should virtually never re-code the core algorithms that make its features possible. high-performance versions of virtually every element already exist--**xu60** is a thin application layer built around known technologies. plus I'm dumb
5. the "known technologies" that **xu60** relies on should (wherever possible) already be infrastructurally important to the web and unlikely to disappear or be deprecated with any rapidity
6. **xu60** should be easy to run in a number of configurations to serve a number of applications--hypermedia-ing, mirroring, addressing, serving, distributing, archiving, auditing, etc.


## installation and demo

**xu60** comes with a demo application (built with htmx!! [under construction]) that serves as both a technical demonstration of the server's capabilities, proof-of-concept object browser, and tour of the server's own code.

### source
```sh
# to run xu60 from its source:
git clone https://github.com/rfinz/xu60.git #clone the repository
cd xu60 #navigate into the project
python -m venv env #create a virtual environment
source env/bin/activate #activate the virtual environment
pip install -e . #install required dependencies and the xu60 application
uvicorn xu60:app #run the asgi application -- you may need to install uvicorn separately
# -> the demo should now be available at 127.0.0.1:8000
```

### pypi
```sh
# to run as a package:
pip install xu60[server]
cd <your git repo>
uvicorn xu60:app 
```

# the interface
**xu60** exposes three read-only endpoints for interacting with content-addressed documents.

the **xu60** interface is designed to be agnostic to back-end (not that they are [currently] swappable, but that there is nothing in principle stopping **xu60** from being based on another technology), but the current content-addressable object database is provided by [git](https://git-scm.com).

all "movement" is accomplishable via URL segments. this means that if you want to change the piece of *content* that you are looking at, you should be able to get there in the `path/path/path/path` part of the URL. this leaves the query parameter part of the URL (under development) to freely alter the presentation of said content, plus configure units, encodings, etc.

---

## object
this is the primary affordance of **xu60**: the object API delivers document data based on its content id. it also supports server-side slicing of the document to deliver only requested character ('utf-8') ranges.

### index
#### `/object` 
→ a plaintext listing of all the available objects, an epoch (seconds) timestamp associated with each object's creation, object's reference name (for keeping track of versions), and length.

> ```
> GET /object
>
> object,time,name,length,indices
> 23413cdfecdeb434cd5ae7ce8ea72e71fec1b0b5,1764053925,xu60/main.py,10602,chars
> 7d31564ba2a01c8d75d01ed050a1185280da454c,1764044450,whitepapers/design.md,11802,chars
> 2acac76e44d2ace1cf3f8b395f4fbeeec26c6d50,1764042716,xu60/main.py,9720,chars
> e01a8f3de37189c322812df39dccebae82dac5c9,1763962600,README.md,2635,chars
> .
> .
> . (etc)
> ```

### contents
#### `/object/{object: str}` 
→ return the full contents of the document represented by the content id `object`

> ```
> GET /object/23413cdfecdeb434cd5ae7ce8ea72e71fec1b0b5   # a version of xu60/main.py
>
> """
> Hopefully a single file server.
> """
> import re
> import datetime
> .
> .
> . (etc)
> ```

### slicing
slicing is accomplished by adding a few url segments to the end of your object endpoint. the `-` character allows open ending slicing....you may leave off either the start or end index.

#### `/object/{object: str}/{start: int}/-/{end: int}` 
→ contents between `start` and `end`

#### `/object/{object: str}/{start: int}/-`
→ contents between `start` and the end of the document

#### `/object/{object: str}/-/{end: int}`
→ contents between the beginning of the document and `end`

> ```
> GET /object/23413cdfecdeb434cd5ae7ce8ea72e71fec1b0b5/4/-/6
> 
> Ho
> ```

---

## versions
the `versions` endpoint is the main way to query **xu60** about the presence of other document versions.

### index
#### `/versions`
→ a plaintext listing of all the available objects, an epoch (seconds) timestamp associated with each object's creation, object's reference name (for keeping track of versions), and length. this is currently *identical* to the listing created by the `object` endpoint.

> ```
> GET /versions
>
> object,time,name,length,indices
> 23413cdfecdeb434cd5ae7ce8ea72e71fec1b0b5,1764053925,xu60/main.py,10602,chars
> 7d31564ba2a01c8d75d01ed050a1185280da454c,1764044450,whitepapers/design.md,11802,chars
> 2acac76e44d2ace1cf3f8b395f4fbeeec26c6d50,1764042716,xu60/main.py,9720,chars
> e01a8f3de37189c322812df39dccebae82dac5c9,1763962600,README.md,2635,chars
> .
> .
> . (etc)
> ```

### versions for name
#### `/versions/{name: path}`
→ return all versions for a given name (`name` is a path-like string). versions are listed newest to oldest.

> ```
> GET /versions/xu60/main.py
> 
> a9083f8cce97c1c83473000460f9de3bde35ac82
> 9c6b6c847e6682ec319ad64a0274c6f7ee366472
> c7563b7d2149cb8371647881a2f960b2f6dd544f
> 7d217e22d67e5e30b65ab8554a6866e5be3f004f
> cb80696bc75b9ebc69e7047eca5c6ea4cb15fc53
> 4b424a220ac9410307d0b82635d53bb1759acf2d
> d75af2786adcf34a71d875eba132c6f92048b0b6
> .
> .
> . (etc)
> ```

### time slicing
parallel to the way that the `object` interface allows slicing content by character indexes inside the document, the `versions` interface allows slicing by *second indexes inside of time*.

#### `/versions/{name: path}/{start: int}/-/{end: int}`
→ versions between `start` and `end` (epoch seconds)

#### `/versions/{name: path}/{start: int}/-`
→ versions between `start` and the end of time

#### `/versions/{name: path}/-/{end: int}`
→ versions between the beginning of time and `end`


let's say we want to grab the versions of `xu60/main.py` mentioned in the truncated output of `/versions` above, plus anything newer, just in case there's a new version since this README was written.

> ```
> GET /versions/xu60/main.py/1766035196/-   # notice no end time
> 
> a9083f8cce97c1c83473000460f9de3bde35ac82
> 9c6b6c847e6682ec319ad64a0274c6f7ee366472
> c7563b7d2149cb8371647881a2f960b2f6dd544f
> 7d217e22d67e5e30b65ab8554a6866e5be3f004f
> ```

---

## meta
the `meta` endpoint delivers a more complete set of machine-readable metadata in json format. besides the main meta entrypoint, `/meta` wraps and modifies object and version endpoints. this endpoint is changing rapidly so I am intentionally leaving the documentation more sparse.


### index
#### `/meta` 
→ json containing site-level metadata.

> ```json
> GET /meta
> 
> {
>   "site": "http://127.0.0.1:8000",
>   "truth": "https://github.com/rfinz/xu60.git",
>   "head": "98f6ae10b7c6ad5c7f1e90a76626b4bb0fb0185e",
>   "last_updated": "2025-12-21 22:53:27",
>   "content_id": "sha1",
>   "mirrors": {},
>   "meta": "/meta",
>   "object": "/object",
>   "versions": "/versions"
> }
> ```

### wraps
#### `/meta/{object endpoint}`
→ more metadata about objects

> ```json
> GET /meta/object/23413cdfecdeb434cd5ae7ce8ea72e71fec1b0b5/4/-/6
> 
> {
>   "id": "23413cdfecdeb434cd5ae7ce8ea72e71fec1b0b5",
>   "names": [
>     {
>       "name": "xu60/main.py",
>       "commit_id": "300133b9b17d5bfbed20bb1b589afab61908423f",
>       "time": 1764053925,
>       "message": "probably needs more testing but introducing time slicing!\n"
>     }
>   ],
>   "length": 10603,
>   "indices": "chars",
>   "window": {
>     "start": 4,
>     "end": 6
>   },
>   "previous_version": {
>     "id": "2acac76e44d2ace1cf3f8b395f4fbeeec26c6d50",
>     "changes": [
>       {
>         "from": "8216/-/8217",
>         "to": "8216/-/8243"
>       },
>       {
>         "from": "8281/-/8281",
>         "to": "8281/-/8764"
>       },
>       {
>         "from": "8268/-/8572",
>         "to": "8777/-/8812"
>       },
>       {
>         "from": "8907/-/8907",
>         "to": "8907/-/9549"
>       }
>     ]
>   },
>   "next_version": {
>     "id": "ee1b33e686015ba51b168111d12744abfa7ce1fd",
>     "changes": [
>       {
>         "from": "2142/-/2189",
>         "to": "2142/-/2185"
>       },
>       {
>         "from": "6630/-/6689",
>         "to": "6626/-/6681"
>       },
>       {
>         "from": "7723/-/7763",
>         "to": "7715/-/7751"
>       }
>     ]
>   },
>   "body": "Ho"
> }
> ```

#### `/meta/{versions endpoint}`
→ more metadata about names and versions

> ```json
> GET /meta/versions/xu60/main.py/1766035196/-
> 
> {
>   "name": "xu60/main.py",
>   "versions": [
>     {
>       "id": "a9083f8cce97c1c83473000460f9de3bde35ac82",
>       "commit_id": "48508790c473cfc8cdbd25a2f42d6a2d9e9ea6f5",
>       "time": 1766294358,
>       "message": "being a janitor used to mean something\n"
>     },
>     {
>       "id": "9c6b6c847e6682ec319ad64a0274c6f7ee366472",
>       "commit_id": "3b3d4458bcad078134bc730ca1c622d7a33e90ed",
>       "time": 1766088642,
>       "message": "fix bug, use cache for object requests\n"
>     },
>     {
>       "id": "c7563b7d2149cb8371647881a2f960b2f6dd544f",
>       "commit_id": "f36337f94bc43eb69a986a9f77a82d82dae4a737",
>       "time": 1766083424,
>       "message": "implemented the nobody query finally\n"
>     },
>     {
>       "id": "7d217e22d67e5e30b65ab8554a6866e5be3f004f",
>       "commit_id": "7abef08ae162f53d2f2b042d41e0f8e56b078240",
>       "time": 1766035196,
>       "message": "use bytes if binary data\n"
>     }
>   ]
> }
> ```

## suggested types of **xu60** deployments
- **"[quinish](https://en.wikipedia.org/wiki/Quine_(computing))"**

  a site's git repository and the site itself are one in the same -- **xu60** delivers the contents on the www. The website for this project is itself a quinish [under construction].
  
- **version tracking**

  a site maintains its display layer separate from its content (and outside of **xu60's** purview). The role of **xu60** is to maintain a history of the content, independent of its display details. Alternatively, **ux60** could be used to track changes to a site's display layer, even as the content is so dynamic that "version control" no longer makes sense.
  
- **diff+link**

  use the **xu60** client to visualize changes of the content across time, and transclude and annotate content from external sites. The website for this project [under construction] is itself a quinish sort of diff+link
  
- **indieweb**

  built on top any other type (version tracking, quinish, diff+link) of **xu60** deployment, linking to an object slice on a friend's deployment is adequate indication of a "mention". No need for a "blog roll", scraping your transclusions and links into a central table accomplishes most of that for you.

- **content mirror**

  use **xu60**'s mirroring mechanism to help keep important content on the web. Sites that are listed as full mirrors are automatically cached alongside the primary site contents, and have their objects browseable in an identical manner.
  
  

---

> [!IMPORTANT]
> **xu60** is experimental and unstable :)

---
