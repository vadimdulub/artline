# Artwork gallery order

Painters → Paintings and All → Artworks share the atlas gallery query. From
4 October 2026, it orders eligible images by the recorded work type:

1. Paintings (including painted icons), frescoes, watercolours and manuscript illuminations.
2. Other objects and unknown work types, including icons whose medium is unknown.
3. Drawings, prints and calligraphy.

Creation year and ID give a stable order inside each group. This is a display
preference, not an assessment of artistic quality or actual image brightness.
No catalogue classifications, dates, visibility rules or images are changed.
Explicit work-type filters still apply before ordering.

PostgreSQL applies the priority before the page limit. Keyset cursors carry it,
and previous/next navigation uses the same tuple. Artwork cursor scopes include
an ordering version so a pre-change chronological cursor is rejected rather
than silently skipping records. Book/event order remains chronological. Internal
priority values are omitted from public item metadata.

## Validation

The existing local catalogue was queried using enforced read-only connections;
no migrations, fixtures, imports or database writes were performed.

- Atlas and HTTP API unit tests passed.
- A complete 30-record selection covering 13 actual media, including icons and
  frescoes, passed pagination and navigation across priority boundaries.
- All, highlights, painter, print-only, search and geographic filters passed the
  read-only gallery/discovery/navigation regression checks.
- Both tabs were checked in Chrome at 1440px and 390px using an isolated API.
  Rembrandt's first page contained 77 paintings, then 13 unclassified works,
  then 60 graphic works. Scrolling to 300 records and drawer navigation passed
  without duplicates or browser errors.

Actual `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` plans were captured under
`/tmp/artline-gallery-order-20261004/`. On the current local catalogue, the broad
artwork query matched 101,015 records and ran in about 1.13s under EXPLAIN; the
Rembrandt query matched 1,329 and ran in about 56ms. The painter path retained
`artwork_artists_artist_work_idx` and artwork primary-key lookups. Existing
covering indexes for image and holding evidence remained in use. No new index
or schema migration is required for this change.

These are catalogue checks, not evidence of performance at 10 million artworks.
Large-catalogue cold-cache, concurrent-request and deep-page load tests remain
necessary, including measurement of the existing totals/density materialization
and the additional priority sort.
