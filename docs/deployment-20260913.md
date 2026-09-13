# Production release — 13 September 2026

Application commit: `9d2f3b50aae15411d65d40e5dbd97e3672d55834`.
Release tag: `20260913-9d2f3b5`.
Project: `artline-508319`; region: `europe-west1`.

The release corrects timeline period counts to match overlapping painter dates
and adds bounded country/movement suggestions for crowded periods. The commit
also preserves the expanded research commands, schema migrations and evidence.
Research commands were not run as part of deployment.

The commit was pushed to `origin/master` before building. Cloud Build used an
archive of that commit, isolating the release from continuing workspace edits.

| Service | Cloud Build ID | Live revision |
| --- | --- | --- |
| API | `5cd9ba35-2593-4114-9ab7-feb97fa2609b` | `artline-api-00008-vtn` |
| Web | `e6fdec06-3c52-41d4-bb4f-12a22c75a2c8` | `artline-web-00008-f2d` |

Both revisions receive 100% of service traffic. Verified image digests:

- API: `sha256:249f80052b5389c3bebf1b3ccbb1e3f76026f822d645fe4ef9820841959b03d6`
- Web: `sha256:4a0639dea1984dd5d630e8627ba875034ca618e12f06004349c5dbe685d5f401`

Terraform applied only the two application-image updates: zero additions,
two changes, zero removals. The final full plan returned exit code 0 and no
changes. A read-only production check confirmed migrations 0001–0018 were
already applied, so this release had no pending schema migrations.

## Verification

- Go package tests passed with fixture-database opt-ins unset.
- Read-only local timeline checks passed, including count equality, suggestion
  bounds, and query-plan checks with an in-query 20,000-painter fixture.
- All 32 web unit tests and ESLint passed.
- All 41 research-tool tests passed against the committed source snapshot.
- Both Cloud Build production builds succeeded.
- All 11 discovery/crowded-period browser regressions passed locally and on
  production, including accessibility, desktop/phone layouts, history,
  filtering and artwork-image viewing.
- Live API smoke checks passed for health, database readiness, period count
  equality, suggested counts, response bounds and unauthenticated editor access
  protection. The popular view returned 100 painters; 1900–1909 returned 4,000.

These checks are not evidence of 10-million-artwork capacity.

## Open finding: museum directory timeout

Post-deployment log inspection and a direct request found that
`GET /api/v1/museums` can exceed its eight-second request deadline and return
500. The `/museums` page itself returns 200, so page-status checks alone do not
validate its data load. The museum query and handler code were unchanged by
this release.

Read-only production timings observed about 9.7 seconds for the directory count,
6.2 seconds for the first 24 cards, and additional facet-query time. A regional
directory check exceeded the diagnostic timeout. These are diagnostic
observations on the current shared-core database, not stable benchmarks or a
confirmed root cause. Query-plan optimization and further load investigation
remain necessary; the request deadline was not increased.

Disposable build, Terraform and browser artifacts are under
`/tmp/artline-release-20260913/`. Saved Terraform plans are private and must not
be committed. Later research edits in the active workspace are outside this
release snapshot.

Live site: https://artline-web-lpuqqlugnq-ew.a.run.app
