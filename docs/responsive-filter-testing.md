# Responsive filter regression pack

From `apps/web`, run:

```sh
npm run test:responsive
```

The dedicated configuration starts a temporary copy of the frontend on
`127.0.0.1:3097` and an in-memory, GET-only API on `127.0.0.1:3098`.
It builds and serves the production frontend so development refreshes cannot
reset a filter interaction while another route compiles.
Standalone deployment packaging is disabled only in the temporary copy;
production compilation and type checking still run.
It preserves existing development servers, catalogue databases, sessions and
research workers. Application source and generated build files are copied into
the OS temporary directory; large content and public assets are read through
symlinks. The API fixture has no credentials or database connection. External
browser requests are blocked in the new filter pack.
On macOS, a temporary awake assertion lasts only for the test server’s lifetime.

## Coverage

Chromium and WebKit exercise the painter, book, event and combined timelines,
artist and museum directories, museum collection, artwork directory and
exhibition archive. Filter layouts cover 320, 390, 430, 760, 761, 768, 1024 and
1440px, including both sides of the mobile breakpoint.

- Every available primary choice, checkbox, select, text and year field.
- Equal cell padding, mobile text sizes and touch targets, bounded dropdowns,
  long names and queries, removable chips, empty searches and retry recovery.
- URL state, outgoing filter parameters, reloads, resets, focus after removal,
  individual chip removal, search clearing, slash/Escape shortcuts and resizing
  while editing.
- The four current map layer pickers: painter selection, record searches,
  individual and layer visibility, search clearing and returning to Layers.
- Filter help popovers, compact map toolbars and secondary museum filters.
- Signed-in catalogue sidebars, including the narrow rail, expanded/collapsed
  states and the phone layout where the sidebar is hidden.
- Full-view filter sheets at 320×568 and 740×390, with date controls remaining
  visible after the sheet closes and timeline content scrolling independently.
- WCAG A/AA automated checks of open primary filters at 320 and 1440px.
- Existing mobile timeline layout, touch scrolling, rotation, full view,
  date controls and introductory guidance regressions. The existing CDP touch
  helper runs in Chromium; portable filter and date tests also run in WebKit.

Maps intentionally omit the date bar, as specified in
[the design approach](DESIGN_APPROACH.md). Tests check that returning to a
timeline restores the saved period and working date handles. The retired
“Add a layer” action is not a current UI entry point; coverage follows the
rendered Layers interface.

These are UI regression tests with bounded fixtures. They verify interactions
and request parameters, not production search results, catalogue totals, map
location evidence or physical iOS/Android hardware.

## Regression fixes

The shared filter grid distributes space among its actual fields rather than
reserving unused columns. Text, numeric and select fields share the same
geometry; phone controls have consistent insets, 16px value text and usable
touch targets. Native select value text is bounded for Safari, and long option
names wrap inside the choice list.

Desktop popovers fit within the viewport. Phone, compact-map and full-view
panels open inline in their scrollable shell. Opening a map layer picker keeps
its content aligned to its own panel. Filter help also stays within the screen.

Search clearing keeps its disclosure open even when the clear button unmounts
during the click. Focused controls remain expanded through rotation, and removing
the final museum chip returns focus to the filter trigger. Full view hides
introductory copy and keeps date controls outside the scrolling timeline content.

## Reports and focused runs

The OS temporary directory contains `artline-responsive-report/index.html`,
`artline-responsive-report/results.json` and `artline-responsive-results/`.
The HTML report includes representative screenshots; failures retain screenshots
and traces. Each run replaces these reports.

```sh
npm run test:responsive -- --project=webkit
npm run test:responsive -- --grep 'filter geometry'
npm run test:responsive -- --grep 'layer:'
npm test -- --maxWorkers=2 --testTimeout=15000
npx tsc --noEmit
```

Two browser workers keep the run bounded alongside background research. The
unit-test command also bounds concurrency and allows the existing guide/sitemap
file scans time to complete. No deployment is part of this command.

## Verified release candidate

Verified 24 October 2026, 20:57 UTC against current `master` plus the map/filter integration:

- 472 browser tests passed; no failures, skips or flaky retries.
- 739 unit tests passed on this exact source tree.
- Production compilation and TypeScript validation passed.
- The affected Go geography, HTTP API and atlas test packages passed with database integration disabled.
- Targeted frontend lint and whitespace checks passed.

The source checkout’s unrelated research, infrastructure, analytics and Play work is excluded.
