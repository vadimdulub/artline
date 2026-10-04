# Production deployment — 1 October 2026

Live at [artlines.org](https://artlines.org). API revision `artline-api-deploy-1001` and web revision `artline-web-deploy-1001` each serve 100% of normal traffic. The user explicitly requested deployment and added the Books timeline and overlapping year-handle fixes during preparation.

The release includes the All-mode section isolation icons, book covers and selected author portraits, filter/date fitting, and the updated Books display. Books and Authors use timelines for selections of up to 150 entries and galleries for larger selections. Mixed undated entries remain accessible below the timeline; an entirely undated selection uses cards. Gallery pages contain at most 150 records, with three pages mounted. Close year handles separate vertically while retaining their exact horizontal date positions, across Painters, Books, Events and All. Mouse, keyboard and touch remain supported; dragging previews the dates and commits on release.

The web source is the application snapshot validated at the start of this release plus the requested Books and handle changes. Concurrent membership-preview edits made after that snapshot were excluded from the release archive and left untouched in the workspace.

## Images and recovery

| Component | Cloud Build | Immutable image digest |
| --- | --- | --- |
| API | `92185302-f2d1-42b8-8f0f-39a306a4f2db` | `sha256:75042c16e892ebc6fbb6821f1d6dd679ee2a6bdbcc17dd3d4e1d48b6575ddf31` |
| Web | `e29f7a43-4a23-4ebc-9c94-018d9778ffc0` | `sha256:8beea43a8f21af6393925055c31418445ff20e1e0134650cacd03296f23d45b3` |

Both source archives match Cloud Build's SHA-256 provenance. No earlier preparation images were deployed. Each candidate was created with zero normal traffic and checked before promotion. The Cloud Run v2 update used an etag and explicit field mask; full runtime templates were compared before and after. Only the images and revision names changed. Google OAuth settings, secret references, public preview, storage, domain and service settings were preserved. Local ignored Terraform image pins now match the live digests. No Terraform apply or Git commit was performed.

The embedded migrations are identical to the previously deployed API source. This release required no database migration, catalogue publication or ingestion. Real local catalogue checks used read-only connections; no fixtures or test databases were created.

Private configuration snapshots and immutable archives are under `/Users/vadimdulub/Library/Application Support/Artline/backups/production-deploy-20261001/`. API source is in `r2/`; final web source is in `r3/`. Previous revisions remain available:

```sh
gcloud run services update-traffic artline-web --account=vadim@alingva.com --project=artline-508319 --region=europe-west1 --to-revisions=artline-web-privacy-0928=100
gcloud run services update-traffic artline-api --account=vadim@alingva.com --project=artline-508319 --region=europe-west1 --to-revisions=artline-api-google-0930=100
```

Restore the corresponding local Terraform image pins if rolling back. The previous API revision retains enabled Google sign-in.

## Verification

- Go package unit tests passed; the member tests required a rerun outside the sandbox to bind their local HTTP test server. Frontend verification passed: 187 tests, lint, TypeScript and production builds.
- Focused read-only catalogue audits passed for highlights pagination, author visibility/lifespans and matched date extents. The older broad `TestReadOnlyBookCatalogue` audit stopped on its stale assumption that every book remains in review: `wd-q1479512` is now published. This pre-existing catalogue assumption was recorded rather than changing publication data. This is not a full historical integration-suite pass or a capacity benchmark.
- Browser checks passed locally and against the candidate using production data: small book/author timelines, dense galleries, pagination, details, portrait delivery, all three section-isolation controls, independent handles and keyboard operation. Handle checks covered every tab at 1440, 390 and 320 pixels, without horizontal overflow or page JavaScript errors.
- Five mouse/touch regression checks passed across all four screens, including touch cancellation and deferring date changes until release.
- Candidate and canonical API checks passed for health/readiness, bounded All responses, Books display modes, date extents and portraits. Anonymous sessions report Google sign-in enabled and local debug disabled.
- The final canonical-domain browser check passed for covers, book timelines, separate handles, isolate/restore, mobile layout and the Google sign-in button. No new authenticated Google login was performed.
- Final service reads confirmed readiness, unchanged runtime configuration, the exact image digests and 100% traffic. Error-log queries for both new revisions returned no errors during release verification.

Sanitized browser/API checks, source manifests and build results are stored beside this receipt. Disposable scripts and screenshots remain in `/tmp/artline-deploy-20261001/`. The unavailable in-app browser connection was replaced by the project's standalone Chrome/Playwright checks.
