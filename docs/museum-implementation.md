# Museum foundation and browsing

Approved 8 September 2026 after the museum/filter plan. This milestone adds local
schema, reviewed links for the existing 15 artworks, museum list/detail pages and
editable owner must-see selections. No bulk ingestion, new artwork downloads,
publication, commits, Terraform or deployment.

## Design before implementation

Retain Artline's requested paper-and-ink visual language: paper #f2efe8, stone
#e8e3d9, ink #1b1916, charcoal #12110f, muted #625d55 and red #c85139. Georgia
headings and reading text; the existing Avenir/system sans for controls. All text
left-aligned. Let real artwork reproductions carry the visual identity.

```
Museums and collections                [Search]
[Museum regions ▾] [Countries ▾] [Selection ▾] [Display ▾]
[Selected filters ×]

[Artwork detail] Museum name       [Artwork detail] Museum name
                 City, country                     City, country
                 Catalogued works                  Catalogued works

Museum page: name / place / official visiting information
[All works | My must-see works | Museum highlights]
[Search] [Painter ▾] [Movement ▾] [Venue ▾] [More filters]
Artwork cards → right-hand record / image viewer / must-see editor
```

Critique: a photo-led travel directory would imply travel information we do not
maintain. Use collection artworks, explicitly label counts “in Artline”, and link
to official visiting information. Do not use a map, fabricated venue photographs,
numeric masterpiece ratings or imply every holding is on display. A foundation
without a verified visiting venue remains a collection, not a visit recommendation.

## Data and acceptance

- Reuse existing institution, place, source, citation and artwork identities.
- Seven collections; physical venues only when documented. Do not infer which
  building contains a work from the institution's address or a gallery number.
- Preserve original holding text and check dates. New accepted holding assertions
  produce the existing institution-ID compatibility field transactionally.
