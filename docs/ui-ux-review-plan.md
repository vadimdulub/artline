# Global UI/UX review and implementation plan

Date: 2026-09-08. Scope: all existing Artline screens and their connected journeys,
plus a small, source-checked artwork collection. No commit, deployment, Terraform
apply, or automatic publication. This does not replace the broader feature audit.

## Design direction and review method

Preserve the user's chosen full-width black chronology, integrated focus controls,
paper reading surfaces, and full-height right-hand painter drawer. The painting,
not decorative dashboard chrome, should carry the visual interest.

Tokens: charcoal `#12110f`, paper `#f2efe8`, stone `#e8e3d9`, ink `#1b1916`,
rule `#d0c9be`, red `#c85139`. Georgia is the display/reading face; Avenir/system
sans is for navigation, controls, and metadata. Left alignment; prose below 75ch.
Use readable secondary text, sufficient contrast, visible focus, and at least
32px controls (44px for primary navigation and touch interactions where practical).

```text
Timeline + visible active filters
  → right painter drawer → next/previous painter
      → selected artwork → larger image / evidence / shareable record
      ← return to selected works
Catalogue ↔ coverage ↔ clearly labeled future imports
```

This is a refinement of the supplied references, not a new visual identity.
Keep compact spacing, but do not achieve it by shrinking essential information.
Real works must remain uncropped in the detail viewer and must never be replaced
with generated approximations. Distinguish missing data from an application error.

Review method: inspect implementation and screenshots; record concrete issues;
implement in dependency order; inspect desktop and phone screenshots; test the
critical journeys and failure states. Automated accessibility checks supplement,
but do not replace, a full assistive-technology assessment.

## Prioritized implementation checklist

| ID | Priority | Observed issue | Planned correction | Acceptance check |
| --- | --- | --- | --- | --- |
| U01 | P0 | 9–11px metadata and small editor actions are difficult to read | Raise the control/metadata scale and touch areas without adding a hero | Readable desktop/phone screenshots; no horizontal page overflow |
| U02 | P0 | Right-aligned timeline labels are not accounted for in lane collision checks | Compute occupied label + interval bounds, clamp labels to the viewport | Long-name/right-edge unit tests; dense fixture screenshot |
| U03 | P1 | Filters hidden in More filters are easy to forget | Show removable active-filter chips; make clear/reset behavior consistent | Individual filter removal preserves other filters |
| U04 | P1 | Search requires locating a small control | Add the advertised discoverable `/` shortcut; ignore typing and modal contexts | Shortcut focuses search without inserting `/` |
| U05 | P0 | Old results can look current during loading or after a failed request | Mark loading results, prevent stale selection, hide stale error results | Aborted request and failed-load recovery checks |
| U06 | P1 | Painter browsing requires closing and reopening the drawer repeatedly | Previous/next painter buttons with truthful filtered position | Navigate between records; correct disabled ends and URL history |
| U07 | P0 | Drawer navigation can lose the original opener/focus | Keep the dialog session stable while the painter changes | Escape/backdrop closes and restores focus; body stays fixed |
| U08 | P1 | Selecting a work scrolls a long way with no direct return | Add a visible return-to-selection control and selected-work count | Open details and return within the same drawer |
| U09 | P1 | A large reproduction cannot be inspected comfortably | Add an accessible full-window image view with preserved aspect ratio | Nested Escape closes image only, then drawer; focus returns |
| U10 | P1 | Sharing a selected artwork requires copying the browser state manually | Add copy-link feedback and a safe fallback | Canonical work URL resolves after reload |
| U11 | P0 | Technical attribution/date values obscure what is known | Human-readable metadata, uncertainty labels, explicit unknowns | Date/medium/dimensions/place/collection/rights/citations visible |
| U12 | P1 | One-work profiles occupy one tiny column of a five-column strip | Size the selection grid according to the real work count | One-, two-, and five-work records remain balanced |
| U13 | P1 | Catalogue form/error feedback is separated from the initiating action | Scroll/focus the form and publication report; show save errors at the form | Failed edits stay present and their error is immediately visible |
| U14 | P1 | Unsaved catalogue edits can be lost on navigation | Warn for dirty drafts and prevent input changes during save | Navigation/reload warning; unchanged forms do not warn |
| U15 | P1 | Editorial vocabulary and publication progress are terse | Friendly statuses, biography word count, clear read-only explanation | Existing token authorization remains enforced |
| U16 | P1 | Coverage/import pages lack consistent local navigation | Shared editor navigation with active state and planned-import label | All editor pages reachable; active navigation correct |
| U17 | P1 | Coverage is disconnected from work on the catalogue | Link status totals to filtered catalogue views; explain partial coverage | Links apply expected status; empty/pending metrics remain honest |
| U18 | P1 | Help does not describe the newer drawer and image workflows | Update exploration help and keyboard guidance | Instructions correspond to actual controls |
| U19 | P0 | Most painter views have no real artworks | Add source-checked works across all 11 current painters | Every painter has a representative work and a permitted local image |
| U20 | P0 | New images need reproducible rights/provenance, not just URLs | Versioned content manifest, sources, alt text, checksums, append-only seed migration | Every new image is local and traceable to its specific source/file page |
| U21 | P0 | Artwork fields could be guessed to make the demo look complete | Cite object-specific evidence; keep unsourced creation places null | No invented dimensions, dates, influences, or publication claims |
| U22 | P0 | A broad redesign needs more than a successful build | Unit/integration/browser/accessibility tests and visual critique | Record actual passing checks and remaining limitations below |

