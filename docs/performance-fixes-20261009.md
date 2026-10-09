# Catalogue performance fixes — 9 October 2026

This implements the bounded-read, query, payload and cache changes identified in
[the production audit](performance-20261009.md). All active catalogue records
remain visible; archived exclusions, date handling, source links and member
access rules are unchanged.

- Public catalogue reads have an end-to-end deadline, four concurrent cache
  fills per API instance, and at most 16 queued fills waiting 500 ms. Cache hits
  bypass admission; overload returns 503 with `Retry-After: 1`. Authentication
  and member routes are outside this gate. `Server-Timing` exposes queue time.
- Artist and museum directories/details/works and bounded SEO reads now share
  the existing revision-aware, one-minute, size-limited cache. Every lookup
  still checks a fresh database revision. Migration 0040 adds the missing
  opening-artwork-selection invalidation dependency. Facets have a separate
  revision-keyed cache capped at 64 entries / 2 MiB.
- Museum filter queries deduplicate scoped creator IDs before joining movement
  records. Influence citations are fetched in one bounded batch rather than
  one query per returned claim (up to 40).
- Public responses omit internal citation evidence notes that the UI does not
  render. Source names, URLs, attribution qualifications and other metadata
  remain intact. Full evidence stays in storage and direct repository reads.
- Migration 0041 adds a narrow title-search projection. Artwork triggers update
  it in the same transaction; deletion cascades. A trigram index identifies
  candidates before ordered keyset pagination; only returned IDs receive full
  artwork/creator/media/museum enrichment. A partial media ID index supports
  image eligibility without denormalizing a cross-table boolean. This avoids
  stale image flags during concurrent source updates. Counts use the same
  filter as pages. Unmigrated read-only local catalogues retain a fallback.

The initial production candidate using the wide artwork table still spent
21.24 seconds selecting title candidates, with 2,259 disk block reads. This is
why the final implementation uses a compact projection rather than relying
solely on a change to query ordering. The projection is derived search data;
it does not change source records or editorial statuses.

## Validation

All Go packages pass. Opt-in read-only comparisons on the existing local
catalogue verify identical title results/order, unknown-date and image filters,
cursor continuity, museum choices, and every public painter field except the
explicitly omitted citation notes. The tested local painter response shrank
from 216,466 to 24,685 JSON bytes. This measures API JSON, not browser rendering.
Unit tests cover cache revision/expiry/size/copy semantics and admission,
cancellation, deadlines, authentication independence and cache-hit bypass.

The real local database is unchanged. No database fixtures were created or
loaded. The full suite uses existing ignored historical research evidence;
database fixture tests remain opt-in. Production migration, query plans, exact
build provenance and rollout checks are retained in the release backup folder.

This is not a 10-million-artwork capacity claim. Representative large-dataset
and sustained concurrency tests remain outstanding, as does separating a
lightweight artist identity read from full single-artwork page enrichment.

Private release evidence:
`/Users/vadimdulub/Library/Application Support/Artline/backups/performance-fixes-20261009/`.
