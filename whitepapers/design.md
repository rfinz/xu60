# the design and demise of xu60

- Link rot
- bit.ly, doi.org, NFTs
- BitTorrent
- Source control(git, mercurial)
- VSCode file timelines
- Hypermedia (the Possiplex, Hypercard, HTTP, HTML, HTMX, HATEOAS, REST)
- IPFS / IPLD, DNSlink
- The Dark Forest internet
- the federated social internet

How does one extend the functionality of static websites in a way that
1. brings them to life?
   - static websites have very little *conversation* to them
   - the distinction between "static" and "dynamic" can be boiled down to this: "static" just means "receding", while dynamic just means "racing to keep up"
   - dynamism *could* be inserted by the *end user*, in fact, this seems to be the design ethos of hypermedia systems
2. requires very little "out of band" information about the nature of the extension
   - no additional protocols
   - no arcane chain of actions
   - mostly human readable by default
   - mostly "self-documented", i.e. an end user can figure out what is going on without reading much documentation
3. doesn't force a particular vision for a particular product or configuration
   - extensible(? what this means I'm not particularly sure, especially if I intend to keep the project under the GPL)
   - as few keywords/reserved words/concepts as possible
   - more options available, but "out of the way": you don't need to know about them in order to access all of the functionality of the extension
   
It seems to me that [htmx](https://htmx.org/) holds a piece of the solution: blur the lines between static and dynamic "web" "site" by making HTML into a ***true***, fully capable, hypertext.
   
The other piece of the solution *may* lay *here*-- early conceptions of hypertext afforded significantly more granular levels of addressing. In the early days of computing this would have required incredibly specific sorts of data structures and algorithms to do it... now we have the compute to work rapidly with basically any text data.

The large jump in compute and network speeds is what allows us to lay down bespoke solutions and instead work directly with existing technologies, bending them *only slightly* with an application layer to accomplish the goal of granular addresses in both computer and human memory.

Almost all [git](https://git-scm.com) hosting HTTP services (e.g. github, gitlab) have simple URLs by which to access the blob of a file that exists in a commit. The URL typically follows a pattern like this: `commit ID/tree element name/tree element name/file name` with as many tree elements as their are directories that the tree needs to traverse to get to our content. This makes sense when one is interacting with code, since the "commit" is the basic unit in which we think about merges, pull requests, code changes, etc. However, the average writer/internet person does not think about a "commit"-- instead they think about versions, timelines, references, pull quotes, and other accoutrements of intellectual work. Although **xu60** strives to be as neutral a technology as possible, the heart of its inspiration lies in attempting to resolve this small gap between a great technology and the totality of its possibility.

To fit the paradigm of git to the deeply intertwingled world of intellectual work (writing, diarizing, archiving, filing, connecting, laying out, reorganizing, historicizing, socializing, etc.) **xu60** exposes an API that pushes the commit ID into the *metadata* layer of the objects, allowing raw objects and their versions to be the basic units of interaction. In this new bent git paradigm, the commit that a file is associated with is less important than the time at which it was authored, and the contents of the file at that point in time. The "commit" becomes a way of auditing/confirming what an archive says about its contents, but becomes less important to the way that files are addressed and accessed.

In **xu60**, if you know an object's ID, you can access it (or ranges of bytes from inside of it) directly (`object_endpoint/object ID/start byte/-/end byte`). If you know an object's name (it's path within the repository) you can query for the IDs of any of its versions (`version_endpoint/path/to/file`). If you need to know more, you can query for the metadata of its name, any object/version, or the repository as a whole. 

Meanwhile, [IPFS](https://ipfs.tech) represents a somewhat mature (if a bit technically opaque) way of content-addressing files across the whole of the entire web, accessible most securely through a locally-running web service that you request the content from. This is a great fit for many of the goals of this project, and in the future if there are spinoff endeavors from **xu60**, we may delegate networking concerns and addressing to the IPFS network. 

However, most static websites are *already* content addressable inside of their own git repositories. Relying on git feels like the lowest barrier to entry. In addition to git's ubiquity, the "commit" does indeed contain information that **xu60** deems to be invaluable: a time stamp. The goal here is not to be able to verify that every single object was authored at the time that the repository purports--but instead that the timings are written into a record that, once mirrored or otherwise distributed, become nearly impossible to re-write without clear evidence of the tampering.

**xu60** is far from the best considered application of hash-based technologies. It does not concern itself too much with trust, truly decentralized management of state, or standardization into sane, efficient protocols.

Instead, the contribution of **xu60** lies in the foregrounding of its non-technical goals and commmitment to the conceptual affordances of hypertext, which may be under-explored at their intersection with afforementioned content-addressable systems and hash-based content verification technologies.

Although the goals of the project are "non-technical," the execution must be rock solid. Response times matter when we use computers, and for **xu60** to be a viable medium for hypertext on the web, apps based on it must render smoothly and behave responsively. Practically, these concerns mean that complex calculations should be cached, roundtrips should be reduced (i.e. the tradeoff of payload size vs. extra HTTP requests should be considered carefully), and datatypes should err. on the side of immediately renderable. Decoding, munging, searching through text, etc. that is left for the client should be kept to a minimum (excepting of course the cases in which that is the *point* of the client). 








