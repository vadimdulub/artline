# Artline design approach

Artline should feel like an illustrated collection catalogue that visitors can
explore. People, works, places and recorded dates lead; the interface helps
visitors connect them. The strongest next step is a more consistent hierarchy
and fewer competing surfaces within the existing visual identity.

Use this approach with the [design guidelines](DESIGN_GUIDELINES.md). The
guidelines define the shared tokens and components. This document explains
how to choose the information, layout and interactions for a particular view.

## What the current design establishes

The existing application has a recognizable approach:

| Observed pattern | Evidence | Design implication |
| --- | --- | --- |
| Paper, ink and thin rules frame cultural content | [Shared styles](../apps/web/app/globals.css) and the current map panels | Use alignment and spacing before adding containers. |
| Serif titles identify people and works; sans-serif controls support exploration | [About](../apps/web/app/about/page.tsx), artist records and explorer screens | Give content titles the strongest typography. Keep interface text quieter. |
| Authentic reproductions provide visual character | About carousels, guide covers and map artwork previews | Preserve the full image composition and its identity. |
| Dates and relationships organize exploration | Timeline range controls and documented map connections | Preserve the meaning of a date or relationship while simplifying its presentation. |
| Missing facts are omitted or qualified | [Artwork facts](../apps/web/components/ArtworkFacts.tsx) and location precision | Empty fields add no value; uncertainty that changes interpretation must remain visible. |
| Controls appear when relevant | Collapsed catalogue filters, selected-record panels and source disclosures | Keep frequent actions available and reveal detail through a clear request. |

These observations support an **editorial atlas** direction: calm catalogue
reading within a spatial exploration tool. This is an interpretation of the
existing product, rather than a new visual brand or a user-research finding.

## Establish one visual hierarchy

The main working surface should dominate each exploration screen. On the map,
that surface is the geography and its records. The left panel controls what
is visible; the right panel explains the selected record. Neither panel needs
to become a second dashboard.

Use three levels of attention. First comes the cultural content: a name,
artwork, place or recorded date. Next comes the relationship that makes it
relevant. Controls, sources and explanatory notes support those two levels.
A heading, border or badge should clarify this hierarchy, rather than repeat
something the surrounding layout already explains.

The marketing entrance can use larger compositions and more generous type.
The map must keep the same identity at a practical reading scale. A discovery
screen does not need the About page's promotional hierarchy.

## Keep the established palette and typography

| Token | Value | Application |
| --- | --- | --- |
| Paper | `#f2efe8` | Reading panels and artwork frames. |
| White | `#faf8f3` | Controls and raised panels. |
| Ink | `#1b1916` | Primary text and selected controls. |
| Muted | `#625d55` | Supporting captions and secondary actions. |
| Line | `#d0c9be` | Boundaries that distinguish functional regions. |
| Dark | `#12110f` | Global navigation, map water and the dated exploration frame. |

Use the existing CSS variables. Stone remains the image mat; rust remains the
established action and focus accent. The 50 map identity colours identify data.
They do not recolour the application shell or imply a new brand palette.
Shared authorship colours require an explicit catalogue identity.

Georgia identifies content; Avenir/system sans identifies controls and metadata.
Use regular serif titles around 25–30 px in the inspector, 18 px names in the
record index, 16–18 px map names and 11–12 px supporting captions. Phone search
fields use 16 px. Small map captions are orientation aids, never the only
available record name or source.

## Decide what deserves to appear

Information earns visible space when it helps the visitor identify something,
understand a relationship, assess its precision, or take the next useful action.

| Show immediately | Reveal on request | Remove or avoid |
| --- | --- | --- |
| Record title, relevant creator/lifespan, selected place, relationship and date | Source note and citation | Generic type labels repeated beside a clear title |
| Location precision or an unresolved-location statement | Complete documented place history | A second copy of a single place connection |
| Search, visibility checkboxes and bulk actions | Catalogue refinements and uncommon place types | Empty tabs, disabled single-item navigation and zero-value fields |
| Map movement, zoom and an explicit Fit action | Map coverage and modern-boundary notes | A full-width strip for a small set of map tools |
| An understandable action to inspect the full artist/work/book/event | Longer biography and object details in the existing record view | External-link symbols for actions that open an internal drawer |

Simplification must not turn a country into a precise site, an unknown date
into a definite year, a current holding into a historical location, or a
partial chronology into a complete route. Keep these distinctions even when
other metadata is hidden.

## Give each interaction one job

