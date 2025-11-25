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
> object,time,name,length
> 23413cdfecdeb434cd5ae7ce8ea72e71fec1b0b5,1764053925,xu60/main.py,10602
> 7d31564ba2a01c8d75d01ed050a1185280da454c,1764044450,whitepapers/design.md,11802
> 2acac76e44d2ace1cf3f8b395f4fbeeec26c6d50,1764042716,xu60/main.py,9720
> e01a8f3de37189c322812df39dccebae82dac5c9,1763962600,README.md,2635
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
> object,time,name,length
> 23413cdfecdeb434cd5ae7ce8ea72e71fec1b0b5,1764053925,xu60/main.py,10602
> 7d31564ba2a01c8d75d01ed050a1185280da454c,1764044450,whitepapers/design.md,11802
> 2acac76e44d2ace1cf3f8b395f4fbeeec26c6d50,1764042716,xu60/main.py,9720
> e01a8f3de37189c322812df39dccebae82dac5c9,1763962600,README.md,2635
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
> 23413cdfecdeb434cd5ae7ce8ea72e71fec1b0b5
> 2acac76e44d2ace1cf3f8b395f4fbeeec26c6d50
> 9c0229c95a31e68b2ee462144958d5cd8b086bbc
> 4f447767d9769b488b5c8f09cf9aac8e3a63199c
> 618c18287da9a58ab788f576489bc5e1fb5fb17b
> 41448625864ff4b3e0893342d941972213a6392b
> aeddd83401a4d616fed2d44b63c2ffb15c1e1d6b
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
> GET /versions/xu60/main.py/1764042716/-   # notice no end time
> 
> ee1b33e686015ba51b168111d12744abfa7ce1fd
> 23413cdfecdeb434cd5ae7ce8ea72e71fec1b0b5
> 2acac76e44d2ace1cf3f8b395f4fbeeec26c6d50
> ```

oh yeaaaa actually I did make a bugfix while writing this (ee1b33e686015ba51b168111d12744abfa7ce1fd)

---

## meta
the `meta` endpoint delivers a more complete set of machine-readable metadata in json format. besides the main meta entrypoint, `/meta` wraps and modifies object and version endpoints. this endpoint is changing rapidly so I am intentionally leaving the documentation more sparse.


### index
#### `/meta` 
→ json containing site-level metadata.

> ```
> GET /meta
>
> {
>   "site": "http://127.0.0.1:8000/meta",
>   "origin": "git@github.com:rfinz/xu60.git",
>   "head": "49d4b0e9e2fce503f37c925b5b263b02ca03299e",
>   "last_updated": "2025-11-25 21:06:42",
>   "meta": "/meta",
>   "object": "/object",
>   "versions": "/versions"
> }
> ```

### wraps
#### `/meta/{object endpoint}`
→ more metadata about objects

> ```
> GET /meta/object/23413cdfecdeb434cd5ae7ce8ea72e71fec1b0b5/4/-/6
> ```

#### `/meta/{versions endpoint}`
→ more metadata about names and versions

> ```
> GET /meta/versions/xu60/main.py/1764042716/-
> ```

---

> [!IMPORTANT]
> **xu60** is experimental and unstable :)

---
