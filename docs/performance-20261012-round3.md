# Performance research, round 3 — 12 October 2026

Broad geographic browsing is the next useful optimization. The deployed broad
All query is fast, but country/continent filters still construct geography for
the whole eligible artwork collection before filtering it. A read-only SQL
prototype substantially reduced this work with identical results. It must be
used selectively: applying it to the original Romanticism selection caused a
large regression. Preserve the existing query for tightly selected creators.

This round changed no application code, schema, catalogue data or deployment.
The real local database was not used. Production SQL experiments ran read-only;
the pending-refresh experiment used query-local CTEs, without fixtures or writes.

## Baseline and method

- API: `artline-api-atlas-browse-1012-v1`, receiving 100% of traffic.
- Web: `artline-web-event-artworks-1012-v2`, receiving 100% of traffic.
- The seven API implementation/migration files match the hashes in
  [the deployed release manifest](deployment-20261012-atlas-browse.json).
- Projection during the baseline experiments: 302,162 eligible illustrated
  artworks. Observed pending queue: 0.
- PostgreSQL `work_mem`: 4 MB; no configuration changes.
- 38 sequential public HTTP requests, including repeats and cursor pages.
- Captured production SQL, then `EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON)`.
  Geography variants were compared within the same read-only repeatable-read
  transaction, including every returned aggregate and page result column.
- These are observed timings, not p95 measurements, a concurrency benchmark,
  cold-disk tests, or validation at ten million artworks. Diagnostic queries
  themselves contribute to database load.

## Public HTTP measurements

Seconds, including the public web proxy and network. “Miss” means the HTTP
response cache reported `MISS`; it does not imply cold PostgreSQL buffers.
All 38 requests returned HTTP 200. Repeated requests reported `HIT` for the
cached routes. Exhibitions did not expose the catalogue cache header.

| Route / selection | First response, miss | Repeat | Next page, miss |
| --- | ---: | ---: | ---: |
| All, broad, all types | 0.444 | 0.145 | 0.267 |
| All, artwork, Japan | 3.668 | 0.146 | 1.971 |
| All, artwork, France | 3.745 | 0.204 | 2.060 |
| All, artwork, Japan or France | 3.268 | 0.154 | — |
| All, artwork, Asia | 2.934 | 0.233 | 1.613 |
| All, artwork highlights | 0.532 | 0.149 | — |
| Original Romanticism selection | 0.376 | 0.158 | — |
| Painters, default | 0.661 | 0.143 | — |
| Painters, all | 0.496 | 0.144 | — |
| Painters, search | 0.535 | 0.150 | — |
| Books, default | 0.483 | 0.335 | — |
| Books, all | 0.407 | 0.253 | — |
| Books, author view | 0.987 | 0.251 | — |
| Events, default | 0.380 | 0.197 | — |
| Events, all | 0.437 | 0.175 | — |
| Events, search | 0.453 | 0.338 | — |
| Exhibitions, first / repeat, cache unknown | 0.200 | 0.429 | — |

The broad/geographic All probes requested 21 items per lane. Native book
summaries requested 300 items, and the author view requested 150. Full request
paths and headers are preserved in the evidence archive. Checked cursor pages
did not repeat IDs from their first pages.

The native book author query took 429 ms of database execution in a separate
trace. It is a smaller opportunity than geographic All browsing. This round did
not authenticate into museum or account routes, so it does not establish their
performance.

## Why geography remains slow

In [the repository query builder](../apps/server/internal/atlas/repository.go),
any artwork geography predicate currently enables the shared
[`artworkGeographyScope`](../apps/server/internal/atlas/artwork_scope.go).
The Japan plans materialized 302,162 candidate artworks, 260,081 artist links
and 276,279 geographic rows before applying the country condition. Both the
aggregate and the page query did this work. Limiting the returned page to 21
items therefore did not bound the geographic preparation.

Each main Japan query wrote 9,882 temporary 8 KiB blocks, approximately 77.2 MiB.
Together the first-page aggregate and page queries wrote approximately 154.4 MiB.
Both plans reported zero shared-buffer reads: this remained expensive when the
source pages were already in PostgreSQL's cache. Subsequent pages can reuse the
aggregate cache, but still repeat the expensive page preparation.

