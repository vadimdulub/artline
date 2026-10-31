# Artline design code

Use this guide when creating or changing Artline interfaces. It brings together
the existing visual language, interaction ideas, icons and filter conventions.
Start with the closest established page and reuse its components.

Baseline reviewed: 30 October 2026, using the existing design documents and
current frontend source. This describes the project's design conventions;
release receipts establish which implementation is deployed.

## Design ideas

Artline is an editorial atlas and an illustrated collection catalogue. People,
works, places and recorded dates lead the experience.

- Let authentic artworks supply the colour and character. Frame them with warm
  paper, dark ink, quiet metadata and thin rules.
- Establish a clear order: content identity, relevant relationships, then
  controls and supporting evidence.
- Use alignment, typography and spacing to group information. Add a container
  when it explains a functional boundary.
- Keep common actions available; reveal longer biographies, sources and
  uncommon refinements through explicit controls or native disclosures.
- Preserve uncertainty. A cleaner layout must retain qualified attributions,
  approximate dates and the precision of a recorded location.
- Keep exploration continuous: retain filters, selection and context when
  opening a record, changing a view or returning from sign-in.

## Page families

| Family | Examples | Established treatment |
| --- | --- | --- |
| Exploration | Atlas, Painters, Books, Events, maps | Compact paper controls, near-black working canvas, dates and labelled data colours; use the available viewport. |
| Editorial and collection | Guides, artist/artwork records, directories, About | Paper background, serif headings, stone image mats, readable copy, captions and sources. |
| Account and utility | Account, Bookmarks, Studies, Catalogue, error states | The same palette and typography, with forms, lists, tabs or tables suited to the task. |

About can use a larger headline and artwork carousels. Keep exploration headings
compact. Development-only membership previews and archived mockups are reference
material; use the established application components for new work.

The Atlas entrance uses “Start with a story” for every historical topic. All
topics use the same large artwork-and-caption cards, with Women’s rights first.
Keep search and era filters available; use four columns on wide screens, two
on tablets and one on small phones. Preserve full image frames and load the
first visible row eagerly while later cards load lazily.

## Colour and typography

Use the variables in [globals.css](apps/web/app/globals.css). The values below
are a reference; page styles should use the variables.

| Token | Value | Meaning |
| --- | --- | --- |
| `--paper` | `#f2efe8` | Page background and light text on dark surfaces. |
| `--ink` | `#1b1916` | Primary text and selected/primary controls. |
| `--muted` | `#625d55` | Supporting copy, captions and quiet icons. |
| `--stone` | `#e8e3d9` | Artwork mats and inset surfaces. |
| `--line` | `#d0c9be` | Thin borders and dividers. |
| `--white` | `#faf8f3` | Fields and raised panels. |
| `--dark` | `#12110f` | Header and exploration canvas. |
| `--ultramarine` | `#8f3a29` | Rust editorial links/actions; the legacy name does not indicate blue. |
| `--red` | `#c85139` | Brand detail and selected exploration accents. |
| `--oxblood` | `#903f35` | Existing bookmark and alert accents. |
| `--moss` | `#53745b` | Supporting green where an existing component defines its meaning. |

Movement, record and layer colours identify data. Keep their labels and identity
assignments; use the shared palette for the surrounding interface. Avoid new
gradients, decorative badges or differently tinted cards solely for variety.

Use `var(--serif)` (Georgia / Times New Roman) for content headings, names,
artwork titles and editorial reading. Use `var(--sans)` (Avenir Next / Avenir /
system fallbacks) for controls, navigation, dates and metadata. Reuse these
stacks without adding font downloads.

| Text role | Typical scale |
| --- | --- |
| Directory title | Regular serif, `clamp(36px, 4.5vw, 60px)`, following `AtlasPageHeader`. |
| Section heading | Regular serif, approximately 28–34px. |
| Card or inspector title | Regular serif, approximately 23–30px. |
| Editorial copy | Serif, 17–21px with generous line-height; roughly 60–75 characters per line. |
| Controls and descriptions | Sans, generally 13–16px; phone input/select values use 16px. |
| Dates and credits | Sans, generally 11–13px; keep essential information readable. |

Default to sentence case, regular-weight titles and left alignment. Wrap long
names and credits. Match the nearest component before selecting new sizes.

## Layout and surfaces

