# Catalogue performance review, second round — 12 October 2026

The remaining priority is **uncached, broad All browsing and pagination**. The
full illustrated artwork view took **10.81 seconds** on one public request and
**3.83 seconds** on a later uncached repeat; the corresponding cache hits took
150 and 141 ms. This is different from the smaller Romanticism selection.

A read-only SQL prototype reduced the broad query from **4.32–4.35 seconds to
3.32 seconds**, approximately **23%**, with the complete SQL result unchanged.
Combining it with a transaction-local memory experiment reached **2.85 seconds**,
approximately **34%**. These are database experiments, **not deployed speedups**.

This round adds a reusable diagnostic test and this report. Application behavior,
production schema, persistent database settings and service configuration were
not changed. No catalogue records, local database contents or account data were
written. No deployment, Terraform apply or commit was performed.

## Scope and baseline

The review covered public requests across Painters, Books, Events and All,
including broader selections, search, author browsing, real browser loading,
pagination, SQL execution plans, Cloud Run request logs and monitoring data.

Production had moved forward since the first performance release. The measured
revisions were `artline-api-event-artworks-1012-v1` and
`artline-web-event-artworks-1012-v2`, each receiving 100% of traffic. The event
artwork release preserves the earlier All optimizations. The local catalogue
was never used for these measurements. Production table statistics estimated
1,018,119 artwork rows; this is not a ten-million-row capacity test.

Requests and database experiments were bounded and sequential. There was no
cache purge, forced service restart, synthetic ingestion or concurrent load
generator. Browser filter-choice requests retain the application's normal
concurrency. Cache MISS means a response-cache miss, not necessarily a cold
instance or cold database buffers. Results are observations, not percentiles.

## Public request measurements

The first pass used fresh curl connections through `artlines.org/api/backend/v1`.
The numbers include connection setup, proxying, compression and transfer.

| View | Uncached request | Immediate cache hit |
| --- | ---: | ---: |
| Painters, default selection | 305 ms | 174 ms |
| Painters, all | 800 ms | 201 ms |
| Painters, Rossetti search | 759 ms | 231 ms |
| Books, default selection | 810 ms | 194 ms |
| Books, all | 437 ms | 182 ms |
| Books, Shakespeare search | 369 ms | 162 ms |
| Book authors, all | 1,422 ms | 184 ms |
| Events, default selection | 293 ms | 190 ms |
| Events, all | 392 ms | 184 ms |
| Events, France search | 428 ms | 251 ms |
| All artworks, Highlights | 2,851 ms | 222 ms |
| All artworks, Highlights off | 10,809 ms | 150 ms |

The All samples use `type=artwork&artwork_popular=false&limit=24`, adding
`highlights=false` for the full view. A small page does not make its exact counts
cheap: the full request still matches **302,137** artworks. It does not mean all
one million catalogue records are eligible for this illustrated timeline.

A later sequential HTTP pass measured Highlights at 1,837 ms and the full view
at 3,827 ms, both uncached. These samples are retained rather than selecting only
the fastest or slowest result. All valid sampled requests returned HTTP 200.
An initial author-view probe used an invalid limit of 300 and correctly returned
400; it was replaced with the supported 150-record request and excluded from
the latency comparison.

## All: the work that remains expensive

The full-view plan matched 302,137 records after considering 302,395 native
candidates. Its holding-evidence branch scanned **892,707** accepted assertions.
The first captured plan executed in 4,829 ms, with 711,563 shared-buffer hits,
zero physical shared-buffer reads and **12,455 temporary blocks written**, about
**97.3 MiB** at the verified 8 KiB block size. Warm buffers do not eliminate the
CPU and temporary-file work of this query.

The previous covering indexes are being used. Artwork and holding scans had only
604 and 2,151 heap fetches respectively. This evidence does not justify another
blanket vacuum or adding duplicate indexes as the next step.

### Pagination repeats counts and density

Fetching the next 24 artworks produced another **4,243 ms** SQL execution, with
711,595 shared-buffer hits and the same 12,455 temporary blocks written. The
response retained the same total and density, and its 24 IDs did not overlap
the first page.

The SQL materializes the full matching set for totals, density and the page.
The cursor filters the page after that materialization. The HTTP cache includes
the cursor, so it cannot reuse aggregates from a different page.

