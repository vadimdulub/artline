# Books catalogue and timeline

Books and ArtWorks share the dark workspace, search/filter bar, filter chips,
multi-select dropdowns, period overview, grid, markers, range controls and right
drawer. The book drawer includes a description, creator biographies and sourced
birth/death labels. Collective authorship has no single lifespan; traditional
attributions are labelled. Unknown dates are never replaced with an author's dates.

The wide overview uses the ArtWorks density intervals: 50 years, then 25 and
10 years as the range narrows. In the full view, dates before 1700 occupy 25% of
the width (5% for BCE and 20% for years 1–1700), leaving 75% for 1700–2000.
The chart labels the scale change at 1700.
The range slider uses the same mapping, with an inverse conversion for pointer
input; its keyboard controls still move in actual years. Selecting earlier or modern periods keeps the complete axis visible. Compression anchors stay fixed when a mixed view crosses 1700 or the BCE
boundary. BCE-only views use regular calendar spacing. Positive year labels have no era suffix; negative
years use BCE. Controls omit year zero.
The slider labels 1700, 1750, 1800, 1850, 1900 and 1950 on wide screens,
alongside its 2000 endpoint. Narrow screens use century labels and omit markers
too close to the endpoint to avoid overlapping dates.
Compression only changes screen positions. API periods, book dates, filtering,
counts and chronological ordering remain unchanged. Labels are spaced by pixels
to remain legible across the change of scale, and early overview bars use narrower
gaps so they remain visible. ArtWorks now uses the same forward/inverse scale
approach: 1100–1400 takes 15% of a broad view, with 85% for 1400–2000. Earlier and later selections retain that same full-axis spacing. Its slider uses numeric years instead
of Roman numerals. Both timelines' range buttons advance the start by one year while preserving
the selected band's visual width (until constrained by the endpoints).
Books can overlap several period counts. Undated records remain accessible in
the full-range text index. Collections is no longer a filter.

Books has no visible range-presets heading or buttons, and neither timeline
shows the range-movement helper sentence. From/To fields, labelled handles,
date markers, Earlier/Later buttons, period drilling and Reset view remain.
Both timelines treat From/To as one draft: Tab moves between the fields without
changing the range; Enter or leaving the group commits a valid pair. Invalid
dates produce an accessible message and never change the catalogue. Escape
restores the current range. The fields retain keyboard focus on commit.
Pointer and touch gestures preview dates locally and commit once on release,
keeping the chart stable while dragging. When narrow-range handles overlap,
dragging left expands the start and dragging right expands the end. Cancelled
gestures restore the range. Moving the selected window preserves its width on the fixed compressed axis.
Both edges move the same screen distance while the full chart stays fixed.
Ticks and retained entries keep their full-axis horizontal positions; a subtle
band identifies the selected years. Calendar duration may change across
compression boundaries. Edge handles and From/To edit the selected interval
without zooming the chart.
The Books screen shows a compact title/author/date index instead of cover cards.
Covers appear only in the right details drawer, so no cover image request is
made until a book is selected. Pagination remains server-bounded to 100 records.

## Author lifespan view

The **Show author lifespans** checkbox above the Books timeline is off by
default. It writes `view=authors` to the URL and preserves search, discovery
filters and years. Reload and browser history retain the choice. Reset view
returns to books; changing views clears the pagination cursor.

In author mode, the year range filters recorded life intervals instead of book
dates. Other filters still select books, then PostgreSQL groups their credited
creators by source ID. Each author appears once with their life dates; matching
book counts appear in the author index. Women authors limits
the displayed creators to the recorded women IDs,
so male coauthors are not included merely because a book has a woman author.
Top 100 still means authors of the Top 100 books, not a separate author ranking.
The current default selection contains 92 creators, including five unplaced
collective/unknown records; the Russian-language selection contains 107.

Exact dates produce solid lifespan bars. The server parses only the source
import's complete year/range/alternative grammar; approximate outer bounds
produce dashed bars labelled `c.`. Original birth/death labels and attribution
credits remain in the author drawer. A lone birth or death date is represented
by its recorded point/range, without inventing the missing endpoint or assuming
the person is still living. Collective authorship has no single lifespan.
Unplaced records remain in the full-range author index.

Clicking an author opens the shared right panel with biography, life dates
and source. **Show books by this author** switches to the
book view, selects that author and restores the full book-year range. Other
book filters remain selected.

The API returns at most 100 author records per keyset page, with server-owned
counts, overlapping period totals and suggestions counted in authors. Periods,
filter suggestions, year controls, layout and panel behavior reuse the existing
timeline components. This requires no catalogue mutation or migration.

The enforced read-only audit verifies grouping, women/coauthor membership,
publication gating, cursor pages, exact period/suggestion counts, approximate
BCE dates and missing death dates. Local count plans on the real 4,092-creator
catalogue measured about 45 ms for all creators and 6.3 ms for Russian-language
creators. These are local observations; larger collections and concurrent
loads still need separate measurement. Browser checks run headlessly and cover
the checkbox, history/reset, drawers, Russian filtering, year semantics,
pagination and accessibility at 1440, 390 and 320 pixels.
Validation passed: six new author browser cases, 26 existing timeline browser
cases, 19 frontend unit checks, Go books/HTTP checks, the read-only author audit,
lint and the production build. Final screenshots are under
`/tmp/artline-book-authors-final/`; no browser window was opened for these tests.

