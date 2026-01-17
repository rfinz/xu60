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
- HTTP range requests

## The Questions

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

It seems to me that [htmx](https://htmx.org/) holds a piece of the solution: blur the lines between static and dynamic "web" "site" by making HTML into a ***true***, fully capable hypertext.
   
The other piece of the solution *may* lay *here*-- **xu60** harkens back to early conceptions of hypertext that afforded significantly more granular levels of addressing. In the early days of computing this would have required incredibly specific sorts of data structures and algorithms, but now we have the compute to work rapidly with basically any text data.

The large jump in compute and network speeds allows us to lay down bespoke solutions and instead work directly with existing technologies, bending them *only slightly* (with an application layer) to accomplish the goal of granular addresses in both computer and human memory.

### git

Almost all [git](https://git-scm.com) hosting HTTP services (e.g. github, gitlab) have simple URLs by which to access the blob of a file that exists in a commit. The URL typically follows a pattern like this: `commit ID/tree element name/tree element name/file name` with as many tree elements as their are directories that the tree needs to traverse to get to our content. This makes sense when one is interacting with code, since the "commit" is the basic unit in which we think about merges, pull requests, code changes, etc. However, the average writer/internet person does not think about a "commit"-- instead they think about versions, timelines, references, pull quotes, and other accoutrements of intellectual work. Although **xu60** strives to be as neutral a technology as possible, the heart of its inspiration lies in attempting to resolve this small gap between a great technology and the totality of its possibility.

To fit the paradigm of git to the deeply intertwingled world of intellectual work (writing, diarizing, archiving, filing, connecting, laying out, reorganizing, historicizing, socializing, etc.) **xu60** exposes an API that pushes the commit ID into the *metadata* layer of the objects, allowing raw objects and their versions to be the basic units of interaction. In this new bent git paradigm, the commit that a file is associated with is less important than the time at which it was authored, and the contents of the file at that point in time. The "commit" becomes a way of auditing/confirming what an archive says about its contents, but becomes less important to the way that files are addressed and accessed.

In **xu60**, if you know an object's ID, you can access it (or ranges of bytes from inside of it) directly (`object_endpoint/object ID/start byte/-/end byte`). If you know an object's name (it's path within the repository) you can query for the IDs of any of its versions (`version_endpoint/path/to/file`). If you need to know more, you can query for the metadata of its name, any object/version, or the repository as a whole. 

### inter-planetary file system

Meanwhile, [IPFS](https://ipfs.tech) represents a somewhat mature (if a bit technically opaque) way of content-addressing files across the whole of the entire web. It is accessible most securely through a locally-running web service through which you request the content you need. This is a good fit for many of the features of this project, and in the future **xu60** may delegate some networking concerns and addressing to the IPFS network. 

However, most static websites are *already* content addressable inside of their own git repositories. Relying on git feels like the lowest barrier to entry. In addition to git's ubiquity, the "commit" does indeed contain information that **xu60** deems to be invaluable: a time stamp. The goal here is not to be able to verify that every single object was authored at the time that the repository purports--but instead that the timings are written into a record that, once mirrored or otherwise distributed, become nearly impossible to re-write without clear evidence of the tampering.

### **xu60**, hashing, and hypertext

**xu60** is far from the best considered application of hash-based technologies. It does not concern itself too much with trust, truly decentralized management of state, or standardization into sane, efficient protocols.

Instead, the contribution of **xu60** lies in the foregrounding of its non-technical goals and commmitment to the conceptual affordances of hypertext, which may be under-explored at their intersection with afforementioned content-addressable systems and hash-based content verification technologies.

Although the goals of the project are "non-technical," the execution must be rock solid. Response times matter when we use computers, and for **xu60** to be a viable medium for hypertext on the web, apps based on it must render smoothly and behave responsively. Practically, these concerns mean that complex calculations should be cached, roundtrips should be reduced (i.e. the tradeoff of payload size vs. extra HTTP requests should be considered carefully), and datatypes should err. on the side of immediately renderable. Decoding, munging, searching through text, etc. that is left for the client should be kept to a minimum (excepting of course the cases in which that is the *point* of the client). 

The choice to champion hypertext and use other hypermedia technologies in the demonstration of **xu60** is somewhat at odds with the fact that **xu60** *does not render arbitrary hypermedia* and is intended to work with non-hypermedia repositories as well. The approach of bare **xu60** clearly violates certain REST principles as well as a constraint from the authors of [htmx](https://htmx.org):

> #### [Scripting for Hypermedia](https://hypermedia.systems/client-side-scripting/#scripting-for-hypermedia)
>Borrowing from Roy Fielding’s notion of “constraints” defining REST, we offer two constraints of hypermedia-friendly scripting. You are scripting in an HDA-compatible manner if the following two constraints are adhered to:
> - *The main data format exchanged between server and client must be hypermedia, the same as it would be without scripting.*
> - Client-side state, outside the DOM itself, is kept to a minimum.

(emphasis mine)

The central tension is that a complete hypermedia *reveals its own affordances* to a user; non-hypermedia content cannot speak for itself in the same way. The question for **xu60** is this: *what is the minimum viable data API that allows arbitrary text content to, at least in some sense, __become__ hypermedia?*

I think to  power through this question we can to look at other implementations of hypermedia. In a "[xanalogical](https://www.xanadu.com.au/ted/XUsurvey/xuDation.html)" hypertext, the display of of the document contents is somewhat separated from the concerns of content order, durable linking, and transclusion (the display of contents from documents elsewhere on the web). That's not to say the display of the document and the revelation of hypermedia affordances is unimportant to a xanalogical hypermedia: much to the contrary. Xanalogical hypertext demands very specific guarantees about the presentation and (and especially) interactivity of its affordances, and as such strips away the server's role in presentation entirely, offloading the role of presentation to a well specified client.

>    Project Xanadu, the original hypertext project, is often misunderstood as an attempt to create the World Wide Web.
>
>    It has always been much more ambitious, proposing an entire form of literature where links do not break as versions change; where documents may be closely compared side by side and closely annotated; where it is possible to see the origins of every quotation; and in which there is a valid copyright system-- a literary, legal and business arrangement-- for frictionless, non-negotiated quotation at any time and in any amount.  The Web trivialized this original Xanadu model, vastly but incorrectly simplifying these problems to a world of fragile ever-breaking one-way links, with no recognition of change or copyright, and no support for multiple versions or principled re-use.  Fonts and glitz, rather than content connective structure, prevail.
>
>    Serious electronic literature (for scholarship, detailed controversy and detailed collaboration) must support bidirectional and profuse links, which cannot be embedded; and must offer facilities for easily tracking re-use on a principled basis among versions and quotations.
>
>    Xanalogical literary structure is a unique symmetrical connective system for text (and other separable media elements), with two complementary forms of connection that achieve these functions-- survivable deep linkage (content links) and recognizable, visible re-use (transclusion).  Both of these are easily implemented by a document model using content lists which reference stabilized media.
>
>    This system of literary structure offers uniquely integrated methods for version management, side-by-side comparison and visualizable re-use, which lead to a radically beneficial and principled copyright system (endorsed in principle by the ACM).  Though dauntingly far from the standards which have presently caught on, this design is still valid and may yet find a place in the evolving Internet universe.

(from Project Xanadu, document linked above -- Copyright Theodor Holm Nelson)

There is an interesting line of investigation here, I think, because the data model *always lives somewhere*. Regardless of whether it lives entirely in the users head (think a pile of files with mostly random names), or is well specified in a database (every bit of binary with its narrow classification), or somewhere in between (think basic OS primitives - files, directories, and a little TLC using them correctly)... when someone goes to retrieve data and *use* it, the data model materializes-- at least momentarily. In a Roy Fielding / htmx version of hypermedia, the data model lives behind the scenes, mostly invisible to the end user. What is exposed to the end user is all the available actions and states. In a xanalogical hypermedia there is little if any idea of an application that could have actions and states. Instead the idea is to render to the user as much of the data model as is tolerable, providing *obvious* affordances for exploring said data. The model *is* the media, in some sense. And the media is *always* parallel lines of thinking and the way that they're interwoven. This paradigm works extraordinarily well for capturing the intellectual tasks of writing, revising, referencing, placing into context, etc--but does not generalize in the same way that a data-model agnostic hypermedia does.

### stating the obvious

If it's not already obvious, **xu60** is an attempt to build web affordances on top of stabilized media and character-level addressing: the basic requirements of the Original Hypertext Project. But, by creating a standard interface for the World Wide Web (and fleshing out a surface for scriptable document discovery) we enable the fonts, glitz, and front end experience that our current hypermedia universe relies on. **xu60** attempts to strike a (better?) balance between the various conceptions of hypermedia. I believe that *if* this technology is *easy* to use it will have many applications across social media, academic writing, journalism, preservation/archival, and distributed digital systems.

This is not a particularly novel idea, and I am not very smart. A quick glance at one of Ted Nelson's more recent [youtube videos](https://www.youtube.com/watch?v=72M5kcnAL-4) (that I am just now glancing at, FFS) reveals that 8+ years ago folks were already putting together the pieces and understanding that IPFS, version control, and certain blockchain technologies solve the problem of stabilized, versioned content.

The question, then, remains as above: *what is the minimum viable data API that allows arbitrary text content to, at least in some sense, __become__ hypermedia?*


## The Answers?

In Ted Nelson's PhD. Dissertation, "The Philosophy of Hypertext" he calls out:
> - INTERCOMPARISON
> - VERSIONS
> - MARGINAL NOTES
> - DIFFERENT DOCUMENTS

and

> - PARALLEL DOCUMENTS

as the substructed elements of his conception of hypertext. Specifically, "PARALLEL DOCUMENTS" supersedes the other list items as the primary technological concern. Looking at this list, and thinking about git's capabilities....I see a problem of presentation, not a problem of technical capability. 

Ted (can i call u ted) specifically calls out modern version control software as containing processes that mirror, in some way, his original ideas (though he is just as quick to remind the reader that the interface of version control is arcane and hardly targeted at a general audience or an audience of creatives). Because of this it is unsurprising that a view logic layer built on top of git would be able to provide the majority of infrastructure that **xu60** requires. If there is a "curse" of Xanadu® it may be this: during the only time period in which it was being actively developed, the technical concerns dominated the development efforts. Datastructures, addressing systems, windowing....all these seem to have engaged developer efforts for many years. In this, the year *End of 2025*, compute has rendered most of these concerns immanently solvable (though not without value, as Xanadu® design documents have proven to be delightful companions throughout the implementation process). Instead, we have low level protocols mapped and identified, and it is now up to developers to harness those protocols in service of truly distributed, transpointable, and stabilized, documents.

### narcissism of small differences

Where Ted's design had [tumbler addresses](https://web.archive.org/web/20021230190017/http://udanax.com/green/febe/tumblers.html) (a sort of numeric cataloging of the web, somewhere between IP addresses, the Dewey Decimal System, and Semantic Versioning--**xu60** relies on a mixture of DNS and content addressing. Where Ted's clients would have no choice but to transclude data from it's source, **xu60** relies on asynchronous loads in standard web pages, that are vetted by the server user to be appropriate. It is a far cry from the "every client must be xanalogical" future that Ted believed in, but it does have many distinct advantages, mainly ones that Ted has begun to embrace with projects such as the mostly defunct "perma.pub", that collected text sources from across the web in order to provide a plausible platform for the distribution of "xanadocs".

**xu60** relies on existing web technologies as the *distribution* layer, and relies on html as the *markup* that other text formats get transpiled to, but it attempts to re-work the form that intra-website linking takes, as well as providing a relatively transparent way of mirroring and validating other forms of text content.

### why?

It seems like the web has mostly lost the thread. Modern websites are applications delivered via HTTP, not shining examples of hypertext. Trendy knowledge management tools tout two-way linking but seem to ignore where the value comes from when tracing a thought to its original source. Distributed protocols are amazing but the opacity of the systems that employ them leave an enormous chasm between them and lay-users that is easily filled with grift and magical thinking. AI is simultaneously amazing and underwhelming--the most expensive and least accurate library ever published--but at least it's charming. It seems like we're learning all the wrong lessons over and over and over again. So maybe a better question is why not? Why wouldn't we want to be able to access character spans from any content-addressable source on the web?

We also find ourselves at a critical moment when the town square has disintegrated. There are some interesting conversations in private venues and worthwhile newsletters delivered to our inboxes, but much of what made web1/web2/web3 charming and connective is gone. Social media is a hell-scape and much of what remains is just group chats and vague gesturing.

### un/intended consequences

1. Sites hosted with **xu60** are censorship resistant. The website and its repository are one and the same--backing up the contents is as simple as cloning the repo and mirroring it elsewhere. **xu60** directory pages contain the content ids of every object in the tree--it's trivially easily to confirm that the site has been faithfully reproduced.

2. **xu60** sites are discoverable. The presence of a `xu60.txt` well-known file in the repository is easily detectable via the built-in search functions of any widely used code forge. This discoverability doesn't mean that the site isn't slop, and *eventually* simplistic search may not suffice, but basic discoverability on large platforms is enough for now. The presence of `xu60.txt` in the same location on the live site is a positive indicator that conventions and protocols are being respected.

3. **xu60** is exclusive. Large database-driven applications *could* have associated **xu60** sites, but the purpose is largely different at that point (remember how I said **xu60** wouldn't force a vision of a particular product or process and then almost immediately started describing my preferred product and processes? I had forgotten).

4. **xu60** doesn't need adoption to be useful. Even if there are only ever a few *live* instances, **xu60** can index and transclude any content from git repositories anywhere on the web that are accessable via HTTP.

5. **xu60** doesn't rely on notifications. Want to see if someone is transcluding your site? Do a string search for your repository name on the major code forges, or check the transclusion stats on your live site. In the age of codebots this is eminently scriptable.
