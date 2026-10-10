# Bookmarks, mobile navigation and timeline filters — 10 October 2026

The release is live at https://artlines.org. API revision
`artline-api-all-1010-099e008` and web revision
`artline-web-all-1010-099e008` each serve 100% of public traffic.

Source commit: `099e008ae609edc26578e0fa7fa366935cc8c706`, pushed to
`origin/master`. The commit contains the pending application changes, research
reports, operations scripts and public image assets present when the release
snapshot was taken. Both Cloud Build uploads were extracted from that commit.
Other work continued editing the shared directory afterward; those later edits
were preserved and are outside this release.

Suggested filters now preserve the selected years on painter and event
timelines, including suggestions opened through crowded columns or the painter
index. The release also includes private artist/artwork bookmarks, museum
sign-in controls, retained sign-in destinations, mobile navigation and layout
improvements, source/image evidence and research tooling. Artist and individual
artwork pages remain public. Local-debug bookmarks remain ephemeral.

## Build and rollout

| Service | Successful Cloud Build | Container digest |
| --- | --- | --- |
| API | `3bd747ae-70ef-4b18-b02b-f9edfbcd0204` | `sha256:f868d1767affb590be1fbf9781b331bd96278bcd51a93620b59ff22fb9c2e75a` |
| Web | `a57991de-bae7-4f77-ae39-fee2b36d5922` | `sha256:964f2f02e859470f16d401b98dcd1cba74075924534142b9ecb1f9eb9ad401fd` |

Cloud SQL backup `1791631546053` completed successfully before the API candidate
was started. The API startup migration runner completed with migration
`0043_member_bookmarks.sql` included; this additive migration creates the two
bookmark tables and their indexes. No catalogue imports, account/session
fixtures or bookmark fixtures were created. The real local database was not
modified.

Both revisions were first deployed with zero public traffic. After candidate
checks passed, the API was promoted, followed by the web. Before/after service
comparisons verified unchanged runtime specifications and template annotations:
environment variables, secret references, service accounts, resource limits,
scaling, concurrency and networking were preserved. No Terraform apply or IAM
change was performed. The ignored local Terraform image pins were updated to
the deployed digests.

## Verification

- All 315 web unit tests and web lint passed. Both production container builds
  succeeded, including the Next.js production build and type checking.
- API/member race tests passed. The remaining Go suite passed with the five
  archive-dependent tests listed below excluded. Database fixture tests were
  not enabled.
- Eleven candidate API checks passed: health, readiness, anonymous production
  session, museum and bookmark authentication, public artist/artwork access,
  both timeline ranges and books.
- Six candidate web HTTP checks passed, including public artwork rendering and
  destination-preserving redirects for signed-out museum/bookmark browsing.
- Five controlled browser regressions passed against the candidate: event
  suggestion buttons/columns and painter suggestion buttons/columns/index.
- Five additional candidate browser checks and the same five public-domain
  checks passed using real catalogue reads: event/painter suggestion counts and
  retained years, reload/history, public artwork and bookmark sign-in at
  1440/390 px, and museum sign-in from mobile navigation. Sign-in image delivery
  was checked on the public site; mobile screenshots were inspected.
- Ten final public-domain HTTP checks passed. Control-plane checks confirmed
  both expected revisions serving 100% traffic.

The initial full Go run could not complete these older ingestion tests because
their archived research JSON inputs are absent from the working tree:
`TestContinuationPinsAndRollbackReplay`, `TestEuropeanCatalogueEvidenceAndCutoff`,
`TestEuropeanDeepSnapshot`, `TestNGACatalogueEvidence`, and
`TestRussiaItalyEvidenceRollbackReplay`. This is retained as a validation
limitation, not reported as an all-green full Go run. No real Google login or
production bookmark write was performed during verification. These checks are
functional spot checks, not load-capacity measurements.

## Rollback and evidence

Previous API: `artline-api-performance2-1009-0850`.
Previous web: `artline-web-performance2-1009-0850`.
Restore the previous web traffic first, then the API. The additive bookmark
tables can remain in place; no database rollback is required for the previous
application versions. No rollback was performed.

Machine-readable receipt: [deployment-20261010-all-changes.json](deployment-20261010-all-changes.json).
Private build records, backup receipt, service snapshots and HTTP/browser
verification evidence are retained under
`/Users/vadimdulub/Library/Application Support/Artline/backups/release-all-20261010/`.
