# Maps for Artlines — research and implementation

16 October 2026. Branch `map-research`, based on checkpoint `6488fce7`.

## Result and scope

A Timeline / Map switch now exists in Painters (lifespans and paintings), Books,
Events and All. It preserves native filters and record drawers. Each map enriches
only the current bounded result page. It reports located / loaded / matching
records separately, exposes records without coordinates, and retains native
pagination. The map is a research implementation, not global geographic coverage.

Use these local examples with the web preview on port 3016:

- [Van Gogh's life and painting places](http://127.0.0.1:3016/?canvas=map&painter=vincent-van-gogh-q5582&popular=false)
- [Van Gogh paintings, 1888–1890](http://127.0.0.1:3016/?canvas=map&view=paintings&painter=vincent-van-gogh-q5582&popular=false&start=1888&end=1890)
- [Frankenstein](http://127.0.0.1:3016/books?canvas=map&q=Frankenstein&top100=false)
- [The Great Exhibition](http://127.0.0.1:3016/events?canvas=map&q=Great%20Exhibition&top100=false)
- [All, 1850–1900](http://127.0.0.1:3016/all?canvas=map&selection=true&type=artwork&type=book&type=event&start=1850&end=1900&highlights=true)

All database inspections and API preview connections were read-only. No migration,
fixture database, catalogue mutation, Google service call or deployment was used.
The initial preview used a separate worktree. On 17 October, at the user’s
request, the main checkout moved to `map-research`; its pre-existing uncommitted
timeline work was preserved while reconciling the map controls.

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
The initial self-hosted 1:110m background was about 260 KiB; the product pass
below replaces it with labelled 1:50m geometry. The original download URL and
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

## Artist filters and event regions — refinement

The artist map now combines native painter records and the bounded painting page.
Checkboxes select **Paintings made, Born, Lived or worked, Studied, Died,
Travelled**, and **Country affiliations**. These can be combined; affiliations
are off by default. Existing painter, country, movement, work type and year
filters still select the underlying records. Painting eligibility and pagination
remain those of the illustrated painting browser. Artist and artwork drawers
remain native. Density-mode artists still require narrower filters.

Repeated `map_relation` URL values preserve selections through reload and Back;
`map_relation=none` preserves an explicitly empty selection. Relationship filters
are sent to the map endpoint and applied before the per-record connection cap,
including in the native SQL query. Curated evidence carries explicit category
arrays: Antwerp can match both residence and education. Citizenship and cultural
affiliation cannot become residence, and residence cannot become work creation.
Unknown native association dates remain unknown, even where a curated connection
has an exact date; filtering does not silently enrich or merge source claims.

Events and All now offer **Highlight event regions** (on by default, with
`map_regions=off` to preserve the off state). Only an exact country-level event
location supplies the country code used to shade its Natural Earth polygon.
Selecting a country from the map or place list emphasizes its outline and opens
its event connections. Polygon keyboard activation moves focus to the place
heading. A city-only event such as the Great Exhibition remains a point; neither
its containing country nor a participant's country is inferred as event extent.

The camera frames the polygon component around the country's label point; the
full modern country geometry remains available. This avoids overseas components
pushing the main area offscreen. It refits on viewport resizing. Modern polygon
shading is orientation for the recorded country association, **not a historical
territorial or battlefield reconstruction**. Unsupported historical states and
subnational areas remain unresolved; continent/category tags do not become shapes.

[Leaflet's GeoJSON choropleth example](https://leafletjs.com/examples/choropleth/)
supports the chosen styling, selection and bounds interactions. Natural Earth's
[admin-1 dataset](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/)
was also reviewed. Its current administrative divisions do not establish the
geometry of a historical region. No admin-1 data or name-based matching was added;
subnational and historical regions need exact identity and dated geometry research.

Examples:

- [Birthplaces with painting creation](http://127.0.0.1:3016/?canvas=map&painter=vincent-van-gogh-q5582&popular=false&map_relation=birth&map_relation=creation)
- [Event country highlighting](http://127.0.0.1:3016/events?canvas=map&q=Seventh%20Coalition&top100=false)

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


Refinement validation: 21 focused web tests pass (map semantics, map requests and
All layer/filter behavior); geography and HTTP API Go packages pass. Browser
checks cover combined birth/painting filters, study-only and explicitly empty
selections, reload and Back, both native drawers, country polygon keyboard
selection and toggle persistence, city-only event exclusion, and region rendering
in All. Artist and event layouts were inspected at 1440, 768, 390 and 320 px;
controls retain 44 px touch targets and no horizontal overflow after resize.
Both map regions have zero axe violations and no browser runtime errors. Proofs
are `map-refinement-browser-report.json` and the `artist-filters-*` /
`event-regions-*` screenshots in the external directory above. The in-app browser
connection failed before initialization; standalone Playwright was used instead.
The refinement production build (including TypeScript) passes. ESLint has no
errors and retains the existing native-thumbnail warning. No catalogue,
background programme or production service was modified.

## Product direction — 16 October continuation

The next pass makes the map the primary browsing surface. The recommended pattern
is a labelled, zoomable atlas with a synchronized place index and selected-place
record view. The map answers **where**; the index answers **what happened here**;
the existing record drawer supplies the full artwork, book, artist or event.

Design plan before implementation:

- Colour: existing paper `#f2efe8`, ink `#1b1916`, stone `#e8e3d9`, rust
  `#8f3a29`, event moss `#53745b`; a subdued pale water surface provides map
  contrast. These are Artlines' established materials, not a new brand palette.
- Type: Georgia for places and record titles; Avenir/system for navigation,
  relations, dates and map labels. Left alignment throughout.
- Layout: compact controls above a generous map; a narrow place index beside it.
  A place selection replaces the index with illustrated records and clear dates.
  On phones, the map precedes a compact, reachable place panel.
- Principle: named places and authentic works carry the experience. Cluster nearby
  places only for display; never merge their identities or invent precise sites.
  Source notes and coverage stay accessible in disclosures.

```text
Shared catalogue filters / Timeline–Map / years
Title + mapped-place count                         Map options
Painting / birth / life filters
+-------------------------------------+-----------------------+
| country labels, named place markers | Find a mapped place   |
| nearby-place clusters               | compact place index   |
| selected event outline              | or selected records   |
| zoom / Show all places               | images, dates, source |
+-------------------------------------+-----------------------+
Coverage and map guide / native page controls / year controls
```

Review against the brief: the old large introduction, repeated evidence blocks
and anonymous count dots hid the collection. Remove that duplication; give the
map more room and let the place index reveal records on demand. Retain Artlines'
existing visual language and real source limitations.

Keep Leaflet for this bounded city/country atlas: it already supports the required
[vector layers, named markers and camera interactions](https://leafletjs.com/reference.html)
and [keyboard access](https://leafletjs.com/examples/accessibility/). Upgrade the
self-hosted geography to Natural Earth 1:50m with country labels. For future
street-level maps or catalogue-wide spatial tiles, evaluate MapLibre with
[self-hosted PMTiles](https://docs.protomaps.com/pmtiles/); that is a separate
hosting and backend coverage project. A renderer replacement alone would not
resolve sparse historical place evidence. No live geocoder, paid map account or
Google service is introduced by this product pass.


### Product implementation and verification

- The artist, book and event maps have one title/date row, compact controls and
  a generous map. All retains its native layer/context controls. Existing date
  editors, catalogue filters, record drawers and bounded page controls remain.
- Self-hosted 1:50m Natural Earth geometry has 242 features and is 1,898,455 bytes
  before HTTP compression. Country labels are background context, never a new
  geocoding source. Original source SHA256 and processing are in the map asset README.
- Markers name places and identify the content type. Nearby places cluster by
  screen distance, with a representative name and the number of other places.
  They retain every original identity. Zoom separates them where possible; a
  keyboard-accessible chooser handles places too close at the maximum zoom.
  Selected places remain individually visible. Displaced labels use short
  leader lines to their original map position; these are label annotations,
  not historical routes or changed coordinates.
- A compact, searchable place index shows authentic thumbnail previews and
  relationship summaries. Search applies only to mapped places on the current
  page. A selection opens dated, illustrated records; `map_place` preserves the
  selection on reload and Back. Country/city display options also persist.
- Native catalogue dates and location-connection dates stay separate. An
  event's known year remains visible when the location association is undated.
  Evidence and precision are retained under Source & location / About this map.
- Additional place filters and map options dismiss on Escape or outside click.
  Menus preserve native checkbox semantics. Failed reproductions have an explicit
  unavailable state and retain record access. Data and map-background failures
  have separate recovery actions. The map remains mounted during data refresh.

Production build and TypeScript pass. All 25 focused web tests pass, including
clustering identity/selection, URL selection, place search, failed images, stale
requests, and All's native layer/filter behavior. ESLint reports no errors and
one existing-style native-image warning. No backend or database changes were
required by this pass.

Browser verification uses the real read-only preview, without fixture records:
artist overview/detail, books, event regions, All, relationship combinations,
place search, record drawers, reload and Back, full view / Escape, timeline
return, and failed-place-service recovery. Artist layouts were checked at 1440,
1024, 768, 390 and 320 px. Axe found zero map-region violations in the checked
artist, book, event and All states, including phone views. The final visual pass
also checks selected-label separation, map-background retry and independent
record/location dates. Proofs and screenshots are in the existing external
`map-research-20261016` directory (`product-browser-report.json`,
`product-final-report.json`, `product-*.png`, build and lint logs).

Two missing Van Gogh preview images reuse exact existing files in the original
working copy through ignored local symlinks. The final bounded preview needed
no further image links. No reproduction was generated,
redownloaded, relabelled or added to the catalogue. Production asset delivery
is unchanged; these links only make existing local images visible in this worktree.
The in-app browser again failed before initialization, so standalone Playwright
provided the visual and interaction checks.

The preview also exposes a pre-existing catalogue-date inconsistency: the native
Frankenstein record shows 1810 while its sourced writing connection says 1816.
The map preserves both fields; it does not silently correct catalogue evidence.
The catalogue date requires a separate factual review.

Remaining product work is factual coverage and catalogue-wide spatial delivery:
reviewed city/region identities, historical geometries, global coverage counts,
viewport aggregates and realistic capacity tests. This pass improves the working
atlas interface; it does not turn sparse evidence into complete geographic coverage
or authorize a production deployment.

## Record journeys — 17 October continuation

Design plan before implementation: extend the existing atlas with a record view
that follows one artist, work, book or event through its documented places.
Keep paper `#f2efe8`, ink `#1b1916`, stone `#e8e3d9`, rust `#8f3a29`, moss
`#53745b` and the existing pale water background. Georgia carries record/place
titles; Avenir/system carries dates, relationships and controls. Left alignment.

```text
Map title / relationship filters                 Copy map link
+----------------------------------------+-------------------------+
| labelled map of selected record places | Places / Records / Gaps |
| selected connection is highlighted     | Record title / open     |
|                                        | Previous / Next         |
|                                        | dated place connections |
|                                        | undated evidence        |
+----------------------------------------+-------------------------+
Existing year controls and bounded catalogue pages
```

Review against the brief: a generic itinerary would imply journeys and precise
routes that the evidence does not establish. This is a dated connection browser:
no route lines, automatic playback or invented chronology. Unknown coordinates
remain readable and unknown dates stay separate. Add a small Records switch to
the existing panel rather than another dashboard. Go owns connection ordering
and stable keys; the browser manages bounded selection and map highlighting.
This pass does not change catalogue records, add infrastructure or deploy.


Implemented and verified:

- A Records view opens a single record's bounded, sourced place connections.
  Previous/Next, the dated list and map markers select the same connection.
  The map shows that record's places while following it; All records restores
  the loaded page. Full catalogue drawers remain available.
- Go supplies deterministic chronological order and stable evidence keys. Start
  bounds order first; an end-only connection uses its documented end for sorting
  and still displays its unknown start. Fully undated connections appear last.
  Same-place relationships remain distinct. Ordering is over the returned capped
  evidence, not a claim of a complete chronology or actual travel route.
- `map_panel`, `map_record` and `map_stop` preserve the current connection alongside
  catalogue filters. Stale/out-of-page links explain what changed. An unresolved
  connection clears the selected marker instead of retaining the previous place.
- Copy map link retains the filters and connection, omits an open native drawer,
  and offers a selected manual-copy field when clipboard access is unavailable.
  Escape and outside clicks dismiss that field. No link is sent to another service.
- Place-type display counts reflect the visible map; coverage remains explicitly
  about loaded records. No evidence, dates, catalogue records or geometries were
  created by this continuation.

Verification: 28 focused web tests pass, as do the geography and HTTP API Go
packages. The production web build and TypeScript pass; ESLint has zero errors
and the existing native-image warning, now in the extracted shared map visual.
Real read-only browser checks cover artist, book, event and All journeys; Next,
Previous, Back, reload, source dates, unresolved historical countries, native
record drawers, clipboard success/failure, and mobile layouts at 1440/1024/768/
390/320px. Checked map regions have zero axe violations and zero browser runtime
errors. Screenshots were inspected; selecting a chronology entry scrolls its
current detail into view. Evidence is in `journey-browser-report.json`,
`journey-*.png`, `journey-tests.log`, `journey-build.log` and `journey-lint.log`
in the external proof directory.

Main-checkout preservation: the map branch and the uncommitted timeline
introductions touched the same insertion points in AllAtlas and TimelineExplorer.
Both controls and introductions were retained. Other tracked edits remain byte
for byte unchanged; research files were not stashed, committed or removed.
A preservation patch/copies are in external `checkout-preservation-20261017/`.
The existing 35 introduction/All tests and main-checkout TypeScript check pass
with the branch's locked map dependencies installed. These unrelated edits
remain uncommitted. The preview API remains local, uses
`default_transaction_read_only=on` and `--skip-migrations`; no deployment or
Google service was used. The in-app browser failed at bootstrap, so the documented
standalone browser fallback supplied the interaction and visual checks.
