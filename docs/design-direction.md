# Design direction

Updated 2026-09-08 after reviewing the supplied prototype screenshot with the frontend-design skill.

The reference establishes a dark navigation bar, warm paper, oversized painter
names, a selected-work strip, and an adjacent artwork record. The redesign
follows that specific direction. Artline remains the project name.

## Tokens

- Charcoal: `#12110f`
- Paper: `#f2efe8`
- Stone: `#e8e3d9`
- Text: `#1b1916`
- Rule: `#d0c9be`
- Accent: `#c85139`

Georgia carries the display and reading typography. Avenir/system sans handles
controls, dates, and compact metadata. Text is left aligned. Movement colors
are always paired with names.

## Layout

```text
Artline                    Timeline / Catalogue             About
Compact full-width search / region / movement / more filters
One full-width dark chronology panel:
  Large date range and painter intervals
  Focus the timeline: zoom presets / exact years / draggable range
  Century markers and compact movement legend
Chronological painter list

Painter record:
Name, dates, geography                           Artwork record
Short biography / incoming / outgoing claims     Selected image or placeholder
Selected-work strip                             Origin / collection / rights
Expandable essay and sources                    Previous / next / source links
```

The first review found the full biography pushed artworks too far down the
page. The page now leads with a short excerpt and an explicit expansion control.
Cards align at the top despite different title lengths. On small screens the
artwork panel follows the strip; selecting a work scrolls to its detail.
Native dialogs handle keyboard trapping, Escape, and focus return. Reduced
motion preferences disable animated scrolling.

Painter selection on the timeline opens a full-height right-hand drawer,
approximately 40% of the desktop width, over a dimmed and softly blurred
timeline. It becomes full-width on phones. The drawer uses a paper toolbar
with a persistent circular close button, a large name, a full-width biography,
two influence columns when claims exist, and vertical artwork rows with dates
and locations. Empty biography/influence sections use a compact research note.
Selecting a row scrolls to its detailed artwork record within the drawer.
The canonical painter page retains its wider split-column layout.

The second timeline reference places the range controls inside the black
chronology surface. That relationship is preserved at desktop and mobile
widths. The introductory text block is removed, the filters form one compact
band, and painter lanes use a tighter pitch without reducing their label sizes.
The focus slider uses a fine ivory line and circular handles, with presets and
exact-year fields retained. Country filtering remains under More filters.

The global usability pass adds visible filter chips, a search shortcut, clamped
collision-aware labels, previous/next painter navigation, return-to-selection,
canonical copy links, and a full-window image viewer. Artwork details and
thumbnails preserve the full composition. Secondary text is darker and larger;
coverage, catalogue, and imports share navigation. Catalogue drafts have visible
dirty/error states and link/unload protection.

Snapshots are in `docs/screenshots/`. These are review artifacts, not a claim
of a completed WCAG audit or visual parity with an unavailable full prototype.