| Interaction | Result | Preserve |
| --- | --- | --- |
| Hover or keyboard focus on a record | Preview its mapped connections | Visibility, selection, URL, source requests and camera |
| Click a record name or a concrete place | Inspect that record and connection | Other records and their colours; pan only when the selected place needs to be brought into view |
| Change a checkbox | Change visibility | The inspected record, source data and manual camera position |
| Change catalogue filters or years | Request the corresponding bounded catalogue selection | Source identity, factual qualifications and the distinction between loading, failure and no results |
| Fit visible places | Frame the visible selection | The selected record and the source coordinates |
| Open a source | Read the supporting evidence | The current map context |

Preview is temporary emphasis, not another selection mode. Do not dim or hide
other records to simulate focus. Mixed clusters retain their member identities
and open explicit connection choices. Closing an inspector returns keyboard
focus to its trigger; expanding a phone inspector makes the covered map inert.

The place chooser replaces the index temporarily: group connections by their
documented place, show existing artwork thumbnails, and offer one Back to list
action. A nearby-place zoom and the inspector's Find on map action move the
camera explicitly while retaining record visibility and source selection.
Return focus to the map after these camera actions, and retain focus in the
date handles or catalogue inputs when background place evidence refreshes.

## Apply the approach to the map

The map before this application already supplied grouped checkboxes, a stable
camera, source disclosures and an inspector for selected details. The next
changes follow the hierarchy above:

| Starting tension | Application of the approach |
| --- | --- |
| A separate dark toolbar consumes the full width for a few actions | Put a compact paper tool group on the map, below the global view/filter row. Reserve its actual bounds when placing labels. |
| An inspector header says Details, then a second header names the record | Combine the record identity and close/expand actions into one header. |
| The selected connection has another complete box inside the panel | Use a ruled factual passage with the record's identity colour. |
| The full-record button looks like an external link | Use a named action such as View artwork with an in-place navigation affordance. Keep external-link treatment for actual external citations. |
| The list and map require visitors to match names and colours manually | Add a temporary record preview on hover and keyboard focus, without moving the map. |
| Secondary map names and phone input text are small | Increase map caption readability and use the established phone input size. |

Keep the desktop relationship `selection | map | selected details`. Below the
width needed for comfortable map use, the left panel becomes a drawer and the
inspector becomes a bottom sheet. Short landscape screens can use a narrow
side inspector. A selected long title must remain readable through internal
scrolling or explicit expansion. Keep the page within the viewport.

The baseline at 1440 × 900 allocates 647 px of height to the map and 52 px to
its separate toolbar. At 320 × 640, the corresponding map is 431 px tall.
These are measurements from [the preceding local fixture review](design/maps-concept-20261020/review/production/qa.json),
not catalogue coverage statistics. Moving the tools onto the map should recover
that toolbar space while keeping controls and source markers reachable.

## Review the result against the approach

Use the same bounded examples before and after the change. Compare overview,
selected creator, selected artwork, long title, empty selection and failed
request states at 1440, 1024, 768, 390 and 320 px, including short landscape.

The result should provide more map area, one inspector identity header,
readable names and a clear route to the full record. Hover and keyboard preview
must leave the camera, visible record set and URL unchanged. Controls must
retain 44 px targets, avoid label collisions and remain reachable beside a phone
sheet. Existing source, date, image, sharing and recovery behavior must hold.

The applied implementation and verification belong in the
[map visual review](design/maps-concept-20261020/VISUAL-REVIEW.md). New exhibition,
museum or author-life adapters remain separate catalogue work; a visual
refinement must not imply that their data is already integrated.

## First application

The first application introduced compact paper tools on its surface, one record identity header
with close/expand actions, ruled connection facts and named internal record
actions. Pointer hover and keyboard focus preview a record's mapped connections
without changing the visible selection, camera or URL. Map labels are larger,
phone search text is 16 px, and labels avoid the actual tool boundaries.

| Viewport | Map height before | Map height after | Recovered height |
| --- | --- | --- | --- |
| 1440 × 900 | 647 px | 699 px | 52 px |
| 320 × 640 | 431 px | 483 px | 52 px |

The [applied validation](design/maps-concept-20261020/review/approach/validation.json)
records 58 passing unit/component tests, 182 passing browser checks, and clean
TypeScript/ESLint results. Browser checks use intercepted map fixtures across
six viewport sizes; they include preview invariants, control/label separation,
source preservation, internal actions, sharing, recovery and keyboard focus.
The changes are local and have not been deployed.

[Map overview](design/maps-concept-20261020/review/approach/painters-overview.png) ·
[Selected artwork](design/maps-concept-20261020/review/approach/artwork-selected.png) ·
[Phone inspector](design/maps-concept-20261020/review/approach/selected-390x844.png) ·
[Existing About typography](design/maps-concept-20261020/review/approach/reference-about-desktop.png)

