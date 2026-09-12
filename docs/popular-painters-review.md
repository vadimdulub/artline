# Popular painters and museum coverage — 8 September 2026

This report describes the discovery/Prado pass. The subsequent
[museum-coverage follow-up](museum-coverage-followup.md) adds Uffizi and Mexico
records and records updated totals. Original results below are preserved.

## Design plan

Keep the user's preferred dark chronology and right-hand record panel. The chart,
not a new marketing hero, remains the memorable element.

- Palette: paper `#f2efe8`, ink `#1b1916`, charcoal `#12110f`, stone `#e8e3d9`,
  rule `#d0c9be`, and vermilion `#c85139`. These preserve the approved atlas rather
  than introduce a competing visual identity.
- Type: Georgia for painter names and dates; Avenir/system sans for controls and
  evidence. Keep functional text readable, sentence case, and left aligned.
- Layout: a quiet, always-visible popular-painter checkbox above the dark chart;
  fixed-height, keyboard-scrollable lanes with the focus controls in the same
  black surface; a bounded painter index below. Museum links belong beside the
  painter's artwork chronology, not hidden below a long biography.

```text
Search / regions / movement / more
☑ Only popular painters            About this selection
┌ Dark timeline: dates + count ────────────────────────┐
│ Year axis; scrollable, non-overlapping painter lanes│
│ Focus range and date controls                      │
└───────────────────────────────────────────────────┘
Painter index / time periods              Right record drawer
```

Brief review: a new cream/serif landing page would duplicate the atlas and hide
the tool. Retain the existing identity, reduce the enormous density-results list,
and spend design effort on navigation, coverage honesty and artwork inspection.

## Backend and content plan

1. Default `popular=true` for timeline discovery and its facets; explicit
   `popular=false` persists in shared URLs and browser history. Reset restores
   the default; clear filters genuinely removes the popularity restriction.
2. Store popularity separately from artworks and publication. Start from the
   imported Pantheon top 100, with documented editorial additions/exclusions.
   Hokusai belongs in the selection despite the source's occupation taxonomy;
   Donatello is retained in the catalogue but excluded from painter discovery.
   Image counts must never determine popularity. No hidden fallback to all data.
3. Share the same SQL popularity predicate across counts, chart nodes, density
   bins and facets. Aggregate density navigation into time periods on the server.
4. Add a bounded, reviewed Prado selection with official object evidence and
   independently checked reusable-image evidence. Do not label every holding a
   museum-designated masterpiece, or imply that a holding is currently on view.
5. Test defaults, URL round trips, reset/clear, regions, the Velázquez panel,
   museum navigation, keyboard focus, mobile overflow and accessibility. Record
   exact results after verification; do not overwrite historical screenshots.

## Implemented and verified

- Default discovery contains 100 painters; unfiltered preview contains 1,001.
  An indexed database selection is shared by discovery counts, nodes, density
  bins and facets. Fresh imports populate it without overwriting editorial edits.
- The full catalogue now uses one navigation row per time period instead of
  hundreds of repeated movement/period rows. Painter lanes, their index and the
  movement key stay bounded and keyboard-accessible; focus controls remain black.
- Painter aliases are collapsed, collection links precede the chronology, and
  links preserve the painter filter when opening a museum. Missing work counts
  say “Works to add”, not an implied lack of historical output.
- Twelve Prado paintings and twelve public-domain Commons reproductions were
  added. Velázquez now has five works, including four at the Prado. The batch
  also covers Goya, Bosch, El Greco, Rogier van der Weyden, Titian and Dürer.
- Local totals: 377 artworks, 211 with images, ten museum/holding collections.
  Imported cohort coverage is 185 painters with artworks and 121 with images.
  The complete 1,000-painter illustrated catalogue is still not finished.
- All imported works remain in review. No display assertions, commits, Terraform
  apply, or deployment. Import replay added zero duplicate works/images.
- Six Playwright scenarios pass, including the painter → Prado → enlarged image
  journey, history/reset, search/regions, failure recovery, keyboard focus and
  axe WCAG checks at 1440, 390 and 320 pixels. Screenshots are under
  `docs/screenshots/popular-after-*` and `velazquez-prado-*`.
- Twenty frontend unit tests, lint, production build and Go tests pass (including
  isolated PostgreSQL regressions). In-app browser bootstrap still fails, so the
  existing local Playwright runner was used. The older seed-specific browser suite
  was not claimed as passing against the enlarged database.

## Painter review and next source priorities

Popularity and coverage are different: **25 of the 100 popular painters have no
artworks here, and 40 have no images**. Keep them discoverable and use those gaps
to prioritise source work; never make the image-rich museums define the canon.

The [Prado's collection introduction](https://www.museodelprado.es/en/the-collection/)
describes its particularly extensive holdings of Velázquez, Goya, Bosch, Titian,
El Greco and Rubens. This explains why the original US-API-only import was a poor
representation of Velázquez. The app's counts describe imported records, not the
fraction of a painter's entire output owned or displayed by that museum.

Next high-priority gaps identified in the popular selection:

- Botticelli: no works imported yet. The Uffizi's official records for
  [Birth of Venus](https://www.uffizi.it/en/artworks/birth-of-venus) and
  [Spring](https://www.uffizi.it/en/artworks/botticelli-spring) are concrete source
  candidates. Review reproduction permissions separately before importing images.
- Frida Kahlo: no works imported yet. Mexico City's Museo de Arte Moderno includes
  [Las dos Fridas in its highlighted works](https://mam.inba.gob.mx/destacadas.html).
  A catalogue record does not itself grant image-reuse rights.
- Picasso, Dalí and Matisse: selected metadata exists, but this batch has no
  locally reusable images for them. Prioritise rights review, not arbitrary web
  image substitution. Never infer public-domain permission from the 1970 cutoff.

The broader occupation/movement imports still need editorial review. The popular
selection is a transparent starting list, not a universal or definitive ranking.
