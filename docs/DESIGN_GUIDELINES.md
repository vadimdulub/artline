# Artline design guidelines

Established interface review: 11 October 2026. Use this guide before creating
or redesigning an Artline page. It records the patterns already used by the
application; the About page follows those patterns too.

## 1. The visual identity

Artline feels like a study atlas and an illustrated collection catalogue.
Artworks carry the colour and character. The interface supplies calm typography,
clear labels, thin rules and practical ways to explore.

There are three related page families:

| Family | Existing examples | Treatment |
| --- | --- | --- |
| Exploration | Painters, Books, Events, All | Paper filter bars above a near-black canvas; compact dates, timelines and image strips; the content uses the available viewport. |
| Editorial and collection | Guides, artist and artwork records, museum and artist directories, About | Paper background, dark serif headings, stone image surfaces, readable introductions, source notes and simple links. |
| Account and utility | Account, Bookmarks, Catalogue, Privacy, missing/error states | The same palette and typography, with forms, tables, tabs or a narrower reading measure as needed. |

Choose the closest existing page as the starting point. Keep the shared palette,
typography and interaction patterns even when a page serves a different purpose.

**About refinement, 11 October 2026:** the user requested a shorter, more vivid
marketing entrance. Following a [20-page marketing benchmark](design/marketing-benchmark-20261011.md),
About opens with a large centered headline and a nine-work artwork carousel on paper (12 October 2026 refinement).
The dark canvas belongs to the dated timeline preview. Museum guides use compact
cover compositions; a larger artist carousel follows. Portraits and landscapes fit fully inside equal-height frames, with titles, artists and recorded dates below. Phones show one full card and a glimpse of the next, with native swipe, arrow and keyboard navigation. Keep explanatory copy short, with
image credits and ranking details in compact disclosures, and label navigation
to this page simply “About”. This is a purposeful entrance treatment, not a new
palette for other editorial pages.

## 2. Colours: use the existing CSS tokens

The source is [`apps/web/app/globals.css`](../apps/web/app/globals.css).
Reference variables instead of copying their hex values into page CSS.

| Token | Value | Role |
| --- | --- | --- |
| `--paper` | `#f2efe8` | Default page background; light text on dark surfaces. |
| `--ink` | `#1b1916` | Primary text, filled primary controls, selected light-page tabs. |
| `--muted` | `#625d55` | Supporting copy, metadata, unselected icons. |
| `--stone` | `#e8e3d9` | Artwork mats, inset information, restrained hover surfaces. |
| `--line` | `#d0c9be` | One-pixel dividers, field borders and table rules. |
| `--white` | `#faf8f3` | Raised form/popover surfaces and account panels. |
| `--dark` | `#12110f` | Global header, timeline canvas and immersive image views. |
| `--ultramarine` | `#8f3a29` | Rust-brown editorial links and actions. Despite its legacy name, this is **not blue**. |
| `--red` | `#c85139` | Brand detail and selected timeline/record accents; not a default small body-text colour. |
| `--oxblood` | `#903f35` | Saved bookmark accents and existing alert treatments. |
| `--moss` | `#53745b` | Existing supporting green; use only where the component has an established meaning. |

Dark surfaces also use warm secondary text (`#b5ad9f` or `#d7d0c3`), subdued
gold (`#c1a579`) and a light peach focus/hover colour (`#f0b29c`). Reuse the
appropriate timeline/header component rather than creating a second dark theme.

Movement and content-type colours are data/legend colours. Keep their meaning
and accompanying labels. They are not a supply of new page-brand colours.
Do not add gradients or individually tinted guide cards merely for variety.

## 3. Typography

Use the two existing font stacks. There are no new web-font downloads:

```css
font-family: var(--serif); /* Georgia, "Times New Roman", serif */
font-family: var(--sans);  /* "Avenir Next", Avenir, system fallbacks */
```

| Content | Existing pattern to follow |
| --- | --- |
| Directory page title | `AtlasPageHeader`: weight 400, `clamp(36px, 4.5vw, 60px)`, line-height 1.08, tracking −.035em. |
| Guide/editorial page title | Weight 400, approximately 42–70px, line-height 1.1, tracking −.04em; about 38–48px on phones. |
| Section heading | Georgia 28–34px, weight 400; a major editorial feature can reach 40–54px. |
| Card, artwork or artist title | Georgia, usually 23–30px, line-height 1.15–1.3. |
| Editorial introduction/body | Georgia 17–21px, line-height 1.6–1.8; keep long copy roughly 60–75 characters wide. |
| Interface descriptions | Avenir/system sans, normally 13–16px, line-height 1.5–1.7. |
| Buttons, tabs, navigation | Sans, normally 12–14px on desktop and 14–16px for phone controls. |
| Dates, credits, provenance | Sans, generally 11–13px; existing dense desktop charts use some smaller labels. Do not use chart-sized text for new body copy. |

