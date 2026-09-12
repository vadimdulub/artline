# Museum browsing, masterpieces and filter design

8 September 2026. Working plan based on the two supplied museum research files
and the actual Next.js / Go / PostgreSQL application. No commit, deployment,
publication, database migration or external ingestion is authorized by this plan.

**Subsequent approved milestone:** the user then approved proceeding with the local
museum foundation and browsing implementation. See
[museum-implementation.md](museum-implementation.md) for the delivered schema,
museum routes, must-see editor and verification. The starting-point observations
and proposals below describe the earlier planning snapshot, not the current code.
Bulk ingestion, deployment and Terraform remain outside the implemented milestone.

## This turn

Implement removal of Record status from the timeline, and multi-region selection.
Keep status controls in the editorial Catalogue. Ignore/remove old timeline status
bookmarks so no invisible status filter remains. Backend publication/preview
authorization stays unchanged.

Regions use OR semantics: Northern Europe **or** Eastern Asia. Search, date range,
country, movement and work type combine with that group using AND. Preserve all
other filters and the visible range when a region changes. Show separate removable
chips, selected count, Clear regions and Done. Use native checkboxes, keyboard
navigation, Escape/focus-away dismissal and URL-persisted repeated parameters.
Region options come from the catalogue, not a hard-coded Europe/Asia-only list.

The visual direction remains paper #f2efe8, stone #e8e3d9, ink #1b1916, charcoal
#12110f, muted #625d55 and red #c85139; Georgia for reading, Avenir/system sans for
controls. Left-aligned, compact toolbar, 44px checkbox rows. Keep secondary fields
under More filters rather than adding a large permanent panel. This deliberately
preserves the user's timeline and right drawer instead of introducing a new style.

On phones, Regions and Movement each have half the toolbar width. Reset view
stays available inside More filters, keeping the primary controls readable without
adding another permanent row. Checkbox selection applies immediately; Done only
closes the menu. Filter changes replace the current URL state, matching existing
behavior; opening a painter adds a history entry. Reload and returning from a
painter retain all selected regions. Legacy comma-separated regions are accepted;
new changes use repeated `region` parameters, normalized and deduplicated.

