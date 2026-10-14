# Museum loading performance — 14 October 2026

The latest observed signed-in directory navigation took 3.519 seconds in the
web service and 3.458 seconds in the API. The API's own request logger recorded
3.455 seconds, so this was application processing, not merely container startup.
An earlier directory request took 7.842 seconds; cache hits were much faster.

The deployed museum repository matched the committed source. Read-only production
plans exposed collection-wide grouping and sorting for a single card, per-work
highlight probes, and tens of thousands of media lookups for one cover. The old
Rijksmuseum card constructed membership for roughly 401,000 holdings.

The new card query counts indexed holdings, adds distinct current incoming loans,
starts highlights at the museum's curated selection, and selects the first cover
from each branch before choosing between them. Only that cover is enriched.
Shared source, display expiry, conflict, archived-record and creator policies are
retained, including unknown dates and unillustrated fallback covers.

Production migration `0057_museum_cover_seek.sql` was applied concurrently and
recorded after checking `indisvalid` and `indisready`. Its partial covering index,
`artworks_museum_illustrated_cover_idx`, occupies 33 MB and was built in 2.994s.
Ordinary `VACUUM (ANALYZE, INDEX_CLEANUP AUTO) artworks` completed in 13.72s to
refresh index-only visibility and planner statistics. No catalogue records were
edited, no real local database was written, and no research processes were stopped.

Same-snapshot `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` comparisons, milliseconds:

| Overview | Previous query | New query |
| --- | ---: | ---: |
| Metropolitan Museum | 1,169.299 | 36.708 |
| Rijksmuseum | 4,339.717 | 159.981 |
| National Gallery of Art | 789.313 | 25.217 |
| Louvre | 29.307 | 2.121 |
| Ateneum | 19.501 | 1.765 |

Both variants in this comparison ran after index creation and maintenance.
The new Rijksmuseum illustrated-cover index scan returned one row, performed
zero heap fetches and took 0.046ms. The previous intermediate query still checked
89,741 media rows; bounding each branch eliminated that mistake.

The default 24-card directory query fell from 66.938ms in the initial plan to
21.479ms in the final plan. Final directory count/geography/movement queries took
15.272/30.880/36.008ms. These are observed database execution times, not browser
latencies, p95 estimates, cold-disk measurements or a ten-million-row capacity test.

Validation compared entire responses in one read-only repeatable-read production
snapshot: default and maximum directory pages, country filters, highlights,
creators, movements, on-view, no results, next cursors and five large overviews.
An isolated disposable PostgreSQL cluster also checked incoming loans, expired
and conflicting display evidence, overlapping holdings/display, missing images,
and archived objects. Production and the real local catalogue received no fixtures.

Catalogue and member unit tests, targeted HTTP museum/cache/access tests, the
frontend build/TypeScript check, ESLint and four museum-request tests passed.
The existing full HTTP test suite has an unrelated Books-limit expectation failure
(`TestBooksAcceptLegacyParametersAndValidBounds`, limit 151); the identical failure
was reproduced on the untouched deployed source. The older general fixture helper
also assumes public-schema triggers; the new isolated test uses its own migrated
disposable cluster and rolls back its changes.

The production page already includes a loading boundary. Browser checks against
the isolated release preview and read-only production API showed loading feedback
at 108ms and 24 directory cards at 898ms in the final run, with no hydration
duplicate, working search/reset, and no overflow on a fresh mobile navigation or
JavaScript errors. A desktop-to-mobile viewport resize exposed an existing sidebar
offset until reload; that separate responsive-navigation issue was not changed.
Network and cache conditions affect these observations. Signed-in production browser timing
requires an existing authenticated browser; the in-app browser tool was unavailable.

Release packaging is an explicit file overlay on the current deployed API build,
preserving unrelated deployed functionality and excluding unfinished workspace work.
The frontend needs no production changes. Index receipts, source hashes, query
plans and release checks are retained under
`~/Library/Application Support/Artline/backups/museums-performance-20261014/`.

PostgreSQL references: [CTE planning](https://www.postgresql.org/docs/17/queries-with.html#QUERIES-WITH-CTE-MATERIALIZATION)
and [concurrent index creation](https://www.postgresql.org/docs/17/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY).