The highest-priority structural change is to separate the filter-scoped
aggregates from the bounded page query. Cache totals/density by the complete
semantic filter and catalogue revision, independently of the cursor and page
size. A page query must then apply its seek before broad enrichment. Merely
caching aggregates while retaining the current materialized page query would
still scan the broad set.

This needs explicit consistency handling: preserve the existing revision
invalidation, all visibility and evidence rules, preset/creator/geography
semantics, image eligibility and cursor ordering. Define behavior when a
catalogue revision changes between aggregate lookup and page selection. It is
not a browser-side cache workaround. The potential latency improvement of
this structural change has **not** been benchmarked yet.

### Verified date-grouping prototype

The current density calculation visits every matching work and calculates two
bucket changes. In the broad view, 302,137 works share only **13,859 distinct
start/end pairs**. Grouping those pairs first allows each bucket change to use
the number of works in the group as its weight.

| SQL experiment, in execution order | Execution | Temporary data written |
| --- | ---: | ---: |
| Current query, 4 MB work memory | 4,319 ms | 97.3 MiB |
| Current query, 16 MB work memory | 3,732 ms | 57.5 MiB |
| Grouped dates, 4 MB work memory | 3,320 ms | 97.3 MiB |
| Grouped dates, 16 MB work memory | 2,850 ms | 57.5 MiB |
| Current query repeated, 4 MB | 4,352 ms | 97.3 MiB |

The final baseline repeat guards against attributing simple warm-up to the
prototype. The comparison checked all five returned SQL columns—total, first
year, last year, density and ordered item details—in one read-only repeatable
read snapshot. They matched exactly. This proves this broad case, not the full
filter, boundary, neighbour and pagination regression matrix needed for release.

The grouped-date hash used about 1.8 MB in the measured plan. The experiment
does not require changing the global memory setting. The 16 MB trials used
`SET LOCAL` inside read-only transactions; a subsequent connection confirmed
the database default was still 4 MB.

