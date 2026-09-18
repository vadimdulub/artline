# Artline

Artline is a chronological catalogue for exploring painters, their working lives,
movements, places, artworks, and museum collections.

## Content scope

The catalogue focuses on artworks **created by 1970, inclusive**: curated
masterpieces/highlights or works with a documented museum connection. Painters
may have lived beyond 1970; the cutoff applies to artworks, not lifetimes.
Museum holdings are not automatically described as currently on view.

The aim is a useful curated atlas, not an exhaustive download of every painter's
output. Select metadata first, then obtain only the chosen reproductions with
verified reuse terms. Unknown dates and ranges crossing the cutoff need review;
they are not silently assigned an eligible year.

The Go importer and painter-publication validator now enforce this scope. The
PostgreSQL policy function has parity tests against Go. Existing research records
are preserved; eligibility alone never publishes a record. Unknown/open-ended or
crossing-cutoff dates cannot be automatically accepted by the importer.

## Stack

- Next.js App Router frontend in `apps/web`
- Go HTTP API in `apps/server`
- PostgreSQL for structured catalogue data
- Markdown with YAML front matter for painter essays
- Local image assets under `apps/web/public/assets`; production images in Cloud Storage
- Production-only Google Cloud infrastructure under `terraform/prod`

## Repository and deployed data

This repository contains application source, migrations, curated selections,
research notes and deployment configuration. Local environment files, Terraform
state and credentials, downloaded source catalogues, generated research
inventories, run outputs and artwork image files are excluded from Git. These
files remain in their local locations; cloning this repository does not restore
the populated database or image collection. See
[local data locations](docs/LOCAL_DATA_LOCATIONS.md) for retained evidence and
backups.

Editor browser tests read `ARTLINE_E2E_EDITOR_TOKEN` from the test process
environment. Supply a token for a disposable test environment when running
tests that edit records; do not run those tests against the real catalogue.

The deployed website uses Cloud SQL and serves images from the private
`artline-508319-images` bucket through its `/assets/...` route. It runs an
explicit public research preview, showing review records without publishing
them; editing still requires authentication. Deployment details and validation
are recorded in [the GCP deployment receipt](docs/deployment-20260912.md).
The Catalogue supports bounded, read-only browsing without an editor token.
Archived records and editorial operations remain restricted to the editor.

## Local setup

Use Node 24 (see `.nvmrc`) and Go 1.24 or later.

Create the database and environment files:

```bash
createdb artline
cp apps/server/env.example apps/server/.env
cp apps/web/.env.example apps/web/.env.local
```

Run migrations and the API:

```bash
make migrate
make server
```

In another terminal, install and start the web application:

```bash
make web-install
make web
```

Open <http://localhost:3000>. The web application proxies `/api/backend/*` to
the Go API at `http://localhost:8080`.

Set `ARTLINE_EDITOR_TOKEN` in `apps/server/.env`. For local catalogue changes, enter that value from
`apps/server/.env` in the Catalogue editor-token field. Replace that local
value whenever the project is shared; production receives a separate token
from Secret Manager.

To see unpublished records locally, set `ARTLINE_RESEARCH_PREVIEW_TOKEN` in
`apps/web/.env.local` to the same value. This read-preview option is honored
only by `next dev`; the production build ignores it. It is not sent to browser
JavaScript. Catalogue and must-see selection mutations still require the editor-token field.

The original seed migrations create 11 review painters, 15 review artworks,
15 local images, and audit/slug-history triggers. The eighth migration adds
ingestion evidence and policy/search indexes. The owner-requested local import
is separate from the seed: see [curated import results](docs/curated-ingestion-results.md).
In the original seed every painter has at least one illustrated work; Giotto has five. The
original prototype's 28 painters and 140 artworks were not supplied. Records
remain in review. Published-only reads exclude them; the deployed public
research preview explicitly includes review records.

## Painter chronology and scale