## Content selection and safeguards

- Start with the existing 11 painters. Add at least one real work for each painter
  currently without works, and a few additional examples where source quality allows.
- Prefer holding-institution collection records; use Commons file records for
  reproduction provenance when institutional reuse/download routes are unavailable.
- Record object title, date precision, medium, dimensions when sourced, current
  holding institution, retrieval date, attribution, source URL, and image rights.
- Artwork date and reproduction copyright are separate. Do not assume the former
  proves the latter. Store only clearly reusable image files with reviewed metadata.
- Keep these additions in review. They are a demonstration/research selection,
  not a claim that all painters satisfy the specification's 5–10 published-work rule.
- Add records non-destructively. Do not overwrite user edits, archive existing work,
  or alter previous migrations. Keep a manifest and asset integrity check.

## Execution order

1. Review and write this plan; establish source and screenshot baselines.
2. Research the bounded artwork selection while refining navigation/readability.
3. Implement timeline, drawer, image-viewer, and catalogue feedback corrections.
4. Import the documented artwork selection and verify local media/DB links.
5. Inspect all pages with real content at phone, tablet, and desktop widths.
6. Run regression/accessibility/build checks, fix findings, and record completion
   evidence and explicit remaining limitations here.

## Completion evidence

Implemented in the local application; no commit, publication, Terraform apply,
or cloud deployment. The screenshots and checks below cover the scoped review,
not every feature in the original specification.

| Items | Completion evidence |
| --- | --- |
| U01–U02 | Larger/darker secondary text; 320/390/768/1024/1440px overflow checks; interval + label collision unit tests; 28-painter long-name desktop/phone fixture with pairwise bounds assertions |
| U03–U05 | Removable filter chips, range-preserving clear, discoverable search shortcut, loading-disabled painter/bin selection, error recovery browser checks |
| U06–U10 | Previous/next painter and truthful position, stable native dialog session, selected-work return, enlarged image, copyable canonical URL; Escape/backdrop/history and nested scroll-lock tests |
| U11–U12 | Friendly date/attribution labels; dimensions, collection accession, source notes and unknown-place explanations; full images without cropping; work-count-driven grid |
| U13–U15 | Form/report focus and scrolling, visible inline rejected-save error, draft preservation, dirty state, link/unload warnings, disabled saving fields, word count, explicit read-only mode |
| U16–U18 | Shared active editor navigation, status-count links into filtered catalogue, clearer published-work coverage wording, planned-import state and updated help |
| U19–U21 | Migration 0005 applied locally: 11 review painters, 15 review works and 15 images; every painter illustrated; exact object/source matching, unknowns and conflicts retained; checksum verifier passes |
| U22 | Go unit and PostgreSQL integration tests, frontend tests, browser suite, accessibility scans, lint, production build, manual screenshot and original-image inspection |

