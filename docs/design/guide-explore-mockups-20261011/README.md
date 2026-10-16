# Guide exploration mockups

Prepared 11 October 2026 for design approval. No article component, article content,
translations, PDFs or production web deployment was changed for these concepts.

- Open [interactive preview](index.html) and choose A, B, C or D.
- Open [comparison board](compare.html) to see all four together.
- Desktop images: [A](mockup-a.png), [B](mockup-b.png),
  [C](mockup-c.png), [D](mockup-d.png).
- Mobile images: [A](mockup-a-mobile.png), [B](mockup-b-mobile.png),
  [C](mockup-c-mobile.png), [D](mockup-d-mobile.png).

A is the recommended balanced gallery pair. B emphasizes paintings; C occupies
less vertical space; D previews the actual types of timeline views.

Each concept contains two fully clickable image-led destinations. The existing
Munich guide's filters are preserved: 30 artwork IDs in the combined explorer and
25 artist slugs in the artist timeline. Separate events/books navigation is removed
from the concepts, while books and history remain context inside the combined view.
All real artwork images come from the published guide, with credits in `assets.json`
and the preview footer. Artist lifespan values were checked against the public API.

All four concepts were rendered and visually inspected at 1440px and 390px widths.
Image loading, horizontal overflow, destination counts and filter parameters were
checked. The exhibition grid's initial vertical overflow was corrected before the
final images were exported. `verification.json` records the local checks.

The local preview server uses `http://127.0.0.1:8790/`. The HTML files also open
directly with their sibling assets. A choice of concept is required by the user's
brief before implementing the redesign in the articles.

## Selected direction: revised D

The user selected D and asked for static imagery instead of live previews. The
current D shows Sunflowers, a Frankenstein title page and a painted depiction
of the French Revolution in its first card; the second uses Dürer’s self-portrait.
The original charts, axes and chronology markers are removed. The link
destinations and their preset filters are unchanged. No article changes or
deployment have been made.

Open `index.html?view=d` or [the revised desktop image](mockup-d.png).
Original D images are preserved as `mockup-d-v1.png` and
`mockup-d-mobile-v1.png`. `verification-d-static.json` records desktop/mobile
checks for four loaded images, two links, zero charts and no horizontal overflow.
Additional book/event image sources and credits are in
`static-context-assets.json` and the preview footer.

## Guide section integration

The user clarified that D applies only to the existing section’s right side.
The heading “Explore this selection in Artline”, explanatory copy and five-work
strip stay on the left. Two illustrated cards replace the original four links:
“Artworks in context” and “Who lived when?”. Both retain each guide’s exact
artwork/artist filters. Their images are static, with no timeline preview request.

This is implemented in the shared MuseumGuide component for all six guides and
ten languages. The later-period guides use Treasure Island (1883) and the Paris
Exposition (1889); the remaining guides use the previously approved Frankenstein
title page and French Revolution painting. Sources and credits are recorded in
`apps/web/content/articles/museum-guide-portal-images.json`. Guide artwork images
keep their source credits in the corresponding full artwork entries.

Local browser verification passed all six guide selections and ten locales at
1440, 900, 800, 560, 390 and 320 pixels. All nine section images loaded; each right
side contains exactly two links. The existing twelve guide unit checks passed.
The direct local typecheck encountered stale generated `/about` route types;
production compilation is checked from the isolated release source.

Production release: `artline-web-guide-portal-1011-v1` serves 100% of traffic.
The clean production build (including TypeScript), all nine existing guide
browser checks, and final public-domain checks passed. Final screenshots are
`guide-portal-prado.png` and `guide-portal-prado-mobile.png`. Deployment receipt:
`docs/deployment-20261011-guide-portal.json`.
