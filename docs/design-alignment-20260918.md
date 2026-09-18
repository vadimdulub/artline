# Artline design review, 18 September 2026

## Direction and research

Artline is an atlas for exploring connections between art, literature, and
history. Its defining element is the large dark chronological field. Preserve
that, the serif dates, restrained paper controls, and right-side detail panels.
This is a refinement of the user's established design, not a new visual theme.

The desktop and 390px phone audit found three priorities:

1. Museums and Catalogue use different search bars, label spacing, filter chips,
   and reset conventions. Bring those into the same reusable filter system.
2. On phones the open filter grid pushes Books' timeline below 480px. Make filter
   groups collapsible while keeping search, Reset view, and applied choices in
   view. Filters remain expanded on desktop.
3. The shared masthead still says “Atlas of painters · 1100–2000,” which does not
   describe Books or Events. Group ArtWorks, Books, and Events together in the
   navigation and describe the broader atlas consistently.

[W3C consistent identification](https://www.w3.org/WAI/WCAG22/Understanding/consistent-identification.html)
supports using the same names and controls for equivalent actions.
[W3C target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
informs visible keyboard focus and comfortable touch controls.
[Baymard's applied-filter research](https://baymard.com/research-articles/how-to-design-applied-filters)
supports retaining removable selected filters outside the mobile filter panel.
The [Met's essay collection](https://www.metmuseum.org/essays) demonstrates
connected cultural subjects with restrained search, categories, and short
context. These support the recommendations; the layout choices below are
Artline-specific design judgments.

## Compact design system

- Paper `#f2efe8`, ink `#1b1916`, timeline `#12110f`, muted text `#625d55`,
  rules `#d0c9be`, and accent `#c85139` retain the existing palette.
- Georgia: display headings, dates, and reading text. Avenir Next/system sans:
  navigation, filters, metadata, and controls. Shared page titles use a single
  responsive scale; timeline years keep their existing scale and emphasis.
- Shared horizontal gutters: 24px desktop, 18px phone. Use 8px spacing steps,
  44px primary touch controls, and thin rules. No new card chrome or decoration.
- Left-align content and labels. Keep source credit subordinate but readable.

Desktop:

    Artline                ArtWorks / Books / Events / Museums / Catalogue
    search                                                    Reset view
    same filter labels, selections, and control heights
    applied filters                                      Clear filters
    timeline or collection content

Phone:

    Artline / section navigation
    search                                      Reset view
    Filters                                          Show
    applied choices remain visible
    timeline or collection content

Review against the brief: the existing palette and typography were explicitly
chosen by the user and stay intact. A large introductory hero, more cards, or
new accent colours would compete with the timeline and are omitted. Museums
retain artwork-led collection browsing; Catalogue retains its editorial table.
Consistency means shared controls and hierarchy without forcing unlike content
into the same layout.

## Future All tab

All is the next feature, not a placeholder navigation item in this change.
It should reuse the shared search, active filters, year controls, grid, and
record drawer. Its backend must provide bounded, typed chronological results
across art, books, and events, with explicit date semantics (creator life,
publication, event duration), per-type counts, and independent cutoffs. It must
not fetch all three collections into the browser. Labelled content lanes and
type filters will be more dependable than colour alone for mixed content.

Before implementing All, define what the art lane plots: individual artwork
creation dates or painters' life periods. Preserve the difference between
observed overlap in time and evidence of historical influence.

## Implemented and checked

- ArtWorks, Books, Events, Museums and Catalogue now use the shared search,
  filter layout, active chips and reset controls. Museums and Catalogue also
  share a page-heading component. Native selects have explicit accessible names.
- Phone filter groups collapse behind a 44px control, with a count of applied
  facets. Search and removable active choices remain visible. Escape dismisses
  an open tooltip or selector before dismissing its containing filter group;
  keyboard focus returns to the relevant control.
- The ArtWorks Top 100 default now appears as an active chip, as it already did
  in Books and Events. Removing it and resetting use the existing URL semantics.
- Catalogue search, status, sort and page are URL state; reload and browser
  history restore them. Editor access is collapsed until needed. Its existing
  editing functions remain intact.
- The masthead and footer identify art, literature and history. Navigation groups
  the three chronological views together. The event drawer's ArtWorks link now
  uses ArtWorks' actual popularity parameter so browsing a period includes the
  full matching collection.

Measured in headless Chrome at a 1,000px viewport height: the three timelines
begin at **219px** on a 1,440px-wide screen and **286px** on a 390px-wide screen.
Books previously began around 482px on the phone: approximately **196px** more
of the dark timeline is exposed before scrolling. Shared search fields are 44px
high across all five tabs. The existing dark canvas, date compression, plotting,
date inputs, range gestures and right-hand drawers are preserved.

Validation: **65 distinct browser tests passed** across shared layout,
accessibility, Books/author views, Events/descriptions, year editing and dragging,
Russian-language filtering, Museums selection/pagination and Catalogue history.
Widths include 320, 390, 768 and 1,440px. The tooltip Escape regression found in
the first run was fixed and its suite passed on rerun. Build/TypeScript and lint
passed; source-enrichment Go/Python tests and the read-only event audit passed.

Disposable visual evidence is in `/tmp/artline-design-before/`,
`/tmp/artline-design-after/`, `/tmp/artline-design-final/` and
`/tmp/artline-design-regressions/`. Desktop Museums, phone Catalogue and phone
Books were visually inspected, in addition to automated overflow and accessibility
checks. All remains a future backend feature; no mixed collection is downloaded
into the browser and no claim of full-scale load testing is made here.

The companion [event-description research](research/event-description-followup-20260918/README.md)
records 118 additional sourced English summaries, retained conflicts and the
remaining follow-up leads.