Headings and artwork titles are usually regular weight. Use weight and size for
hierarchy, not a different font family for each section. Left alignment is the
default. Preserve dates and qualified attributions; wrap long record names.

Sentence case is the default for new headings and controls. Uppercase eyebrows
exist in the All starting screen, Account and Bookmarks; they are specific legacy
treatments, not a requirement for every section. About uses one large benefit-led
headline (up to 104px); major section headings can reach 54px. This larger
marketing scale should not replace compact headings in the exploration tools.

## 4. Layout, spacing and surfaces

- Standard pages use `width: var(--page); margin: auto`, with approximately
  32px top padding and 60–64px bottom padding. The shared page width caps at
  1800px and uses 24px desktop gutters, 16px phone gutters.
- Long museum-guide articles use a 1360px maximum; prose-only pages use about
  800px. These are purposeful reading limits, not alternative global gutters.
- Use 24–32px grid gaps, 12–20px between related controls, and 32–60px between
  editorial sections. Prefer existing component spacing to inventing a scale.
- Separate related content with `1px solid var(--line)`. Most collection cards
  are image-and-caption blocks or ruled rows, not floating boxes.
- Use stone behind artworks and near-white behind fields and small panels.
  Shadows belong mainly to dialogs/popovers; remove decorative artwork shadows.
  About's guide covers use near-white paper and a stronger left border to suggest
  a reading object. They are navigation previews, not facsimiles of PDF covers.
- Use small radii where existing controls need them: roughly 3–5px buttons,
  4–7px fields and 5–8px bordered guide panels. Navigation account icons and
  close controls can be circular; filter chips can be pill-shaped.
- Build grids with `minmax(0, 1fr)` and `min-width: 0` where necessary. Let
  long credits wrap; do not hide layout overflow to disguise an oversized child.

## 5. Icons

The established language is monochrome outline SVG, usually a 24×24 viewBox,
`fill="none"`, `stroke="currentColor"`, approximately 1.5px strokes and round
joins/caps. The normal display size is 16–24px. The click target is larger.

Reuse [`NavigationIcon`](../apps/web/components/MemberNavigation.tsx) for:

| Meaning | Existing `kind` / shape |
| --- | --- |
| Artists | `artists`: framed portrait. |
| Artworks | `artworks`: framed landscape. |
| Museums | `museum`: classical building/columns. |
| Guides and reading | `guide`: open book. |
| About and information | `about`: circled information mark. |
| Account | `user`: head and shoulders. |
| Bookmarks | `star`: five-point outline star. |
| Sidebar collapse | `chevron`: left-facing chevron, rotated for expansion. |

Other existing patterns are the magnifier/clear icon in `AtlasSearchField`,
sliders for filters, corner brackets for full view, a chain/check for copying
an artwork link, and three horizontal strokes for the mobile menu. The `menu`
kind in `NavigationIcon` depicts a panel; it is not the phone hamburger.

Native disclosures use `+` / `−`; close actions use `×`; previous/next record
controls use `←` / `→`. Small arrows may clarify a navigation action. Do not
add an arrow to every sentence or introduce a competing icon library, emoji,
filled multicolour symbols or decorative category badges.

Decorative SVGs use `aria-hidden`. Icon-only controls require a useful accessible
name and visible focus. A bookmark uses the existing `StarIcon` and
`BookmarkButton`: outlined when unsaved, filled when saved, with `aria-pressed`.

## 6. Shared navigation and actions

- Keep the existing wordmark on desktop, dark header and footer. On phones,
  use the small serif “A” with its timeline crossbar and red dot before a compact
  current-section label and Menu button. The actual wordmark asset spells
  **Artlines**; do not redraw it to reconcile it with the Artline product name.
- Desktop header links are currently open text links with an active underline.
  `SiteNavigation.css` overrides older pill-navigation rules in `globals.css`.
  Follow the rendered component, not the superseded rule.
