# Account bookmarks and small save stars — 10 October 2026

Bookmarks now live in Account. The header account link opens `/account`; the
standalone header star, mobile Bookmarks menu entry and footer shortcut are
removed. Account retains its collection link and desktop collection navigation.

Saving uses a 16px star with a 44px target, a filled saved state, an accessible
record-specific label and keyboard focus styling. Record stars sit beside titles;
gallery stars sit on pictures. Heading margins sit outside the alignment row,
so stars center on the text and stay beside the title. Artist directory stars
align with the first line of each name. Artist and event index rows also expose stars.
Book and event saves join artists and artworks in the private, filtered collection.
Signed-out saves retain the selected record and destination through sign-in.

## Storage and release

Migration `0044_member_book_event_bookmarks.sql` adds member/book and member/event
foreign keys, idempotent primary keys and paging indexes. Apply it through the
normal release process before serving this API in persistent member mode. It has
not been applied to the real local database; no deployment was performed.

The local API runs with `-skip-migrations`, read-only PostgreSQL connections and
loopback-only local-debug access. Local saves live only in memory. Book visibility
keeps its existing 2000 cutoff and undated handling; archived records remain
excluded. Selected book/event reproductions preserve their source, label, credit
and license. No catalogue status, metadata or assets were changed by this work.

## Verification and capacity limits

- 321 web unit tests; TypeScript and ESLint pass.
- Go member, event and HTTP API tests pass, including private/idempotent saves,
  invalid references and 137 mixed bookmarks paged across equal timestamps.
- 16 targeted browser checks pass across Account, bookmark flows and mobile
  navigation. One new test's close-button locator was corrected before rerunning
  it. Accessibility checks cover Account and the mobile collection.
- Real local book/event lookups, temporary saves and removals succeed without
  database writes. Browser checks preserve any prior temporary save states.
- The mixed PostgreSQL page query was executed read-only using bounded CTEs
  selecting 35 existing records per kind, with no inserted fixtures, new database
  or temporary tables. Four 31-row pages exercised text and UUID cursors. A
  representative `EXPLAIN (ANALYZE, BUFFERS)` used primary-key lookups for catalogue
  enrichment, including the scoped artwork/creator lookup; it took 7.58ms locally.

Each persistent query starts at one member's bookmarks, takes at most 31 per kind,
then enriches the final 31 candidates. State requests contain at most 100 mounted
references. The CTE check establishes query correctness and bounded enrichment;
it does not measure the new bookmark-table indexes or 10-million-artwork capacity.
Production-sized member distributions, archived-heavy collections, deep cursors
and concurrent writes still need a dedicated load environment after migration.
Disposable screenshots and query-plan output were kept under `/tmp`.
