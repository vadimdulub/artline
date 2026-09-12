# Painter artwork chronology

8 September 2026. Show a painter’s recorded artworks through time, not only the
ten representative profile slots. Preserve the right-hand painter panel unless
the owner chooses expansion in the main diagram.

## Design plan and brief check

Keep paper #f2efe8, stone #e8e3d9, ink #1b1916, charcoal #12110f, muted #625d55
and red #c85139. Georgia remains the reading/heading face and Avenir/system sans
labels controls. Left-aligned date groups and actual artwork thumbnails are the
content; no new decorative numbering or charts unrelated to creation dates.

The focused chronology is the distinctive element: the painter’s interval carries
dated marks, with a separate dashed terminal marker for undated or missing data.
It never presents an unknown work as made in the painter’s final year. A year
picker provides a non-precision-pointer way to browse dense years. An empty year
means “no works recorded for this year”, not “the painter made nothing”.

```
Artworks by year                       N recorded works
Painter interval: start ── dated marks ── end | ? Missing dates/data
[Artwork year: All recorded years]       [Reset year]
1305 / date range beginning 1305
  Work / original date label / location → full record
1310
  Work / original date label / location → full record
Undated (after dated works, never assigned a year)
[First page] [Next artworks]
```

Compared with simply sorting the existing list, this requires all catalogue works
independent of representative order, bounded pagination, deduplicated attribution
links, public/research visibility and deep links outside the ten-work selection.
Exact, approximate and open-ended dates retain their labels; date ranges are
grouped by their recorded starting boundary, not duplicated across every year.

## Acceptance

- Chronological ordering across years, multiple works per year, unknowns last.
- Unknown-date and zero-record endpoint markers have readable help on pointer,
  keyboard and touch; missing data never uses a made-up creation year.
- Large catalogues page rather than downloading every full record.
- Representative selection and publication validation remain unchanged.
- Error/retry, painter switching, work details, image viewer and deep links work.
- Test mixed exact/range/unknown dates, more than ten works, pagination, duplicate
  attributions and unpublished/archived records; inspect desktop/phone layouts.

The in-app browser connection failed at bootstrap (missing sandbox metadata).
Use the existing isolated Chrome/Playwright suite for local verification.

## Backend-first implementation and scale constraint

The owner clarified a target of approximately 20,000 painters and 10 million
artworks. Recorded this in the root `AGENTS.md`. This superseded an initial reuse
of the museum query and client-side grouping: neither remains on this painter path.

Go/PostgreSQL now own date classification, duplicate-attribution resolution,
unknown-last ordering, year summaries, page groups, chart extent, filtering and
pagination. The response includes group offsets/counts into a bounded work page;
the browser slices those groups for presentation rather than inferring dates or
sorting the catalogue. Chart pixel geometry and modal/URL state remain frontend
concerns.

`GET /api/v1/artists/{slug}/works` returns 24 records by default, at most 60.
Filters are `year` or `undated=1`; the cursor is bound to painter, filter, page
size and visibility. Same-year ties preserve representative order where present,
then title and ID. Membership is independent of representative order. The existing
representative profile/publication rules remain unchanged.

`GET /api/v1/artists/{slug}/works/{id}` retrieves a visible associated work even
when it is not in the representative selection. Canonical shared artwork links
support this without adding the work to that selection.

The query first materializes only one painter's deduplicated attribution links.
It selects/sorts narrow page keys before fetching full artwork JSON, and then
batch-loads media, location evidence and citations for those returned UUIDs. The
shared artwork-evidence helper also no longer uses a global museum CTE. Existing
holding/display/rights/publication policies remain enforced. PostgreSQL documents
why materializing a large CTE can prevent restriction pushdown; the materialized
set here is explicitly painter-scoped.
[PostgreSQL CTE documentation](https://www.postgresql.org/docs/17/queries-with.html#QUERIES-WITH-CTE-MATERIALIZATION).

Local migration `0007_artist_chronology_indexes.sql` adds a covering
`(artist_id, artwork_id)` index. It is intended to precede bulk import. On an
already populated production catalogue, build the index concurrently in a separate
approved maintenance step first: the migration runner is transactional and cannot
run `CREATE INDEX CONCURRENTLY` within that transaction.
[PostgreSQL CREATE INDEX documentation](https://www.postgresql.org/docs/17/sql-createindex.html).

## Verification and honest limits

- Functional PostgreSQL tests add 33 transaction-scoped works to the five-work
  seed: multiple dates, 31 works in one year, an open-ended date and an unknown
  date. They verify pagination, unknown-last grouping, non-representative detail
  lookup, deduplication, cursor validation and public/review/archive boundaries.
- An opt-in query-plan test creates isolated temporary tables with 100,000 works,
  500 associated with the chosen painter. It runs `EXPLAIN (ANALYZE, BUFFERS)` on
  year aggregation and the page query and rejects a full artwork-table scan. The
  painter index and artwork primary-key lookups are used; no planner switches
  disable sequential scans to force the result. Temporary tables disappear when
  the test transaction rolls back; real catalogue records/statistics are untouched.
- A 40-work browser fixture verifies server page boundaries, the terminal undated
  marker and original date labels. Empty-data and connection-error cases are
  distinct. Keyboard/touch help, nested viewer focus, URL history, existing
  timeline/museum/catalogue regressions and 320/390px overflow/Axe checks are covered.
- The design review moved the biography into an expandable section and kept the
  chronology visible earlier on phones. Date labels use readable HTML text rather
  than shrinking with the SVG. Desktop/mobile screenshots are saved under
  `docs/screenshots/chronology-*.png`.

Reproduce the opt-in plan check:

```bash
cd apps/server
ARTLINE_TEST_DATABASE_URL='postgres://localhost/artline?sslmode=disable' \
ARTLINE_TEST_QUERY_PLANS=1 go test ./internal/catalog -run TestArtistChronology -count=1 -v
```

This is a query-shape regression guard, not a production SLA or a full-scale load
test. Full 10-million-row, concurrent and cold-cache tests remain necessary. Very
large individual painter catalogues may need maintained artist/year summaries and
an artist/date read projection to avoid recounting/sorting even a painter-scoped
set on every request. Such projections require explicit ingestion/publication
invalidation, not an arbitrary client cache.

The broader museum/global search queries still need their own scale review before
bulk import; this change does not certify them for ten million artworks. No bulk
ingestion, generated content, commits, Terraform or deployment occurred.

Final verification: all 34 browser tests, 19 frontend unit tests, Go tests with
PostgreSQL integration, the opt-in 100,000-row plan guard, lint and production
build pass. The real local catalogue still has 11 painters and 15 artworks; seven
migrations are applied and the new chronology index is valid.
