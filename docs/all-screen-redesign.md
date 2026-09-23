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
- All 30 periods expose their reviewed geographic or subject scope. Thirteen
  offer editable country defaults for artworks, preserving books and events for
  historical context. A checkbox can apply countries to those lanes too. Period
  changes replace automatic defaults while preserving custom geography. See the
  [complete filter audit](starting-point-filter-review.md) for decisions and counts.
- The complete “More starting points” list stays on the same dark page. Its
  container grows with the content at desktop and mobile widths. Only All calls
  the reset action “Show starting points”; other views retain “Reset view”.
- Painters offers “Painter lifespans” and “Paintings”. Paintings uses the same
  server-filtered artwork gallery, details and keyset pages as All, retaining
  the current painter filters and interpreting the range as creation dates.
  Artwork highlights is independently switchable. Only illustrated eligible
  artworks are returned; the existing 1970 creation cutoff still applies.
- One server-searched Creators filter uses role-qualified catalogue identities.
  Selected painters scope artwork links and selected authors scope book links;
  selected roles combine, while events retain period/geography context.
- Artwork thumbnails open details directly. Pages contain at most 60 records,
  ordered by creation date, with cursor navigation and a separate 30-item Browse
  view. The optional year histogram still supports narrowing the shared range.

Verification uses only the existing catalogue under PostgreSQL read-only mode.
The creator audit checks both roles, independently retained selected labels,
public cover visibility, bounded image enrichment and non-overlapping pages.
EXPLAIN ANALYZE for a selected painter confirms indexed artwork links and primary
key lookups; the plan is under /tmp/artline-all-redesign-plans. The actual audit
returned 213 Monet artworks, three Tolstoy books and 1,697 Renaissance artworks.
This is correctness and local query-plan evidence, not a 10-million-artwork load
test. Representative large-catalogue concurrency and cold-cache load testing
remain outstanding; no synthetic data was inserted into the real catalogue.
