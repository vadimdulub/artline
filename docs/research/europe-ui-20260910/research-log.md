# European collection wave and large-catalogue UI — 10 September 2026

## Delivered data

| Official source | Metadata examined | Selected records | New artworks | Exact existing matches | New local images |
| --- | ---: | ---: | ---: | ---: | ---: |
| Statens Museum for Kunst, Copenhagen | 5,096 | 894 | 888 | 6 | 80 |
| Rijksmuseum, Amsterdam | 41 | 24 | 24 | 0 | 0 |
| Total | 5,137 | 918 | 912 | 6 | 80 |

The local catalogue now contains **105,633 artworks**, including 14,649
paintings, 32,005 drawings, 58,974 prints and five frescoes; 5,315 artist
authorities; 294 institution/collection records; and 310 media records. The
institution count does not mean 294 independently verified physical museums.
No new artist authority was invented. All 918 source-linked works remain in
review and have creation intervals ending by 1970. No artwork was published,
and there are still no current-display assertions.

SMK now has 894 local catalogue works, including 80 illustrated works.
Rijksmuseum now has 25 local works, including its earlier Monet record.

## Sources and limits

- [SMK official API documentation](https://api.smk.dk/api/v1/docs/): captured
  51 pages of the `Painting`, `public_domain:true`, English-language feed.
  This is not SMK's entire multi-medium collection. Full snapshots and SHA-256
  receipts are in `content/imports/europe-smk-20260910/`.
- [Rijksmuseum official search](https://data.rijksmuseum.nl/docs/search) and
  [Linked Art resolution](https://data.rijksmuseum.nl/docs/http): eight selected
  painting/image-available creator searches, then their 41 unique object
  records. Search results: Rembrandt 24, Vermeer 3, Frans Hals 8, Van Gogh 4,
  Monet 2; Pissarro, Bosch and El Greco zero for these specific queries. Zero
  results are **not proof of absence from the museum**. No full-collection
  coverage claim is made. Snapshots: `content/imports/europe-rijks-20260910/`.
- [Nationalmuseum image policy](https://www.nationalmuseum.se/en/explore-art-and-design/images)
  provides an explicit open subset; its wider media portal is not a blanket
  reuse grant. Reviewed as a future source; nothing imported this wave.
- [Finnish National Gallery official API example](https://github.com/FinnishNationalGallery/APIexample)
  requires an API key for object/search requests. No key was supplied; no
  third-party substitute or access workaround was used.

The wider European campaign remains incomplete. Louvre, Prado, Russian,
Italian and many other collections still need further independently reviewed
source batches. This work does not claim to have scanned every museum website.

## Metadata gates

SMK: unique full-name/alias authority matches, literal lifespan conflict checks,
one unqualified creator, closed source creation dates, exact object URL and
inventory number, explicit public-domain flag and object-level rights URL.
Rejected/deferred: 3,280 authority matches, 368 multiple creators, 438 qualified
creator roles, 115 dates and one identity. These source records were retained
in snapshots, not silently assigned guessed values.

Rijksmuseum: exact museum-supplied Wikidata authority identifiers, one production
creator, explicit painting classification, closed creation interval, primary
English title, accession and museum-returned catalogue URL. Of 41 records,
10 required creator review, one authority review, one date review and five
identity/title/unit reviews. Selection never infers a masterpiece designation.

Descriptions are factual source-backed catalogue summaries, not generated
art-historical interpretation. Holdings, ownership and current display remain
separate. Complete source records are retained for editorial work.

## Local image batch

80 selected SMK reproductions across 80 painters, including Matisse, Munch,
Modigliani, Manet, Rembrandt, Rubens, Cranach and Tiepolo. The selector has a
three-per-artist maximum and an 80-image total cap; this particular breadth-first
batch selected one per artist. Popularity only prioritizes selection, never
creates a museum-highlight claim.

- Fresh source `public_domain=true` and exact per-object Public Domain Mark.
- Original source IIIF identity retained, bounded 700-pixel rendition requests,
  serial fetching, 2 MiB transfer ceiling and stop-on-access-denial/rate-limit.
- Local JPEG recompression only, no generated content and no additional local
  crop. A museum's supplied source rendition may itself already be trimmed.
- **35,642–99,051 bytes per file; 5,939,867 bytes total** (5.94 MB decimal).
- Assets: `apps/web/public/assets/artworks/imported/smk-<sha256>.jpg`.
- 80 matching `media_rights_evidence` records preserve object evidence, source
  URL, source/derivative hashes, dimensions, compression quality and timestamps.
- `node ops/verify-europe-images.mjs` checks every file against the approved
  selection and application receipt. All 80 passed.

Selection: `smk-images-v1.json`, SHA-256
`17a6c25903f8eeacd06f57e88c2ffdd1572e14f85358619af9ee2ca5c1207f23`.
The image importer preserves existing media; replay added zero and preserved 80.

## Backup and receipts

Before writes, a custom-format public-schema backup was completed and its
251-entry restore inventory read successfully:
`/Users/vadimdulub/Documents/artline-europe-backup-20260910.SYGBdy/before-europe-ui.dump`.
SHA-256: `32d0f2275abd448dabe4ff1985ce9756918672b05b21a1001db0447aeed4ba46`.
The backup contains local account/catalogue data and is outside the repository.

SMK pinned manifest:
`5ca7c08c06568ffeec711ec88f5ec7f525ee178913dee45918d7000df67edd53`.
Rijksmuseum pinned manifest:
`d5913c114ae310bc7594313ad772a465c6781c654379ec9730dc336ff54559c2`.

Both sources passed rollback preview, explicit local application and unchanged
replay. Receipts are under `output/europe-{smk,rijks}-20260910-{preview,apply,replay}/`.
Image receipts: `output/europe-smk-images-20260910-{apply,replay}.json`.
Nothing was committed, deployed, published or applied to Google Cloud.

## UI/design and backend work

The frontend-design skill guided a preserve-and-refine pass: keep the existing
paper/serif atlas and right-hand drawer, improve density and hierarchy. Practical
inspiration came from [Art UK discovery](https://artuk.org/discover/artworks) and
[Rijksmuseum's object-first catalogue](https://data.rijksmuseum.nl/about/).

Implemented compact headers, optional collection/visiting notes, Grid/List
layouts, 24/48-item server pages, Previous/Next/First controls, formatted counts,
an exposed image-only filter, and a European museum shortcut that preserves
multi-painter choices. Chronology paging also gained Previous. Cursor history
retains at most 50 small tokens, not artwork arrays. Long museum names now wrap
on phones; full artwork titles remain available in accessible names/details.

Database inspection found repeated whole-catalogue scans for directory cards,
repeated selection-table scans per artwork, and unnecessary artwork enrichment
for facets. The revised query selects a bounded museum page, computes narrow
holding/display memberships, uses indexed selection joins, and chooses a cover
ID before enriching its detail. Parameter descriptions are cached without
reusing selectivity-insensitive named query plans. No stale summary cache or
browser-side catalogue loading was introduced.

Local plan example: The Met card (21,383 works) decreased from approximately
1,733 ms to 184 ms. The final directory repository checks completed in about
1–1.5 seconds for all locations and a broad northern-Europe/America combination.
These are local diagnostic timings, not a concurrency SLA or 10-million-row
benchmark. Production-scale aggregation, cache invalidation and load tests
remain necessary before scaling to that capacity.

The in-app browser connection failed during its documented bootstrap. Visual
QA therefore used the project's existing Playwright/Chrome tests, not a claimed
successful in-app browser session. Screenshots are in `docs/screenshots/`,
including `europe-smk-grid-*`, `europe-smk-drawer-*`, and
`large-collection-{grid,list}-*` at 1440, 390 and 320 pixels.

## Final verification

- 25 focused Playwright tests passed: chronology, large collections, Europe
  shortcut, real local images, multi-select filters, museum semantics, editor
  error handling and Italian catalogue descriptions. Accessibility scans used
  WCAG 2/2.1/2.2 AA tags at desktop and phone widths; no detected violations.
- Frontend lint, all 24 unit tests and the Next.js production build passed.
- Go unit tests, catalogue integration tests and `go vet ./...` passed.
- Source import rollback/replay integration checks passed for SMK and Rijksmuseum.
- The 100,000-row temporary museum-scope query fixture used indexed artwork
  access (approximately 3.08 ms for the bounded test query).
- Eight consecutive real HTTP directory requests all returned 200, alternating
  all locations and northern Europe plus northern America. Timings in ms:
  `2045, 1129, 752, 1143, 660, 1066, 634, 1060`. Counts stayed 294 and 14;
  returned pages stayed bounded at 24 and 14 items. No extended timeout was used
  to conceal a slow query.
- All 80 image files passed byte-size, SHA-256, dimensions, type and selection
  linkage checks. All have corresponding database rights evidence.

These checks are focused regression coverage, not a claim that every historical
test suite or every museum record has been editorially validated.