Click a painter on the timeline to open **Artworks by year** in the right-hand
panel. It covers all catalogued artworks, not only the ten representative profile
slots. Choose a recorded year or browse bounded pages. Original approximate/range
labels remain visible; undated works appear last with a dashed end marker and an
explicit explanation. No artwork data is distinguished from a failed request.

Capacity planning allows for **20,000 painters and 10 million artworks**, not a
quota to import or download. Go and
PostgreSQL compute date classification, year groups, counts, extent, filtering,
ordering and cursor pagination. Next.js renders the returned groups. Requests
start with an indexed painter lookup; full artwork rows, media and source details
are loaded for the bounded page (24 by default, maximum 60).

Painter and museum-scoped paths have isolated 100,000-row query-plan tests; the full application
has **not** been load-tested at 10 million rows. See
[chronology implementation and scale notes](docs/painter-artwork-chronology.md).
The scale constraints are also recorded in `AGENTS.md` for subsequent work.

## Museums and must-see works

Open <http://localhost:3000/museums>. The original seed contains seven museums
and holding collections and eight physical venues. The curated import additionally
represents Cleveland, Chicago and the Prado, with sourced museum highlights and holding links.
Personal must-see lists remain distinct from institution designations.

Museum regions and countries support multiple choices. Each collection offers
artwork search, painter/movement/date/venue filters, selection ordering, pagination,
and full artwork details in the right-hand panel. Museum counts cover only Artline
records. A holding collection is not a promise of current display: no on-view
assertions have been seeded. The Confirmed on view filter therefore starts empty.

To curate your own list, expand **Edit my must-see list** on a museum page and
enter `ARTLINE_EDITOR_TOKEN`. Open an artwork, choose **Include in my must-see
works**, optionally add a reason, set its order, and save. Saved changes remain
in review. Revision checks reject conflicting edits without silently overwriting
the saved list. This is a single-owner editorial tool, not per-visitor accounts.

See [the museum implementation notes](docs/museum-implementation.md) for schema,
evidence, tests and limitations. The 111-source registry is not bulk-imported;
source connector placeholders remain disabled. Curated imports run only through
the explicitly invoked Go CLI; there are no unattended ingestion jobs.

## Curated local import

The timeline defaults to **Only popular painters**: the imported Pantheon top
100 with documented editorial corrections (include Hokusai, exclude Donatello).
Uncheck it to browse all records. `popular=false` persists in URLs; Reset view
restores the default and Clear filters removes it. The ninth migration stores
discovery selections independently from image coverage and publication status.
Counts, chart bins and filter choices use the backend selection predicate.

The local catalogue now has a sourced 1,000-painter candidate cohort, with bounded
museum highlights and explicitly labelled personal selections of museum holdings. This is not a definitive artistic ranking
or a complete set of illustrated profiles. Pantheon HPI supplies a reproducible
popularity proxy; Wikidata adds source-labelled review metadata. Coverage and
rights gaps are reported, not filled with invented masterpieces or images.

```bash
cd apps/server
go run ./cmd/ingest-curated -source pantheon                 # preview cohort
go run ./cmd/ingest-curated -apply -images                   # bounded museum import/resume
go run ./cmd/ingest-curated -apply -source wikidata          # review metadata enrichment
go run ./cmd/ingest-curated -source prado -run prado-highlights-2026-09-08 -apply -images
go run ./cmd/ingest-curated -source uffizi -run uffizi-coverage-2026-09-08 -apply
go run ./cmd/ingest-curated -source mam -run mam-coverage-2026-09-08 -apply
go run ./cmd/audit-curated                                  # read-only asset/data audit
```

