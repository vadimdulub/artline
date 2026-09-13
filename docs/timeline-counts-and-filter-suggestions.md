# Timeline period counts and suggested filters

Updated 12 September 2026.

Period counts now use the same inclusive overlap of recorded life/activity dates
as the timeline opened by selecting those dates. The previous midpoint buckets
were disjoint, but opening them used overlap; a small bucket could consequently
open hundreds more painters. Neighbouring periods now intentionally share painters,
so their counts must not be added to calculate the unique view total.

The server merges a trailing single-year bucket into the preceding period. Every
returned period can therefore be selected without the UI expanding its dates.

Density responses include at most three suggested country/movement filters,
calculated from the current server-filtered painter IDs. Suggestions must reduce
the result and use a dimension without an existing selection. This prevents an
OR filter from being replaced by a wider selection with a misleading count.
Suggestions with 300 or fewer painters rank first; applying one preserves the
years, search, popular preference, and other filters. A crowded terminal column,
its index entry, and the corresponding filter button all apply the same suggestion.
When no suggestion is available, the column offers access to the existing filters.

## Verification

`TestTimelineReadOnlyCountsAndSuggestions` uses an explicitly opted-in existing
database inside a repeatable-read, read-only transaction. It creates no databases,
runs no migrations, and inserts no fixtures. Set `ARTLINE_READONLY_DATABASE_URL`
to run it; do not use `ARTLINE_TEST_DATABASE_URL` for the real catalogue.

The local check verified every period and suggested count for the full range,
1900–1949, 1900–1909, the 1999–2000 boundary, combined France/Italy filters, and
the popular selection. It also checked response bounds and inspected actual
`EXPLAIN (ANALYZE, BUFFERS)` plans. Sample timings were 17.6 ms for overlap
aggregation and 4.7 ms for suggestions on the current local catalogue. An in-query
synthetic fixture with 20,000 painter intervals took 39.0 ms for overlap aggregation;
these are single-run observations, not latency guarantees.

Browser regressions check count equality across two zoom levels, applying a
suggestion from the chart, index and filter buttons, actual result counts, opening
a painter, retained dates/preferences, reload/history, accessibility and layout
at 1440, 1366, 390 and 320 px.

Remaining load tests: realistic country/movement association skew at 20,000
painters, concurrency, cold-cache latency, and search/work-type predicates against
10 million artworks. The new aggregation does not enrich or download artworks;
the synthetic painter plan is not evidence of artwork-scale search performance.

Disposable plans and browser screenshots remain under `/tmp/artline-timeline-*`
and `/tmp/artline-suggestions-*`.

## Production request timeout correction — 13 September 2026

The popular timeline's per-painter artwork counts joined the full artwork rows
to check their status. On the expanded cloud catalogue, the individual-painter
query exceeded a ten-second diagnostic deadline; actual HTTP requests sometimes
continued beyond the web proxy's twelve-second deadline and returned 503.

The server now selects at most 300 painter rows before requesting their artwork
counts in one bound-ID query. Artwork links have a foreign key to artworks, so
preview counts can exclude archived IDs through the status index without reading
every linked artwork row. Published requests additionally require a published
artwork. Distinct counts still handle multiple attribution roles correctly, and
painters without linked artworks keep a zero count.

Timeline queries cache parameter descriptions instead of reusable named
statements, preserving planning with the current filter values. The HTTP handler
also cancels timeline work after eight seconds, before the web proxy deadline.

Read-only cloud measurements found 126.8 ms for the scoped count query, versus
the former query exceeding ten seconds. Eight consecutive requests through the
updated repository code and one read-only cloud database session returned the
same 100 painters and counts in 0.25–0.78 seconds each. These are diagnostic
observations, not latency guarantees. Local read-only tests compare the new
counts with the former positive artwork join. Fixture-database tests remain
opt-in; the real catalogues were not modified for these checks.

This correction does not resolve the separately recorded museum-directory
performance issue. Ten-million-artwork load testing remains outstanding.