### Verification results

- `npm run test:e2e`: **13 passing browser tests**, including the crowded
  timeline fixture, every seeded painter and image, right drawer, image viewer,
  sharing, history, filters, failure recovery, and editor draft protection.
- Axe: **no violations returned** for WCAG 2 A/AA + WCAG 2.1 AA rules on the
  tested timeline, canonical painter, catalogue, coverage, imports, help,
  painter drawer, and enlarged image states. Findings in muted/placeholder/date
  contrast were corrected. Disabled controls are intentionally subdued.
- Responsive overflow checks: **320, 390, 768, 1024, 1440px**; full-width phone
  drawer and independent desktop panel verified. Tiny clipped activity intervals
  and labels at the year-range edge remain inside the plotting area.
- `go test ./...`: passed. PostgreSQL integration run with
  `ARTLINE_TEST_DATABASE_URL`: passed, including all 11 illustrated records,
  Hokusai's specific accession and unknown-place explanation, density,
  revision/authorization/publication checks. Test mutations roll back.
- `npm run lint` and `npm run build`: passed; TypeScript passes.
- `node ops/verify-artwork-assets.mjs`: **15 files, 30.6 MiB, all hashes match**.
  File signatures and declared size/path/provenance completeness are checked.
- Unit coverage includes label bounds/lane packing, range normalization/presets,
  nested modal cleanup order, one/two/five-work grids, metadata uncertainty,
  and unsafe image-path rejection.

### Visual critique and refinements

The initial drawer had repeated empty influence boxes and pushed the first work
too low. These now become one compact, honest research note; real claims retain
the directional layout. The artwork view keeps the whole composition, including
very tall van Eyck and wide Hokusai/Krøyer works, and provides a full-window view.
The canonical five-work strip and one-work profiles use their actual content
count instead of five permanent columns. The black chronology remains a single
compact surface including focus controls.

Reviewed artifacts include `timeline-compact.png`, `timeline-mobile.png`,
`timeline-dense-fixture-1440.png`, `timeline-dense-fixture-390.png`,
`painter-drawer-desktop.png`, `painter-drawer-mobile.png`,
`painter-drawer-artwork.png`, `artwork-enlarged.png`,
`review--artists-giotto.png`, `catalogue-desktop.png`,
`review--coverage.png`, `review--imports.png`, and `review--about.png`
under `docs/screenshots/`. The dense fixture is test data, not catalogue content.

### Remaining limits and editorial work

- This is not a complete implementation of the original specification:
  structured artwork/citation/influence editing, import/review/export workflows,
  identity-backed roles, complete coverage reports, and other gaps remain in
  `spec-audit.md`.
- Ten painters still need biographies and larger representative selections;
  no influence claims are fabricated. All 15 works remain in review and none
  have been promoted to published. Local preview and public production differ
  intentionally.
- Unknown creation places stay null. Museum holdings are not promises of being
  on view. Giotto's cycle dates and Hilma's dimensions retain source-discrepancy
  notes. Some source images have limited resolution.
- Dirty-draft warnings cover in-app links, form switching, and browser unload.
  Draft persistence/recovery and a universal guard for every SPA history
  navigation remain future work.
- Automated Chrome/viewport tests and contrast scans are not a full screen-reader,
  Safari/Firefox, physical-device, or WCAG 2.2 conformance audit.
- The in-app browser bridge was unavailable (`missing sandboxPolicy`); verification
  used the repository's isolated Playwright/installed Chrome workflow.
- The shell currently runs Node 23.11; tests/build passed, but Node 24 remains
  the supported recommendation in `.nvmrc`. No infrastructure was applied.
