# Museum coverage repairs and production release, 5–6 October 2026

The Louvre symptom had several causes: images were attached to separate source
records, the museum gallery opened in date order, some institutions had duplicate
identities, and large museum queries enriched too many artworks before pagination.
This release reconnects verified images, shows available images first, resolves
four museum aliases, and bounds gallery enrichment to the requested page.

## Release status

The initial application release and the first eight data operations below were
deployed before the session interruption. The remaining venue corrections and a
follow-up overview performance fix were completed after login was renewed.
Cloud Run reports these final revisions ready and serving 100% of traffic:

| Service | Revision | Promotion confirmed UTC | Cloud Build |
| --- | --- | --- | --- |
| API | `artline-api-museum-overview-1006` | 2026-10-06 06:20 | `4e82fb34-ccd0-4b7b-845e-51703cad0780` |
| Web | `artline-web-museum-images-1005` | 2026-10-05 20:36 | `11cf3379-9476-4d70-a394-39beabfa402b` |

Images, including the registry prefix
`europe-west1-docker.pkg.dev/artline-508319/artline/`:

- API: `api@sha256:26ed83d035c55cf8151a959cc99f1dd77f631522a071d57edc6eb17040c4c482`
- Web: `web@sha256:ffc69a0ea71bc8dffba7df2a278d505a8a833b0d02e1627244d73095b2ac37da`

The release archives were isolated from the exact previously serving source.
The initial release overlaid five API files and two web files. The follow-up
changed only `internal/catalog/museums.go` and added a read-only regression test
to the exact previously serving API source. Concurrent directory,
navigation, books and research work in the shared workspace was preserved and
excluded from these builds. Runtime settings, secrets, resources and unrelated
traffic tags were preserved. Local ignored Terraform image pins match these
digests; no Terraform apply or Git commit was performed.

After the Google Cloud session was renewed on 6 October, all twelve additional
verified museum venues were applied to production from a fresh pinned plan and
backed up. Direct production verification of the venue records and earlier
artwork/image changes passed. Both deployed services were confirmed ready and
serving 100% of traffic with their runtime configuration preserved.

All 60 live checks of the twelve venue details and positive/negative country and
region filters passed at 06:12 UTC. Those museums contain 15,915 catalogue works,
including 5,125 image attachments. These are existing records now discoverable
through the corrected geography, not additional artwork imports.

The previous API revision `artline-api-museum-gallery-1005` remains available for
rollback. Its successful build was `9c819758-47c8-40d6-adeb-cc807b19ee8e`, digest
`sha256:4f1e10885d9b9172f5444c8440aaca6d30759d8458a14026b57b572d66610279`.

## Catalogue changes

The initial audit covered 1,220 museum records with artworks and 298,372 active
artwork records. Both local and production received:

| Operation | Result | Plan / runner |
| --- | --- | --- |
| Louvre image identities | 19 existing reproductions reconnected to exact museum objects | `ops/repair-louvre-image-links-20261005.py` |
| Icon delivery paths | 3 period-containing filenames corrected; exact bytes retained | `ops/repair-icon-delivery-paths-20261005.py` |
| Selected existing museum works | 12 Art Institute of Chicago images and 1 National Gallery of Art image added | `ops/deliver-selected-museum-images-20261005.py` |
| Orsay identity | M5060 source institution reconciled with the canonical Musée d’Orsay | `ops/reconcile-orsay-institution-20261005.py` |
| Other museum identities | Alte Pinakothek, London Museum, Centre Pompidou aliases reconciled | `ops/reconcile-museum-aliases-20261005.py` |
| National museum image identities | 6 Orsay and 1 Louvre reproductions reconnected | `ops/repair-national-museum-image-links-20261005.py` |
| Cleveland additions | 6 distinct artworks with CC0 images | `ops/add-selected-museum-works-20261005.py` |
| Orsay additions | 2 distinct acquisition records, without copied images | `ops/add-orsay-acquisitions-20261005.py` |

Total for this pass: **8 new artwork records, 45 added image attachments, 3 repaired
delivery paths, and 4 institution reconciliations**. Nineteen new image files were
delivered; the other 26 attachments reuse existing verified reproductions.

Final production audit captured at 2026-10-05 20:37:26 UTC:

| Museum | Artline works | Available images |
| --- | ---: | ---: |
| Musée du Louvre | 3,286 | 33 |
| Musée d’Orsay, unified | 1,943 | 79 |
| Cleveland Museum of Art | 12,558 | 8,737 |

Louvre image coverage rose from 13 to 33. Orsay previously had images split across
two institution identities (33 and 40); six more verified attachments bring its
unified total to 79. Cleveland gained six works and six images. These are Artline
catalogue counts, not estimates of the museums’ complete holdings.