## Data and visibility

`0020_books_catalogue.sql` adds independent work, creator and credit tables.
`GET /api/v1/books` returns at most 100 records, a keyset cursor, scoped counts,
period counts and range metadata. PostgreSQL owns visibility, date overlap,
filtering, counts, ordering and pagination. The browser renders a bounded page.
Creator details are batched for the returned book IDs. `GET /api/v1/books/authors`
searches a bounded list of 30 creator names. Repeated author/language/country/region parameters
match any selected value within a filter; filter dimensions combine.

`GET /api/v1/books/{id}` loads a single work independently of the list filters.
`?book=<id>` preserves selection and supports history navigation. Books reuse
ArtWorks' modal focus handling, scroll lock, Escape and backdrop dismissal.

Imports remain in review. Public reads require published status unless an
authorized research preview is enabled, following the existing catalogue policy.
There is no implicit book publication route. The original 17 editorial records
keep their IDs, descriptions and date intervals within the larger selection.
They are no longer embedded into the production API. Cover reproductions are
selected separately from source-linked rights metadata; the server attaches only
the matching work's selected image from its versioned cover manifest. The drawer
shows the edition image, creator credit, source page and public-domain/license
link. It uses original Artline typography when no selected image exists or a
remote image fails. The fallback is explicitly labelled as an original text
cover, not a historical edition. See the [cover research record](research/book-covers-20260917/README.md).
The user confirmed this fallback on 17 September 2026: use an original Artline
text cover for works without a verifiably reusable edition cover.

## Research and import

The user requested a 10,000-book collection and confirmed inclusion from any year
on 16 September 2026. On 18 September the user changed the display cutoff to
2000. All 10,000 records remain in the database; the current display includes
8,685 records with a recorded end year no later than 2000, or unknown dates.
Records whose date interval crosses 2000 remain outside the visible selection.
The cutoff applies to details, totals, facets, suggestions and author eligibility,
as well as the Books layer in All. Creator life dates remain source facts even
when a death occurred after 2000. See
[the research record](research/historical-books-20260916/README.md) for selection
criteria, source limitations, evidence and verification.

`ops/research-historical-books.py` saves source responses and prepares review JSON;
it never connects to PostgreSQL. The `cmd/import-books` command validates a fixed
record count, unique source/work identities, provenance, creator links and dates.
Without `-apply` it only validates files. With `-apply`, one transaction inserts
new review records. Identical imports are harmless; changed/partial existing
imports abort for reconciliation. Existing editorial changes are not overwritten.
Migrations are a separate operation.

The local preview API can run with `-skip-migrations`, no editor credentials and
`default_transaction_read_only=on`. This permits browsing the actual catalogue
without enabling writes. Backups for this change are under the designated
`Library/Application Support/Artline/backups/books-20260916/` folder.

## Verification

Unit checks cover historical date precision/qualifiers, BCE intervals, cursors,
import validation and publication gating. Browser-only fixtures exercise layout,
accessibility, filters, history, drawers and the large period chart. They never
enter PostgreSQL. The opt-in `ARTLINE_BOOKS_READONLY_DATABASE_URL` audit forces
read-only connections and checks all catalogue pages, count consistency, creator
dates and unpublished visibility against the actual 10,000-record collection.

The 17 September scale update passed 13 timeline unit checks and 18 browser
checks, including native handle dragging, selected-window duration, keyboard
navigation across 1 BCE/1, earlier zoom, the 1731–2026 view from the supplied
screenshot, mobile layout, accessibility, filtering and ArtWorks regression
checks. Lint and the production build passed. Disposable screenshots are in
`/tmp/artline-books-compressed-scale/`; no database changes were needed.

This scale does not establish performance for millions of books. Larger loads,
search indexes and maintained summary projections require representative load
tests and explicit invalidation/review semantics before expansion.

The subsequent controls/cover update passed 29 distinct browser cases, 15
timeline unit checks, 6 cover-rights policy checks, the Go books/HTTP API checks,
lint and the production build. Real selected images were verified after decoding
on desktop and phones; failed images were checked against the text fallback.
The cover manifest matches 801 existing book identities in a read-only audit;
all 10,000 base records remain in review. See the cover research verification
artifact for counts and checksum. ArtWorks density intervals keep their inclusive
end-year spacing, and clicking the final period preserves its exact server range.

The year-editing and crowded-filter follow-up passed 32 Chrome browser cases,
19 timeline/books/URL unit checks, Go books/HTTP checks, the enforced read-only
catalogue audit, lint, TypeScript and the production build. Browser coverage
includes year-pair editing, invalid drafts, BCE, overlapping handles, cancelled
touch gestures, Russian-language period/author filtering, history and exact
suggestion counts. Six repeated overlapping-handle cases also passed. Final
browser runs are headless, as requested; screenshots and traces remain under
`/tmp/artline-timeline-headless-final/`. No database writes were made.
