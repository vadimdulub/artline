# All: a canvas for existing content

## Current design

Primary navigation: **Painters / Books / Events / All**. Museums and Catalogue
remain available at their existing URLs and through native record links, but
are absent from the main tabs. “Painters” describes the lifespan timeline;
“All” continues to place individual artworks by creation date.

All starts empty. Only preset metadata and bounded country choices are requested
before the user acts; no collection response is fetched.
The black surface fills the remaining viewport; there is no lower entry index
or footer on this page. All 30 starting points are visible: twelve main periods
sit in the center, with the other eighteen arranged on either side. On narrower
screens the additional periods wrap below the main group. All 30 remain in
the searchable period picker. Choosing a period on an empty canvas loads three
layers with the context window. Search and geographic filters also start all
three layers from an empty canvas. Changing a filter preserves the selected
layers and their native filters. Clear restores the empty canvas.

    Painters / Books / Events / All
    Search                                  + Add | Reset view
    Historical period | Continents | Countries | Region | Highlights
    Filtered by …                                      Clear filters
    ┌ black canvas ────────────────────────────────────────┐
    │ 9 periods | Choose a starting point | 9 periods      │
    │           | 12 main periods        |                │
    │ (after selection: common axis and selected lanes)    │
    │ (after selection: shared year controls)              │
    └─────────────────────────────────────────────────────┘

Established tokens remain: paper #f2efe8, ink #1b1916, dark #12110f, muted
#625d55, rules #d0c9be, and the existing type colours. Georgia carries dates and
titles; the existing sans carries controls. Desktop/phone gutters stay aligned
at 24px/18px. All reuses `AtlasFilters`, `ActiveFilters`, `MultiSelectFilter`,
`AtlasSelect` and `AtlasCheckbox` from the other tabs. Search, Reset view and
Add share the first row; the second row holds the filters. Active chips use
the same removal and focus behaviour as Books, Events and Painters. The actual
header height determines the remaining canvas height. Phone filters collapse
behind the shared Filters toggle.

Historical periods, continents, countries, region and Highlights are visible
in the desktop filter bar. The period reuses the shared searchable picker with
one radio selection and appears as a removable active filter. Removing it clears
its year window while keeping layers and other filters. Clear filters removes
global search/geography, the selected period and its years, and unchecks
Highlights, preserving layers and any manually selected years. Reset view restores the empty
canvas with Highlights checked. Highlights is enabled by default and can be switched off. Artworks always require an attached, renderable picture; this is not a main-screen option. The period’s info button opens its
description, sources and Main period / Before and after switch in a side panel.
All 30 periods have a reviewed focus. Twenty-two use recorded country/region
associations and explicit related entries; eight retain worldwide cultural
coverage. Eleven thematic presets restrict events to a reviewed sequence.
Byzantium also matches reviewed object traditions independently of creator
identity or present custody. Selected surrounding events carry a “Context” label.
Explicitly selected core books/events count as highlights within their preset;
global highlight membership is unchanged. Visibility, dates, pictures and user
filters still apply. Changing years retains this focus; removing the period or
Zoom out clears it. These associations do not assert influence. Dense lanes use period bars; selecting one narrows
all layers. Browse opens a bounded side panel, keeping every entry reachable
without placing another section below the canvas. Native details replace that
panel and restore focus to its Browse button on close.

## Add means existing content

Add opens a layer picker for Artworks, Books or Events. Choose the type, apply
its native filters and add every matching dated record as one layer. The matching count summarises the selection; Add contains no catalogue list. Each type has one layer; reopening
Add updates that layer's filters. Browse and timeline marks still open details.

Layer type and filters are saved in the URL. Refresh and browser history retain
the view. Removing a layer removes its filter scope. The All interface no longer
creates or reads individual `pick_*` selections; changing the view clears those
legacy URL fields. Existing API support for older clients is unchanged.
No external-data submission, title/source form or catalogue write is involved.
The retired `atlas/drafts` routes still return 404; the existing migration and
any historical data remain preserved.

