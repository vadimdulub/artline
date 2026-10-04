# All discovery redesign — 23 September 2026

The combined view should expose pictures and people immediately. Remove Add;
use a shared creator search for painters and book authors, with explicit content
switches. Events retain their historical context when creator filters are used.

Design plan: retain Artline's paper #f2efe8, dark #12110f, ink #1b1916,
muted #b5ad9f, artwork #c78168 and book #c1a579. Georgia identifies periods
and dates; the existing sans serif carries descriptions and controls. Left-align
the content and use actual catalogue reproductions for the starting points.

    Search                                      Show starting points
    Period | Creators | Countries | Continents | Region | Highlights
    Explore a moment in history
    Featured periods: image / dates / description / geographic starting scope
    All other periods, grouped with dates and context

    Period title + explanation        Artworks / Books / Events
    Shared year ruler
    Artworks: immediately visible image gallery, bounded page, Browse all
    Books: publication timeline
    Events: historical timeline
    Full-history year controls

Review: an equal button wall hides the differences between periods. Use larger
illustrated entries for a small set of starting points and quieter grouped rows
for the rest. All starting points remain available. The artwork gallery is the
visual focus; controls retain the established design. Country defaults are an
editable starting lens, not a claim to represent the whole historical event.

Implementation must keep filtering, record visibility, counts and keyset paging
in Go/PostgreSQL. Enrich only returned artwork IDs with existing image metadata.
Creator identities retain their catalogue roles rather than being merged by name.
No metadata imports, publication, image downloads or database writes are needed.


Implemented behavior:
- Four illustrated starting points and all 26 remaining periods, grouped with
  dates and descriptions. Cover metadata is resolved only for four explicit,
  eligible artwork IDs and honors public versus preview visibility.
- All 30 periods have reviewed country, creator and Highlights defaults. Specific
  movements use researched creator identities and selected books; broad cultural
  surveys use country defaults and optional Highlights. Events use reviewed
  core/context lists. Countries initially apply to artworks, with an option to
  apply them to books/events too. Choosing another period replaces its defaults;
  deliberately cleared filters survive reload. Byzantium retains anonymous
  object traditions without a hard country filter. See the
  [24 September review](research/all-starting-points-20260924/README.md) for all
  decisions, creator evidence, current counts and coverage gaps.
- The complete “More starting points” list stays on the same dark page. Its
  container grows with the content at desktop and mobile widths. Only All calls
  the reset action “Show starting points”; other views retain “Reset view”.
- Painters offers “Painter lifespans” and “Paintings”. Paintings uses the same
  server-filtered artwork gallery, details and keyset pages as All, retaining
  the current painter filters and interpreting the range as creation dates.
  The scrolling Paintings view includes all matching illustrated eligible
  artworks, without a separate artwork-highlights filter. Old links carrying
  `painting_highlights` no longer restrict the results. The existing 1970
  creation cutoff still applies.
- One server-searched Creators filter uses role-qualified catalogue identities.
  Selected painters scope artwork links and selected authors scope book links;
  selected roles combine, while events retain period/geography context.
- Artwork thumbnails open details directly. The shared horizontal gallery in
  All and Painters fetches the next 150-record keyset page near the end of the
  visible row. It retains the scroll position and renders at most three pages
  (450 artworks), replacing older pages with spacers. Scrolling back refetches
  evicted pages using their original cursors. The initial response and a compact
  cursor index are retained; it never preloads the complete collection.
- A failed incremental request leaves the visible paintings in place and offers
  retry. Filter changes abort outstanding loads and start a fresh gallery.
  Artwork detail navigation keeps the full filter scope. In All, the Artworks,
  Books and Events headings open their filtered 30-item lists. Layer visibility
  is controlled by the top checkboxes, without duplicate remove buttons. The
  separate artwork-year disclosure is removed from All.
- The Painter lifespans / Paintings switch uses a compact 37px row. The gallery
  introduction and visible page-count caption are removed. Screen readers still
  receive loading/end status and artwork positions within the collection.
- Every timeline places its year fields between Earlier and Later, below the
  range slider. The movement key sits beside the dates on the left and opens
  when returning to Painter lifespans. The four painter range-preset buttons
  and “About these dates” disclosures are removed; index links remain.
- In All, Books lanes above the server's 150-object cutoff show a horizontal cover
  gallery. Each card contains only its title and recorded publication date,
  with the full title on hover and the existing book drawer on selection.
  Smaller Books lanes retain their individual timeline marks. Books and
  artworks share bounded scrolling, retry and page-eviction behavior.
- The standalone Books screen always renders individual title-and-year marks,
  including the full date range and crowded periods. Author lifespans likewise
  stay individual. Both use the current bounded server page, with Next / First
  page controls beside the timeline and the existing index pagination. No book
  histogram or density suggestions are rendered or calculated by this endpoint.
- Book covers come from the existing reviewed cover manifest. Only the current
  page's eligible book IDs receive a single indexed source-identity lookup;
  source mismatches and missing or failed images use a simple placeholder.
  Images load lazily, and the drawer retains edition and source credits.

Verification uses only the existing catalogue under PostgreSQL read-only mode.
The creator audit checks both roles, independently retained selected labels,
public cover visibility, bounded image enrichment and non-overlapping pages.
EXPLAIN ANALYZE for a selected painter confirms indexed artwork links and primary
key lookups; the plan is under /tmp/artline-all-redesign-plans. The actual audit
returned 213 Monet artworks, three Tolstoy books and 1,697 Renaissance artworks.
This is correctness and local query-plan evidence, not a 10-million-artwork load
test. Representative large-catalogue concurrency and cold-cache load testing
remain outstanding; no synthetic data was inserted into the real catalogue.

The 24 September gallery checks cover desktop/mobile scrolling, page eviction
and backward loading, the final page, request failures, late-response cancellation,
filter resets, detail focus restoration and accessibility. Browser artifacts are
under `/tmp/artline-infinite-scroll-ui`; no database data or API rules changed.

The cover-gallery checks are under `/tmp/artline-book-gallery-e2e`. A read-only
audit verified 300 distinct books across two pages, including selected and
missing covers. The 150-ID cover identity lookups used indexes and took about
0.16 ms each locally. This is bounded-page evidence; large-catalogue concurrency
and cold-cache load testing remain outstanding.

Books mark verification (25 September 2026): the existing catalogue was audited
under PostgreSQL read-only mode for bounded, ordered pages, retained filters,
visibility, creator metadata and unknown dates. All 18 Chrome checks passed across desktop,
390px and 320px layouts, two-line labels, page navigation, drawers, author view,
filter/history behavior and accessibility. Captures and logs are under
`/tmp/artline-book-marks-browser` and `/tmp/artline-books-marks-readonly.log`.
