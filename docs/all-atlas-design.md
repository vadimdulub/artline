# All: a canvas for existing content

## Current design

Primary navigation: **Painters / Books / Events / All**. Museums and Catalogue
remain available at their existing URLs and through native record links, but
are absent from the main tabs. “Painters” describes the lifespan timeline;
“All” continues to place individual artworks by creation date.

All starts empty. Only preset metadata and bounded country choices are requested
before the user acts; no collection response is fetched.
The black surface fills the remaining viewport; there is no lower entry index
or footer on this page. Six suggested periods offer starting points, while the
selector retains all 30 historical lenses. Choosing a lens loads three layers
with the context window and highlights enabled. Clear restores the empty canvas.

    Painters / Books / Events / All
    Search                                  + Add | Reset view
    Historical period | Continents | Countries | Region | Highlights
    Filtered by …                                      Clear filters
    ┌ black canvas ────────────────────────────────────────┐
    │ Choose a starting point / six suggested periods      │
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
in the desktop filter bar. Clear filters removes global search/geography and
unchecks Highlights, preserving layers and years. Reset view restores the empty
canvas and default Highlights selection. The period’s info button opens its
description, sources and Main period / Before and after switch in a side panel. Main-period shading
remains on the timeline. These are chronological windows, not claims that one
record influenced another. Dense lanes use period bars; selecting one narrows
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
Browse retrieves at most 30 records per page; Add uses a minimal count preview. A whole layer uses its own native discovery filters, including its Top 100
setting. Those filters override the lens highlight default for that type.

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

A new preset is a record in `internal/atlas/presets.json` with an ID, name, group,
description, main/context ranges and sources. A future content type adds a native
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

Year navigation keeps the established compressed early periods on a fixed axis.
Dragging the selected band translates both edges by the same screen distance;
dragging an edge or editing the From/To pair changes the selected interval.
Following the user’s explicit preference, the full chart remains fixed: date
selection never zooms or shifts the axis. Compression anchors, tick positions
and each retained entry’s horizontal position stay at the full catalogue scale.
A subtle band marks the selected years. Timeline containers retain their identity. Shared controls keep the existing
paper/ink palette and type. Books ends at 2000, including aggregate discovery;
recorded creator life dates and underlying records remain intact. Collections is
removed from book UI, request parsing and suggestions. All keeps geographic
filters, adding countries and continents alongside its existing regions.


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
