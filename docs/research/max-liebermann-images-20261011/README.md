# Max Liebermann: pictures for 104 paintings and 271 drawings

Completed research and selected production delivery on 11 October 2026 for the
**375 artwork IDs in the user's request**. The earlier catalogue subsequently
grew to 796 works; this image pass retains the original 104-painting,
271-drawing scope.

**Picture sources were located for 366 of 375 works. 227 new images were
uploaded, attached and publicly verified.** Ten existing images were preserved.

| Requested type | New images | Existing images | Now illustrated | Remaining |
| --- | ---: | ---: | ---: | ---: |
| Paintings | 63 | 7 | 70 / 104 | 34 |
| Drawings | 164 | 3 | 167 / 271 | 104 |
| Total | 227 | 10 | 237 / 375 | 138 |

- [Live artist catalogue](https://artlines.org/artists/max-liebermann-q158062)
- [All 375 image results, CSV](image-results.csv): artwork links, museum,
  image-source page and file URLs, rights labels, reasons for gaps, and the
  public Artline image URL where attached.
- [Final production verification](final-verification.json),
  [coverage counts](coverage.json), [file verification](file-verification.json).

## Remaining pictures

- **118 exact image sources are recorded but not attached:** 112 have unresolved
  public/commercial reuse permission, including 25 also needing date evidence;
  another six Berlin drawings have usable source rights but no object-specific
  pre-1956 date bound. Their original unknown dates remain unchanged.
- **11 downloads are held:** one Art Institute of Chicago image returned HTTP
  403; ten Commons originals are on a host that returned HTTP 429. Ordinary
  delayed retries were bounded and the access limits were respected. The
  Strasbourg orphanage painting is among these recorded image links.
- **Nine exact reproductions were not located:** four Hamburg pages contain no
  artwork image, NGA's *Spring* and *Winter* report unavailable images, the Met
  beer-garden drawing has no API image, the Hannover horse study could not be
  distinguished securely from other versions, and Berlin's knee-length
  self-portrait source contains a war-loss placeholder. No placeholder or
  different version was attached.

See [individual missing-image findings](unresolved-findings.json) and the
[six Berlin date reviews](remaining-berlin-date-review.json). Hamburg's own
photograph policy permits private/noncommercial use; selected approved WikiArt
or usable Commons reproductions were used where an exact alternative was found.
Native policy pages and file-level labels are retained in the capture receipts.
These results do not claim complete image coverage.

## Sources and image review

The 227 new files comprise 144 from Staatliche Museen zu Berlin, 27 from Städel,
27 from Wikimedia Commons, 17 from ALBERTINA, six from the Bavarian State Painting
Collections, three from Rijksmuseum and three from WikiArt. File-level labels
are public domain for 221 and CC BY-SA for six. WikiArt's standing user approval
is recorded separately from its actual source labels.

Every delivered image was visually inspected against its object identity,
inventory and source metadata. Photographs preserve the complete supplied frame,
including source frames and margins. Black-and-white source photographs remain
black and white. Recto/verso labels, the questioned-authenticity title
*Badende Knaben (Fälschung?)*, and the chosen side of the Kraków double-sided
painting remain explicit. No AI-generated pictures were used.

All derivatives are proportionally resized JPEGs of at most **99,968 bytes**.
Their hashes and the archived source hashes were checked; all 227 derivative
hashes are distinct. Public storage downloads were checked byte-for-byte before
attachment. The main batch contains 224 images and the separately pinned
[inventory-match followup](followup/verification.json) contains three.

Creation eligibility uses the project's museum-image cutoff of 1955, with
literal dates or documented object acquisition/provenance bounds. The two
[specific date reviews](date-review-overrides.json) retain conflicting or
qualified source evidence without rewriting catalogue dates. An artist's
lifespan alone was not used to invent eligibility or dates.

## Production integrity and evidence

The delivery only added media, image evidence and citations, and set missing
primary images. Before/after checks across all 375 artworks preserved titles,
dates, artist links, holdings, existing media and editorial statuses. Holdings
do not imply current display. All 16 public artist API pages were traversed;
each attachment and the ten original images were verified. The real local
database was never connected to or modified. No deployment or commit was made.

Cloud SQL backups `1791705087192` and `1791705541934` completed successfully
before their respective batches. The first main-batch transaction rolled back
on an HTTPS-only policy-URL constraint; three historic Rijksmuseum Creative
Commons HTTP policy links were normalized to HTTPS, preserving their literal
source values in evidence, before the successful atomic retry.

The runner is [ops/max-liebermann-images-20261011.py](../../../ops/max-liebermann-images-20261011.py).
Selection, visual review, pinned-plan hashes, upload receipts and application
receipts are retained here; `--followup` selects the second batch. Applied stages
are guarded against reapplication. Research captures contain source metadata;
full-resolution image bodies and contact sheets are archived outside Documents
under `~/Library/Application Support/Artline/source-images/` in the two operation
directories. Database snapshots and pinned plans are under the corresponding
`~/Library/Application Support/Artline/backups/` directories.
