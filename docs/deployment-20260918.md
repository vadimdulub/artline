# Catalogue, Atlas and finished UI release — 18 September 2026

Production: <https://artline-web-lpuqqlugnq-ew.a.run.app>

The latest completed UI is deployed, including responsive year controls,
loading/retry feedback, preserved filters, cancelled superseded reads and equal
All-axis year spacing from 1400 through 2000. Women
artists, Books, Events and the unified All view are present in production. The
user's in-progress UI work was included after its final checks completed.

## Immutable release identity

| Service | 100% traffic revision | Image digest | Source |
| --- | --- | --- | --- |
| API | `artline-api-atlas-0918` | `sha256:f546e77367063eec0eb941a325263b77410e80c2cc2e48a2ea456b189b1cea30` | `dbcaebe` |
| Web | `artline-web-scale-0918` | `sha256:d4a86e56b1001b2fff867e0c7aebeb1dc75cf470ab5b6ab0d62d521299efb234` | `3c8300f` |

Both images are in `europe-west1-docker.pkg.dev/artline-508319/artline`, in the
`api` and `web` packages respectively. Successful builds:

- API: `69392ed0-532b-4224-a568-11069935b09a`.
- Final web: `0cab5c35-36df-49dd-af94-8d7c07c3d6c1`.
- Intermediate responsive UI: `054f74da-45b6-49bc-b8e8-4d23c79ec13a`, source `0cfcc28`.
- Earlier web baseline: `1461064d-1c85-4805-ad1d-1c432c2685ba`, source `1a62f79`.

Builds used isolated `git archive` snapshots, not a changing workspace. The
first web attempt failed because browser-only test fixtures referenced server
files outside the standalone Docker context. Commit `1a62f79` excludes browser
fixtures from that context; TypeScript checks were not disabled. The final UI
build succeeded and was tested at zero normal traffic before switching traffic.

The earlier baseline went live just before the user's reply to wait for new UI
edits. The follow-up release includes those completed edits; it does not leave
production on the earlier snapshot.

## Data and images

Cloud SQL backup `1789759341285` succeeded before production data changes.
Missing Books/Events tables and data were delivered transactionally: 10,000
books, 10,000 events and their supporting creator/discovery records. Two sourced
Woodville review artworks, their existing images and provenance were delivered,
along with 35 additional original source citations. No records were published,
archived records revived, creator biographies inferred or on-view claims added.

The image inventory checked every existing database storage path against local
files and Cloud Storage. The final database recheck additionally verified six
images delivered by the concurrent regional research workflow. **All 80,164
active image paths match verified storage bytes.** Missing withdrawn/rights-held
historical assets were deliberately not restored. Not every artwork in the
catalogue has an image; remote on-demand book covers are a separate manifest.

Final production counts: 264,953 artworks, 13,450 artists, 859 institutions,
80,776 media records, 10,000 books and 10,000 events. The Books UI shows 8,685
date-eligible books; the women-artists filter shows 535 painters.

See [the detailed audit and retained receipts](research/production-release-20260918/README.md)
for exact scope, target-specific evidence differences and historical-record
identity verification.

## Verification

- Go tests and real-local **read-only** Books/Events/Atlas checks passed; no real
  catalogue was used as `ARTLINE_TEST_DATABASE_URL` and no fixtures were inserted.
- 547 existing Python operation tests and six release-audit tests passed.
- Final UI: 45 unit tests, ESLint and TypeScript passed. Its development workflow
  recorded 60 passing browser scenarios, including mobile range interactions.
  The subsequent axis change passed 36 additional read-only browser scenarios.
- Six no-traffic candidate checks and six final public-site checks passed:
  women artists, Books/Events, desktop/mobile All, a real cover with source
  credit, and responsive year controls while a read is pending.
- Twenty-six final public artwork-image responses passed byte checksum/size
  checks, including six newly observed regional images that also received fresh
  file/database/GCS checks. Receipt: `public-images-final.json`.
- Desktop/mobile screenshots were retained; the final phone rendering was
  visually inspected. Final public browser artifacts are under
  `/tmp/artline-scale-release-public/`; candidate artifacts are under
  `/tmp/artline-scale-release-candidate/`.
- The in-app browser runtime failed before initialization with a sandbox
  metadata error. Repository read-only Playwright checks were used after the
  documented browser fallback; no catalogue writes were allowed by release tests.

During heavy provenance scans, API checks hit deadlines on the existing
`db-f1-micro` instance. The failing test artifacts were preserved. The scans were
stopped, and all final candidate/public checks then passed. Routine interactive
traffic and bulk auditing should not share unrestricted scans on this tier.
Capacity changes, sustained concurrency tests and 10-million-row load tests are
not part of this release and remain outstanding.

## Configuration and commits

Only Cloud Run image revisions/traffic and the explicitly reviewed additive
database changes were applied. Runtime secrets, service accounts and private
bucket policy were retained. The ignored local Terraform image pins now match
the deployed API and final web tag `20260918-3c8300f`; format and validation
checks passed. **No Terraform apply was run.** The previous variables file is
backed up under
`/Users/vadimdulub/Library/Application Support/Artline/backups/production-release-20260918/`.

The work is split into museum-query performance, Atlas/Books/Events features,
ingestion tools, research evidence, standalone build packaging, finished UI
interaction fixes, and release auditing/documentation commits. The unrelated
business-plan HTML remains local and uncommitted.

## Rollback

For a web-only rollback, retain the new API/data and restore the tested
responsive-UI revision from before the axis change:

```sh
gcloud run services update-traffic artline-web --project=artline-508319 --region=europe-west1 --to-revisions=artline-web-ui-0918=100
```

The pre-Atlas API revision is also retained for an emergency API rollback:

```sh
gcloud run services update-traffic artline-api --project=artline-508319 --region=europe-west1 --to-revisions=artline-api-museum-directory-0917-v2=100
```

That older API does not provide the new Books/Events/All endpoints. Review the
web/API pairing before using it. Do not delete catalogue additions as part of a
traffic rollback; the migrations are additive. Update local Terraform image pins
to the selected rollback images while preserving unrelated configuration.
