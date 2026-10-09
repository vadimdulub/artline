# Second performance round — 9 October 2026

Implemented and verified locally on top of `e17e22c`. This round has no database
migration, source-data changes or infrastructure changes. It is not deployed.

## Measurement and changes

The production request-log sample from 07:53–08:13 UTC contains 2,067 requests
and 26 server errors across the API and web services. These are requests, not
unique visitors or independent incidents. Among web artist routes, all eight
errors occurred in 105 individual artwork requests; 680 painter-page requests
had no errors. A database snapshot also caught an artist collection summary
waiting on a disk read. This supports removing the artwork page's dependency
on a complete painter summary; it does not prove the cause of every timeout.

Individual artwork pages now load a narrow creator identity and the selected
artwork concurrently. The identity read performs one indexed artist lookup
and resolves canonical slug aliases. It uses the existing revision-aware cache,
deadlines and admission limits. Full painter biographies, influences, gallery
pages and collection summaries are no longer prerequisites for an artwork page.
The full painter catalogue remains linked, retaining browsing filters. The
standalone page retains the image viewer, qualified attribution, recorded dates,
holdings/display distinction, descriptions, sources, sharing and structured data.
Those details render without JavaScript. Painter gallery behavior is unchanged.

The book-author timeline previously evaluated its full filtered author scope
twice: once for counts and again for the page. It now computes the counts and
bounded keyset page from one materialized scope in a single database query.
Only the returned creator records are serialized. Date parsing, uncertain and
unknown lifespans, filtering, exact counts and cursor ordering are preserved.

| Paired repository observation against production, read-only | Before | After |
| --- | ---: | ---: |
| Rembrandt creator lookup | 12 queries, 2,682 ms, 54,307 bytes | 1 query, 226 ms, 123 bytes |
| Giotto creator lookup | 12 queries, 1,154 ms, 32,305 bytes | 1 query, 74 ms, 119 bytes |
| Full book-author view, 30 returned records | 983 ms | 449 ms |

These are individual sequential samples through the local Cloud SQL proxy,
with uncontrolled buffer-cache and production-load conditions. They are not
percentile benchmarks. A separate full author HTTP read returned identical
41,126-byte JSON on the old production service and the local candidate; both
were cache misses. Its 1.92 s / 1.49 s observations are not directly comparable
because the request paths and deployment locations differ.

The Ginevra artwork's uncompressed HTML shrank from approximately 98 KB to
38 KB (about 61%). This is a response-size comparison, not a claim about page
load time: the sampled production page was already warm and faster than the
local candidate over the database proxy.

## Verification

- Production read-only comparison: identical author responses for full,
  highlights, women, language/year, Homer and empty-result selections, including
  next pages where present. Local comparison also covers the undated cursor.
- Creator identity agrees with full public painter records. Existing active
  statuses remain available; archived and missing artists remain excluded.
  Existing slug aliases resolve to canonical identities. No fixture writes.
- All Go packages and affected package race tests pass. Historical ingestion
  tests use existing ignored research evidence through read-only file links.
- 43 read-only local API subchecks pass, covering unified visibility, pagination,
  review records, SEO, books and the new identity route.
- Web unit tests (269 in the isolated change; 284 after integrating existing
  working-tree changes), lint and the Node 22 production build pass. Desktop and mobile browser
  checks verify image loading/enlargement, no horizontal overflow and no automatic
  painter-summary/gallery requests. The no-JavaScript check verifies complete
  artwork content, indexing metadata, canonical links, redirects and missing IDs.
- Screenshots were inspected; a legacy fallback width rule was removed from the
  new page. Existing source evidence and unrelated member controls are preserved.

## Remaining work and rollout

Cold museum reads, complete painter collection summaries and broad title-search
counts can still exceed their deadline. This round does not resolve every
production timeout. Sustained concurrency, cache eviction and representative
10-million-artwork tests remain outstanding; no database resize is justified by
these measurements alone. No production cache flush or load test was performed.

Deploy the API before the web because the new page needs the identity endpoint.
The old web remains compatible with the new API. A web rollback needs no database
rollback. Preserve unrelated working-tree member changes when preparing a release.

Aggregate results: [performance-round2-20261009.json](performance-round2-20261009.json).
Private request logs, query plans, test results and screenshots are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/performance-round2-20261009/`.
