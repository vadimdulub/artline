# Books discovery filters — 17 September 2026

Books and ArtWorks use the same `AtlasFilters`, `AtlasCheckbox`,
`MultiSelectFilter`, selection hint and active-filter components. Books starts
with Top 100 checked by default (updated 17 September); ArtWorks retains its existing default
100-painter selection, now labelled **Top 100 painters**. Both checkboxes can
combine with every other filter. Reset restores each tab's default. Clearing
filters removes discovery selections while preserving the visible date range.
Books sends the selection explicitly to list, facet and author requests.
Unchecking writes `top100=false` so the choice survives reload and browser history;
Reset view restores Top 100. Direct API calls retain their existing defaults.

The 18 September display cutoff is 2000: 8,685 books remain visible, including
832 with women authors. The stored 10,000-record research collection is preserved.
Collections has been removed from book filters and suggestions, including All/Add.
The historical coverage counts below describe the original research import.

## Meaning and evidence

- **Women authors:** at least one credited creator has a retained, non-deprecated
  Wikidata P21 statement for female or transgender female. Preferred statements
  take precedence over normal-rank statements. Names and biographies are never
  used to infer gender. Unknown creators are simply absent from this selection.
  This currently includes 1,171 books; 19 also belong to the Top 100.
- **Top 100 books:** 100 unranked editorial starting points from the existing
  catalogue, spanning literature, religious traditions, philosophy, science
  and society. This is independent of Wikimedia popularity and publication
  status. The original 17-book editorial selection is retained. Every selected
  ID and editorial basis is in
  [top-100-editorial.json](research/historical-books-20260916/top-100-editorial.json).
  The selection is revisable and does not claim a universal canon.
- **Languages:** exact source language/variety statements on the work,
  [Wikidata P407](https://www.wikidata.org/wiki/Property:P407).
  9,460 books have usable statements across 248 language/variety choices.
  English, British English and American English are separate recorded values;
  selecting several matches any of them. These are not claims about available
  translations or the creator's native language.
- **Countries:** recorded country of origin,
  [Wikidata P495](https://www.wikidata.org/wiki/Property:P495), including
  historical states. No birthplace or citizenship fallback is used. Coverage:
  6,696 books, 244 choices. Some works have multiple origins.
- **Regions:** only a direct source country ISO-alpha2 match to
  [UN M49](https://unstats.un.org/unsd/methodology/m49/overview/), using intermediate
  region when available and otherwise subregion, as ArtWorks does. All 63
  existing ArtWorks country classifications were checked for agreement.
  Historical states or origins without a direct ISO match remain unclassified;
  they are not converted into modern countries. Coverage: 5,874 books, 18 regions.

Unknown metadata remains in the unfiltered collection. Values within a filter
are alternatives; different filters intersect. A book with several origins may
match France and Eastern Asia simultaneously (for example, the retained source
for *Soul Mountain* records France and China). Region and country filters both
apply to the work, not necessarily to the same individual origin statement.

The UI explains these meanings in dropdown help text and the Top 100 tooltip.
Geographic and language filters use source IDs in URLs to avoid ambiguous names.
The dropdown search, multi-selection, removable chips, keyboard controls and
phone layout match ArtWorks.

## Crowded timelines

Books and ArtWorks also share `TimelineFilterSuggestions`. When a Books view
contains more than 100 dated works, its period overview offers up to three
suggestions from the server. Language, country, region and author
suggestions keep the current years, search and other filters. Only unused
dimensions are offered, so a suggestion cannot replace an existing multi-select
and unexpectedly broaden the view. Suggestions prefer nonempty groups of up to
100 books; a still-crowded group can be narrowed again. A period that already
fills the selected range applies the leading suggestion, matching ArtWorks.
The Top 100 shortcut keeps the selected years and other filters as well.

Counts use the list's exact visibility/date/filter predicate and count distinct
book IDs. Author suggestions include both the recorded author label and linked
creator names, matching the author filter. Counts ignore pagination cursors;
selecting a suggestion clears the cursor and opens its first bounded page.
Labels distinguish language from recorded origin, including historical states.

The real Russian-language selection has 505 books. Selecting 1850–1899 opens
206, then 1880–1889 opens 89; choosing Leo Tolstoy within 1850–1899 opens 33.
These are collection observations, not assumptions about language or origins.
The read-only suggestions audit checks every suggested count against the opened
query, including multiple language/country selections, women, Top 100, search,
authors and publication gating. Local EXPLAIN ANALYZE on the real
10,000-book collection recorded approximately 77 ms for full-scope suggestions
and 6.5 ms for Russian-language suggestions. Larger collections and concurrent
load still require separate tests; these timings do not establish capacity for
the artwork-scale target.

## Projection workflow

Migration `0021_book_discovery_filters.sql` adds separate discovery terms and
one projection per book, indexed by book ID, positive membership and GIN arrays.
No base book/creator records, dates, descriptions or review statuses change.

`ops/prepare-book-discovery.py prepare` reads the real local catalogue in a
read-only transaction and builds projections from retained source responses.
It requires Python with psycopg 3. It never downloads books or images.
`apply` is an explicit local-only action. It locks base tables while checking
all source checksums, rejects conflicting existing projections, inserts missing
rows transactionally and permits identical replay without changes. Source
responses, claim IDs, revisions where present, source-file checksums, region
mapping and the editorial version are retained under
`docs/research/historical-books-20260916/`.

The pre-change dump and source-checksum snapshot are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/books-discovery-20260917/`.
Research manifests and verification receipts are in the research directory.

Reads only join projections whose checksum still matches their base record.
Changes to a book or creator source checksum also invalidate affected projections
through database triggers. Rebuild/reconcile research before restoring invalidated
membership. A future creator-credit editing/import workflow must likewise
invalidate affected projections; there is no mutable credit editor in this
change. Editorial changes and terminology refreshes need explicit reconciliation,
not an automatic overwrite. Publication status is always checked live.

Go/PostgreSQL own filtering, counts, chronology, sorting, density and pagination.
Every books response has at most 100 records, creator details are batched for
those IDs, author options are bounded to 30, and vocabulary facets are bounded
to 1,000. Facets and author choices respect publication and the women/Top 100
scope. The browser holds interaction state and vocabulary labels, not a full
book collection.

## Verification

Read-only tests audit all 10,000 real records across 100 keyset pages; all
1,171 women-author records across 12 pages; combined language, country, region
and discovery filters; filtered density/drill count agreement; remote author
scope; and publication gating for details and facets. No test databases or
database fixtures are used.

Playwright covers checkbox combinations, reload/back/reset, active chips,
empty intersections, facet failure/retry, both right panels, BCE navigation,
cover layout and automated accessibility at desktop/tablet/phone widths.
The fifth dropdown spans the phone row so both checkboxes sit together and
the tooltip stays in the viewport. Disposable screenshots stay under `/tmp/`.

Read-only EXPLAIN ANALYZE captures use the actual repository predicate on the
real 10,000-book collection. The recorded women/English page was 15.8 ms,
Top 100 page 0.5 ms, and combined count 0.2 ms. Plans and parameters are retained
in `discovery-query-plans.sql` and `plan-discovery-*.json`. These are local
observations, not evidence of performance at the artwork capacity target;
larger book volumes and concurrent-load testing remain separate work.