## Art atlas visual direction

The map's strongest visual element is the art itself. The current direction
uses ink-dark water and restrained charcoal land, with names set directly on
the geography. Creator colours remain data colours in the markers and index;
the main reading panels retain Artline's paper and serif typography.

Actual catalogue reproductions illustrate documented location groups. They are
complete compositions with named captions, never generated imagery or invented
historical scenery. At most three illustrations appear on a large map, two on
a medium map and one on a small map. If an illustration cannot be placed
clearly near its source anchor, a text caption takes its place. Mixed locations
retain their place and connection counts.

The index uses larger serif names and quieter lifespan/creator metadata.
Selected artwork records show a larger reproduction on desktop. Phones retain
a compact identity header and an expandable inspector. Maps use the available screen height without a date bar. Recorded dates remain
in the inspector, and timeline views keep their date handles and validation.

[Art atlas overview](design/maps-concept-20261020/review/art-atlas/painters-and-paintings.png) ·
[Selected artwork](design/maps-concept-20261020/review/art-atlas/artwork-selected.png) ·
[Phone](design/maps-concept-20261020/review/art-atlas/selected-390x844.png)

The [current validation](design/maps-concept-20261020/review/art-atlas/validation.json)
records 65 passing unit/component tests and 196 browser checks across six
viewport sizes, with clean TypeScript and ESLint results. The map is 736 px
high at 1440 × 900 and 486 px at 320 × 640 in the local review. Catalogue data,
coordinates, evidence and identity assignments remain intact. This is a local
frontend change and has not been deployed.

## Map layers and complete painter context

The left panel owns visibility: Painters, Artworks, Books and Events. A layer
checkbox controls the whole kind, including records loaded on later pages.
Individual record choices remain independent. Each layer has a small outline
icon beside its name. Long work, book and event lists start closed so their
size does not bury the controls. Search reveals matching records.

The map toolbar contains only the Layers icon. The left panel starts closed
at every screen size. That icon opens visibility controls; selecting an artwork
image, map place or country opens its connected records on the right. The left
panel contains layers only. A connection opens its record inspector on the
right, with Back to location restoring the grouped list. Phones use the same
sequence in the information sheet. Panning never opens the left panel. There
is no share-link button or Show all / Show none action.

Choose one or several painters inside Layers. Their recorded birth, death,
study and other biographical connections remain available across the complete
lifespan. The saved period still delimits artworks, books and events; its date handles
remain on timeline views. Painter
selection scopes the artwork layer while books and events retain their own
selections. Display located artworks even when a reproduction is unavailable.
Keep native result limits; the map does not download the entire catalogue.
The map fills the viewport beneath its toolbar, without a paging footer.

The right panel owns the selected location, its connected records and their
evidence. Group each canonical painter once, show the recorded lifespan below
the name and arrange its connections on a vertical line with dots. Every
milestone shows its relationship and place directly, even when all connections
share one location. Lead with the fact (for example, Born in Zundert), then its
recorded date; reading this information must not require opening the inspector.
Show only the recorded geographic precision: a country alone is not a city.
Known dates
appear in order; undated associations follow with hollow dots. A lifespan is
context, not the duration of a cultural affiliation or another undated connection.
The map API can supply a missing birth/death milestone date from the corresponding
recorded artist date, retaining qualifications, source keys and location precision.
Do not assign an inferred year to other associations. Event details also
provide Show events and Colour recorded countries. A country colour uses that
event's identity colour and requires an explicit country-level event location.
Painter nationality and a city connection do not imply an event territory.
Country outlines remain modern orientation geometry, not historical borders.
Clicking an event country opens its event-only location list on the right. Turning the
Events layer off retains the inspected record and the other visible layers.

Remove Place types and the aggregate Without a map location control. Preserve
precision, unknown facts and source disclosures in each record. Visibility,
country-colour preference and record selection remain shareable URL state.
Each picker replaces the layer overview with a full-height panel view. The
header retains its name, Back, visibility and Close controls. Search stays
above a separately scrolling list. Record visibility changes apply immediately,
and Back returns focus to the originating selector. Mapped records appear
first; explicit searches retain loaded source records without coordinates.
See the [picker UX review](design/maps-concept-20261020/PICKER-UX-REVIEW.md) for
the research, applied decisions and current screenshots.

The [layer review](design/maps-concept-20261020/VISUAL-REVIEW.md#independent-map-layers)
records the applied behaviour and local verification.