The picker always uses the timeline’s current years. Adding a layer preserves
that range; date changes remain in the timeline controls.
Browse retrieves at most 30 records per page, with Previous/Next page controls; Add uses a minimal count preview. Record arrows seek individual previous/next entries in the current filtered layer, across page boundaries. Direct record links use that same sequence. Enlarged artwork images stay open when moving between records and reset image magnification. A whole layer uses its own native discovery filters, including its Top 100
setting. Those filters override the lens highlight setting for that type.
New Add drafts inherit Highlights. The Books label is “Book highlights” because the editorial list can grow beyond 100. Toggling global Highlights clears explicit book/event highlight overrides. The artwork popular-painter filter stays independent of artwork highlight membership.
Artwork Browse actions say “View”; Books and Events retain “Read”.

## Server ownership and scope

Go/PostgreSQL owns visibility, dates, eligibility, filtering, counts, density,
sorting and keyset paging. The browser renders bounded responses: at most 60
entries per lane and 30 per Browse page. Add requests at most one item alongside
the matching total and renders only the total. Artworks keep the creation cutoff of
1970 and source-backed selection/holding rules. Books retain their recorded
publication intervals; events stop at 2000. Undated entries stay in their native
catalogues. Named, anonymous and unresolved creator labels are preserved.

`selection=true` distinguishes an explicitly empty canvas from a catalogue
search. Repeated `type` values enable complete layers. For legacy API clients,
`pick_artwork`, `pick_book` and `pick_event` retain their existing ID semantics. Server validation enforces
known types, bounded ID lists, unique IDs and safe identifier syntax. Visibility
and eligibility predicates still apply to every selected ID. UUID artwork IDs
use an indexed array predicate before creator/media enrichment. Cursor scope
includes the complete selection and filters, including page size.

Each lane evaluates its matching ID/date relation once, sharing it between the
total, density buckets and bounded detail page. When artwork countries or
continents are selected, PostgreSQL first materializes the geographically scoped
native columns, then applies eligibility. This prevents a broad country selection
from checking holdings across the entire catalogue. Native painter/ID predicates
remain inside that scope; creator/title detail enrichment is bounded to page IDs.

A new preset is a record in `internal/atlas/presets.json` with an ID, name, group,
description, main/context ranges, sources and reviewed focus. A focus declares
regional or worldwide coverage, optional object traditions, core/context IDs,
and whether its event sequence is explicitly selected. Cursor scope includes
this configuration so a review invalidates older pagination cursors. A future content type adds a native
Go provider/definition, its date and evidence rules, and a detail renderer; the
common controls, picker, lanes and pagination can be reused. Evidence-backed
relationships between entries would be a separate model from time overlap.

## Verification

All browser work is headless. Screenshots/traces stay in `/tmp`; no browser test
inserts catalogue fixtures. Real database audits use connections forced to
`default_transaction_read_only=on`. No content ingestion or publication occurs.

The revised All suite covers blank start/no collection request, 30 presets,
responsive canvas height and accessibility, compact filters, all three whole
layers, filtered matching counts, cancellation, zero write requests, reload,
removal, bounded side-panel pagination, native drawers/focus, BCE/manual years,
density drill-down, URL history and the removed draft endpoint. Shared-tab
regressions cover the four-link navigation and existing responsive controls.

Go checks cover selection bounds, typed identifiers, cursor isolation, empty
responses, mixed layers/individual IDs, public visibility and API validation.
Real read-only selection tests verify exact IDs/counts and that adding a book
layer does not expand the selected art/event lanes. The selected-artwork EXPLAIN
plan retains the artwork primary-key lookup; evidence is saved under
`docs/research/all-historical-lenses-20260918/query-plans/`.

Earlier read-only aggregate observations on the actual local catalogue were
about 2 seconds for WWI highlights and 3.5 seconds for the unfiltered full range.
The bounded artwork page took 76ms; single-artwork eligibility and detail
lookups used the primary key. Broad aggregates still scan eligible metadata,
with indexed holding/creator lookups. These local observations are not proof of
10-million-row performance. Before that scale, measure concurrent cold-cache
full-range/search load and implement any required backend discovery projection
with explicit visibility, evidence and invalidation semantics. Do not compensate
by loading full collections into Next.js.

