# Production application deployment — 28 September 2026

The latest working application is live at [Artline](https://artline-web-lpuqqlugnq-ew.a.run.app). API revision `artline-api-deploy-0928` and web revision `artline-web-deploy-0928` each receive 100% of their service traffic. This deployment was explicitly requested by the user.

The new account page and Google identity integration are included. Production has no Google OAuth credentials configured, so the account page correctly shows “Google sign-in is coming soon” and the session endpoint returns `enabled: false`. A real Google sign-in was not tested or enabled. Existing artwork collections, private image delivery, editorial protection and research-preview configuration remain intact.

## Release and recovery

| Component | Cloud Build | Deployed digest |
| --- | --- | --- |
| API | `fc16f6a6-67f8-4ca4-b547-5932cf2c63ef` | `sha256:85944159f1559a68fae79445b3b4fed06caa0497d3cb95494db3a74de03d0ee9` |
| Web | `1dfe3c46-d912-4792-a59f-02c2649f9248` | `sha256:057552791a18d14dcf3b7fac177599ae6be8ded43c323f8985ddff47be84273d` |

Immutable source archives were checked against Cloud Build's SHA-256 provenance. Both production builds succeeded. Existing runtime configuration was compared before and after deployment and is unchanged apart from the container images. Local Terraform image pins were synchronized; no Terraform apply, infrastructure changes or commit was performed.

Cloud SQL backup **1790603928092** completed successfully before deployment. The API startup migration runner applied only `0032_member_accounts.sql`, in its normal transaction under an advisory lock. Both new tables were verified empty, with all five expected indexes. No artwork rows, publication statuses or local database records were changed.

The first build submission failed because the CLI selected its default source bucket. Retrying with the project's existing authorized `artline-508319-build-source` staging bucket succeeded; no IAM changes were made.

Private service configurations and source archives are under `/Users/vadimdulub/Library/Application Support/Artline/backups/production-deploy-20260928/`. Previous revisions remain available for an application rollback:

```sh
gcloud run services update-traffic artline-web --project=artline-508319 --region=europe-west1 --to-revisions=artline-web-starting-0928=100
gcloud run services update-traffic artline-api --project=artline-508319 --region=europe-west1 --to-revisions=artline-api-starting-0928-r2=100
```

The additive member tables can remain in place during an application rollback.

## Verification

- All Go package tests, 184 frontend tests across 19 files, lint and production container builds passed. Database integration tests were not pointed at the real catalogue, and no test fixtures were inserted.
- Candidate API checks passed for health, database readiness, disabled member sessions, unauthorized editorial access, and all 31 historical starting points. Each artwork response was bounded to 150 items, contained image references, and respected the 1970 creation cutoff. Decolonisation retains 104 artworks, 9 books and 9 events.
- Candidate and canonical production browser checks passed at 1440 px and 390 px. The account page, session proxy, navigation, all 31 topic covers, Decolonisation gallery and illustrated Hood Museum artwork details worked without browser errors or page overflow. No “In review” label appeared.
- Final service reads verified the exact image digests, readiness and 100% traffic. Canonical API health, readiness and session checks passed. These are release checks, not a 10-million-row load benchmark.

The in-app browser connection failed at the tool boundary; background standalone Chrome/Playwright provided the browser checks. Disposable screenshots and smoke scripts remain under `/tmp/artline-deploy-20260928/`.

Machine-readable receipts in this directory include source manifests and uploads, build provenance, the SQL backup and schema verification, candidate checks, traffic switches, final service state, canonical browser/API checks and the revision error-log check. Full private service configurations are retained only in the backup directory.
