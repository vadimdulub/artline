# All browsing implementation — 12 October 2026

Implemented and deployed the next stage of the [second performance review](performance-20261012-round2.md).
The API revision `artline-api-atlas-browse-1012-v1` receives 100% of traffic.
The existing web release, service resources, connection pool and admission limits remain unchanged.

## Measured results

Sequential requests to the previous API and the candidate returned identical complete JSON responses.
The following times include connection setup and transfer. Both first responses were HTTP cache misses.

| Request | Previous API | Candidate |
| --- | ---: | ---: |
| Broad illustrated artworks, 23 items | 7,931 ms | 515 ms |
| Original Romanticism selection, 150 items | 1,098 ms | 694 ms |
| Rossetti artwork search, 23 items | 657 ms | 508 ms |
| Broad Japan country filter, 23 items | 2,536 ms | 2,990 ms |

The broad artwork improvement is approximately 94%. Its next page took 246 ms,
with an HTTP response-cache miss but reusable aggregates. All three lanes together
returned in 385 ms after the artwork aggregate had been warmed; that is not an
independent cold-aggregate measurement.

After promotion, public requests through `artlines.org` measured:

| Public request | Total time | HTTP cache |
| --- | ---: | --- |
| Fresh All request, all three lanes | 606 ms | MISS |
| Next page, same selection | 268 ms | MISS |
| Repeated first page | 253 ms | HIT |
| Original Romanticism request | 589 ms | MISS |

The fresh All request used a previously unrequested date window, `start=-11998&end=2000`,
with 22 items per lane, to obtain a fresh semantic aggregate without purging caches.
These are observed requests, not p95 measurements or cold-instance/cold-buffer guarantees.
The broad country-only case remains around three seconds and was slightly slower in
this comparison; geographic filtering still needs further optimization.

## Database and query changes

Migration `0054_atlas_browse_projection.sql` adds a narrow derived browsing table
containing eligible illustrated artwork IDs, dates, gallery priority, image identity,
work type, cultural context and highlight membership. Ordered indexes support
cursor pages. A reverse primary-media index was built concurrently before installing
the migration, avoiding a blocking index build on the artwork table.

The initial refresh processed 302,407 candidates in 73.6 seconds and produced
302,149 browsing rows with no pending IDs. Later source-backed imports account for
small count increases during verification. The projection and its indexes occupied
about 93 MiB. No original catalogue metadata, historical status, images, holdings
or account data were changed by this work.

Totals and timeline density now group identical date ranges before accumulating
weighted bucket changes. They are independent of the bounded detail page. The
aggregate cache includes the complete SQL/filter scope and the catalogue revision,
while excluding the page cursor and page size. Each repository cache is bounded to
128 entries, 4 MiB, 128 KiB per entry and a one-minute TTL. Concurrent identical
loads share a calculation; failures and cancelled loads are not cached.

Each request uses a read-only repeatable-read transaction. Its catalogue revision,
aggregate calculation, page and image enrichment therefore describe one snapshot.
A projection refresh does not change catalogue semantics or invalidate aggregates;
a source change does through the existing revision triggers.

Clean projection rows and pending source rows are queried separately before their
local page limits are combined. This matters: PostgreSQL initially sorted the full
union before applying the limit. The final plan uses an ordered index scan and
merges bounded candidates. Text searches retain a single search relation per query;
empty lanes skip their page query altogether.

A representative broad artwork plan on 302,157 matching records measured:

- Aggregates: 251.9 ms, 3,487 shared-buffer hits, no temporary blocks written.
- Page: 13.0 ms, 510 shared-buffer hits, an index-only browse scan returning 25 IDs.
- Image enrichment: 0.34 ms for the bounded page.

The preceding review's combined query took 4,829 ms, with 711,563 buffer hits and
about 97.3 MiB of temporary writes. Database `work_mem` remains 4 MiB. No global
memory increase or additional service capacity was used.

## Refresh correctness and operation

Statement-level transition-table triggers mark affected artwork IDs transactionally
when eligibility dependencies change: artworks, creator links/status, primary-image
paths, holdings, institutions, sources and curated selections. Relevant bulk edits
are batched. Unrelated title/credit edits do not rebuild eligibility rows.

Readers exclude dirty projection rows and evaluate those IDs directly from source
records until refreshed. Imports, archival, image removal and source deactivation
therefore take effect without waiting for the worker. Legacy review/publication
statuses remain audit data; archives are excluded and holdings do not imply display.

The worker locks markers, reads sources in a subsequent READ COMMITTED statement,
refreshes only those IDs, then removes the locked markers. Invalidators use conflict
updates so a concurrent source writer leaves a new marker after the worker commits.
The isolated concurrency test proves this case rather than assuming trigger order
alone prevents lost updates.

The deployed API polls every five seconds, refreshes at most 500 IDs per batch with
a four-second deadline, and uses a shared advisory lock to serialize refreshers.
Local-debug and `--skip-migrations` previews do not start this writer. Cloud Run CPU
throttling can defer background work; the live overlay preserves correctness, though
large pending import batches may temporarily increase read cost. Monitor
`SELECT count(*) FROM artwork_atlas_dirty` and `atlas browse refresh deferred` logs.

## Validation and release

- Atlas, HTTP API and API-command packages passed Go tests with race detection.
- An isolated PostgreSQL 17 cluster under `/tmp` applied every migration. Tests covered
  source/image/status/date/creator/curation changes before and after refresh, rollback,
  deletion, a blocked concurrent writer, snapshot consistency, aggregate reuse and
  empty-search query elimination. The real local database was never written.
- Twelve production read-only A/B scenarios matched the old implementation in a
  single snapshot, including complete density arrays, ordering, cursors and neighbors.
  Search and empty-result changes received additional comparisons afterward.
- Discovery filters, picked entries and all three navigation lanes passed production
  read-only regression checks. Gallery checks passed after updating their expected
  indexed table from the original artwork table to the new browsing projection.
- Candidate HTTP responses matched the existing API for broad artwork/All views,
  Romanticism, country filtering and search. Pagination preserved totals/density and
  returned distinct IDs. Painters, Books and Events endpoints remained healthy.
  Museum access still returned 401 and invalid dates returned 400. These expected
  responses were the only warning-level candidate request logs; no application errors
  were observed during verification.
- The release used the exact prior deployed build plus seven explicitly hashed source
  files, preserving unrelated local work and the existing event-artwork expansion.
  No commit or Terraform apply was performed. The local API image pin was updated.

This verifies current production data, not the ten-million-artwork capacity target.
Sustained concurrency, very large pending import batches, cache churn during heavy
writes and large country-only filters remain performance work.

The [deployment receipt](deployment-20261012-atlas-browse.json) records the image,
build and checks. Detailed plans, source preimages, comparison logs, migration receipt
and operational scripts are archived under
`/Users/vadimdulub/Library/Application Support/Artline/backups/atlas-browse-20261012/`.
The temporary reference implementation was archived and removed; the disposable
PostgreSQL cluster was stopped.

Rollback consists of routing the API back to
`artline-api-event-artworks-expansion-1012-v1`, only if no newer release supersedes
this deployment, and restoring that API image pin. The previous API ignores the new
derived tables. Keep the additive migration in place; do not drop source data or
reset catalogue revisions.