Earlier canvas revision checks: 18 All browser cases and 19 shared-tab cases passed,
along with Go package tests, the read-only selection audit, production build,
TypeScript and ESLint. All browser runs were headless.

## Shared Add filters (18 September revision)

Add uses the native Books, Painters and Events filter fields, with the same
search, multi-select popovers, selected chips, clear/reset and Top 100 defaults.
The existing paper controls sit above a bounded result list in the right panel;
two columns keep the drawer readable, and phone filters collapse as on each tab.
Books expose authors, regions, countries and languages. Art exposes
painters, movements, regions, countries and work types. Events expose topics,
types, regions and countries. Women filters retain their native meanings.

Adding a layer saves its complete filter scope in the URL. Each layer keeps its
own filters; switching picker types retains unsaved choices. Add/update applies
the previewed years and filters for a whole layer.
Go applies the same scope to totals, density and bounded pages; changed filters
invalidate cursors. Verify Russian books, combined facets, all three layer types,
reload/history, empty results, keyboard/popover behaviour and mobile overflow.

Verification before the whole-layer follow-up: 54 headless browser checks passed
(18 All, 7 Add filters, 19 shared controls, 3 Books and 7 Events), including
Russian-language count parity, author search, combined event facets, painter
selection, per-type drafts, saved scope/reload, bounded pagination and an explicit
book outside its filtered layer. Accessibility and screenshots were checked at
1440, 390 and 320px. Production build, TypeScript, lint and Go checks passed.
The read-only catalogue audit compares dated Books/Events counts with their
native repositories and verifies returned artwork creator/type evidence.
The selected-painter plan starts with the painter slug index and indexed artwork
links before artwork enrichment. The local Monet key query took approximately
4ms with a warm cache; this is not a large-scale load test.

## Whole layers only (18 September follow-up)

Add now has a single add/update action per type. Result rows only preview the
filtered collection; per-entry Add buttons and the 60-pick notice are removed.
The empty canvas, shared filters, Top 100 defaults, year range, bounded paging
and detail browsing retain their existing behaviour. Browser coverage replaces
individual-pick flows with whole-layer search, combination and cancellation.

Whole-layer verification: 26 headless All/Add checks passed, including mobile
accessibility, filter persistence, cancellation and detail browsing. TypeScript,
ESLint and the production build passed. No database changes were needed.

## Compact Add panel (18 September refinement)

Keep the existing Artline tokens: paper #f2efe8, ink #1b1916, dark #12110f,
muted #625d55 and rules #d0c9be. Georgia carries the heading; the existing sans
carries controls. Preserve the native filter grid and left alignment.

    Add a layer                         Close
    Artworks | Books | Events
    Search / shared entity filters / selected chips
    Matching count
    [ Add or update this layer ]

The panel ends at its action. Remove all artwork, book and event catalogue
previews and pagination from Add. The compact count gives useful feedback;
a solid ink button makes the single action clear. Review against the brief:
no extra cards, decorative sections or replacement filter patterns are needed.
Browse retains its separate bounded entry list and detail actions. Add requests
one item at most for the existing aggregate response, which it does not render.

Refinement verified with 26 headless All/Add checks, including absence of lists
and pagination for every Add type, unchanged Browse/details, filter counts,
reload and cancellation. Desktop and 320px screenshots were visually reviewed;
390px accessibility/layout checks also passed. Build, TypeScript and ESLint passed.

## Stable year navigation and geography

All’s full-history overview and navigation slider compress earlier centuries,
with equal year spacing from 1400 through 2000. Books and Events retain their
existing fixed axes and 1700 breakpoint. Dragging the selected band translates
both edges by the same screen distance; dragging an edge or editing the From/To
pair changes the selected interval.

The 20 September zoom request supersedes the previous fixed-axis behavior for
All. Selecting a historical period, density interval, or custom pair of years
fits that interval across the complete timeline width. Focused ticks, entries,
and density bars use equal calendar-year spacing, including across 1400 and the
BCE/CE boundary; there is no year zero. Tick spacing adapts to viewport width
and always includes both selected endpoints. Periods retain their existing
Before and after / Main period choice. The slider continues to show all years.

