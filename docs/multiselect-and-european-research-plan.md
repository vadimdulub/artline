# Multi-select filters and European collection research

## Scope and progress

Completed: bounded source discovery, focused Nordic/Central European gap wave,
critical-claim reconciliation, filter implementation and verification. Delivered
59 candidates across 26 institutions / 12 countries, with a 14-page research PDF
and structured JSON inventory. Sources, uncertainty and rights are preserved.

Go integration tests, frontend lint/20 unit tests/build, 15 focused browser tests
and the 100k scoped query-plan fixture passed. All PDF pages were visually checked;
the final small grammar correction was rendered and spot-checked. See
multiselect-verification.md for scope and remaining capacity/content work.

No automatic imports, publication, image downloads, commits or Terraform actions.
Subject-genre modeling and source-backed classification repair remain separate
follow-up work; they were not fabricated to fill missing research data.

Assumptions: Europe includes the UK; creation cutoff remains 1970; selected museum
paintings, not exhaustive image downloads. Research candidates are not silently
imported or published. Original works, disputed attributions, copies and historical
loans must stay distinct. No current-display claim without fresh dated evidence.
The plan-update tool is unavailable in this environment; progress is recorded here.

## Design pass

Keep the approved atlas: paper #f2efe8, ink #1b1916, charcoal #12110f, stone #e8e3d9,
rule #d0c9be and vermilion #c85139. Georgia remains the record/display face and the
existing sans-serif serves controls. This is a filter-system change, not a rebrand.

```text
Search the atlas                         Reset view
Painters [Monet + Pissarro]  Movements [2]  Regions [2]  More
Selected: Monet ×  Pissarro ×  Impressionism ×  France ×
☑ Only popular painters       Any within a filter; all filters combine
Dark timeline and existing right-hand record drawer
```

Use consistent searchable checkbox panels, selected counts and removable chips.
Keep selected painters visible while searching for another. Desktop panels stay
within the viewport; mobile panels become contained full-width overlays. Escape,
Done and outside dismissal preserve keyboard focus. Do not nest hidden dropdowns
inside a clipping popup. Text/search state is distinct from the painter selection.

Brief review: the chart remains the primary visual; no new hero/cards/decorative
animation. Existing regions already use checkboxes, so extend that interaction
rather than introducing an unrelated combobox convention for each category.

## Backend contract

- OR within a category; AND between categories. Empty selection means unrestricted.
- Repeated URL parameters; retain old single-value URLs. Painter selection in the
  timeline uses `painter`, distinct from the `artist` currently open in the drawer.
- Go validates/deduplicates bounded lists; SQL owns filtering/counts/pagination.
- Painter choices use bounded server search plus explicit selected-ID resolution,
  never all 20,000 painters in the browser. Popularity remains the timeline default.
- Countries, movements, work types and museum painters/venues support multiple values.
- Subject genres are not currently modeled; do not rename movements as genres or
  invent classifications. Clarification requested while existing filters proceed.

## Research process

Two independent source lanes cover Bosch/El Greco and Monet/Pissarro. Official
museum object records, collection catalogues, open-data/IIIF documentation and
reuse policies are preferred. First merge discovery evidence, then target missing
identity/date/holding/rights claims. Preserve confidence, contradictions and access
limitations in a gap ledger. Stop when representative, actionable coverage is
supported; disclose that the inventory is not a complete census.

The coordinator owns cross-checking, synthesis and artifacts. Research workers
return evidence only and do not import, publish, contact museums or create files.
