# Private account studies · 11 October 2026

The latest research-only revision is documented in
[`../studies-research-only-20261011/README.md`](../studies-research-only-20261011/README.md).
It replaces the workflow selector and the original 100-study library described below.

Implemented the approved account workspace and the revised light timeline from
the user’s reference. This is connected to the existing Go catalogue and member
authentication; the six-record mockup has not replaced any catalogue data.

Preview: <http://127.0.0.1:3111/studies>.

## Implemented

- Studies in desktop account navigation, the phone menu and account settings.
  Both Studies and Bookmarks require a member session on the server and API.
  Sign-in retains the selected study and filters. Artist and artwork pages remain public.
- Private named studies with creation, renaming, deletion and Research, Teaching
  and Exhibitions workflows. Account changes clear the previous member’s client state.
- A native Add dialog with Catalogue, Bookmarks and Your link tabs; title/subject
  search, creator/author, record type, year range, undated and artwork-image filters;
  removable filter chips, bounded paging, multi-selection and existing-record states.
- URL-only personal artwork, book and event cards. Title, creator and year are optional.
  Only HTTP/HTTPS links without credentials are accepted. No remote page scraping or
  automatic image import occurs. Personal references never become catalogue records.
- Light timeline, type counts, gallery, source inspector, notes, two independently
  selectable artwork comparisons, and references/CSV exports. Reproductions retain
  their proportions. Image credits and original date labels remain attached.
- First phone visits default to Gallery; an explicit view choice is remembered.
  Phone record details and filters use full-width dialogs. Escape closes the active
  dialog, including when focus is in a search input, and restores the trigger.
- Loading, empty, missing-image and network-error states, retry controls, failed-note
  draft retention, inline year validation and accessible focus treatment.

## Storage and integrity

`0045_member_studies.sql` adds only the private `member_studies` table. Every lookup,
mutation and export is scoped to the authenticated account. Row locks make additions,
removals and note updates atomic. Existing member cookies and origin checks protect
the API; the Next proxy restricts methods/paths and buffers at most 32 KiB per mutation.

Study records contain dated catalogue snapshots, identified as such in the inspector,
settings and references. They do not imply live catalogue synchronization. Source
links, qualified creator labels, unknown dates, holdings and image evidence are retained.
Unverified/open-ended dates stay unplotted. Separate recorded intervals are tested
independently, including the gap between Seurat’s painting and border intervals.
Displayed dates take precedence over conflicting numeric fields within a study snapshot;
the discrepancy is retained in the date note. Catalogue records themselves are unchanged.

Limits: 100 studies per account, 200 records per study, 50 visible study records per
page, 24 catalogue search results/additions per request. Go owns filtering, ordering,
counts and pagination. Default artwork browsing uses the existing primary-key index;
text searches narrow candidate IDs before sorting and batch enrichment. Artworks lead
the gallery; the timeline follows dates. Formula-like user text is neutralized in CSV.

The preview API runs on port 8085 with `-skip-migrations`, loopback-only local debug,
and PostgreSQL `default_transaction_read_only=on`. Studies and bookmarks are held
in memory and disappear when that API restarts. No real account, session, bookmark,
study or catalogue rows were written. The separate web preview runs on port 3111.

## Verification

- Go member, catalogue and HTTP packages pass, including race detection. New coverage
  checks authentication, ownership, cross-site rejection, local-debug loopback checks,
  unsafe links, duplicate adds, note persistence, exports, date gaps, bounded paging
  and concurrent updates.
- 25 focused web tests pass: study proxy/input behavior and existing member/bookmark guards.
- Eight Playwright scenarios pass against the local API: full study workflow;
  1440/1024/768/390/320px layouts; session expiry; bookmark selection, URL-only cards
  and recovery from failed searches/saves. Add dialogs pass axe WCAG A/AA checks.
- TypeScript, focused ESLint and the production Next build pass. The build uses an
  isolated preview tree with the repository’s existing dependencies.
- An independent signed-out API and production web build returned 401 for private
  APIs and 307 to sign-in for Studies and Bookmarks. A study’s range/view survived the
  redirect. Real Caillebotte artist/artwork URLs returned 200 without authentication.
- Opt-in read-only catalogue tests verify the real selected objects, first/next pages,
  cursor/filter isolation, local bookmark scope, and constant query counts: five queries
  for 24 artworks, two for 24 books/events. Observed complete reads were about 9–47 ms.
- Read-only query plans are retained in `query-plans.json`. On this catalogue (roughly
  306,000 estimated artwork rows), representative execution times were 0.43 ms for
  indexed browsing, 12.45 ms for a title search, 2.23 ms for a creator search and 0.10 ms
  for a two-object image lookup. These measurements are not a 10-million-row load test.
- Real browser captures are numbered in this folder. `visual-verification.json`
  records the final populated workspace/mobile accessibility and overflow checks.

## Release boundary

No commit, migration application or deployment was performed. Before a production
release, apply the new migration through the normal release process and exercise
account persistence in staging. The production PostgreSQL mutation path has not been
run against the real read-only local database. Live Google OAuth was reused, not
reconfigured or exercised with a real account. High-concurrency and 10-million-row
capacity tests remain release work.

The original approved mockups remain in `../account-studies-mockups-20261011/`.