- Standard pages use `width: var(--page); margin-inline: auto`. The shared
  width caps at 1800px, with 24px desktop gutters and 16px phone gutters.
- Long guide articles use a narrower reading layout, approximately 1360px;
  prose-only pages use about 800px.
- Follow existing spacing: 24–32px grid gaps, 12–20px between related controls,
  and 32–60px between editorial sections.
- Prefer image-and-caption blocks and ruled rows. Use `1px solid var(--line)`
  for separation, stone behind images and near-white behind fields.
- Keep control radii small, generally 3–7px. Existing circular close/account
  controls and pill-shaped filter chips retain their component treatment.
- Reserve shadows mainly for dialogs and popovers. Use `minmax(0, 1fr)` and
  `min-width: 0` to let content fit; fix oversized children instead of masking
  page overflow.

## Icons and actions

The shared icon language is monochrome outline SVG: usually a 24×24 viewBox,
`fill="none"`, `stroke="currentColor"`, 1.5px strokes and rounded caps/joins.
Icons normally display at 16–24px inside larger interactive targets.

Reuse [NavigationIcon](apps/web/components/MemberNavigation.tsx):

| Meaning | `kind` | Shape |
| --- | --- | --- |
| Artists | `artists` | Framed portrait. |
| Artworks; current exhibition navigation | `artworks` | Framed landscape. |
| Museums | `museum` | Classical building and columns. |
| Guides / reading | `guide` | Open book. |
| Studies | `studies` | Divided record panel with linked marks. |
| Events | `events` | Calendar. |
| Timeline | `timeline` | Vertical chronology with horizontal marks. |
| About / information | `about` | Circled information mark. |
| Account | `user` | Head and shoulders. |
| Bookmarks | `star` | Five-point star. |
| Sidebar panel | `menu` | Divided panel. |
| Collapse / expand | `chevron` | Chevron, rotated for the opposite direction. |

Reuse the magnifier and clear action in `AtlasSearchField`, sliders in
`AtlasFilters`, timeline/map symbols in `MapViewSwitch`, and corner brackets
for full view. The phone menu uses three horizontal strokes. Disclosures use
`+` / `−`, close uses `×`, and previous/next controls use `←` / `→`.

Keep decorative SVGs `aria-hidden`. Give icon-only buttons an accessible name
and visible focus. Use `BookmarkButton` for saved state and its `aria-pressed`
semantics. Extend the established SVG vocabulary only when an existing icon
cannot express the action; avoid a competing icon library or emoji controls.

## Filters and search

Build on [AtlasFilters](apps/web/components/AtlasFilters.tsx),
[AtlasSearchField](apps/web/components/AtlasSearchField.tsx),
[MultiSelectFilter](apps/web/components/MultiSelectFilter.tsx) and
[EntityFilterFields](apps/web/components/EntityFilterFields.tsx).

| Concern | Guideline |
| --- | --- |
| Search | Provide a programmatic label, useful placeholder and clear action. Preserve the shared `/` shortcut where implemented; it must respect typing and open dialogs. |
| Filter choices | Reuse searchable checkbox lists for multiple choices and native selects/radios for a single choice. Keep selected values available when facet results change. |
| Matching | Multiple values within a normal filter match any selected value; different filters combine. Preserve route-specific creator roles, geography scope and layer semantics. |
| Active state | Show removable chips and a clear selected summary. Removing one chip preserves the other selections. |
| Reset | Use the route's existing reset behavior. Most explorers say “Reset view”; Atlas says “Show starting points”. “Clear filters” clears the applied filters in its existing scope. |
| Help | Explain distinctions beside the relevant control, using `SelectionHint` where appropriate. Editorial highlights must be identified as editorial selections. |
| Results | Keep counts, sorting, filtering and paging on the server. Use bounded requests and existing cursors. |
| Failure | Distinguish loading, unavailable choices, no matches and failed results. Preserve context and offer the relevant recovery action. |

Filters, date ranges and selected records use the route's existing URL state.
Changing a filter resets its pagination as required. Preserve reload/back
behavior and meaningful explicit choices, including deliberately cleared filters.

Phone, compact-map and full-view filters open in their scrollable shell. Desktop
popovers stay within the viewport using the existing fitting helper. Escape and
Done/Close return focus appropriately. Removing a phone chip should retain focus
on the remaining controls without opening the keyboard unnecessarily. Preserve
each route's existing live-update or explicit-submit behavior.

