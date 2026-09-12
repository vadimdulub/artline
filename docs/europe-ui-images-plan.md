# European collections and large-catalogue polish — 10 September 2026

## Scope

Polish large-collection browsing; research and import European museum records;
download a selected, individually rights-cleared image batch to local disk at
**at most 100,000 bytes per artwork**. Preserve Go/PostgreSQL filtering,
1970 creation cutoff, review-only imports, right-hand drawers and the compact
black painter timeline. No commits, publication, cloud writes or deployment.

## Design pass 1: preserve the study atlas, improve the working surface

- Palette: paper `#f2efe8`, ink `#1b1916`, image mat `#e8e3d9`, quiet text
  `#625d55`, selected terracotta `#c85139`, verified moss `#53745b`.
- Type: existing Georgia display and Avenir/system sans controls; display
  headings reduced on collection pages, readable titles, tabular numeric counts.
- Layout: left-aligned compact collection introduction, optional visiting
  details, search/filters, a persistent results toolbar, then the artworks.
- Work images are the memorable element. Avoid new decoration, gradients,
  giant numerical heroes or a new brand palette.

```text
Museum name                         Visiting information (expand)
All works / My picks / Museum highlights
Search                 Painters             Movements
More filters     With images     Active filters
Results count       Grid / List        Sort       Previous / Next
Artworks: image-first grid OR compact illustrated catalogue rows
Page position / First / Previous / Next
```

## Critique against the actual app

The current 1440×1000 screenshot places the first artworks around y=895.
Four-column cards repeat missing-image and unverified-display text; long titles
stretch the grid. Pagination only offers Next/First, not a previous page.
Artist chronologies already use bounded pages, but browsing backwards and
retaining position are awkward.

Revision: preserve the owner-chosen paper/serif/black identity (despite it being
a common template palette); spend the change on usable density and navigation.
Bring works above the fold, add explicit Grid/List modes, expose image-only
filtering, clamp card titles without removing accessible names, move general
display caveats out of every card, and retain a bounded cursor trail—not an
ever-growing artwork array. Browser back/forward must still work. Do not infer
fake page counts from loaded items or choose highlights by image availability.

## Evidence and inspiration

- [Art UK discovery](https://artuk.org/discover/artworks): image availability,
  artwork type and location are practical entry points into large collections.
- [Rijksmuseum collection/data design](https://data.rijksmuseum.nl/about/):
  object-first discovery and a separate detail experience. Borrow information
  hierarchy, not their visual identity or unrestricted claims about every image.
- [SMK API](https://api.smk.dk/api/v1/docs/): structured creator, creation,
  source identity and per-work image rights, suitable for the European wave.
- [Nationalmuseum images](https://www.nationalmuseum.se/en/explore-art-and-design/images):
  use only the explicitly public-domain subset; catalogue presence alone is not permission.

## Execution / verification

1. Baseline screenshot and source/access review — complete. In-app browser
   bootstrap failed before connection; use the installed Playwright test suite.
2. UI implementation and desktop/mobile interaction/accessibility checks — complete; 25 focused browser tests passed.
3. European metadata selection, backup, rollback preview, apply and replay — complete: 912 new artworks, six exact existing matches.
4. Selected images — complete: 80 local files, all ≤100,000 bytes; fresh rights
   evidence, bounded downloads, local JPEG compression and full file verification.
5. Final frontend/backend tests and dated [research report](research/europe-ui-20260910/research-log.md).

The image budget is a file-size ceiling, not permission to take every picture.
No generated substitutes, cropping away artwork, or inferred rights. Where a
museum blocks access or has unclear rights, keep metadata and defer the image.