Native, labelled checkboxes are appropriate for several selections; the menu has
an explicit group description, rather than relying on modifier-key selection in a
native multi-select. This follows the interaction guidance in the
[GOV.UK checkbox component](https://design-system.service.gov.uk/components/checkboxes/),
while retaining Artline's visual language.

## Research audit and actual starting point

Reviewed the complete supplied `MUSEUM_INGESTION_RESEARCH.md` and structurally
parsed every record in `GLOBAL_MUSEUM_SOURCE_REGISTRY.csv`. The CSV contains
111 unique source IDs and 28 columns. Its SHA-256 is
`25f6fccb27a6a8f0271393b017c9f18d87a8a94a39ea87a5cb79f2e9496c6f30`.

| Registry grouping | Entries |
| --- | ---: |
| Individual museums | 72 |
| Museum networks / multi-museum networks | 15 / 4 |
| National / national-museum / regional aggregators | 11 / 1 / 3 |
| Other aggregators, directory, authority and media sources | 5 |
| Priority A / B / C / D | 27 / 43 / 35 / 6 |
| Marked verified official / partially official | 95 / 14 |
| Legacy verified / legacy or recheck | 1 / 1 |

These verification labels are claims in the supplied file, not the result of a
new live check of 111 endpoints. Structural checks found no duplicate IDs,
malformed verification dates, formula-leading cells or flagged URL parameters.
Eleven rows lack a sample artwork link: `dpla`, `museum_data_service_uk`,
`registro_museos_iberoamericanos`, `japan_search`, `shuzo_japan`, `emuseum_korea`,
`museums_of_india`, `national_gallery_iceland`, `mnac_barcelona`,
`national_gallery_prague`, `national_gallery_indonesia`. Some discovery services
may reasonably lack an object URL; adapters still need a tested object fixture
before activation. Neither a successful URL parse nor a tier-A label proves
endpoint safety, data quality, display status or reproduction permission.

Registry regional labels are broad coverage groupings (including Global and
Latin America & Iberia), not the atlas's painter-region vocabulary. Do not copy
them directly into painter filters or infer a museum's physical location from a
source's coverage. Region options now come from visible catalogue associations.
The future museum geography should likewise come from canonical venue places.

The reproducible, read-only structural audit is:

```bash
cd apps/server
go run ./cmd/registry-audit /Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv
```

It reads a file and prints JSON; it does not fetch URLs, import rows, activate
sources or connect to PostgreSQL. It is not a production ingestion validator.
The supplied files remain unchanged. The spreadsheet runtime was unavailable,
so structural review used Go's CSV parser, not a generated workbook.

Read-only inspection of local PostgreSQL 17.6 and the repository found:

- 11 review painters and 15 review artworks, not the supplement's assumed
  28 painters / 140 works. Nothing is published.
- An `institutions` table already exists, but contains **zero rows**. All 15
  artworks have a null `current_institution_id`; holding information is text.
- No museum slugs, physical venues, display assertions, museum pages or source
  connectors exist. A location-check date is not an on-view assertion.
- The current source/citation/media schema already records useful evidence.
  Extend those entities; do not create a parallel incompatible catalogue.
- The stack is Go + PostgreSQL + Next.js, with local assets and production-only
  Google Cloud planned. The supplement's D1, R2 and TypeScript backend examples
  must be translated, not adopted. No Cloudflare migration is proposed.

## Product direction: museums as a second way into the atlas

Keep Timeline as the chronological entry point, and add Museums as the place-based
entry point in a subsequent milestone. Catalogue remains editorial. Start with a
useful list/grid; a map is optional later and must not be the only navigation.
Preserve the right-hand detail-panel pattern when opening an artwork from a museum.

Proposed layout (not implemented):

```text
Timeline   Museums   Catalogue

Museums                         Search museum, city or country
Museum regions [several]   Countries [several]   More filters
Selected filters ×                              Clear filters

Museum name · City, Country
  N works catalogued here · H selected highlights
  C recently confirmed on view / Display status not verified
  Explore collection →          Official visit information ↗

Museum detail: name · physical venue · official visit information
  Selection: All catalogued works | My must-see works | Museum highlights
  Display:   Any status | Confirmed on view
  Painter [several]   Movement [several]   Dates   More filters
  Artwork cards → right-hand record and full image viewer
```

Do not add empty Museums navigation before the reviewed institution backfill and
routes are ready. Counts always say **in Artline**, not a museum's entire holdings.
An illustrative card may use a rights-cleared artwork reproduction; no invented
museum photograph or empty image taking most of the card. Keep credits available.

### Filter rules and scope

| Screen / filter | Meaning and behavior |
| --- | --- |
| Timeline: Regions | Painter country associations; several values use OR. Not artwork location. |
| Museums: Museum regions, Countries, City | Physical venue geography. Values within one field use OR; different fields use AND. Retain selected chips even when no longer available. |
| Museums: Has highlights | At least one visible work selected by the chosen curator. Not inferred from popularity or rights. |
| Museums: Confirmed on view | At least one matching work with accepted, fresh on-view evidence at that venue. Unknown is not false. |
| Museum detail: Venue | For multi-site museums, choose the actual building. Holding institution and current venue may differ. |
| Museum detail: Selection | All catalogued works, My must-see works, or Museum highlights; both types can appear with separate labels. No universal masterpiece score. |
| Museum detail: Painter / Movement / Work type / Dates | Filters on the artworks and accepted attributions. Creation date is not the painter's lifespan. Include a separate unknown-date choice. |
| More filters: Image available | A usable, rights-cleared reproduction; not a prerequisite for listing important works. |
| Editorial Catalogue | Record status, source health, rights review and publication checks. Keep these out of public browsing. |

Use stable URL IDs, repeated parameters for multiple selections, individual chips,
counts and filter-preserving empty-state recovery. A selection in one page should
not silently reinterpret a painter-region filter as museum geography on another.
If showing option counts, compute each with the other dimensions applied but its
own selection excluded; do not remove checked options when they reach zero.

Initial museum sort: name, with city/country context. Initial collection sort:
creation year, stable title/ID tie-breakers. Within a curated selection use its
explicit editorial order, with a visible choice to sort chronologically. Avoid an
opaque “best” ranking. Pagination starts at 24 artworks, with a hard API maximum
and stable cursor. Never load a museum's full collection into browser memory.

Empty states distinguish no catalogued works, no highlights chosen, no confirmed
display information, and no matches for the current filters. An upstream outage
should not make the local museum page empty. Link to official visiting information;
do not copy opening hours, prices or bookability without a separate refresh design.

## What “masterpiece” should mean here

Recommendation pending the owner's choice: support **both**, visibly separated:

1. **My must-see works** — the owner's curated, ranked selection, with a short
   reason and optional supporting references. Personal importance is valid and
   does not need a fabricated museum endorsement.
2. **Museum highlights** — a designation made by the museum, with the exact
   supporting object page/API field and checked date. The Met's `isHighlight`
   is one possible source of that designation, not a global ranking.
   [Met Collection API documentation](https://metmuseum.github.io/).

Represent these as named collections with ordered membership, curator kind,
editorial state and attribution. Do not put an unexplained `is_masterpiece`
boolean on `artworks`. The same work can belong to both selections without being
duplicated in results. Museum selection must be independent of the painter's
5–10 representative works: a work can be important to a museum without consuming
one of those profile slots. Newly imported museum works still need accepted
identity/attribution and publication review; a highlight flag never publishes them.

For “masterpieces I can see at this museum,” intersect the chosen selection with
fresh, accepted display assertions at its venue. Display the checked date and
official record link. Do not promise availability during a future trip.

### Holding and viewing evidence

- Separate legal owner, collecting/holding institution, physical venue, gallery,
  temporary exhibition and loan relationship. “Held at” is not “on view.”
- Model display states as on view, explicitly not on view, and unknown. Storage
  or loan is additional sourced context, not something inferred from missing data.
- Keep historical observations, effective dates where supplied, retrieval time,
  source update time, parser version, review decision and supersession link.
  Null source dates stay null; retrieval time must not masquerade as source time.
- Proposed refresh target: seven days for tracked display records. After 30 days
  without sufficient confirmation, show “Last reported on view [date]” and remove
  the work from Confirmed on view. These are product policies, not museum guarantees.
- A transport failure is an import-health event, not a new location assertion.
  An explicit current correction can supersede a prior positive observation.
  An unchanged, successfully rechecked authoritative record may refresh verification;
  merely refetching a dated historical snapshot may not.
- When credible sources conflict, retain both and require review; until resolved,
  do not label the disputed venue confirmed. A borrowed work can count as on view
  at the destination without becoming a holding of that destination.

The Art Institute API explicitly distinguishes `is_on_view`, gallery information
and `on_loan_display`; use the documented field meanings, not a guess based on
the presence of a room number. [AIC API documentation](https://api.artic.edu/docs/).

## PostgreSQL model: extend, normalize, retain provenance

Proposed logical entities, not migrations applied this turn:

| Entity | Changes / purpose |
| --- | --- |
| `institutions` | Add stable slug, institution kind, canonical identifier review and editorial visibility. Keep existing UUID identity. |
| `institution_venues` | Institution FK, place FK, name/slug, official visit URL; separate building from organization. |
| `sources` + connector configuration | Extend existing sources with registry ID, kind/tier, explicit disabled-by-default connector, field capabilities and separate metadata/image policy. Existing `is_active` citation visibility must not mean “allowed to crawl.” |
| Source-to-institution mapping | Many-to-many: one network may describe several institutions; several sources can describe one museum. Authoritative mapping is reviewed, never based only on names. |
| External object records | Unique connector/source + upstream object ID; object URL, payload hash/version, local snapshot reference, observed time and normalized candidate fields. Link reviewed identities to canonical artworks. |
| Location assertions | Artwork, claim kind, institution/venue when known, source record/citation, state/context, effective and checked dates, acceptance/conflict/supersession. Preserve original wording. |
| Curated collections and items | Curator kind (owner/museum), owning institution when relevant, name/slug/status; artwork membership, position, short rationale and designation evidence. |
| Import runs / items | Bounded scope, connector/config version, actor, cursor, counts, retries and failures. Unique idempotency keys prevent duplicate processing. |

Use UUID foreign keys, booleans and `timestamptz`, not JSON strings containing
museum IDs or CSV lists in artwork rows. Small raw/source payloads can be JSONB;
filterable canonical fields and relationships belong in normalized columns.
Large raw payloads and image bytes stay in local files now; store references,
hashes, media metadata and explicit rights evidence in PostgreSQL. Use a private
storage abstraction so a later approved GCS change does not alter entity identity.
Cloud Run's writable filesystem is not the durable production store for ingestion.

Keep one documented source of truth for location. Accepted assertions may produce
a compact current-location projection for reads; update it transactionally with
review acceptance. Existing `current_institution_id`/location text can temporarily
be compatibility projections. Never maintain two independently editable truths.
Explicitly model no accepted assertion as unknown, not a made-up institution.

Backfill the 15 existing location strings through a reviewed mapping with exact
work/object references, then populate institution IDs without discarding text or
citations. Do not automatically split city names out of free text or merge
institutions based only on normalized name. Verify which records are institutions,
chapels or venues. Extend slug redirects to museums when their public routes exist.

Deduplicate incoming records by source-scoped object ID first. Accession numbers
are useful reconciliation evidence but must **not** be blindly unique, even
within one institution: the Met documents exceptions. Different impressions,
panels, versions and casts need their own object identities when the evidence says
so. Same title + artist does not prove same physical work.
[Met object identifiers and accession fields](https://metmuseum.github.io/).

Painter “Museums” sections are derived from accepted selected artworks, their
holding relationships and separately their known display venues. No manually
maintained `artist_museums` truth table. The UI should say “Selected works held
at,” and show loans/display destinations separately. Museum-wide artwork queries
must not reuse `artistArtworks`' representative-only, ten-record limit.

## Database optimization, sized to the actual application

Implemented now: the multi-region timeline predicate uses a parameterized
`text[]` and `EXISTS`. This avoids duplicating a painter with several countries or
relationship types. Totals, individual nodes and density bins share that same
predicate. Inputs are bounded, normalized and validated at the HTTP boundary.
No index or schema migration was needed for this change.

Existing useful indexes include artist status/year indexes, the reverse
`artist_countries(country_code, artist_id)` index, representative-work lookup and
entity-field citations. Eleven painters are not evidence of a scale bottleneck.
The existing plain name B-tree does not solve arbitrary substring search.

Optimization work for the approved museum milestone:

1. **Queries first.** Return a bounded card projection. Fetch citations/media and
   related venues in batches. `artistArtworks` currently queries citations once
   per work; replace that N+1 pattern before reusing the record loader for a
   paginated museum page. Preserve source visibility and bounded citation counts.
2. **Targeted candidate indexes.** Evaluate holding-artwork lookup by
   `(current_institution_id, status, id)`, venue place/institution lookups,
   current display by `(venue_id, display_state, checked_at)`, source objects by
   unique `(source_id, upstream_object_id)`, and collection items by
   `(collection_id, position, artwork_id)` plus reverse artwork membership.
   Use each actual query's equality/sort predicates to choose column order; avoid
   building every candidate automatically.
   [PostgreSQL 17 multicolumn index guidance](https://www.postgresql.org/docs/17/indexes-multicolumn.html).
3. **Search only as justified.** Evaluate `pg_trgm` GIN for normalized titles,
   museum names and aliases if substring search becomes slow. It supports
   non-prefix LIKE/ILIKE searches; very short/no-trigram queries can still scan
   broadly. Do not introduce Elasticsearch just to search this catalogue.
   [PostgreSQL 17 trigram indexes](https://www.postgresql.org/docs/17/pgtrgm.html).
4. **Avoid multiplying joins.** Use EXISTS or pre-deduplicated artwork sets for
   geography/highlight filters and counts. Holdings and visiting loans require
   separate membership semantics, not a single `museum_id` OR joining every
   historical assertion. Count distinct works, not assertion or image rows.
5. **Measure representative growth.** In an isolated fixture database, test 10k
   and 100k artworks, multiple venues/attributions per work, sparse/unknown dates
   and stale evidence. Save `EXPLAIN (ANALYZE, BUFFERS)` for read-only search,
   counts, facets and detail queries. Compare plans before/after candidate indexes
   and report API p50/p95 on the same machine; no performance target is claimed
   achieved by today's small seed. [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/17/using-explain.html).
6. **Cache only after correctness.** Prefer a normal view/current projection
   initially. Consider materialized counts only if measured cost warrants refresh
   complexity. Any cache key includes canonical filters and visibility mode;
   unpublished results never share a public cache. Account for time-driven expiry
   of on-view claims, not just content edits. Do not encode `now()` into a moving
   partial-index predicate; store checked timestamps and compare a request cutoff.

Keyset pagination needs stable sort keys, an ID tie-breaker, explicit null-date
ordering and cursors bound to the current filter/sort set. Reset pagination when
filters change. Counts, cards, facets and details must use the same publication
rules. No need for PostGIS, a search service or a separate analytics database in
the first museum milestone.

## Safe source onboarding, not bulk collection downloading

The registry is a discovery allowlist, not an instruction to fetch 111 sites.
Start with disabled metadata connectors. Require explicit per-source object/page
limits, painter/object scope and dry-run preview before a run. Normalize fields
to review candidates; source data cannot overwrite an editor's accepted facts
without a conflict/review path. Preserve attributions such as workshop/formerly
attributed, original language, uncertain dates and unknown values.

Use official Met and AIC documentation as two initial adapter candidates, not as
already-completed adapters. For the Met, plan against the currently documented
versioned search/pagination contract and record API version in fixtures; do not
assume a legacy unbounded search response. Confirm terms, rate limits and the
specific endpoint contract immediately before enabling either connector.
[Met API](https://metmuseum.github.io/), [AIC API](https://api.artic.edu/docs/).

An authorized pilot should be metadata-first, limited to a few named painters or
existing works, with a small hard item budget. Expand to the supplement's broader
source-family/institution coverage only after identity, provenance and retry
tests pass. The registry's rights/download rules are varied; do not flatten them
into “images allowed.” Unknown, conflicting, NC/ND or restricted reproduction
terms remain link-only/manual-review by default. IIIF, a downloadable URL or an
old painting does not grant reproduction permission. No new images were fetched
for this turn.

Before any live adapter: exact HTTPS host allowlists, resolve/check addresses,
reject private/link-local/cloud metadata destinations, and repeat checks across
redirects and actual connections. Restrict API, object-page and media hosts
separately. Enforce timeouts, response byte/pixel limits, MIME checks, safe local
paths and bounded redirects; protect against compressed payload bombs. Do not
enable generic arbitrary-URL fetches from a catalogue field. Follow official rate
limits, Retry-After and robots/terms where applicable; use bounded backoff and a
resumable cursor. Keep tokens out of URLs, logs and saved payloads. Record hashes,
parser versions and run IDs; make retries idempotent and conflict-visible.

## Delivery order and acceptance gates

| Milestone | Deliverable | Acceptance gate |
| --- | --- | --- |
| 0 — this turn | Remove timeline status; multi-region UI/API; registry audit and this plan | OR/AND, legacy bookmarks, publication boundary, keyboard/mobile and density regressions pass. No museum routes or DB migrations. |
| 1 — approved foundation | PostgreSQL schema additions, disabled registry configuration, reviewed backfill of existing locations | Source/network identities do not become fake museums; existing records and citations retained; no automatic publication or downloads. |
| 2 — local museum browsing | Museums list/detail, venue/location filters, separate curation types, right-panel artwork access | Counts and filters agree; known holdings do not imply on-view; representative-work cap does not truncate museum lists; mobile/keyboard/deep links work. |
| 3 — bounded ingestion | Dry-run/review workflow, two initial metadata adapters, field provenance and rights gates | Scope/item limits, deduplication, collisions, retries, parser-change fixtures and SSRF tests; no silent editor overwrite. Additional adapters are separately scoped. |
| 4 — display freshness and scale | Scheduled tracked-record refresh, stale/conflict behavior, measured query tuning | Outage never means not-on-view; loan destination differs from owner; time expiry removes confirmation; performance report on growth fixtures. GCP scheduling/storage changes require approval. |

For museum QA, include one museum with two venues, a loaned masterpiece, an unknown
display status, two impressions with the same title, an accession collision,
conflicting location sources, missing/forbidden imagery and a private draft
selection. Those cases matter more than a large number of imported records.

## Verification of this turn

Filter changes are covered by Go parser/HTTP tests, PostgreSQL OR/AND/public
visibility checks, a rollback-only 305-painter multi-region density fixture, URL
state unit tests, and Chrome interaction/accessibility/responsive tests. Browser
screenshots are in `docs/screenshots/regions-{1440,390,320}.png`. The in-app browser
runtime was unavailable; verification uses the project's isolated Chrome suite.

Final results on 8 September 2026:

- `go test ./...`: passed.
- Database-backed `go test ./internal/catalog -count=1`: passed, including the
  305-painter density fixture with multiple countries/relationship types.
- `npm test -- --run`: 18 tests passed.
- `npm run test:e2e`: all 24 tests passed. The four region tests passed again
  after adding explicit checks for the mobile Reset view control.
- `npm run lint` and `npm run build`: passed.
- Desktop and 320px/390px menu screenshots inspected; selected labels remain
  readable, panels stay within the viewport, and automated WCAG 2.2 AA rule
  scans report no violations. These scans are not a full accessibility certification.
- Registry structural audit: 111 rows parsed; no structural issues flagged by
  its limited checks, 11 missing sample links identified. No live endpoint or
  reproduction-rights validation is claimed for the whole registry.

Museum screens, museum queries, schema additions, curation and ingestion remain
**proposed**, not implemented or tested. Nothing has been committed, deployed,
published or applied with Terraform.