Imports are restricted to local PostgreSQL and a source-host allowlist. Requests
are rate-limited; records retain source snapshots/hashes; existing edits are not
overwritten. New API images require explicit CC0 evidence; the Prado crosswalk
uses separately verified Commons public-domain reproductions. Both require a source snapshot no older
than 24 hours, validated JPEG/PNG bytes, and checksums. The image budget is 512 MiB
per execution, 20 MiB per file. A new `-run` name obtains fresh source snapshots.
`-max-works` bounds each invocation's selections per painter, not lifetime output;
individual-source enrichment may add to earlier selections. No auto-publication.
The explicit Prado adapter uses a reviewed twelve-work manifest instead of
`-painters` / `-max-works`; it does not run as part of the automatic `all` API slice.
The Uffizi and Museo de Arte Moderno adapters likewise use fixed, bounded manifests
(nine and one works). They currently import metadata only: unresolved image-use
permissions block image downloads even with `-images`. Museum designations and
personal must-see picks remain separate. Replay preserves owner edits and removals.
See [the discovery review](docs/popular-painters-review.md) and
[reviewed source notes](content/curation/README.md). The latest totals and remaining
gaps from that pass are in the [museum-coverage follow-up](docs/museum-coverage-followup.md).

The [European research import](docs/european-import-verification.md) adds 58 works
and 25 institutions for Bosch, El Greco, Monet and Pissarro. It preserves qualified
attributions, alternate titles, loans and uncertain dates, with no image downloads
or automatic masterpiece designations. Local totals after this pass: 445 artworks
and 36 institutions; records remain unpublished.

```bash
cd apps/server
go run ./cmd/migrate
go run ./cmd/ingest-european          # full transaction preview, rolled back
go run ./cmd/ingest-european -apply   # local-only, idempotent reviewed snapshot
```

Optional `-report /path/to/new-receipt.json` writes a non-overwriting JSON receipt.
The offline importer pins the researched manifest's SHA-256: editing that inventory
requires deliberate review/versioning, not automatic ingestion of new content.
Back up the database before applying a new batch. Existing published/editorial
content is not overwritten; identity conflicts roll back the entire batch.

Focused browser checks against the current local catalogue:

```sh
cd apps/web
npm run test:e2e -- e2e/discovery.spec.ts e2e/museum-coverage.spec.ts
```

## Implementation status

This is **not the complete implementation** of `CODEX_IMPLEMENTATION_SPEC.md`.
See [the feature audit](docs/spec-audit.md) for every requirement, supporting
code, test evidence, and remaining work. The original downloaded specification
has not been modified.

Database-backed fixture tests require a separately provisioned disposable database.
Never point `ARTLINE_TEST_DATABASE_URL` at the real local or production catalogue;
do not create a test database during collection work. If an approved disposable
database is already available:

```bash
cd apps/server
ARTLINE_TEST_DATABASE_URL='<approved-disposable-database-url>' go test ./internal/catalog
```

Publishing is fail-closed. Before a painter can move from review to published,
the API checks the biography, classifications, geography, citations, and a set
of 5–10 fully reviewed representative works. The Catalogue page lists each
remaining issue and uses record revisions to reject stale updates.

## Content and images

Painter essays live in `apps/web/content/artists/<artist-slug>.md`. Markdown is
used for prose; YAML front matter holds small, queryable document metadata.
Structured catalogue fields remain in PostgreSQL.
The database's `biography_md` is the short, publication-validated profile;
Markdown files hold optional longer essays. A draft/review essay is never
rendered to public readers. Editing an essay does not update the database bio.

Artwork and portrait files belong in:

```text
apps/web/public/assets/artworks/
apps/web/public/assets/artists/
```

Only add an image after confirming its reuse terms. Record its source, rights,
credit, and attribution in PostgreSQL before displaying it.

The September selection is documented in
[`content/artworks/selection-2026-09.json`](content/artworks/selection-2026-09.json).
It records object-specific museum sources, image file pages, rights notices,
credits, alt text, dimensions, byte counts, and SHA-256 checksums. The files total
30.6 MiB; responsive delivery uses Next.js image optimization. Some Giotto
reproductions have modest source resolution. No generated stand-ins are used.

Run `node ops/verify-artwork-assets.mjs` from the project root to check all assets.
This manifest describes a curated seed, not an import/upload workflow. Editing
it does not automatically modify the database; use an additional migration or
the future structured artwork editor. Unsourced creation places remain unknown.

