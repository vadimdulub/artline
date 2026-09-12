# UI/UX review — second pass

8 September 2026. Scope: improve the existing browsing and editorial journeys;
keep the compact charcoal timeline, paper records and right-hand painter drawer.
No content publication, database changes, commits or deployment.

## Benchmarks and interpretation

- [The Met collection search](https://www.metmuseum.org/art/collection/search):
  visible search/filter vocabulary and results with artwork identity. Application:
  make filtered-empty recovery explicit, and secondary filters easy to dismiss.
- [Rijksmuseum Collection Online](https://www.rijksmuseum.nl/en/about-collection-online):
  close inspection and high-resolution reproductions are part of collection study.
  Application: a full-screen fit-only image is not enough; add real zoom and
  scrolling, without introducing accounts, comparison tools or external embeds.
- [W3C dragging guidance](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)
  and [multi-thumb slider pattern](https://www.w3.org/WAI/ARIA/apg/patterns/slider-multithumb/):
  provide clear non-drag alternatives and communicate interdependent bounds.
- [W3C modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
  and [focus visibility](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html):
  keep focus in the current task and visible below sticky chrome.
- [W3C target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html):
  at least 24px or qualifying spacing; aim for 44px on frequent touch controls.

These are selective benchmarks, not claims of museum feature parity or full WCAG
conformance. Source content was inspected; museum interaction testing was not performed.

## Design plan, checked against the brief

Keep charcoal #12110f, paper #f2efe8, stone #e8e3d9, ink #1b1916,
muted #625d55 and restrained red #c85139. Georgia remains the reading/display
face; Avenir/system sans remains the control face. Left-align text; keep control
labels in sentence case. The artwork stays the visual center. Do not add a hero,
dashboard cards, decorative motion, or a new visual identity.

Keep the timeline focus controls on the same dark surface. Add two small labeled
range movement controls, rather than expanding into a separate settings panel.
Keep image zoom controls in their own full-screen viewing surface. Put work
navigation near the work heading, where a reader can find it before scrolling
through all metadata. On mobile, preserve access without shrinking input text.

## Findings and implementation checklist

| ID | Finding | Correction / acceptance |
| --- | --- | --- |
| R01 | Full-screen viewing only fits the image; it cannot reveal finer detail | Original local image on demand; zoom in/out, fit reset, keyboard and scroll support; close stays available |
| R02 | Choosing a work scrolls away while focus stays on its old card; next/previous controls remount | Focus the updated record heading after selection; keep it below the sticky toolbar; return restores selected card |
| R03 | Work navigation sits below lengthy metadata, including two useless disabled buttons for one-work painters | Move navigation next to record heading; omit for one work |
| R04 | Range movement needs dragging or a hidden keyboard instruction | Explicit earlier/later controls, disabled at bounds, preserving interval length |
| R05 | Number inputs can display fractional or cleared values different from the normalized URL; slider limits are misleading | Normalize and write back committed years; expose dependent ARIA bounds without changing track geometry |
| R06 | More filters stays open after Escape/outside click and can obscure later focus | Predictable Escape, click-away and focus-leave dismissal; visible Done control |
| R07 | Empty search results offer only a destructive full reset; public-mode copy can misdescribe a filtered catalogue | Separate clear-filters and full-range recovery, retaining the other dimension |
| R08 | On mobile, specific selectors reduce fields below the intended 16px; small controls remain | Restore readable input text, 44px frequent controls, safe narrow/short viewport layout |
| R09 | Clipboard-denied fallback is not focused/selected; previous success may remain stale | Focus/select fallback and clear stale success, with accessible feedback |
| R10 | Wide editorial table has no scroll guidance/name and stale rows remain actionable while refreshing | Named keyboard-scrollable table region, caption/hint, loading-disabled mutations and pagination |
| R11 | Generic details disclosures have their native marker removed without a replacement | Restore consistent open/closed indicators for artwork and influence evidence |

## Verification plan

First capture/reproduce the navigation, filter, year-field and image-viewer gaps
against the running app. Then add targeted regression tests and inspect updated
desktop, narrow-phone and short-landscape screenshots. Run the existing browser
suite, unit/component tests, lint and production build. Include WCAG 2.2 AA Axe
rules where supported; do not treat a clean automated scan as conformance.

## Implementation and verification

All eleven scoped corrections are implemented. A baseline browser check
confirmed the selected card retained focus **584px above the visible viewport**
after opening the work; the image viewer had only a Close button. The new
regression test confirms focus moves to the chosen work's named heading, below
the drawer toolbar. Work navigation stays mounted and is available above the
image, not below every metadata field.

The original image is requested only when the enlarged viewer opens. Fit preserves
its aspect ratio and does not upscale small files. Explicit zoom levels are
1×, 1.5×, 2×, 3× and 4× relative to fit. Zoom preserves the view center, allows
native scrolling and supports keyboard operation. A failed original image has a
Retry action without losing the record or trapping the viewer.

The visual pass retained the user's chosen identity and right drawer. At 320px,
date controls wrap rather than shrink their text; frequent controls use 44px hit
areas. The full-width black timeline still fits within a 1440×900 desktop screen.
Testing also caught a transient horizontal overflow during resizing while label
positions awaited ResizeObserver: the plotting area now clips only horizontal
overshoot, with a margin for focus rings. The empty-state test was updated for
the intentional change from full reset to filter-only recovery.

Final verification: **20 browser tests pass** in the complete suite (27.7s),
including seven new regression tests. **16 unit/component tests**, lint and the
production build/TypeScript checks pass. Automated accessibility checks, expanded
to WCAG 2.2 AA rules, return no violations on the tested pages and dialogs.

Visually inspected screenshots in `docs/screenshots/`:

- `round2-work-focus-mobile.png`
- `round2-timeline-390.png`
- `round2-image-zoom-desktop.png`
- `round2-image-fit-320.png` and `round2-image-fit-844.png`
- `round2-catalogue-mobile.png`

### Limits

This is not a full screen-reader, physical-device or cross-browser certification.
The in-app browser connection failed (`missing sandboxPolicy`); verification uses
the project's isolated Playwright/installed Chrome workflow. No account on a
museum site was accessed and no museum content was copied into the app.

Zoom cannot recover detail absent in a source file; some Giotto images remain
modest resolution. Image tiling, custom pinch gestures, comparison workspaces,
universal SPA draft recovery and the broader editorial features in `spec-audit.md`
remain outside this pass. No artwork records or publication states were changed.