Do not apply a global memory increase based on this experiment alone. PostgreSQL
allocates work memory per operation, and concurrent operations/sessions multiply
the budget; hash operations also use the hash-memory multiplier, currently 2.
That requires a concurrent workload and memory budget before rollout.
[PostgreSQL 17 resource-consumption documentation](https://www.postgresql.org/docs/17/runtime-config-resource.html#GUC-WORK-MEM).

## Native tabs

Direct diagnostic handler timings include approximately 150 ms per database
round trip from this workstation. They must not be used as in-region API
latencies. The following figures sum the server execution times from the
individual `EXPLAIN (ANALYZE, BUFFERS)` plans; those plans execute separately
after the handler and do not measure a single atomic request.

| Case | Matching records | SQL statements | Sum of plan execution times |
| --- | ---: | ---: | ---: |
| Painters, Rossetti search | 16 | 3 | 319 ms |
| Books, all, summary page of 300 | 8,821 | 3 | 39 ms |
| Book authors, all, page of 150 | 3,436 | 1 | 465 ms |
| Events, all | 10,026 | 7 | 155 ms |

Painter search already used a title index in this sample. It repeated the
matching predicate for the count and returned nodes; those two plans cost
162 and 149 ms. There was no observed million-row artwork heap scan to fix.

The author view classifies source lifespan labels on each uncached query. Its
plan parsed 4,154 creator rows and returned 3,436 eligible authors. A maintained
lifespan projection is a plausible later improvement, with invalidation on
source-label changes and preservation of BCE, approximate, missing and
collective-author cases. It has not been implemented or benchmarked here.

Events uses seven sequential statements in the broad case. Density accounted
for approximately 93 of the 155 ms of SQL execution; counts, page and suggestions
were smaller. Combining repeated matching work is a reasonable later change,
but the measured public response was already below half a second. Books in
summary mode had only 39 ms of SQL execution. These are lower priorities than All.

## Browser, images and infrastructure

Successful fresh-context browser samples at desktop size showed data ready at
1,315 ms for Painters, 1,088 ms for Books and 874 ms for Events. The exact
Romanticism URL returned the same **3,308 entries**: 3,289 artworks, 15 books
and four events.

| Romanticism sample | Data ready | Main API | Largest contentful paint |
| --- | ---: | ---: | ---: |
| Desktop, response-cache miss | 2,817 ms | 2,016 ms | 2,880 ms |
| Phone, subsequent cache hit | 751 ms | 119 ms | 852 ms |

These are different cache conditions, not a desktop/mobile speed comparison.
No browser JavaScript errors, horizontal overflow or long tasks were recorded
in the successful samples. Compressed JavaScript transfer was approximately
169–235 KiB depending on the tab. This desktop-class, unthrottled browser does
not establish low-end-phone performance.

The desktop thumbnails completed in approximately 56–87 ms each in that
successful sample, and the phone thumbnails in 111–118 ms. LCP comes from the
browser's PerformanceObserver; it is not an arbitrary post-load sleep. An
initial image-load listener failed to observe native image events and timed
out. Its timing is excluded; the successful samples use resource timing and
LCP. The Cloud Run log retains the earlier, slower 3.69-second API request from
that attempt, so the 2.82-second page sample is not presented as a stable SLA.

Cloud Run request logs attribute 10,658 ms of the slow full request to the API
and 10,678 ms to the web proxy. That puts the measured bottleneck behind the
proxy. The corresponding response-cache hit spent about 4 ms in the API.
All observed admission timings were zero; this does not prove headroom under
concurrent traffic. The captured 30-minute log set contained no HTTP 5xx errors.

Cloud CDN is already enabled with origin-controlled caching and query strings
included in the cache key. Repeated thumbnail headers included `Age` and a
retained `X-Nextjs-Cache: MISS`; that header alone cannot establish repeated
origin optimization because it can be part of the cached response. Three
sequential image requests took 478, 66 and 61 ms. There is no evidence here for
replacing image delivery as the first performance fix.
[Cloud CDN cache modes](https://docs.cloud.google.com/cdn/docs/using-cache-modes).

Monitoring returned 44 interval samples over approximately 45 minutes. The
maximum reported interval mean CPU utilization was 1.53% for the API and 3.14%
for the web service; maximum interval mean memory utilization was 12.6% and
47.7%. Database CPU reached 77.0% in a sampled interval. The audit itself
contributed database work, and interval means can hide short peaks. These are
not concurrency-capacity measurements.

Both services still allow scaling to zero. No new instance startup was observed
during the sampled requests; the startup-log check only found the earlier web
deployment startup. Thus cold starts remain a separate known risk, but do not
explain this round's measured 10.8-second All request. Keeping a minimum instance
is a separate latency/cost decision, not a remedy for this query.
[Cloud Run autoscaling](https://docs.cloud.google.com/run/docs/about-instance-autoscaling).

## Recommended order and remaining verification

1. Split reusable filter aggregates from cursor pages; prove revision consistency
   and bounded query plans before claiming a pagination improvement.
2. Apply and regression-test the measured date-grouping prototype. Compare full
   responses for selective and broad filters, BCE/CE boundaries, preset windows,
   geography, subsequent pages and previous-item navigation. Retain the 4 MB
   database default while establishing this independent gain.
3. Measure concurrent broad queries and ingestion before deciding on query-local
   work memory or database sizing. The 16 MB experiment still spilled 57.5 MiB.
4. Revisit author lifespan classification and repeated native-tab predicates
   after All. Preserve existing date uncertainty and factual evidence.

The reusable audit is
[`TestCataloguePerformanceReadOnly`](../apps/server/internal/httpapi/performance_readonly_test.go).
It requires `ARTLINE_READONLY_DATABASE_URL`, `ARTLINE_PERFORMANCE_URL` and
`ARTLINE_PERFORMANCE_OUT`. It enforces a single connection, read-only sessions,
a statement deadline and a public timeline-handler allowlist, then saves the
response, query arguments, timings and plans. It does not run migrations or
create fixtures. The HTTP API package tests passed with database opt-ins unset;
the diagnostic test also successfully exercised the six measured cases above,
including the two All pages.

Raw samples, SQL variants and equivalence proof, browser captures, monitoring,
configuration snapshots and logs are retained under
`/Users/vadimdulub/Library/Application Support/Artline/backups/performance-round2-20261012/`.
The HTTP repeat was accidentally triggered by a temporary helper named `http.py`
shadowing Python's standard library during monitoring setup. The helper was
renamed, both HTTP passes were retained, and monitoring was rerun successfully.
No invalid or failed tooling result is counted as a successful measurement.
