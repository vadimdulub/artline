# All timeline performance review — 12 October 2026

The API and web changes are deployed to **artlines.org**. The requested
Romanticism URL still returns exactly **3,289 artworks, 15 books and 4 events**,
including the same first-page records, image metadata, density bins and cursor.

## Measured improvements

These are individual sequential observations, not latency percentiles. No cache
flushes, concurrent load generation or synthetic catalogue records were used.
The database contains approximately 1.02 million artwork rows; this is a real
catalogue measurement, not evidence of performance at ten million rows.

| Measurement | Before | After | Method |
| --- | ---: | ---: | --- |
| Requested artwork SQL execution | 509.7 ms | 144.3 ms | PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)` |
| Requested desktop timeline ready | 2,243 ms | 1,714 ms | Fresh browser contexts, running services, main API cache MISS |
| Requested browser main API request | 1,210 ms | 773 ms | Same URL and result; includes concurrent filter-choice requests |
| Requested artwork SQL buffer hits | 285,376 | 68,685 | Same filtered selection; both plans had zero physical reads |
| Broad All artwork request | 7,832.9 ms | 1,790.7 ms | Public web proxy, cache MISS, `type=artwork&artwork_popular=false&limit=24` |
| All artwork search, Rossetti | 7,749.3 ms | 412.7 ms | Public web proxy, cache MISS, same filter and page limit |
| Requested selection, old/new API comparison | 970.8 ms | 458.8 ms | Sequential direct API requests, same 149-record page; complete responses equal |

The broad request above uses the API's default Highlights selection. It is not
the much larger `highlights=false` view. A separate read-only comparison of that
view improved from 6.9 to 4.5 seconds including remote SQL connection overhead;
subsequent samples varied substantially. Exact counts across hundreds of
thousands of works remain a significant database operation.

The original browser sample showed the timeline after 2.24 seconds. Preset
metadata took 441 ms, and the 1.21-second main request did not start until 972 ms
after navigation. There were no long rendering tasks in that sample.

**Cold-start behavior remains visible.** The first public desktop navigation
after rollout took 4.45 seconds: the document alone took 2.13 seconds to finish,
and the main request took 1.63 seconds. Its mobile repeat took 1.32 seconds with
a cached 160-ms main request. These are different cache/startup conditions and
must not be presented as a steady-state before/after page-speed comparison.
Both Cloud Run services retain their existing minimum of zero instances. Cold
thumbnail optimization also adds time after the data appears.

A later check with the deployed services running showed the exact desktop view
after **1.71 seconds**, with a **773-ms uncached** main request. Its mobile repeat
took **1.22 seconds** with a 264-ms cache hit. All observations, including the
slower rollout sample, are retained; these samples are not an SLA. Image checks
confirmed that reproductions loaded, but the scripted image-check time includes
an intentional post-data wait and is not an exact image-paint measurement.

## Findings and changes

### Repeated native filtering and evidence lookups

The old query applied the selected painters up to three times, repeated native
date eligibility after materialization, and rebuilt geography three times. It
also inspected all 133,620 curated collection entries for a selection of about
3,300 candidates.

The new query establishes eligible candidate IDs once, reuses geography, and
resolves country associations once per distinct artist. Selective collection
checks start from candidate IDs. Broad views join deliverable images and
accepted holding evidence in batches. Detail enrichment still happens only
for the bounded page.

Creator visibility now first identifies works linked to archived creators;
only those require checking for a surviving active attribution. Anonymous
works and mixed active/archived attributions retain their existing behavior.
The artist foreign key and non-null status make this equivalent to the previous
visibility predicate.

### Incorrect cardinality estimates and heap reads

PostgreSQL estimated 155 illustrated eligible candidates where the measured
scan returned 302,090. That estimate encouraged repeated index probes instead
of joins appropriate to a broad window.

Migration `0052_atlas_read_performance.sql` adds statistics for creation-date
eligibility and effective date bounds. It also adds a trigram index for
unresolved creator labels. Migration `0053_atlas_illustrated_identity_index.sql`
adds a **23 MB** covering UUID index for selected-creator queries; the existing
year-first index continues to serve broad windows.

Both indexes were built **concurrently** in production and checked as valid
before recording their migrations. Normal, throttled `VACUUM (ANALYZE)` ran on
artworks, holding assertions, artwork/artist links and media. It did not use
`VACUUM FULL`. Artwork pages marked all-visible increased from 55,755/62,235 to
62,242/62,242 at the maintenance snapshot. The final selected-artwork plan uses
the new index with **zero heap fetches**.

Expression statistics let PostgreSQL estimate these expressions without adding
another maintained index for each expression. See the
[PostgreSQL 17 statistics documentation](https://www.postgresql.org/docs/17/sql-createstatistics.html).

### Search and density aggregation

Artwork searches now use the existing synchronously maintained title projection
and the new creator-label index. Creator name, alias, movement, country and
place matches form separate ID sets, avoiding a broad OR expression with a
severely inflated estimate. Both shared search and artwork-specific search
retain their separate meanings. Literal percent signs, underscores,
backslashes and exclamation marks remain literal search characters.

Density aggregation now adds a record at its first overlapping period and
subtracts it after its last overlapping period. A cumulative sum produces the
same counts without joining every matching record to every period. This applies
to artwork, book and event lanes inside All, including ranges that cross BCE/CE.

### Browser request ordering and diagnostics

An explicit custom URL with both start and end dates now fetches results while
preset labels load. URLs that depend on preset defaults still wait for those
defaults. Metadata arriving later no longer aborts and repeats the same request.
A metadata failure does not prevent an otherwise complete custom view loading.

The web proxy now forwards `Server-Timing` and `Retry-After`, so admission waits
and retry guidance can be observed through the public application. The HTTP
audit script records server timing too.

## Other tabs and shared infrastructure

Painters, Books and Events were inspected and sampled separately. Their initial
public API samples were approximately 392, 310 and 412 ms respectively. After
rollout, Books measured 261 ms; Painters and Events had slower first samples,
and even one cached Events response exceeded a second. These timings show
service/transport variability; they do not establish a SQL regression or a
uniform speedup across all tabs.

Real browser checks passed for each tab and all its filter-choice requests:
Painters returned 100 selected painters, Books returned 256 selected books,
and Events returned 100 selected events. There were no page errors. Their
native query implementations were retained; the measured multi-second SQL
bottlenecks were concentrated in All.

The database is `db-custom-1-3840` with approximately 1.2 GB shared buffers and
4 MB work memory. The API retains an eight-connection pool and four active
catalogue requests, with bounded queueing. The public catalogue cache remains
revision-aware, bounded to 16 MB and one minute; it still invalidates when
catalogue data changes. No stale-cache workaround, pool expansion, instance
resize or permanent memory-setting increase was introduced.

## Verification and limits

- Twelve filter cases compared the previous and optimized implementations in
  the **same read-only repeatable-read transaction**. Complete response objects
  matched, including density, images, ordering and cursors. Selected cases also
  checked a second page and previous-item navigation.
- Cases included country/continent intersections, creator facets, native
  geography, shared and artwork search, punctuation-only search, highlights,
  broad illustrated views, historical presets and the 1960–1970 boundary.
- The deployed candidate returned the exact original response for the user's
  URL. Its next page contained 150 distinct new artwork IDs with the same total.
  Museum login enforcement and invalid-range rejection passed.
- Desktop and phone browser checks passed, with one main atlas request, no
  horizontal overflow and no JavaScript errors. Delayed/missing metadata tests
  confirmed the new request ordering and preserved default-window behavior.
- Atlas, HTTP API, catalogue, books and events tests passed. Web typechecking,
  targeted lint and six starting-point tests passed. The wider Go run passed
  outside `internal/ingest`; that package has missing historical research
  fixture files unrelated to these changes.
- Cloud error-log checks for the released revisions returned no error entries
  at verification time.

Remaining work for a separate capacity pass: percentile/load testing under
representative ingestion traffic; sustained memory and CPU measurements;
image-delivery and scale-to-zero startup latency; and a maintained aggregate
projection if instant exact counts for multi-million-work views become a
requirement. The current measurements do not establish that capacity.

No catalogue metadata, account records or local database contents were changed.
The production database changes were additive statistics/index migrations and
normal maintenance. No Terraform apply or commit was performed.

Release digests, migrations, checks and rollback revisions are recorded in
[the deployment receipt](deployment-20261012-all-performance.json). Detailed
plans, original source, the temporary A/B harness, logs and browser evidence
are retained under
`/Users/vadimdulub/Library/Application Support/Artline/backups/all-performance-20261012/`.