## Timelines, maps and records

Timelines use the dark canvas, compact date heading and labelled colour keys.
Reuse `TimelineRangeControls` for date handles, year fields and mouse, touch and
keyboard interaction. Reuse `ExplorerFrame` for full view, focus handling and
Escape. Keep dates factual; decorative timelines must not invent chronology.

Maps keep selection controls on the left, geography in the centre and location
or record details on the right. Layers starts closed and opens from its icon.
Visibility, temporary hover/focus preview and inspection are distinct actions:
preview must preserve the camera, URL and visible records; visibility changes
must preserve the inspected record and manual camera position.

The current explorer source includes a compact date bar below maps. Selected
painters retain complete biographical place context, while the saved period
scopes artworks, books and events. Preserve source coordinates, location
precision and modern-boundary notes. Record colours remain stable. Phone layer
drawers and information sheets need reachable fixed header actions.

Reuse `RecordDrawer`, `RecordArrows`, `ArtworkFacts`, `ArtworkDescription` and
`ArtworkViewer`. Closing an overlay returns focus to its trigger; Escape closes
the active overlay first. Keep full-record actions clearly named. Use native
`details` / `summary` for optional sources and reading notes.

## Navigation and content

Use `SiteHeader`, `MemberNavigation`, `MobileNavigation` and the existing
member-aware links. Desktop navigation uses open text links with an active
underline; [SiteNavigation.css](apps/web/components/SiteNavigation.css) supplies
the current treatment. Preserve the supplied wordmark, which spells “Artlines”.

The combined art, books and history explorer is named **Atlas**, replacing the
older “All” navigation label. Group the desktop menu as
`Atlas | Painters Books Events | Guides`, with thin decorative dividers. Keep
Play out of the desktop and phone menus. Keep Atlas first in the phone
Explore menu and use the same name in its section heading and return labels.
The existing `/` and `/all` URLs retain their behavior.

Use links for destinations and buttons for state changes. Give actions concrete
names such as “View artwork”, “Explore the timeline” and “Download PDF”. Preserve
the current public/member access rules and the selected destination through
sign-in.

Present authentic, approved reproductions with connected titles, creators,
recorded dates and credits. Guide/editorial image frames preserve the full
composition with `object-fit: contain`; any existing cropped discovery preview
keeps its specific purpose. Never invent images, records or facts to fill a
layout. Distinguish holdings from current display and catalogue coverage from
an institution's complete collection. Omit empty fields and retain meaningful
uncertainty. Keep product copy direct and useful.

## Responsive behavior and review

The principal phone breakpoint is 760px. The shared phone header is 52px;
the desktop member sidebar becomes a narrow rail at intermediate widths and
disappears on phones. Adapt reading grids to their content and keep exploration
controls within the viewport.

For interface changes, review the relevant states at 1440, 1024, 768, 390 and
320px, including both sides of the 760px breakpoint when changing filters.
Check long names, open panels, empty results, loading, failure, signed-in
navigation and anonymous member prompts where relevant.

- Keep interactive targets at least 44px where practical, phone field values
  at 16px, visible keyboard focus and selected-state attributes.
- Preserve semantic headings, labels, skip navigation, dialog names, focus
  return and reduced-motion behavior. State must have a cue beyond colour.
- Use the nearest existing tests for affected behavior. Inspect rendered
  layouts when changing UI; record only verification actually performed.

The [responsive filter regression guide](docs/responsive-filter-testing.md)
describes bounded fixture testing for these interactions and layouts.

## References and maintenance

- [Design guidelines](docs/DESIGN_GUIDELINES.md): detailed palette, typography,
  page families, icons and interaction rules.
- [Design approach](docs/DESIGN_APPROACH.md): information hierarchy and map
  decisions; later applied sections refine earlier iterations.
- [Original design direction](docs/design-direction.md): historical prototype
  context and the origins of the shared visual language.
- [Shared styles](apps/web/app/globals.css), [phone styles](apps/web/app/mobile.css)
  and [navigation styles](apps/web/components/SiteNavigation.css): concrete tokens
  and responsive behavior.

Keep this entry point and the detailed guides aligned when a shared convention
changes. Check the current component and the latest applicable decision when
older notes conflict: for example, older responsive-test prose says maps omit
the date bar, while the current explorer components render it. Archived
screenshots and historical test counts describe their recorded revision.
