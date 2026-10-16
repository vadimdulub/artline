# Research studies · local revision, 11 October 2026

Production release, including the revised **Your own** form: [deployment receipt](../../deployment-20261011-studies.json).
The notes below describe the preceding local revision.

The user requested a research-only workspace, removal of the Workflow selector
and local-preview status line, and a practical library for people with many studies.

Local preview: <http://127.0.0.1:3111/studies>.

## Result

- All new studies are research studies. Creation asks only for a title. Teaching
  and Exhibitions choices, role-specific guidance and local-preview messages have
  been removed from the library, workspace and settings.
- A compact study library shows titles, record counts and last-updated dates.
  Search by title, sort by recent activity or title, and navigate 24 studies per
  page. Search and sort survive reloads and are retained through server sign-in.
  Paging scrolls to the beginning of the new results.
- Each study retains its own artwork, book and event references, notes, timeline,
  gallery and two-artwork comparison. Compare and Export are now in the workspace
  header, including on phones. The searchable, filtered Add dialog is unchanged.
- Member-only access to Studies and Bookmarks remains enforced. Local debug retains
  its loopback safeguards and ephemeral storage; its implementation status is not
  displayed in the research interface.

## Backend and limits

The account limit is now 1,000 studies, with 200 records per study. Go and PostgreSQL
own title search, counts, sorting and pagination. The browser receives at most 24
study summaries; it never loads the account's complete library to filter it.

Pagination uses updated time plus UUID, or lower-case title plus UUID. Cursors are
scoped to the member, query and sort. Searches treat percent, underscore and backslash
characters literally. Counts and queries are scoped to one member. Record documents
are inspected for counts only on the returned page. The existing recent-activity
index and the new member/title index support the two ordering paths.

New studies default to research. Creation and updates reject other modes. Legacy
role values are retained in storage for compatibility and have no effect on the UI;
no historical documents are rewritten to remove them. The existing, unapplied
`0045_member_studies.sql` includes the additional title index.

## Verification

- Go member, HTTP and catalogue packages pass with race detection.
- New backend tests traverse 157 studies with repeated title/date keys in both
  sort orders, check literal search and counts, reject invalid or cross-account
  cursors, and exercise the 1,000-study account bound and Unicode title length.
- All nine browser scenarios pass. The new scenario creates 31 ephemeral studies,
  checks search, sorting, next/previous pages, reload, renaming, empty results,
  390/320px layouts and accessibility, then removes its temporary studies.
- Five study proxy/input unit tests pass. TypeScript, focused ESLint and the
  production Next build pass. The final library refinement was separately retested.
- Desktop and mobile captures are retained here. `visual-verification.json` records
  accessibility, overflow and browser errors from the final populated preview.
- Existing catalogue query-plan evidence and authentication verification remain
  in `../studies-implementation-20261011/`. The new PostgreSQL library path awaits
  staging persistence and index-plan verification because the new table has not
  been created locally. This is not a million-row or high-concurrency load test.

## Local-only boundary

The preview uses web port 3111 and API port 8085. The API starts with
`-skip-migrations`, `ARTLINE_LOCAL_DEBUG=true` and PostgreSQL
`default_transaction_read_only=on`. The example research projects contain authentic
catalogue references and explicit personal source links, solely in API memory.
They disappear when that API restarts. No real database fixtures, account rows,
catalogue changes, migrations, commits or deployment were made.

## Possible professional additions

1. Folders, tags and pinned studies for larger research libraries.
2. Image annotations and synchronized zoom for close visual comparison.
3. Formatted bibliographies and citation-manager exports.
4. Links between studies and notes identifying supporting or conflicting evidence.
5. Shared studies with comments, access roles and revision history.

These are proposed additions, not implemented features of this revision.
