# Events implementation and design

Scope: world history through 2000, confirmed by the user on 17 September 2026.
Events, historical periods and movements are explicitly distinguishable. The
default is an unranked editorial Top 100; clearing that filter opens the broader
source-linked collection. Records remain in review in the personal preview.

Design follows the existing atlas exactly: dark #12110f timeline, paper #f2efe8
controls, ink #1b1916, muted #625d55, accent #c85139, rules #d0c9be. Georgia carries
dates and index titles; Avenir Next carries navigation and controls. Retain the
large dark chart, left alignment, thin rules and right-hand record drawer.

    shared navigation
    search / reset
    topics | types | regions | countries | Top 100
    active filters
    large dark timeline / density overview
    shared year inputs and range track
    compact event index

The brief asks for continuity with ArtWorks, so no new card system, palette,
hero, illustrations or animation is introduced. Reuse AtlasFilters,
MultiSelectFilter, ActiveFilters, TimelineGrid, TimelineMark, TimelineOverview,
TimelineRangeControls and RecordDrawer. The compressed historical scale is the
same presentation function used by Books. No year zero or CE suffix. Dates,
counts, visibility, sorting, overlap tests and page selection belong to Go/SQL.

The API returns at most 100 records with keyset pagination. More than 100 dated
matches switches to the same 50/25/10-year overview intervals as ArtWorks and
Books. Suggested filters use real counts and only unused dimensions so they
narrow an existing selection. Filter URL state survives reload and browser Back.
Details link to Books/ArtWorks in the event's date interval where supported;
these are contextual browsing links, not claims of a researched relationship.

Research methodology, source responses, exclusions and exact counts belong in
`research/historical-events-20260917/`. A source-linked corpus is not equivalent
to independent primary-source verification of every event. Never fill missing
dates, countries, participants or descriptions with invented metadata.
