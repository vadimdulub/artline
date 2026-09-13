# Two Monet images for existing Joconde review records

Both images were saved locally, uploaded to Google Storage and attached to the
matching local and cloud artwork records. `verification-final.json` reports two
verified images, 131,322 bytes in total, a maximum of 97,776 bytes, and no errors.
All non-media artwork metadata and creator links remained unchanged. Neither
artwork was published or given a new accepted holding assertion.

| Existing Joconde object | Accession | Artwork | File evidence |
| --- | --- | --- | --- |
| 000PE003943 | RF 1963 3 | Camille sur son lit de mort, 1879 | [Commons reproduction](https://commons.wikimedia.org/wiki/File:Claude_Monet,_1879,_Camille_sur_son_lit_de_mort,_oil_on_canvas,_90_x_68_cm,_Mus%C3%A9e_d%27Orsay,_Paris.jpg) |
| 000PE003970 | RF 1674 | Carrières-Saint-Denis, 1872 | [Commons reproduction](https://commons.wikimedia.org/wiki/File:Carrieres-Saint-Denis-1872.jpg) |

Selection was limited to these two already identified catalogue objects. Each
current Commons page explicitly names its Joconde ID, Musée d'Orsay accession,
Claude Monet, title and creation year, and carries a file-level Public Domain
Mark. The supplied title `Camille sur son lit de mort` is retained; the Commons
variant includes `Monet`. The exact accession and Joconde identifiers reconcile
that variant without changing catalogue metadata.

Full HTML snapshots with retrieval timestamps and SHA-256 are retained under
`metadata/joconde-commons`. Before downloading, the adapter parses the artwork
fields and the file's license templates, matches the exact museum reference and
accession, and pins the original image URL and published SHA-1. The original
downloads matched those SHA-1 values. Both compressed derivatives were visually
inspected. The rights evidence retains the page URL and full source snapshot.

The Commons API returned HTTP 403; public file-description HTML remained
accessible and supplied the necessary identity, rights and checksum evidence.
No authentication change was needed.

A third lead, [Study of a Figure Outdoors](https://commons.wikimedia.org/wiki/File:Study_of_a_Figure_Outdoors.jpg),
was rejected: its description/category says facing right while its structured
depiction says facing left, and the file page lacks the exact Joconde/accession
reference required here. No image from that lead was downloaded or attached.

Six offline rejection checks on copies of the captured evidence verified that
altered Joconde IDs, public-domain labels and original checksums are rejected.
The shared research attachment identity tests also cover changes to immutable
research provenance. No test database or real-catalogue fixtures were created.

Run with `ops/enrich-joconde-commons-images.py select|apply|verify --run
docs/research/image-expansion-20260913-joconde-commons`. The guarded attachment and
read-only verification reuse `ops/enrich-research-images.py`, with a separately
scoped Joconde identity query and Commons evidence validator.