Zoom out removes the period and custom years while retaining layers, search,
geography, Highlights, and each layer’s native filters. The resulting overview
uses the original compressed scale. Zoom out is disabled once all years are
shown; Clear still returns to the empty canvas. Selection and zoom are derived
from the URL, so reload and Back/Forward restore the same view. This fills the
timeline width without entering a separate fullscreen mode. Shared controls keep
the existing paper/ink palette and type. Books ends at 2000, including aggregate discovery;
recorded creator life dates and underlying records remain intact. Collections is
removed from book UI, request parsing and suggestions. All keeps geographic
filters, adding countries and continents alongside its existing regions.

All's year ruler uses short ticks. Full-height year guides and the overlapping
selected-range/preset overlays are removed from the entry canvas. The existing
dark background, paper text, Georgia dates, sans-serif labels and subtle lane
separators remain. Only the actual entries carry date/duration lines; dashed
entry lines still indicate approximate dates. Period context remains available
in its details panel, and dragging still previews the heading and slider.


Geography uses recorded country names (case-insensitive matching), with historical
states kept as separate choices. Continents group the existing region codes;
records with no geographic evidence do not acquire an inferred location. Choices
are bounded to 1,000 vocabulary entries (741 in this audit). Country and continent
selections apply to every lane, Add counts and Browse, persist in URLs, and form
part of the pagination cursor scope. Native layer filters continue to intersect
with global geography. Inline dropdowns close after a pointer click completes so
collapsing one cannot move the next target underneath the pointer.

Verification: 17 scale unit checks; Go books/atlas/HTTP checks; read-only catalogue,
author, suggestion, native-filter parity and geography audits; focused headless
Chrome checks across all four timelines, year inputs, touch cancellation, Add,
Books filters and mobile layouts. The final 18-case browser run and two mock-only
interaction checks passed. TypeScript, ESLint and the production build passed.
Desktop/mobile screenshots are under `/tmp/artline-years-confirmed/`. No database
fixtures, migrations, ingestion or record updates were used. All 10,000 stored
books remain intact, with 8,685 visible under the new cutoff.

The actual scoped Monet query with France/Europe retained the painter-link and
artwork primary-key index lookups and ran in 8.36 ms locally. Plan evidence is
`/tmp/artline-entity-filter-audit/monet-geography-plan.json`. This checks the real
local catalogue, not 10-million-artwork performance; global aggregate and
concurrent-load tests at the target scale remain outstanding.


The art header now places “Movement colour key · N in this view” beneath the
painter count, replacing the research-preview sentence. Its expandable key is
anchored to the header, with a bounded panel and keyboard dismissal. The count
remains derived from movements in the current response. Desktop, 390px and 320px
checks cover placement, opening, Escape and selecting a movement.

## Loading and range interaction

All keeps the selected years in URL interaction state, independently of the last
server response. Dragging previews the heading and selected band without issuing
requests; releasing commits the range. Earlier/Later and keyboard changes apply
immediately, including when another request is pending. The chart fits the
committed interval; the axis stays steady during an uncommitted drag preview.
Superseded requests are aborted and ignored; the read-only API proxy forwards cancellation upstream as well as its timeout.
Bookmarked presets retain their implicit three layers when years or filters change.
Existing bounded lane data stays dimmed during same-range filter refreshes, with
stale entry actions disabled. After a range change, lane headings remain while
loading placeholders replace old marks and bars, so old dates are never drawn
against the new axis; removed layers disappear immediately. Year controls remain
available after a connection error so a different interval can recover the view.

The shared inline spinner accompanies status text on the timelines, All's period
loading, Add/Browse and record drawers. Retry attempts have their own loading state;
an old error does not hide the progress indicator. Reduced motion disables its
animation. Add previews and retains the current years and global search/geography.

Narrow density bins use proportional bar spacing. Counts and action text that do
not fit are omitted from the bars; hover or keyboard focus describes the period
above them, and Browse remains available. On short screens All can scroll within
its viewport so expanded filters cannot make the year controls unreachable.