## Production

See `terraform/prod/README.md`. Terraform defines two Cloud Run services and a
Cloud SQL for PostgreSQL instance. Assets and Markdown are baked into the web
container, so production content updates currently require a new image build.

## Verification

`go test ./...` runs backend validation and authorization tests. Set
`ARTLINE_TEST_DATABASE_URL` to run PostgreSQL integration tests as well; added
test records live inside a transaction that is rolled back.

From `apps/web`, run `npm run lint`, `npm test`, and `npm run build`.
`npm run test:e2e` uses installed Chrome and the running local API and
development frontend. It expects the review seed and the configured local
development editor token. Screenshots are saved to `docs/screenshots`.
The suite includes Axe accessibility scans (including WCAG 2.2 AA rules), responsive overflow checks from
320px to 1440px, drawer/image-viewer focus and history, error recovery, and all
15 local artwork records. It does not constitute a complete WCAG certification.

See [the UI/UX review and implementation plan](docs/ui-ux-review-plan.md) for
priorities, corrections, verification evidence, and remaining limitations.
The [second review](docs/ui-ux-review-round-2.md) compares museum collection
patterns and W3C guidance, and records improvements to image zoom, keyboard
focus, timeline controls, filtering, and catalogue feedback.

The [museum and filter plan](docs/museums-and-filter-plan.md) records the supplied
111-source registry audit, the implemented multi-region timeline filters, and
the phased museum browsing, must-see selection, display evidence and PostgreSQL
optimization work. Museum browsing and the local schema foundation are now built;
live ingestion, display refresh jobs and bulk-scale performance validation remain
future milestones.

## Catalogue continuation - 10 September 2026

The preceding continuation brought the local catalogue to **63,073 artworks**, up **28,809**:
26,295 from France's Joconde export, 2,075 from Milan SIRBeC, and 439 new Pushkin
paintings. These are museum-connected review records, not 63,073 validated
masterpieces: 9,985 paintings, 24,133 drawings, 28,950 prints and 5 frescoes.
All new works pass the creation cutoff; two preexisting records still need date
review. There are 5,315 artists and 280 institution/collection rows (not necessarily
280 distinct physical museums). No new images were downloaded in this pass;
the existing 230 media assets were preserved. Nothing was published.

The offline Go importer only accepts the checksum-pinned v3 selections. From
`apps/server`, preview a source using a **receipt directory that does not yet exist**:

```sh
go run ./cmd/ingest-continuation \
  -dir ../../docs/research/catalogue-continuation-20260910/sirbec-v3 \
  -reports ../../output/sirbec-manual-preview
```

The same command accepts `-apply` after backup and review; use a different
receipt directory. Other reviewed selections are `joconde-v3` and
`pushkin-kamis-v3`. They have already been applied locally; unchanged replays
are no-ops. New source contents require a separately reviewed version and new
checksum pins. The importer does not fetch network data or create artist
authorities. A chunk is atomic, but completed earlier chunks remain committed
if a later chunk fails; receipts and idempotency keys make resumption explicit.

All 59 rollback previews, applied chunks and replays passed, with unchanged
14-table fingerprints for preview/replay. Full Go integration tests, `go vet`,
26 API checks and both 100k-fixture query-plan tests passed. This is not a
10-million-row benchmark. See the [progress report](output/pdf/catalogue-expansion-september-10.pdf)
and [research log](docs/research/catalogue-continuation-20260910/research-log.md)
for source terms, deferred records, actual receipts and remaining coverage.

## Museum registry expansion — 10 September 2026

The latest verified total is **104,721 artworks**, with **41,648 added** in this
wave: 21,196 Met, 9,835 Cleveland, 323 across 14 Lombardia institutions, and
10,294 Art Institute of Chicago works. Another 241 records matched existing
artworks instead of creating duplicates. There are 5,315 artists and 294
institution/collection rows; the latter is not a count of distinct physical museums.