PostgreSQL documents that a materialized CTE can prevent parent restrictions
from being pushed into it; inlining can instead duplicate work. Both effects
appeared in these experiments.
[PostgreSQL CTE documentation](https://www.postgresql.org/docs/17/queries-with.html#QUERIES-WITH-CTE-MATERIALIZATION)

## A useful prototype, with a necessary restriction

The prototype first finds artwork IDs through country/region → active creator
country links or documented production places, then applies the existing
artwork eligibility, selection, date and page predicates. It reuses the form of
the existing indexed
[`artworkGeographyMatch`](../apps/server/internal/atlas/geography.go), removes
the shared geography materializations and allows the native scope to be inlined.
No index or schema change was needed for these experiments.

Database execution seconds for the aggregate and page statements, excluding
planning, network, image enrichment and HTTP processing:

| Selection | Current aggregate + page | Prototype aggregate + page | Current / prototype combined |
| --- | ---: | ---: | ---: |
| Japan, 3,599 artworks | 1.848 + 1.677 | 0.209 + 0.066 | 3.525 / 0.275 |
| France, 40,067 artworks | 1.753 + 1.742 | 1.030 + 0.329 | 3.495 / 1.358 |
| Asia, 6,208 artworks | 1.623 + 1.610 | 0.411 + 0.037 | 3.233 / 0.448 |
| Japan or France, intersect Asia, 3,607 artworks | 1.813 + 1.764 | 0.302 + 0.211 | 3.576 / 0.513 |
| Europe, 154,273 artworks | 1.820 + 1.852 | 1.024 + 0.842 | 3.672 / 1.866 |
| Romanticism, selected creators and countries | 0.120 + 0.079 | 4.377 + 1.563 | 0.199 / 5.941 |

All variants in this table returned identical complete aggregate results
(total, bounds and density) and page JSON in the same snapshot. Romanticism's
artwork lane contains 3,289 items; its full response also includes 15 books and
4 events. The table measures its two artwork statements, not every request query.

The initial France prototype read 1,317 shared blocks; the initial Romanticism
prototype aggregate read 6,398. Warm repeat controls for Japan and France ran
prototype → baseline → prototype for each statement. All these repeat plans
reported zero shared reads:

| Selection | Current aggregate / page | Prototype aggregate range / page range |
| --- | ---: | ---: |
| Japan | 1.784 / 1.640 | 0.093–0.126 / 0.022–0.023 |
| France | 1.763 / 1.654 | 0.311–0.351 / 0.158–0.169 |

The country improvement therefore survives warm-buffer controls. The original
Romanticism path should remain: even its prototype page, with zero shared reads,
was much slower. Filtering an already-small creator set before resolving
geography is valuable for that selection.

Japan, France, Asia and the combined prototype plans eliminated temporary writes.
Europe still wrote 2,836 temporary blocks per main statement and took about
1.87 seconds combined. This prototype does not establish sub-second performance
for every geographic selection or an end-to-end HTTP improvement after deployment.

Simply changing every geography CTE to `NOT MATERIALIZED` was unreliable:
combined-filter aggregate/page execution rose to 2.450/2.301 seconds, and Europe's
rose to 5.261/2.781 seconds. Removing `IS TRUE` to encourage a semijoin was also
not an obvious universal improvement: France's aggregate/page took 0.563/0.466
seconds, and the aggregate performed roughly 327,000 shared-buffer hits.

Recommended implementation: introduce a conservative broad-geography path and
retain the current path for selected creators, explicit IDs, presets and other
narrow scopes. Start with the tested broad date-range country/continent cases;
test highlights, narrow dates, native facets, picks, anonymous/unlinked creators,
archived links and pending updates before expanding its use. Preserve independent
country and continent membership semantics, production geography, historical
labels, counts, density, deterministic ordering and keyset pagination.

## Pending refreshes are a second scaling concern

The real pending queue stayed empty throughout the observed HTTP requests.
A separate read-only replay selected existing projection IDs into a query-local
CTE named `artwork_atlas_dirty`, exercising the live fallback without writing
markers, catalogue rows or fixtures. Complete aggregate and page results remained
identical at every simulated size.

| Simulated pending IDs | Aggregate | Page | Combined database execution |
| ---: | ---: | ---: | ---: |
| 0 | 0.222 s | 0.012 s | 0.234 s |
| 500 | 0.595 s | 0.022 s | 0.618 s |
| 5,000 | 0.911 s | 0.111 s | 1.022 s |
| 20,000 | 1.304 s | 0.425 s | 1.729 s |

This tests query cost, not ingestion contention, changed-row correctness or actual
worker throughput. The earlier implementation's correctness tests remain separate.
The [refresh worker](../apps/server/internal/atlas/browse_refresh.go) attempts
500 IDs every five seconds, with a four-second batch timeout. That configuration
allows about 100 IDs/second at best while CPU is continuously available; this is
an arithmetic ceiling, not measured throughput.

Both deployed services have CPU throttling enabled. Cloud Run's request-based
CPU allocation is relevant to a worker that must continue between requests.
[Cloud Run billing and CPU allocation](https://docs.cloud.google.com/run/docs/configuring/billing-settings)

Add pending depth, oldest-pending age, processed IDs, batch duration and failure
metrics before choosing capacity. The marker table currently has no age column.
If real ingestion creates persistent backlogs, use a reliably scheduled worker
or allocated background CPU, with bounded batches and the existing advisory
lock. Retain the live fallback so refresh lag cannot hide catalogue updates.

## Cache, browser and infrastructure observations

The catalogue revision was 4,185 before and after every HTTP sample. This round
observed cache reuse, not cache churn during real ingestion. The global revision
still invalidates all cached catalogue families after relevant catalogue writes.
The statement-trigger implementation also permits invalidation from statements
that affect no rows; this is a code-review finding, not a production write test.
Measure invalidations and hit rates during actual ingestion before changing
dependency scopes. Book/event illustration dependencies must remain correct.

The final read-only check at 14:09 UTC found revision 4,188, 302,177 projection
rows and zero pending IDs. Catalogue activity outside this research therefore
continued after the HTTP sampling window. No request series captured those
invalidations, and queue-drain duration cannot be inferred from two snapshots.
The deployed revisions and all seven checked implementation hashes were unchanged.

A browser visit to the Japan All page used its normal 150-item request. In a
fresh desktop context the main API response was a cache miss and took 5.730
seconds; data was ready at 6.304 seconds, and the last observed LCP was an artwork
image at 7.200 seconds. Concurrent geography, preset and creator metadata
requests took 0.263, 0.395 and 0.328 seconds. No long JavaScript tasks or page
errors were recorded; CLS was 0.0208, there was no horizontal overflow, and all
six visible images loaded. Database/API latency remains the strongest target.
This browser request differs from the 21-item HTTP probes; the precise additional
delay was not attributed by a trace of that 150-item request.

A subsequent fresh mobile context received the already-cached API response in
0.130 seconds, with data ready at 0.795 seconds, no long tasks or page errors,
and CLS 0.0014. This is a cache contrast, not evidence that mobile rendering is
intrinsically faster. The recorded mobile LCP was text; the observer did not
establish final image LCP. The desktop screenshot was visually inspected.

The in-app browser tool failed before execution with a missing `sandboxPolicy`
field. Standalone Playwright was used as the fallback; non-GET/HEAD requests
were blocked and no account interaction was performed.

Over the sampled monitoring window, the largest interval-mean API CPU utilization
was 2.3%, API memory 11.0% of 512 MiB, and database CPU 76.0%. Diagnostic reads
contributed to this window, and these values are not request percentiles or a load
test. No error or “atlas browse refresh deferred” entries were returned for the
current API revision in the four-hour log query. The evidence favors reducing
database work before increasing API CPU or RAM.

## Next work, in order

1. Implement selective broad geographic lookup, preserving the fast creator
   selection path. Validate complete responses, cursor pages and query plans for
   both paths, then benchmark the normal 150-item browser request.
2. Instrument refresh backlog and throughput; provision reliable draining if
   observed ingestion exceeds available background execution.
3. Measure cache behavior during real catalogue updates, then consider narrower
   invalidation dependencies if they produce a meaningful benefit.
4. Run a separate representative concurrent/capacity benchmark before making
   ten-million-row or p95 claims. Keep the real local catalogue read-only.

## Evidence

Detailed plans, captured SQL/arguments, equality checks, HTTP headers/responses,
browser measurements/screenshots, service snapshots and monitoring samples are
archived outside Documents at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/performance-round3-20261012/`

Key files: `http-summary.json`, `geography-variants-*.json`, `repeat-summary.json`,
`pending-summary.json`, `browser-all.json`, `final-verification.json`, and the
scenario `*-variants/` directories. Scripts are preserved with their original
paths; prior-round inputs used by the HTTP/pending scripts are copied into
`prior-inputs/`. Connection helpers obtain credentials at runtime; credentials
are not included in this report.