- Painters, Books, Events and All are the exploration routes; Guides sits beside
  them. Account uses the existing circular outlined icon.
- The signed-in sidebar belongs to account, directory, record and resource
  pages; the full-width explorers remain free of it. Use the existing
  `SiteHeader`/`MemberNavigation` behavior rather than duplicating navigation.
- Primary actions use ink on paper or paper on ink. Secondary actions are
  outlined controls or underlined text links; editorial actions use rust.
- Navigation is an anchor/Link; in-place state changes use a button. Keep labels
  concrete: “Explore the timeline”, “Download PDF”, “View larger”, “Clear filters”.
- Museum and bookmark destinations use the existing member-aware components.
  Artist/artwork pages, timelines and guides are public. Sign-in preserves the
  selected destination and restores focus when dismissed.

## 7. UI and UX behavior

**Filters and search.** Reuse `AtlasFilters`, `AtlasSearchField`,
`MultiSelectFilter` and the entity filter fields. Search includes a visible
label, a clear action and the existing `/` shortcut where implemented. Display
applied filters as removable chips. Preserve other selections when removing
one filter. “Clear filters” and “Reset view” have different meanings; reuse
the route's implementation and use its actual control labels.

**URLs and paging.** Keep filters, selected records and date ranges in the
existing URL state. Use the shared bounded paging and record-navigation
components. Counts and sorting come from Go/PostgreSQL; the browser must not
download the whole catalogue to compute them.

**Timelines.** Preserve the dark canvas, compact heading, draggable date handles
and labelled colour keys. Date ranges use the handles on desktop and mobile;
Reset view restores the initial selection. Full view uses
`ExplorerFrame` with focus containment and Escape handling. Do not draw fake
time data as a decoration for an editorial page. About's preview positions six
selected works by their recorded creation dates; date ranges stay visible.
Its main action opens that exact selection in the interactive atlas.

**Visual carousels.** About's artist carousel uses full artwork compositions,
short captions and public artist links. Use native horizontal scrolling and
scroll snapping, with 44px previous/next controls, keyboard navigation and
reduced-motion support. Hide the control pair when all content fits. Keep cards
server-rendered and usable without JavaScript;
do not auto-advance or make essential destinations depend on a carousel script.

**Records and images.** Reuse `RecordDrawer`, `RecordArrows`, `ArtworkFacts`,
`ArtworkViewer` and `ArtworkDescription`. Desktop drawers attach on the right;
phones use the available screen. Escape dismisses the active overlay first,
background scroll is locked appropriately, and focus returns to the trigger.
The enlarged viewer has Fit, zoom and keyboard controls.

**Disclosures.** Use native `details`/`summary` for optional sources, FAQs and
reading notes. Keep important navigation outside a closed disclosure. Preserve
existing fragment destinations, and offset anchors below the sticky header.

**Loading, errors and empty results.** Reuse the local component's loading/status
pattern, keep controls stable while requests resolve, and provide a concrete
recovery action. Empty collections should explain what to do next. Never
generate artwork entries or images to fill an empty layout.

## 8. Artwork and editorial content

- Use authentic, approved reproductions with source and rights evidence. No
  generated art pretending to be a collection object.
- Preserve the full composition in guide/editorial image frames using
  `object-fit: contain`. Some existing discovery thumbnails deliberately crop;
  those are previews, not the rule for artwork presentation.
- Keep image identity, title, creator, date label and credit connected. An
  image link should lead to the same object or its exact guide passage.
- Use the guide index for available guides and edition counts. Do not hardcode
  aspirational catalogue totals as evidence of coverage.
- Preserve approximate dates, unknown information, workshop/anonymous creators
  and qualified attributions. A shared date alone is not evidence of influence.
- Distinguish holdings from current display, Artline counts from a museum's
  complete collection, and editorial selections from museum-designated highlights.
- Use direct, useful prose. Avoid superlatives, invented institutional authority
  and unsupported promises. Product copy should explain the visitor's next step.

## 9. Responsive and accessible behavior

- The principal shared breakpoint is 760px. The phone header is a single 52px
  row. Menu opens the native navigation dialog, grouped into Explore (the four
  timelines), Catalogue, and Your account, and the sidebar disappears. At 761–900px
  the sidebar is a 64px rail; wider screens use 208px expanded / 56px collapsed.
