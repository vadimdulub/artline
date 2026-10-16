# Event illustrations → Artline artworks — 12 October 2026

The user requested that artwork illustrations in historical events use Artline's
catalogue pictures and open the corresponding artwork, starting with January
Suchodolski's **Battle of San Domingo**.

The API and web release is deployed and verified in production. No commit was made.
Live example: <https://artlines.org/events?event=event-q689128>.
Release receipt: `docs/deployment-20261012-event-artworks.json`.
Preview: <http://127.0.0.1:3158/events?event=event-q689128>. This isolated preview
reads the production catalogue through a connection forced read-only and starts
the API with migrations disabled. The real local catalogue remains unchanged.

## Result and review scope

- All **3,922** event-image manifest entries were audited. All 3,922 local files
  decoded successfully; their sizes, dimensions and SHA-256 hashes are recorded.
- Existing captured Commons metadata covered 3,920 entries. Source-file and
  artwork-authority matching was followed by creator-scoped review of 668 event
  illustrations, 363 artists and 38,910 catalogue/creator rows. Perceptual hashes
  of 17,711 available local catalogue files generated candidates, not approvals.
- **75 event illustrations were visually reviewed**, including alternate
  catalogue candidates where necessary. This does not claim visual inspection
  of every file in the manifest.
- **70 event illustrations resolve to 68 distinct catalogue artworks**: 67
  existing works and the one new Suchodolski record described below. Each of the
  70 destinations returned its expected artwork and current primary image; every
  served production image matched the corresponding local file's SHA-256.
- **3,847 entries remain unmatched** and five candidate event matches are held.
  Existing illustrations remain for those entries. The user approved deploying this behavior; unmatched maps/documents/photos
  remain visible with their existing credits. No speculative artwork link was supplied.

The five holds are two uses of the Ourique painting with a holding/version
conflict, a watermarked catalogue reproduction of Gérôme's Christian martyrs,
the Bar-le-Duc/Honnecourt title/image discrepancy, and a Nyborg print whose
source and catalogue describe different physical impressions. These holds do
not change any existing catalogue record, media attachment or event picture.

## Battle of San Domingo

The old event illustration was not an artwork record. Searches checked the
artist, alternate titles, source-file citations and Wikidata artwork identity.
The [Polish Army Museum's own page](https://muzeumwp.pl/losy-mazurka/) identifies
the painting, artist, oil-on-canvas medium, 1845 date and museum collection.
The existing reviewed Commons reproduction and its public-domain label were
retained byte-for-byte. Its 92,991-byte derivative was individually viewed,
uploaded create-only, and verified through public delivery before attachment.

One production **review** artwork was added under the user's catalogue/image
authorization, with the existing artist, two citations, the artwork's Wikidata
identifier, media rights evidence and audit history. No existing catalogue rows
were modified. No museum institution, exhibition or current-display assertion
was invented. Museum holding information is recorded as sourced text.

- Artwork ID: `31b12ec9-2abf-5f56-9d20-531d1e178f2b`
- Slug: `event-artwork-q131622945`
- [Live artwork record](https://artlines.org/artists/january-suchodolski-q1259182/works/31b12ec9-2abf-5f56-9d20-531d1e178f2b)
- Event: `event-q689128` / Haitian Revolution
- Caption retained: `Battle of San Domingo · later painting, 1845`

A direct Commons request returned 403 during this pass. It was not retried;
the access hold is recorded, and already captured source metadata and the
existing reviewed derivative were used. No provider restriction was bypassed.

## Implementation and verification

`events/artwork-selection.json` binds the reviewed event/source pair to a unique
artwork slug. The Go resolver queries only those slugs for the bounded returned
page, then reads current primary media, credits and internal destination IDs.
The slug index is used in both catalogues. There are no per-event SQL requests,
global artwork-enrichment joins, catalogue mutations or new schema requirements
in the request path. No 10-million-row load-test claim is made.

Archived/excluded works, unavailable primary media and unsafe image paths do not
fall back to stale independent copies after a reviewed catalogue binding exists.
Missing production-only works are omitted in the read-only local catalogue.
Artist-linked works open their existing artwork page; two records without an
active artist link open the existing catalogue artwork drawer. No new page
family was created. The event's historical relationship and dates remain
separate from the later artwork date. Source and licence links remain available.

The resolver is shared by event details/lists, bookmarks and new study snapshots.
Existing study snapshots were not rewritten. Both the event image and caption
link internally, and the caption remains usable when an image fails to load.

Validation passed:

- Go unit suites: `internal/events`, `internal/member`, `internal/httpapi`.
- SQL VALUES cases inside a read-only transaction: active review records,
  archived works, missing media, post-1970 works and unsafe media paths.
- Read-only resolution: all **70/70** selections in production; 36 existing
  matches were available locally before the final production-only addition.
- Three EventDrawer interaction tests, focused ESLint and TypeScript checks.
- Browser: 1440px desktop and 390px mobile; actual artwork image loaded,
  image/caption navigation, keyboard activation and Back restored the event.
  No page errors, drawer overflow or axe violations. Creatorless destination
  verified separately in the existing artwork drawer.

Full evidence, the 3,922-row JSON/CSV ledger, screenshots, source captures,
verification receipts and task scripts are retained under:

`~/Library/Application Support/Artline/source-metadata/event-artworks-20261012/`

The single-record production preimage/plan/postimage are under:

`~/Library/Application Support/Artline/backups/event-artworks-20261012/`

`summary.json` gives counts and release state; `evidence-sha256.json` pins the
retained evidence files. No assets or unrelated workspace changes were removed.

## Production release

The API preserves the generation-pinned `all-performance-1012-v1` production
baseline. The web release was rebased onto `fullview-colors-1012-v1` when a
concurrent deployment changed the viewer. The current viewer, palette and
exhibition changes are preserved. Only the
15 reviewed event-artwork files were overlaid. Candidate and live checks resolved
all 70 selections, compared artwork IDs/current media and public image bytes,
and confirmed four unmatched/held examples retained their existing pictures.
Desktop and mobile checks covered internal navigation, loaded images, Back,
overflow, keyboard activation and accessibility. No account or catalogue writes
were made for deployment. One unrelated book-limit test failure was reproduced
on the exact baseline and recorded; all other affected-package tests passed.

Example sheet: `~/Library/Application Support/Artline/source-metadata/`
`event-artworks-20261012/unmatched-examples.html` (and `.png`).