The final active catalogue contained 298,380 works and 101,769 image attachments;
119 artworks remained published and 298,261 remained in review. Other concurrent
research changed museum assignments during the audit, so the overall rise in
holding-linked works is not attributed to this release.

### New artwork identities

- Cleveland 160885: Frans Hals, *Portrait of Tieleman Roosterman*.
- Cleveland 122338: Albert Bouts, *The Annunciation*.
- Cleveland 171296: Robert S. Duncanson, *Vale of Kashmir*.
- Cleveland 97165: Giovanni di Francesco Toscani, *Panel from a Cassone: The Race of the Palio in the Streets of Florence*.
- Cleveland 170235: Johann Georg Platzer, *The Artist’s Studio*.
- Cleveland 132367: Battista di Biagio Sanguigni, *Virgin and Child Enthroned*.
- Orsay 288802: Mary Cassatt, *Jeune fille au banjo*, 1894, pastel.
- Orsay 279803: Jeanne Selmersheim-Desgrange, *Rascasse et citrons*, circa 1911–1914.

Exact titles, creation intervals, media and source identities are pinned in the
plans. Three unreconciled Cleveland creators remain named object-level labels.
Existing Cassatt banjo prints were reviewed as distinct objects; their images
were not substituted for the newly recorded Orsay pastel.

All new artworks remain in review. Existing editorial states, credits and rights
evidence were preserved. No current-display claims, member fixtures, owner
highlights, bulk publication or artwork deletions were introduced. Museum aliases
retain their original records and URLs. Historical review-only holding assertions
were retained rather than rewritten as accepted claims.

### Additional venue geography, local and production application complete

An audit found 859 museums with artworks but without valid venue geography.
Country discovery intentionally uses verified venue locations. Twelve official
visitor-page captures support the following corrections:

| Museum venue | City / country | Primary source |
| --- | --- | --- |
| Smithsonian American Art Museum, main building | Washington, DC / US | [Visitor information](https://americanart.si.edu/visit/saam) |
| Leopold Museum | Vienna / AT | [Getting here](https://www.leopoldmuseum.org/en/visit/getting-here) |
| Whitney Museum of American Art | New York / US | [Visit](https://whitney.org/visit) |
| Yale Center for British Art | New Haven / US | [Hours and visitor information](https://britishart.yale.edu/hours-and-visitor-information) |
| Walters Art Museum | Baltimore / US | [Visit](https://thewalters.org/Visit/) |
| Ateneum Art Museum | Helsinki / FI | [Contact information](https://ateneum.fi/en/contact-information/) |
| Musée Carnavalet | Paris / FR | [City of Paris museum page](https://www.paris.fr/lieux/musee-carnavalet-histoire-de-paris-1518) |
| Petit Palais | Paris / FR | [Prepare your visit](https://www.petitpalais.paris.fr/visiter/preparer-votre-visite) |
| Musée d’Art Moderne de Paris | Paris / FR | [Visitor information](https://www.mam.paris.fr/fr/node/20) |
| V&A South Kensington | London / GB | [Visit](https://www.vam.ac.uk/south-kensington/visit) |
| Albertina | Vienna / AT | [Reaching us](https://www.albertina.at/en/visit/reaching-us/) |
| Wien Museum, Karlsplatz | Vienna / AT | [Museum venue](https://wienmuseum.at/wien_museum) |

The guarded runner is `ops/repair-museum-geography-20261006.py`. It adds twelve
review venues, fills eight previously unknown institution places and adds three
real city records. Source receipts include the captured body checksum and address
fragments checked against that body. It does not assign artworks to these
buildings or assert opening hours/current display. Three additional captures
returned 403/429 and were excluded from this batch.

## Application and database implementation

- Gallery default is **Images first**, with separate total-work and image counts.
  Metadata-only records remain reachable through bounded pagination.
- Go/PostgreSQL perform sorting, filtering, counts and keyset pagination. The web
  receives 24 items by default, with a maximum of 60.
- Museum lookups, gallery pages, artwork details, painter options and must-see
  operations resolve institution aliases to the canonical museum.
- Institution-scoped queries select the page before building detailed cards;
  direct holdings and disjoint incoming loans preserve existing scope semantics.
- Migration `0033_institution_identity_aliases.sql` adds guarded aliases and
  canonicalizes future holding/artwork writes. Migration
  `0034_museum_gallery_covering_index.sql` supports scoped gallery reads.
  The production index was built concurrently before recording migration state.
- The Met query that timed out at eight seconds now passed the large-gallery
  checks. Representative production plans reduced its count query from about
  7.8 seconds to 0.18–0.78 seconds, and its covered page query to about 0.27 seconds.
  End-to-end candidate requests included a 4.3-second cold request and roughly
  one-second warm requests. These measurements are not a 10-million-row capacity
  claim.

### Follow-up: museum overview timeouts

The final log review found two National Gallery of Art overview requests that
timed out at the eight-second API deadline. The issue was reproduced: the
overview endpoint still revisited wide artwork rows while calculating counts
and selecting its cover, despite the earlier gallery-page optimization.

`Museum()` now reuses the institution-scoped directory-card query. Its narrow
materialized visibility set serves all counts and cover selection; only the
chosen cover receives detailed enrichment. No schema or visibility change was
needed. Complete responses matched the preceding query in 20 cases each against
the real local and production databases, including both visibility modes,
aliases and missing records.

Production `EXPLAIN ANALYZE` measurements:

| Overview | Before | After |
| --- | ---: | ---: |
| National Gallery of Art | 4,883 ms | 1,084 ms |
| Metropolitan Museum of Art | 5,263 ms | 526 ms |

Both the workspace and isolated release catalogue/HTTP unit tests passed. All
35 large-museum candidate overviews and their gallery pages returned HTTP 200,
with identical overview/gallery counts, bounded pages and images first. The
slowest overview took 2.506 seconds. After promotion, live HTML pages for NGA,
NGA filtered by Rembrandt, and the Met returned 200 with their expected headings
in 2.151, 0.738 and 0.937 seconds respectively. Query timings describe this
catalogue and run, not guaranteed latency under arbitrary load.

The four live Playwright gallery checks passed again after the follow-up
promotion (11.1 seconds), including mobile/desktop layout and accessibility.

## Verification

- Full workspace Go unit suite passed without the fixture-database variable.
- Real-catalogue read-only catalogue/HTTP tests passed; final scope/image/alias
  tests passed after the bounded-page query change.
- Louvre keyset traversal covered all 3,286 records with no duplicate or omitted
  IDs; image-only pagination covered all 33 images.
- Query equivalence checks covered four museums, twelve filter combinations,
  their next pages, and both preview visibility modes where applicable.
- All 35 large-gallery candidate requests returned HTTP 200 with bounded,
  unique pages and images first.
- Frontend: 209 unit tests passed, TypeScript and focused lint passed.
- Four Playwright scenarios passed locally, on the candidate and on production:
  pagination, image filter, clearing filters, search, sort, artwork deep links,
  390/1440px layout and automated accessibility checks.
- Recovery verification fetched all **48 affected production files**: matching
  SHA-256, exact byte count, decodable image, expected dimensions, under 100 KB.
- All four aliases returned identical live museum, gallery and image-only
  responses to their canonical URLs.
- Forty-seven affected production artwork detail responses matched the pinned
  titles, dates, media, review states and holdings, including all eight newly
  added works. This independent public-API check also succeeded during the
  authentication interruption; direct production SQL verification subsequently
  passed after login was renewed.
- Independent local and production verification checked 45 attachments, all eight new artwork
  identities and creator mappings, source evidence and retained review states.
  It found zero invalid image paths, oversized attached images, missing image
  checksums, stranded alias works, alias chains or inconsistent accepted holdings.
- Twelve local venue details and 24 positive/negative country-filter cases passed.
  The existing directory regression audit also passed after these additions
  (17 filter combinations in both visibility modes, with next-page comparisons).
  Production verification additionally passed all 60 venue-detail, country and
  region checks after the production geography application.
  Production anonymous auth did not expose local-debug access; local loopback
  auth retained its all-features preview without member database fixtures.

Important test limits: six pre-existing Atlas read-only tests retain stale
catalogue expectations (including older book-cover counts and a production-only
Cyprus expectation). That broader opt-in run was not fully green. The isolated
build archive also omits historical research manifests needed by ingestion
evidence tests; the complete workspace Go suite passed with those files present.
No real catalogue data was altered to satisfy those assertions. Full concurrent
10-million-artwork load tests remain outstanding.

## Evidence and rollback preparation

Plans, captures and verification receipts are preserved under:

- `docs/research/louvre-image-coverage-20261005/`
- `docs/research/museum-gaps-20261005/`
- `docs/research/museum-gaps-20261005/verification-20261006/`
- `docs/research/museum-gaps-20261005/overview-fix-20261006/`

Private before/after row backups and Cloud Run preimages are under
`~/Library/Application Support/Artline/backups/`, in the operation-named folders
used by the runners. Original images are under the corresponding Artline
`source-images/` folders. Disposable browser results, query plans and test logs
are under `/tmp/artline-louvre-audit-20261005/`. No unrelated database or real
artwork asset was removed.

Remaining coverage is explicit: thousands of Louvre records still have no
verified reproduction attached, hundreds of museum venues still need primary
geography evidence, and 2,570 pre-existing attached media records retain unclear
rights statuses. These records were preserved. Ambiguous object matches and
unavailable source images were held for research, not fabricated or silently
discarded. This pass fixes the documented, verified defects; it does not certify
the entire worldwide catalogue as complete.