Types: 13,737 paintings, 32,005 drawings, 58,974 prints and 5 frescoes. All newly
added records have descriptions, source evidence, creation dates within the
1970 cutoff and unpublished review status. They are museum-connected records,
not automatically validated masterpieces. The two older unresolved-date records
remain preserved. No new images were downloaded; 230 existing media assets and
their rights evidence were preserved.

The [museum/source CSV](docs/research/all-museums-20260910/museum-register-after.csv)
has 5,937 overlapping entries, exact local coverage and a bounded access audit
of the supplied 111 catalogue routes. Discovery candidates are not confirmed
museums, null counts are not zero, and reachable routes are not complete imports.
The [research log](docs/research/all-museums-20260910/research-log.md) records
source licences, actual catalogue dates, exclusions, backup and remaining gaps.
Chicago's captured export is from February 2025; its descriptions are CC BY 4.0,
not CC0, and include attribution/licence links. Its old display flags are not
promoted to current on-view claims.

Reviewed selections: `met-v2`, `cleveland-v2`, `lombardia-v1` and `chicago-v1`
under `docs/research/all-museums-20260910/`. From `apps/server`, a read-only
preview uses a new receipt directory:

```sh
DATABASE_URL='postgres://localhost/artline?sslmode=disable' \
go run ./cmd/ingest-continuation \
  -dir ../../docs/research/all-museums-20260910/chicago-v1 \
  -reports ../../output/chicago-manual-preview
```

These manifests are already applied locally; unchanged runs are no-ops. Do not
edit pinned chunks to add content—capture and review a new version instead.
No remote DB import, publication, deployment, Terraform apply or commit was made.

All 85 chunks passed rollback preview, apply and unchanged replay, with 15-table
fingerprints. Final Go integration tests, `go vet`, three isolated 100k-row query
plan tests, 31 API requests, and every CSV cell's JSON read-back comparison passed.
The [receipt summary](output/campaign-final-summary-20260910.json) contains the
actual counts. This is not a 10-million-row/concurrent production benchmark.
The broader museum campaign remains incomplete—for example, local Louvre and
Prado coverage is still only 13 and 21 works respectively.

## European images and large-collection browsing — 10 September 2026

The subsequent European wave added **912 paintings**: 888 from SMK in Copenhagen
and 24 from the Rijksmuseum. Six existing SMK records were matched, not duplicated.
Current totals: **105,633 artworks**, 5,315 painters and 294 collection records.
All additions remain in review, with creation dates ending by 1970.

**80 authentic public-domain SMK images** are stored in
`apps/web/public/assets/artworks/imported/`, each under 100,000 bytes
(5.94 MB total). Verify them with `node ops/verify-europe-images.mjs`.
Open `/museums/statens-museum-for-kunst?image_only=1` to browse them locally.

Collection browsing now offers denser Grid/List layouts, 24/48-item pages,
Previous/Next navigation, image-only filtering and a European museum shortcut.
The directory's counts, facets and cover queries were optimized in Go/PostgreSQL;
the browser still receives bounded pages. The existing atlas styling and
right-hand artwork panel are preserved.

See the [design plan](docs/europe-ui-images-plan.md) and
[European research/import report](docs/research/europe-ui-20260910/research-log.md)
for provenance, rights, backup/receipts and remaining coverage limits.
No commit, publication, deployment or Terraform apply was made.

### Normandy regional museums — 10 September 2026

Added 288 source-backed paintings: catalogue total 105,921; MuMa Le Havre now
49 works and Rouen 245. Thirty MuMa museum-designated highlights are linked.
All remain in review; no new photographs or current-display claims were added.
The [Normandy report](docs/research/normandy-20260910/research-log.md) includes
a 90-entry museum coverage audit, source exclusions, backup and test receipts.

Russian icons, Greek artists and Byzantine/post-Byzantine art are explicit
collection priorities. See the [priority checklist](docs/russian-greek-byzantine-priority.md)
for sources and the anonymous-creator/pre-1100 gaps that still need modelling.
