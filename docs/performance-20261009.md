# Catalogue performance audit — 9 October 2026

Production is experiencing read latency and availability problems during a broad
crawl. The main priority is making uncached record pages cheaper and bounding
database work under concurrency. Repeated discovery reads already benefit from
the API cache. This audit did not change production configuration, records,
indexes, robots rules or deployed code.

## Committed application

Commit `fc89398` was pushed to `origin/master`. It records the verified sources
of API and web revisions `unified-catalogue-1008-1955`, including earlier live
changes needed to reproduce that release, compatible regression tests, the
growth guide, and unified-catalogue configuration/documentation. Runtime source
hashes match the deployed archives. One frontend test has whitespace cleanup.
The deployment itself remains the release recorded on 8 October.

Unfinished member-access changes, later local edits, and unrelated museum
research/assets remain in the working tree. The production public artist and
artwork access behavior is preserved in Git.

Validation used an isolated extraction of the staged Git tree: all Go packages
passed, as did 267 frontend tests, ESLint, TypeScript and Terraform formatting
for the changed `.tf` files. Historical ingestion tests require existing local
research archives that are deliberately outside Git; these were made available
to the temporary checkout without changing their contents. Database fixture
variables were unset. The exact production application had already passed its
build and live verification in the deployment receipt.

## Observations

The log sample contains the latest 4,000 request records from
05:47:17–06:05:18 UTC. The query reached its limit; these counts describe this
sample, not all traffic or an availability SLO.

- 2,116 of 2,272 web requests (93.1%) identified themselves as ClaudeBot. User
  agents are self-reported; crawler identity was not independently verified.
- Artist/artwork pages accounted for 1,075 web requests to 1,073 distinct paths.
  There were 107 museum-page requests to 93 paths. This is a broad crawl, so
  caching repeated URLs alone cannot eliminate first-read work.
- The sample contains 145 web HTTP 500s. API responses include 69 HTTP 500s,
  63 HTTP 503s and 26 HTTP 429s. These are request counts across both layers,
  not distinct user incidents.
- Errors preceded the audit: 48 web and 14 API 5xx responses occurred before
  its first HTTP sample at 06:00:16 UTC.
- Artist/artwork server-response medians were 1.37 s, with a 23.92 s maximum;
  museums had a 1.66 s median and 16.04 s maximum. These include failed
  responses and measure server requests, not browser rendering or Core Web Vitals.

The controlled HTTP pass issued sequential GETs with fresh curl connections,
no cache flushing and no concurrent load generator. First requests were not
necessarily cold. Sampling was stopped after capacity errors were observed;
39 completed samples are retained. The reusable probe now stops immediately on
a transport error, HTTP 429 or any 5xx.

| API read | Observed total response time | Result |
| --- | --- | --- |
| Artwork directory, 24 items | 1.97 s miss; 222–244 ms hits | All 200 |
| Default timeline | 260–491 ms, already cached | All 200 |
| Artist directory, 24 items | 3.71–4.95 s | All 200, outside cache allowlist |
| Artwork title search, Madonna | 8.19–8.48 s | Three HTTP 500s |
| Rembrandt detail | 6.99 s once; then 503 at 32 s and client timeout at 35 s | Unstable |
| Rembrandt works, 24 items | 8.22–12.94 s | Three HTTP 500s |
| Museum directory, 24 items | 8.17–8.41 s | Three HTTP 500s |

Met, NGA and Louvre reads also failed during the sampling window. Remaining
planned book/event/atlas/SEO probes and fresh browser benchmarks were deferred
to avoid adding work during the incident. Existing request logs provide the
page-level evidence above. No concurrent production `EXPLAIN ANALYZE` was run.

## Database evidence and limits

Cloud SQL remains `db-f1-micro`, with 15 GiB SSD storage and 100 maximum
connections. The application has eight pool connections per instance. There
were 414,213 active production artworks when the read-only inventory ran.

A database activity snapshot showed four active queries waiting for
`DataFileRead` and two for `BufferIo`, alongside three other active queries.
That supports investigating storage reads and concurrent work; it does not
by itself identify the slowest SQL statement.

The roughly 30-minute metrics sample showed CPU utilization of 13.4–33.2%.
The memory-quota utilization gauge reported 100%, but component metrics showed
38.0–61.2% free memory and 32.3–48.3% usage. These different gauges do **not**
justify an out-of-memory diagnosis. API container memory means were only
4.8–6.3%. No CPU/RAM upgrade benefit was established in this pass. Disk read
operations and database wait events deserve a quiet-window baseline before
choosing infrastructure changes.

Production's estimated Madonna page plan uses
`artworks_directory_title_id_idx`, filtering titles while walking alphabetic
order. Its count query uses the existing `artwork_title_search_idx` trigram
index. Materializing matching IDs/titles before sorting changes the estimated
page plan to the trigram index, without adding an index or changing results.

This is a candidate optimization, not a proven production fix. On the local
309,234-work catalogue, PostgreSQL already chooses the trigram index for the
original query. Original and candidate pages were identical and ran in
11.64 ms and 10.67 ms with warm buffers. Those measurements cannot establish
the production speedup or attribute every search timeout to the ordering plan.
Capture per-query timings and run a bounded A/B comparison during a quiet
production window before changing the search implementation.