- Two Met highlight flags were verified through official object API records:
  [Rembrandt 437397](https://collectionapi.metmuseum.org/public/collection/v1/objects/437397)
  and [Monet 437127](https://collectionapi.metmuseum.org/public/collection/v1/objects/437127).
  This designation does not establish on-view status or change image rights.
- Owner must-see selections start empty, save only with editor authorization,
  retain reasons/order, and use revision checks. They do not publish artworks.
- Display evidence is a separate dated assertion; no current on-view claims are
  seeded from a holdings record. Unverified and stale display evidence stays clear.
- Museum paging is independent of the ten-work representative selection cap.
- Tests cover publication boundaries, multi-location filtering, deduplicated
  counts, stale display/loan behavior, cursor bounds, curation conflicts and
  phone/keyboard/deep-link navigation.

The in-app browser could not connect; use the established isolated Chrome suite
for visual and interaction verification after implementation.

## Delivered milestone

Migration `0006_museum_foundation.sql` has been applied to local PostgreSQL.
The backfill links the existing artworks without changing their original location
text, image files or reproduction rights. The counts after the rollback-only tests
are seven institutions, eight venues, 15 linked artworks, two museum-highlight
memberships, zero personal picks and zero display assertions.

| Collection | Works in Artline | Physical venues recorded |
| --- | ---: | ---: |
| Scrovegni Chapel | 5 | 1 |
| National Gallery of Art | 2 | 2 |
| Uffizi Galleries | 1 | 1 |
| The Metropolitan Museum of Art | 3 | 2 |
| Skagens Museum | 2 | 1 |
| Hilma af Klint Foundation | 1 | 0 |
| National Museum, Oslo | 1 | 1 |

Venue links are institutional visiting information, not artwork-to-building
assignments. Venue metadata and curated lists remain in review. Several seed
holding claims reuse existing object-specific citations and their original check
dates; this is not a claim of a fresh live verification of every institution.

### Browsing and editing

- `/museums`: local collection search, multi-region and multi-country choices,
  owner/museum selection and confirmed-display filters, removable chips and paging.
- `/museums/[slug]`: catalogue counts, official visiting links, independent artwork
  browsing, painter/movement/work-type/creation-date filters, unknown dates,
  permitted-image availability, confirmed venue and deterministic sort choices.
- `?work=<id>` opens a full right-hand artwork record. It retains the existing
  image viewer, zoom, source/rights details, sharing, keyboard dismissal and focus
  restoration. Painter records also link to their works’ holding collections.
- The must-see editor requires the existing editor token, supports membership,
  reason and order, warns before panel-close/link navigation with unsaved changes,
  and blocks dismissal while a save is in flight. A stale revision returns a
  conflict without overwriting either the saved list or the entered form values.
- Mobile navigation now fits all three primary destinations. The frontend-design
  review preserved the atlas typography, paper palette, real reproductions and
  right-panel interaction instead of introducing a separate museum theme.

### Backend and database

Go endpoints cover museum list/detail, paginated works, full artwork detail and
authorized personal curation. Institutions, venues, paintings, artist names and
curated memberships each obey public/review visibility; preview responses are
private and non-cacheable. An anonymous API read still returns zero collections
because the seed is not published.

Holding assertions and display assertions are separate, with source attribution,
review state, dates, supersession and audit history. An accepted holding assertion
updates the compatibility institution ID transactionally. A loan may make a work
visible at its destination without changing that holding ID. Stale, conflicting,
future or inactive-source display evidence does not qualify as confirmed on view;
known not-on-view evidence can exist without a known room or venue.

Indexes cover institution holdings, venue geography, current display/history and
curated membership/order. Cursor pagination is bounded (24 by default, maximum
60) and tied to its filter/visibility context. Museum cards use a small DTO, not
full biographies or citations. Artwork evidence and citations on painter profiles
are batch-loaded instead of fetched once per work. No performance claim at
111-source scale is made: large-fixture `EXPLAIN ANALYZE` and ingestion workload
benchmarks remain necessary before bulk loading.

### Verification

- Go validation/authorization tests and PostgreSQL-backed catalogue integration
  tests pass. Integration writes use an outer transaction that is rolled back,
  including curation, temporary publication and fictitious display/loan fixtures.
- Frontend lint, production build and all 18 unit tests pass.
- All 30 browser tests pass. Coverage includes existing timeline/catalogue regressions plus museum
  filter combinations, source links, deep links/history, nested viewer focus,
  rejected curation edits and invalid-token recovery.
- Axe scans and horizontal-overflow checks cover museum list, detail and drawer at
  1440px, 390px and 320px. Desktop collection and phone detail screenshots were
  visually inspected. Automated checks are not a complete accessibility audit.
- All 15 existing artwork files still match their manifest checksums (30.6 MiB).

Screenshots are under `docs/screenshots/museums-*.png`, `museum-met-*.png` and
`museum-artwork-desktop.png`. The in-app browser bootstrap failed because its
sandbox metadata was unavailable; verification used the established local
Playwright/Chrome suite instead.

## Deliberate limits and next milestone

- No registry-wide import, enabled connectors, scheduled source/display refresh,
  remote image download, publication, commit, Terraform or deployment occurred.
- There are no seeded on-view claims. That filter is correctly empty until actual
  current evidence is recorded and accepted. The 30-day policy is implemented,
  but no automatic refresh job exists yet.
- The must-see editor is for the atlas owner, not individual visitor accounts.
  Personal notes and numeric ordering are implemented; a separate optional
  supporting-reference editor is not. Lists stay in review and do not yet have a
  dedicated publication UI.
- Multi-select is implemented for museum regions/countries. Painter, movement,
  work type and venue on the detail screen are initially single-select. City is
  searchable, not a separate facet.
- Institutions, venues, evidence assertions and museum-highlight ingestion do not
  yet have general-purpose editorial forms or source adapters. Their first seed
  is an additive migration; later content changes need a reviewed migration or
  the subsequent structured editor.
- Unsaved-change guards cover panel dismissal, links and page unload, not every
  same-document browser Back/Forward transition. That remains an editorial
  navigation hardening task.
