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

## Production release

Both revisions serve 100% of traffic with their previous runtime settings:

- API: `artline-api-renaissance-performance-1014-v1`, build
  `eac7fcf6-7e9b-48b7-a74e-e7dfcad5701c`, source `a2a4c3b5`.
- Web: `artline-web-renaissance-performance-1014-v1`, build
  `b0c480b1-21ef-4ac3-b4fb-4b0c3babedcc`, source `c7ffc928`.

The first candidate API comparison took 4.722 seconds on the previous revision
and 1.171 seconds on the candidate; repeated requests on both took about
0.17–0.21 seconds. A later explicit 150-item request took 2.152 seconds on the
previous revision and 1.066 seconds on the live revision, with identical payloads.
These HTTP timings include transport and service conditions, unlike the database
plan timings above.

The live view gained one eligible artwork during delivery. Both revisions returned
the same updated 29,941 entries (29,922 artworks, 12 books and seven events), with
unchanged first-page ordering. The candidate's second page also matched the old
revision exactly, with 150 distinct works and no overlap with its first page.

Public verification on `https://artlines.org/all` confirms the visible spinner,
successful content replacement, 150 initial artwork cards, one timeline request
and no JavaScript errors. API health/readiness, exhibition browsing and protected
museum access checks pass. The preserved artwork-detail rule also passes read-only
checks for supported undated and post-1970 objects.

Rollback revisions remain `artline-api-museums-performance-1014-v1` and
`artline-web-catalogue-ui-1013-v1`.