Regression scenarios in `e2e/all-interaction.spec.ts` delay actual read-only API
responses and simulate connection failures. They cover repeated year clicks,
drag previews, out-of-order completion, retry, removal/reset during loading,
global-filter preservation, crowded bars, short phones, BCE/empty/cutoff ranges,
invalid shared URLs, Add during a refresh, and record loading/recovery. The shared
year suite also exercises All's paired input drafts, overlapping handles and
touch commit/cancellation. No catalogue fixtures or database changes are involved.

Final verification: 60 headless Chrome scenarios and 43 unit tests passed, along
with TypeScript, targeted ESLint and the production build. Desktop, 320px phone,
short-screen and loading-state screenshots were visually reviewed. Browser
artifacts are under `/tmp/artline-all-final/`; the run log is
`/tmp/artline-all-final.log`. The proxy cancellation regression uses an isolated
fetch stub, with no database connection.

The subsequent All-axis spacing update passed 45 unit tests, ESLint, TypeScript
and 36 read-only browser scenarios, including equal spacing from 1400, shared
mark/bar/slider coordinates, unchanged Books/Events scales, and desktop/phone
range interactions. Release validation artifacts are under
`/tmp/artline-scale-release-local/`.

## All zoom verification — 20 September 2026

Added 68 unit cases for focused coordinates, adaptive ticks, endpoint clipping,
BCE/CE continuity, and the unchanged compressed overview at five widths. Added
19 Chrome scenarios for WWII and Renaissance context/main periods, custom
intervals, Zoom out, retained filters/layers, reload/history, responsive layout,
keyboard operation, request cancellation, API errors, and full-range URLs.
Updated the former fixed-axis All assertions to check fitted coordinates; the
other tabs retain their fixed-axis regression checks. The touch test now honors
the configured base URL instead of hard-coding port 3000.

All 113 frontend unit tests, TypeScript, ESLint, the production Webpack build,
and the Go atlas/httpapi unit suites passed. Browser checks used an isolated
production build on port 3100 and the real local catalogue through an API with
migrations skipped and `default_transaction_read_only=on`; no database or
fixtures were created. Temporary screenshots and traces are under
`/tmp/artline-all-zoom-*`. The existing port-3000 dev server hung during initial
page loads. One initial broad Add-artworks request reached the API timeout;
its focused rerun passed in 8.7 seconds. The API queries were not changed, and
these checks do not establish ten-million-record query performance.

Across the regression runs, all 85 distinct browser checks passed after the
artwork timeout recheck and the touch test's base-URL fix. This includes the
19 new zoom checks, chart/slider alignment, native layer filters, and the
unchanged year controls on Painters, Books, and Events. Desktop and phone
screenshots were visually reviewed; WCAG A/AA checks passed in the exercised
period and filter states.

## Filter discovery — 21 September 2026

The starting surface shows all 30 periods, using the existing server-owned
period records and sources. Twelve main choices, including Edo Japan, the
classical world, the Silk Roads, Romanticism, the Russian Revolution and the
Space Age, stay centered and prominent. The other eighteen remain visible
without an expansion control. Desktop uses balanced side columns; narrow
screens wrap the groups and allow vertical scrolling instead of shrinking
touch targets or clipping period names.

Applying search or geography to an empty canvas initializes Artworks, Books and
Events. Shared filter URLs without an explicit selection do the same. Once a
view is populated, edits update its counts and content while retaining native
layer filters and intentional removals. Removing every layer writes an explicit
empty selection, which survives reload/history; Add or another filter action
can populate it again. Multiple countries match any selected country; different
filter groups intersect. The subsequent picture/navigation revision below restores Highlights as the default, as explicitly requested by the user; switching it off includes other eligible matches. Explicit native settings remain respected until the shared Highlights switch is changed. All artwork results require pictures.

Added 35 unit cases for filter initialization, explicit empty URLs, retained
layers and Add defaults; the complete frontend suite passes 159 tests.
TypeScript, targeted ESLint, the isolated production Webpack build and Go
atlas/httpapi unit suites passed. Existing read-only native filter parity,
geography/public visibility and legacy selected-entry audits also passed.