- Reduce editorial grids from three to two to one column as their content
  requires. Museum guides currently use 1100px/600px; follow that pattern for
  the same card layout. Do not squeeze three reading columns onto a phone.
- Phone filters collapse behind the shared Filters control and open in place.
  Keep controls reachable without forcing the whole page to scroll sideways.
- Phone timeline date headings use 22px type (20px for BCE ranges). Painter
  view tabs use 12px labels with 44px touch targets; the painting gallery uses
  the available canvas width and height. The movement colour key opens from
  the timeline header.
- Aim for at least 44px interactive targets. Use 16px text in phone selects.
  Do not copy the smallest legacy desktop chart targets into new interfaces.
- Keep one meaningful `h1`, semantic regions, visible labels, keyboard focus,
  skip-to-content, dialog names and selected-state attributes. Do not encode
  state only through colour.
- Global light-page focus is a 3px rust outline (`#b84a32`); dark headers and
  timelines use peach. Preserve existing component-specific focus treatment.
- Respect the global reduced-motion rule. Use only short interaction feedback
  where useful; avoid scroll reveals or automatic decorative animation.
- Test 1440, 1024, 768, 390 and 320px, including a signed-in sidebar and
  signed-out member prompts. Run appropriate accessibility checks and inspect
  screenshots. Server-render public editorial text and links for no-JS use.

## 10. Review coverage and source of truth

The audit read every page route and shared UI stylesheet/component family,
then rendered these routes locally using the read-only catalogue and its
existing local-debug session. Dynamic records were sampled to review their
templates; this was not an audit of every catalogue object.

| Reviewed route or state | Main observations |
| --- | --- |
| `/`, `/books`, `/events` | Shared filter shell, dark timeline, range controls and view switches. |
| `/all`, populated Renaissance preset | Image-led starting points; three labelled content layers and URL-based filters. |
| `/artists`, Leonardo artist page | Ruled directory rows; large record heading, selected artwork, biography and source sections. |
| `/artworks`, Ginevra artwork page | Stone image fields, serif titles, compact metadata, image viewer and evidence. |
| `/museums`, National Gallery record | Collection directory, member access, filter controls and visiting/holding distinctions. |
| `/guides` and all six current museum guides | Shared editorial heading, image grid, reading copy, guide portal, language and PDF actions. |
| Arabic Louvre guide | Right-to-left article layout and translated navigation/content. |
| `/art-history-timeline`, `/privacy` | Restrained prose layout and underlined inline links. |
| `/account`, `/bookmarks` | Account card, native sign-in pattern, tabs, stars and empty collection state. |
| `/catalogue`, `/imports` | Legacy read-only table; Imports redirects to Catalogue. |
| `/membership-preview` | Development-only concepts. Its alternative coloured panels are **not** the production design standard. |
| `/about` before this alignment | Separate blue accents, promotional spacing and a decorative chronology; these are departures being removed. |
| Missing guide route, `error.tsx` | Missing-record screen rendered; error recovery reviewed in source without forcing a server failure. |

Desktop screenshots cover these route families; phone screenshots cover ten
representative layouts. Temporary audit images and the route report live in
`/tmp/artline-design-audit/`. No account, session or catalogue fixtures were made.

Key implementation references:

- [Global tokens and styles](../apps/web/app/globals.css), [mobile behavior](../apps/web/app/mobile.css), [current navigation overrides](../apps/web/components/SiteNavigation.css).
- [Guide index styles](../apps/web/app/guides/guides.module.css), [museum guide styles](../apps/web/app/guides/museum-guide.module.css).
- [Page heading](../apps/web/components/AtlasPageHeader.tsx), [museum collection styles](../apps/web/components/Museums.module.css), [artist directory styles](../apps/web/app/artists/directory.module.css).
- [Navigation icons](../apps/web/components/MemberNavigation.tsx), [bookmark controls](../apps/web/components/Bookmarks.tsx), [search field](../apps/web/components/AtlasSearchField.tsx).
- [Timeline header](../apps/web/components/TimelineHeader.tsx), [explorer frame](../apps/web/components/ExplorerFrame.tsx), [record drawer](../apps/web/components/RecordDrawer.tsx), [image viewer](../apps/web/components/ArtworkViewer.tsx).

Legacy hardcoded shades, small desktop labels and experimental previews exist.
Their presence does not mean they should be propagated. Prefer shared tokens,
the current rendered components and the closest production page family.
