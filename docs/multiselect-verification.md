# Multi-select verification - 9 September 2026

Implemented searchable checkbox filters while retaining the paper/dark atlas and
right-hand record drawer. Selected names survive another search, reload and history.
Local taxonomy search filters choices only; actual record filtering stays in SQL.

## API contract

- Timeline: repeated `painter`, `movement`, `country`, `region`, `work_type`.
  `artist` still identifies the open profile, not the painter filter.
- Museum discovery: repeated `artist`, `movement`, `region`, `country`.
- Museum artworks: repeated `artist`, `movement`, `venue`, `work_type`.
- Existing scalar bookmarks and comma-separated selection values remain accepted.
  Display, sorting and curated-list mode remain single choices.
- OR within each category, AND between categories. Museum discovery requires a
  matching artwork, not all selected painters in the same museum.
- At most 32 raw selection tokens per category; values normalized, deduplicated,
  validated and sorted before parameterized PostgreSQL arrays are used.
- `GET /api/v1/painters/options?q=...&popular=false&selected=...&museum=...`:
  30 matches maximum, separate resolution of up to 32 selected identities and
  `has_more`. Museum scope is optional; default popular behavior matches timeline.
  Selected-name resolution still obeys publication/editor visibility.
- Keyset museum cursors bind to canonical filter sets; reordering/duplicates do
  not invalidate a cursor, changing the set does. Filter UI resets pagination.
- Museum artist facets retained for compatibility but capped at 30; the new UI
  uses bounded search. Movement facets capped at 500 on museum endpoints.

## Verification performed

- Go `go test ./...` with isolated test schemas: passed. Includes new OR/AND,
  cursor-scope, repeated parameter, malformed input, bounded option lookup and
  public visibility tests. Existing ingestion tests passed without live ingestion.
- Frontend lint, 20 unit tests and production build: passed.
- Playwright: `discovery.spec.ts`, `museum-coverage.spec.ts`, `multiselect.spec.ts`:
  15 passed. Covers painter selection across search/drawer/history/reload, museum
  links retaining filters, multiple countries/movements/types/venues, empty state,
  default popular preference, 320/390/1440-pixel layouts, focus/Escape and axe checks.
- Existing older seed-count-dependent suites were not part of this regression run;
  this is not a claim that every historical e2e fixture was rerun.
- Scoped plan fixture on 100,000 temporary artworks: index assertions passed;
  observed query execution 2.694 ms. Fixture setup is excluded from that SQL timing.
  This is not a 10-million-row benchmark. The global museum list/facet CTE remains
  a documented scaling risk; summary projections and load testing are future work.
- In-app browser bootstrap failed with missing sandboxPolicy. UI testing used
  local Playwright/Chrome, not a successful in-app browser session. Timeline and
  open phone filters were visually inspected; search-row flex direction was fixed.

## Research handoff

`docs/research/european-paintings/inventory.json`: 59 unique official object links,
26 institutions, 12 countries; 15 Bosch, 11 El Greco, 22 Monet, 11 Pissarro.
Three attribution-qualified records are included but explicitly distinguished.
This is a candidate set, not 59 guaranteed new records after database deduplication.

`output/pdf/european-painting-collections.pdf`: 14 pages, 127 link annotations.
All pages visually inspected after fixing collapsed numbered items and institution
headings separated from their first works; final singular-label correction rendered
and spot-checked. Inventory counts, institution references, unique object URLs and
PDF link/text structure validated. No source IDs appear in the delivered PDF.

No museum images were downloaded and no researched candidate was imported or
published. No commits, pushes, Terraform actions or deployments were performed.

## Known content limitations

Camille Pissarro currently has no recorded movement/country in the local database.
Selecting him works; adding those categories may exclude him. The interface warns
that incomplete classifications affect results. Research notes identify source-backed
editorial follow-up without silently mutating the database.

Subject genres (portrait, landscape, still life) are not modeled. A clarification was
requested; existing movements and work types are not falsely relabelled as genres.
Adding subject genres requires a controlled taxonomy and verified assignments.