The new read-only discovery audit passed eight cases against real records:
Japan, Japan + France, Japan + France + Asia, Japanese search, France Highlights,
Monet with geography and work type, an empty country, and the full catalogue.
Repeatable-read transactions compare each lane's count with the prior eligibility
query, verify bounded and ordered pages, and check unchanged density aggregates
across pagination. No fixtures, database creation, migrations or writes are used.

The original Japan + France plan evaluated eligibility before geography and
checked holdings for 237,045 artwork candidates. Its captured artwork query took
5,089 ms; earlier audit executions exceeded 10 seconds. The revised plan scopes
60,121 candidates first, finds 53,169 eligible artworks and enriches 31 page IDs.
Its captured warm execution took 709 ms. The complete three-lane read-only call
took 3.15 seconds on the final audit; Japan took 605 ms, the Asia intersection
288 ms and the full catalogue 1.50 seconds. The actual scoped Monet plan used
indexed artist/artwork links, materialized 355 candidates, returned 283 eligible
paintings and took 14 ms. Plans are in `/tmp/artline-filter-discovery-plans/`.

These observations establish correctness and query scope on the existing local
catalogue, not ten-million-artwork performance. Concurrent cold-cache tests,
broad geographic materialization costs and any required backend projections
with explicit visibility/invalidation semantics remain capacity-planning work.

All 100 distinct headless Chrome scenarios passed across the final regression
run and the layout recheck. The broad run passed 99 cases; one 390px assertion
read the page height before the header ResizeObserver completed. Waiting for
the measured height made all three empty-canvas layout/accessibility rechecks
pass without changing the layout constraint. The 15 new discovery cases cover
expanded presets, Japan at 1440/390/320px, multi-country intersections, live
edits, shared URLs, reload/history, Add/native filter persistence, explicit
empty selections and out-of-order responses. Existing tests cover fitted zoom,
artwork View actions and the shared year controls. Desktop and phone screenshots
were visually reviewed. Browser artifacts are under
`/tmp/artline-filter-discovery-final/` and `/tmp/artline-filter-discovery-layout/`.
The final isolated API recorded 309 atlas requests, with a 1.51-second 95th
percentile and 2.34-second maximum; no atlas request timed out. This sequential
browser run is not a concurrent-load benchmark.

## All starting points visible — 21 September 2026

The expansion control has been removed. The existing twelve main periods form
the central group, using larger Georgia labels and stronger borders; the other
eighteen use quieter sans-serif controls in balanced side columns. This keeps
the established dark canvas, paper text and warm rules. All choices come from
the same bounded preset response, with no extra catalogue read before selection.

At widths below 1000px, the main group remains centered and the side groups wrap
below it. Long labels wrap, every target is at least 44px high, and small screens
scroll vertically without hiding choices or requiring horizontal scrolling.
Keyboard order begins with the main choices, then the earlier and later groups.
Selecting any period keeps the existing three-layer timeline behaviour.

Layout checks cover 1920×1080, 1440×900, 1366×768, 1280×720, 1024×768,
768×1024, 390×844 and 320×800. They check all 30 unique buttons, centering,
desktop viewport fit, phone width, accessible names/contrast, touch targets and
period selection. A keyboard scenario also checks clearing and reaching the
final choice on a narrow phone. Desktop and phone screenshots were inspected.
Development artifacts are under `/tmp/artline-starting-points-results/` and
production-build artifacts under `/tmp/artline-starting-points-production/`.
All nine development layout/keyboard cases and all 45 production browser cases
passed. TypeScript, scoped ESLint and the optimized Next.js build also passed.
The production run includes the existing All, discovery and historical-period
regressions against the read-only local API; no database fixtures were inserted.

## September 21 discovery and picture navigation

The Painters tab puts “With pictures” inside each creator’s Artworks by year list. Go filters the creator-scoped totals, year groups, pages and neighbors together. Artwork dates and images are never substituted by the client. Both All and creator navigation request at most one item per direction using `neighbor_of`, `direction` and `limit=1`; out-of-scope anchors return no neighbor. Cursor scopes include image and historical-focus choices.

Focused-period research, local sourced corrections, image delivery and the current test evidence are documented in `docs/research/revolution-discovery-20260921/README.md`. Query-plan checks use the existing catalogue and remain insufficient to establish performance at 10 million artworks.