## Repository tracing

The new opt-in trace test executes ordinary repository reads once inside
read-only transactions, with one connection and a 15-second statement timeout.
It creates no schema, records or fixtures. These local results measure the
current catalogue on this machine, not production hardware or 10-million-row
capacity:

| Read | SQL calls | Elapsed | JSON bytes |
| --- | ---: | ---: | ---: |
| Rembrandt detail | 11 | 274 ms | 216,466 |
| Rembrandt works, 24 items | 7 | 27 ms | 76,891 |
| Artist directory, 24 items | 6 | 157 ms | 26,951 |
| Met detail | 2 | 148 ms | 1,470 |
| Met works, 24 items | 6 | 906 ms | 28,450 |

The painter's key artwork accounts for 182,742 bytes of the local detail
response, including 180,670 bytes of citations. Production's successful
Rembrandt response was 391,344 uncompressed API bytes. These are different
catalogues, so the local field proportions must not be applied to production.
Web-proxy compression already exists; the API measurement does not establish
uncompressed browser delivery. A small public projection should retain source
names/links and factual qualifications while keeping full evidence in audit
storage or a separate bounded detail request.

Other findings from source and the trace:

- Artist directory facets account for 19,683 of 26,951 response bytes. Three
  global facet queries repeat on each page. They can be cached independently
  with the existing catalogue revision.
- The Met works query producing filter facets took 777 ms of the 906 ms local
  read. A subsequent warm `EXPLAIN ANALYZE` took 284 ms and used an indexed
  scan of 25,893 museum-scoped artworks, not the whole artwork catalogue.
  Deduplicating relevant artist IDs before movement joins and caching these
  facets are candidates for reducing repeated work. First-page latency should
  be addressed before gallery rendering work.
- `artistInfluences` fetches citations separately for each returned influence,
  up to 40. The local Rembrandt sample has no comparable influence population;
  the 11-query result does not measure the production worst case. Batch by the
  returned influence IDs, retaining citation ordering and source visibility.
- `getArtistArtwork` obtains a complete artist response before reading a work.
  Single-work pages consequently depend on biography, representative works,
  key-artwork evidence, influences and collection summaries. Design a smaller
  artist/identity read for those pages before changing their rendering contract.

## Priorities for the next implementation pass

1. **Bound uncached work.** The artist handler has no explicit query deadline,
   unlike the eight-second museum/chronology handlers. Add an end-to-end budget
   and bounded admission to expensive reads. Measure database acquisition waits
   separately from SQL execution. Increasing Cloud Run concurrency alone could
   increase pressure on the same small database. Review crawl pacing without
   hiding active catalogue records or blocking Google indexing by default.
2. **Reduce database work per record page.** Batch influence citations, separate
   lightweight identity/SEO data from full painter enrichment, and investigate
   museum facet plans. The high number of distinct crawled URLs makes this
   more consequential than relying entirely on warm caches.
3. **Extend safe caching.** Artist directories, artist detail/chronology and
   museum routes are outside the current discovery cache allowlist. Consider
   bounded revision-aware entries and coalescing identical reads, preserving
   public/member boundaries, archived exclusions, current-display expiry and
   invalidation after source/catalogue writes. Keep member/session responses
   private. Cache directory facets separately from cursor pages.
4. **Validate title-search planning.** Compare indexed candidate selection with
   the production alphabetical scan, including selective/common titles,
   unknown dates, image filters and cursor pages. Verify identical counts,
   order and continuation; no new production index is justified yet.
5. **Reduce response evidence payloads.** Keep complete provenance in storage
   while returning the bounded source information the public view actually
   renders. Measure SSR HTML/RSC and browser bytes before claiming page gains.

After those changes, repeat quiet and representative-concurrency measurements
on the deployed candidate. Then run browser first-content/interaction checks
and compare p50/p95, errors, pool waits, read IO, cache hits and payload sizes.
An isolated representative 10-million-artwork dataset remains necessary for a
capacity claim; do not create it in or point fixture tests at the real catalogue.

## Reproduction and evidence

Machine-readable, redacted measurements: [performance-20261009.json](performance-20261009.json).

Run the HTTP tool only when the service is healthy; it stops on server errors:

```sh
python3 ops/audit-catalogue-performance.py \
  --base https://artlines.org/api/backend/v1 \
  --route artworks --samples 3 \
  --output /tmp/artline-http-performance.json
```

Run repository instrumentation from `apps/server` with a compatible Go
toolchain. Supply a read-only connection privately; never use the fixture
database variable for the real catalogue:

```sh
ARTLINE_READONLY_DATABASE_URL='postgres://localhost/artline?sslmode=disable' \
ARTLINE_PERFORMANCE_DIR=/tmp/artline-query-traces \
go test ./internal/catalog -run '^TestCataloguePerformanceReadOnly$' -count=1 -v
```

Private raw logs (including client network metadata), metric descriptions,
query text/arguments, plans and trace reports are retained outside Documents:

`/Users/vadimdulub/Library/Application Support/Artline/backups/performance-20261009/`
