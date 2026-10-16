# Maps for Artlines — research and implementation

16 October 2026. Branch `map-research`, based on checkpoint `6488fce7`.

## Result and scope

A Timeline / Map switch now exists in Painters (lifespans and paintings), Books,
Events and All. It preserves native filters and record drawers. Each map enriches
only the current bounded result page. It reports located / loaded / matching
records separately, exposes records without coordinates, and retains native
pagination. The map is a research implementation, not global geographic coverage.

Use these local examples with the web preview on port 3016:

- [Van Gogh's life places](http://127.0.0.1:3016/?canvas=map&painter=vincent-van-gogh-q5582&popular=false)
- [Van Gogh paintings, 1888–1890](http://127.0.0.1:3016/?canvas=map&view=paintings&painter=vincent-van-gogh-q5582&popular=false&start=1888&end=1890)
- [Frankenstein](http://127.0.0.1:3016/books?canvas=map&q=Frankenstein&top100=false)
- [The Great Exhibition](http://127.0.0.1:3016/events?canvas=map&q=Great%20Exhibition&top100=false)
- [All, 1850–1900](http://127.0.0.1:3016/all?canvas=map&selection=true&type=artwork&type=book&type=event&start=1850&end=1900&highlights=true)

All database inspections and API preview connections were read-only. No migration,
fixture database, catalogue mutation, Google service call or deployment was used.
The original working copy remains on master so background programmes are unaffected.

## What the local catalogue actually supports

Read-only inspection of the local catalogue found:

| Existing data | Result | Consequence |
| --- | --- | --- |
| `places` | 388 rows; zero with both coordinates | A textual place is not automatically a precise pin. |
| `artwork_places` | 1,000 links, all `created`, all country-level | Map country label positions with explicit precision; never use museum addresses as creation places. |
| `artist_places` | 0 rows | City-level biography needs new sourced evidence. |
| `artist_countries` | 1,003 birth, 77 active, 1,539 citizenship, 17,890 cultural-affiliation links | Preserve the relation. Citizenship/affiliation do not establish residence or birth city. |
| Active artists | 23,409 | Painter density mode cannot become an unbounded map payload. |
| Books | Country discovery metadata; no native composition-place model | P495 is country of origin, not writing location. Only checksum-current discovery rows are used. |
| Events | Source-linked `locations` in record JSON; many empty | Event location can mean a broad country or area, not a venue. |

Example: Frankenstein's country term Q174193 denotes the United Kingdom of Great
Britain and Ireland. It is **not** mapped to the coordinates of modern Q145.
Unknown places and historical states without reviewed geometry remain unlocated.
No title-string geocoding is performed.

This is a local snapshot audit, not a measurement of current production coverage.

## Place semantics

The useful unit is a sourced **record–relation–place–time** connection. A single
object can have several connections:

| Subject | Useful relations | Must remain distinct |
| --- | --- | --- |
| Artwork | created, begun, continued, completed | depicted place, current holding, past exhibition, current display |
| Book | begun, written in part, completed, first edition publication | country of origin, narrative setting, translation/edition identity |
| Person | born, lived, worked, studied, died | citizenship, cultural affiliation; intervening journeys |
| Event | held at / recorded location | participants' homes, territorial extent, tour occurrences |

This follows the distinction in [CIDOC CRM 7.1.3](https://cidoc-crm.org/html/cidoc_crm_v7.1.3.html)
between production and its place, and an object's current permanent location.
A pin has spatial precision independent of the certainty of the historical claim.
A well-documented town is still represented by an approximate town label point.
Unknown dates are never filled from a person's lifespan or a work's publication year.

Year controls first select native catalogue records, then exclude dated place
connections outside the interval. They are not yet a global composition-date
search: a book dated by publication may be excluded before its earlier writing
connection can be considered. The UI and this report make that limitation explicit.

## Technology decision

| Option | Assessment for this branch |
| --- | --- |
| Leaflet 1.9.4 + self-hosted Natural Earth GeoJSON | Chosen. Small, familiar pan/zoom, keyboard-enabled markers, no account/key or runtime tile/geocoder dependency. Suitable for a bounded research page. |
| MapLibre GL JS | Strong future choice for dense vector tiles and geographic styling. Adds WebGL/rendering complexity before our place data is ready. Clustering a full catalogue in the browser is not a scale solution. |
| Plain SVG map | Good for a static explanatory figure; weaker for the map interaction requested here. |
| Public OSM tiles / Nominatim | Not used. Public services have operational policies and are not a substitute for a planned catalogue geocoding pipeline. |

Sources: [Leaflet reference](https://leafletjs.com/reference),
[Leaflet accessibility](https://leafletjs.com/examples/accessibility/),
[MapLibre large-data guidance](https://maplibre.org/maplibre-gl-js/docs/guides/large-data/),
[OSM tile policy](https://operations.osmfoundation.org/policies/tiles/),
[Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/).

Natural Earth is [public domain](https://www.naturalearthdata.com/about/terms-of-use/).
The self-hosted 1:110m background is about 260 KiB. The original download URL and
SHA256 are recorded in `apps/web/public/maps/README.md`. Country label coordinates
come from the same source. Modern borders provide orientation, not historical
boundaries, disputed-territory adjudication or exact site geometry.

The frontend uses the established paper/ink/rust palette and serif/sans stacks.
The map and adjacent evidence list form one workspace. Circular local-place pins
and dashed country markers distinguish precision through shape and text. The
list offers equivalent record access without requiring map gestures. Nearby
pins can overlap; zoom and the list remain available. There is no invented jitter.

## Reviewed example evidence

`apps/server/internal/geography/evidence.json` contains 18 explicit connections.
These are a version-controlled research overlay, not a database import. They
attach only after a real, non-archived catalogue record passes an exact external
identifier lookup. Same-title objects and editions cannot inherit the claim.

| Exact identity | Connections | Evidence |
| --- | --- | --- |
| `artwork / moma-object / 79802` | The Starry Night, Saint-Rémy, 1889 | [MoMA object](https://www.moma.org/collection/works/79802) |
| `artwork / european-ng-object / NG3863` | Sunflowers, Arles, 1888 | [National Gallery object](https://www.nationalgallery.org.uk/paintings/vincent-van-gogh-sunflowers) |
| `artwork / european-vgm-object / s0047V1962` | First Bedroom version, Arles, 1888 | [Van Gogh Museum object](https://www.vangoghmuseum.nl/en/collection/s0047V1962) |
| `book / sourceId / Q150827` | Frankenstein begun near Geneva, 1816; first published London, 1818 | [Author's introduction and 1818 title page](https://www.gutenberg.org/files/41445/41445-h/41445-h.htm) |
| `book / sourceId / Q180736` | Les Misérables written in part in Guernsey, 1860–61; Brussels original edition, 1862 | [Maisons de Victor Hugo](https://www.maisonsvictorhugo.paris.fr/guernesey/une-maison-guernesey), [Paris Musées bibliography](https://www.parismuseescollections.paris.fr/fr/ressources-bibliographiques/les-miserables) |
| `event / sourceId / Q273095` | Great Exhibition, London, 1851 | [V&A](https://www.vam.ac.uk/articles/the-great-exhibition-of-1851) |
| `artist / wikidata / Q5582` | Ten selected Van Gogh chapters, birth in Zundert through death in Auvers | [Van Gogh Museum life chronology](https://www.vangoghmuseum.nl/en/art-and-stories/vincents-life-1853-1890) |

The Van Gogh chapters omit intervening residences and trips. London 1873–75 is a
selected chapter, not continuous residence. The Guernsey claim does not say the
whole novel was written there or that its final completion occurred there.
Brussels is not labelled the sole publication place; the parallel Paris original
edition is explicitly mentioned. All local coordinates are approximate orientation
points chosen for the town/area, not surveyed historical addresses. None is a
claim about where the work is currently displayed.

Additional leads reviewed but not added: [Joyce's Trieste chronology](https://museojoycetrieste.it/en/james-joyce-and-trieste/chronology/),
[Joyce Foundation chronology](https://joycefoundation.utulsa.edu/resource-center/joycean-timeline/),
[BnF on Madame Bovary](https://gallica.bnf.fr/accueil/fr/html/madame-bovary-mise-nu-par-ses-critiques),
[Yasnaya Polyana on War and Peace](https://ypmuseum.ru/event/1701?lang=en).
In particular, Ulysses Q6511 must not be confused with Q2499206, another local work
with the same title. These leads require further source passage and edition review.

## API and bounded browsing

`GET /api/v1/map/locations?kind=book&id=wd-q150827&start=1800&end=1900`

- Four allowed kinds; 1–80 unique IDs per request; UUID validation for artists/works.
- Server-side date intersection, archived-record exclusion and book date scope.
- Indexed ID selection precedes source/place enrichment. At most 32 connections
  per record are returned, with an explicit truncation flag. Native dated place
  rows are filtered before the per-record limit.
- No new global scan, pagination order or visibility rule is introduced by map lookup.
- Book map pages use 80 records; events retain their existing bounded pages;
  All and paintings retain their native per-lane cursor pages.
- Large artist selections already return density instead of individual records.
  The map asks the user to narrow filters or choose Top 100; it does not fetch all artists.
- Frontend enrichment chunks are serial, abortable and reject stale results.
- Backend counts remain the catalogue totals. The browser stacks equal-coordinate
  markers from the loaded page and calculates displayed-page coverage only; these
  visual counts are never represented as worldwide geographic totals.
- Map/library assets load only in map view. No external tiles, live geocoding,
  account requests or generated artwork images are needed.

The real local database lacks `catalogue_cache_revisions` and `artwork_atlas_browse`,
which caused the baseline combined API to return 503. A local-debug-only schema
check enables existing native predicates when these projections are absent.
It keeps repeatable-read/read-only transactions, disables revision-based aggregate
caching, preserves illustrated eligibility and native filter/scope rules. Production
still requires its normal projections and revision snapshot. This is a preview
compatibility path, not an alternative production performance claim.

## Next research and scale work

1. Add reviewed place identities and geometry to catalogue research, starting
   with exact museum creation statements and primary artist chronologies.
2. Model book composition and edition/publication events separately, with
   source object identity, date bounds, review state, quoted locator, coordinate
   precision and geometry provenance. Preserve conflicting claims independently.
3. Add event occurrences and historical venue identities; broad wars/cultures
   often need polygons or multiple places instead of a single city marker.
4. Add server-side geographic coverage and viewport aggregates using the same
   visibility/filter/date predicates and catalogue revision invalidation.
5. Evaluate PostGIS spatial indexes and server-produced tiles for the 10-million-
   artwork headroom. [Indexed bounding-box queries](https://www.postgis.net/docs/geometry_overlaps.html)
   and [ST_AsMVT](https://www.postgis.net/docs/ST_AsMVT.html) support a bounded tile
   architecture. This is a proposed next stage, not installed infrastructure.
6. Measure realistic import churn, sparse places, highly dense cities, historical
   polygons, antimeridian cases and repeated viewport requests. Current bounded
   correctness checks do not establish 10-million-row performance.

## Validation

The initial full-web baseline had 606 passing tests and one existing failure in
`BackNavigation.test.tsx` (signed-out return to an individual public museum page).
The new run has 613 passing tests and the same failure; all seven new map tests
pass. Relevant Go geography, HTTP API, atlas, books and events tests pass. TypeScript
passes. Baseline full-Go failures in ingest depend on missing ignored research
fixtures; guide search tests also fail before this branch. Those unrelated issues
were preserved in the checkpoint and are not disguised as map regressions.

Browser checks cover painter life places, artwork creation, books, events and the
combined map. All five had zero axe violations within the map region. Books were
inspected at 1440, 1024, 768, 390 and 320 px with no horizontal overflow. Tests
exercise view switching / back navigation with filters intact and native drawer
open / Escape close. Screenshots and full outputs live outside the repository at
`~/Library/Application Support/Artline/map-research-20261016/`.

Observed sample coverage: Van Gogh life 1/1 record; paintings 1888–90 2/71 loaded
records; Frankenstein 1/1; Great Exhibition search 1/2; All 1850–1900 18/181
loaded records, from 6,015 matching entries. These are measured coverage gaps,
not placeholders to fill by inference.

Final interaction checks additionally passed native book pagination, independent
book/event cursors in All, Enter activation of map markers with focus moved to
place details, full-view Escape, simulated location-service failure and retry,
and empty filtered maps. Native marker hit targets are 44 px and have place names.
The production Next build passed. ESLint reports no errors; the map retains the
existing catalogue convention of native image thumbnails (one Next image warning).

`TestLocalMapPreviewReadOnly` also passed against existing local records under
`transaction_read_only=on`. Two five-item pages preserve count and cursor order.
EXPLAIN ANALYZE measured about 90 ms for the selected-painter aggregate and 61 ms
for the first page. The native fallback uses the illustrated date index and the
artist/work index, but examines 3,951 date candidates for the aggregate and 2,293
for the first page; it is deliberately not presented as a painter-only optimal
plan or a production scale substitute. Exact plans are in
`native-map-preview-plans.json` in the external proof directory. No test database,
fixture inserts or local migrations were created.
