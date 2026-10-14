# All timeline: Renaissance loading — 14 October 2026

The live Renaissance starting point took 2.402 seconds from selection to content
in a fresh desktop browser; its timeline request took 1.963 seconds. It returned
29,940 entries (29,921 artworks). These are individual observations, not p95 or
cold-disk measurements.

Read-only production plans found that both the count and first-page queries
materialized geography for 52,187 candidate works. Each scanned approximately
680,000 artwork/artist links and wrote 388 temporary blocks, although the gallery
only needed 150 works. The existing loading label was screen-reader-only, while
lane spinners required an earlier response: the initial canvas therefore looked
blank throughout this work.

## Changes

- Keep the existing set-based count/density query and revision-aware cache.
- For populated period windows of at most 600 years, use indexed geographic
  membership probes while seeking the bounded gallery page. `OFFSET 0` keeps
  the probes correlated; without it PostgreSQL chose full-catalogue hash sets.
- Preserve the existing strategies for sparse selections (150 or fewer), wide
  windows, text searches and record-neighbor queries. Empty results skip paging.
- Preserve independent creator-country and production-place evidence, archived
  creator handling, dirty projection overlays, ordering and cursor semantics.
- Show the shared spinner in a visible, centered status region on initial load
  and filter changes. Hide stale entries while loading, retain accessible busy
  state and reduced-motion behavior, and show retry controls after errors.
  Failed required preset metadata also stops the spinner.

The first-page database plan fell from 636.070 ms to 28.599 ms (about 95.5%),
with zero temporary writes. The count query is unchanged. No new index or
production data modification was necessary; the existing browse and relationship
indexes already support the bounded lookups. Catalogue scope was not reduced.

## Verification and release isolation

Full before/after responses were identical. Same-snapshot read-only comparisons
also preserved first and second pages, Italy, France, narrower dates, highlights,
independent geographic intersections and empty matches. Empty/sparse cases retain
the previous production plan rather than doing a full ordered scan.

Disposable PostgreSQL fixtures check clean and pending projection records,
anonymous production geography, archived/mixed creators, duplicate evidence,
holdings versus origins, independently matching countries/continents, and live
geography changes. No fixtures were written to production or the real local DB.

Frontend tests cover initial metadata/content waits, filter changes, success,
failure/retry and metadata failure. The isolated production build and TypeScript
check pass. Desktop and fresh mobile browser checks verify the visible spinner,
no duplicate initial request, retry recovery, reduced motion, no horizontal
overflow and no JavaScript errors. The in-app browser connection was unavailable;
these checks used a separate headless Chrome instance.

Release overlays contain only the changed API query files/tests and All component
files/tests, on top of the exact current deployed builds. Existing runtime settings,
guide content, museum functionality and research processes are preserved. Source
history also records the already-deployed browse/cache/search dependencies needed
by the query implementation; it does not ship those again as additional changes.
Unrelated working-tree changes remain untouched. The first API build was stopped
by its preimage guard before release: the prior build includes an inline
artwork-detail visibility patch, not an archive overlay. That deployed patch is
preserved byte-for-byte in the corrected baseline and candidate. The source
history now records it as well; this release does not alter detail visibility.

Plans, exact request/response captures, screenshots, source hashes and release
receipts are retained under
`~/Library/Application Support/Artline/backups/renaissance-performance-20261014/`.
