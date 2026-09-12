# GCP deployment and migration — 12 September 2026

Project: **artline-508319**. Region: **europe-west1**. Deployment completed with
Terraform; the final full plan reported **no changes**.

## Follow-up: public research preview

After the initial deployment, the owner requested that the migrated data be
visible on the website. The published-only setting described in the initial
receipt below was replaced by an explicit public, read-only research preview.
`public_research_preview = true` is managed in Terraform for both Cloud Run
services. Go owns access to research reads; editor routes continue to require
the editor token. Record statuses and database contents were not changed.
The web service renders the preview setting at request time, including painter
and museum detail pages, and keeps the review labels visible.

Release `20260912-public-preview-1` updated only the API and web services.
Backend authorization tests and 31 web tests passed. Live anonymous reads
returned 100 popular painters, 5,327 painters with the popular filter disabled,
Giotto with seven works, and 303 museums. Editorial GET and POST requests still
returned 401 without a token. The final Terraform plan reported no changes.

## Follow-up: compact timeline controls

Release `20260912-compact-header-1` moves “Only popular painters” into the filter
row and reduces the desktop header, search, filters and range heading. The dark
timeline fills the remaining desktop viewport; painter lanes scroll internally
while date controls remain visible. Phone filters use a two-column layout.

Two existing discovery/browser tests passed, including responsive painter
details and accessibility checks; lint and the production build passed. Live
Chrome checks at 1024×768, 1366×768, 1440×900 and 2048×1152 confirmed the dark
timeline ends at the viewport edge. Checks at 390 and 320 pixels wide confirmed
no horizontal page overflow. Popular/all views still show 100/5,327 painters;
the live accessibility scan and browser error check were clean.

Cloud Build IDs: web `124959a1-19fb-4bbe-8dbe-df0afd0b3008`, API
`6c40b631-b1c2-4046-856e-446e24763401`. Terraform updated two application images,
with no additions or removals; the final plan reported no changes. Web revision
`artline-web-00003-2km` and API revision `artline-api-00003-jbh` receive 100% of
traffic. Disposable verification artifacts are under `/tmp/artline-compact-header/`.

## Follow-up: selection information icon

Release `20260912-selection-tip-1` removes the filter explanation row and replaces
the separate selection link with a small information icon beside “Only popular
painters”. Its tooltip supports hover, keyboard focus and touch; Escape, blur
and an outside tap dismiss it. Desktop controls now occupy 163 pixels, leaving
the rest of the first viewport for the timeline.

Chrome checks at 1440, 390 and 320 pixels wide verified tooltip positioning,
accessibility, dismissal and that opening the tip does not toggle the checkbox.
Lint passed. Web Cloud Build: `444b41f4-da22-4a1e-89a4-a869729f7bfe`. The API
reuses the prior image under the shared release tag. Verification artifacts
remain under `/tmp/artline-selection-tip/`.
The production build and live browser checks passed. Terraform applied the two
image-tag updates and the final plan reported no changes.

## Follow-up: consistent header across pages

Release `20260912-browse-redesign-1` makes the compact header the shared default,
removing timeline-only sizing overrides. Its 60-pixel desktop height, logo,
navigation and spacing apply to every route. The timeline uses the same height
variable when calculating its available viewport space. Mobile layouts remain
responsive and use identical header dimensions across pages at each width.

Chrome checks compared all nine page types at 1440, 768, 390 and 320 pixels wide,
including museum, painter and artwork detail pages. Header geometry matched
across routes, with no horizontal page overflow or browser errors. Header
accessibility checks passed at all four widths. Verification artifacts are in
`/tmp/artline-shared-header/`.

The release also corrects build ignore rules that excluded `app/coverage/`
along with test coverage output, causing the production Coverage page to return
404. Both Cloud Build upload and Docker context now exclude only `/coverage/`
at the web project root, preserving the application route.

## Follow-up: catalogue browsing and period overview

The same release enables the Catalogue's promised read-only browsing. Go scopes
anonymous reads to published records by default, or non-archived research
records when public preview is enabled. Search, ordering and 50-record UI pages
remain server-owned. Archived records, editor detail reads, coverage summaries
and all mutations still require the editor token. The public Coverage page now
explains its editor-access requirement instead of displaying an unavailable error.

The all-painters view renders the server's bounded period counts as coloured,
clickable bars, with readable counts and keyboard navigation. Colour identifies
periods independently of movement classification. Phones use scrollable
horizontal bars with larger targets. Selecting a period updates the existing
date range; a Catalogue link offers paginated browsing of individual painters.
The search field uses an inset focus line within its row.

Backend read-scope and authorization tests, 31 web unit tests and lint passed.
Browser checks covered period selection, five chart colours, responsive layout,
accessibility, catalogue search and pagination, and contained search focus.
A temporary API used a PostgreSQL connection with transactions read-only and
migrations disabled; no fixtures, test database or catalogue mutations were used.
Anonymous archive searches and editing requests were denied or excluded as
appropriate. Artifacts are under `/tmp/artline-browse-fix/`.

Cloud Build jobs `b1b31abc-3f98-41d8-9345-8d92325dc4c7` (web) and
`21a117d4-bd7f-48b0-8a3b-400c3af4f9e4` (API) succeeded. Live checks passed for
anonymous catalogue pagination/search, mutation and archive protection, coloured
period navigation, search focus, and all nine page types at four viewport widths.
The Coverage page returns 200. The popular-view reload/back/reset regression
test also passed. Terraform changed only the application images; its final plan
reported no changes.

## Live services

- Web: https://artline-web-lpuqqlugnq-ew.a.run.app
- Editorial catalogue: https://artline-web-lpuqqlugnq-ew.a.run.app/catalogue
- API: https://artline-api-lpuqqlugnq-ew.a.run.app
- Cloud SQL: `artline-508319:europe-west1:artline-postgres`, database `artline`.
- Images: `gs://artline-508319-images/assets/`.
- Terraform state: `gs://artline-508319-terraform-state/artline/prod/`.

No custom domain or DNS changes were needed. Google-managed HTTPS is active.

## Preserved data

All **35 public tables, 1,291,719 rows** were copied, including:

| Data | Rows |
| --- | ---: |
| Artists | 5,328 |
| Artworks | 106,350 |
| Artwork location assertions | 106,350 |
| Citations | 255,574 |
| Audit history | 432,880 |
| Import records | 121,360 |
| Research records | 10,324 |
| Media assets | 644 |
| Media rights evidence | 629 |
| Applied schema migrations | 12 |

Every table matched the local catalogue by exact row count and two numeric
checksum sums covering both halves of the MD5 of each canonical JSONB row.
The comparison is independent of row order and was run read-only with UTC
session settings. No table mismatches were found. This is content-integrity
verification, not a load or query-plan benchmark.

All **644 image files, 104,984,001 bytes**, were present locally and matched their
database SHA256 values. Every uploaded GCS object matched its local path, byte
count and MD5. No extra or missing images were found.

No records were published or assigned invented dates. Artist statuses remain
5,327 in review and one archived; all 106,350 artworks remain in review. The
public homepage consequently reports that the first records are still being
reviewed. The owner can open `/catalogue` and enter the editor token. The local
research-preview token is not enabled in production.

The local database and pictures are retained. This was a point-in-time copy;
later local changes are not automatically replicated to GCP.

## Backups and receipts

Local archive:

`/Users/vadimdulub/Library/Application Support/Artline/backups/gcp-migration-20260912/artline.dump`

SHA256:

`1100961ded54f74b8ddda765fc7bdb49b2f098e5c9eabbb8ca0bc475e9a45837`

The archive was restored into an empty cloud database with
`pg_restore --no-owner --no-acl --exit-on-error --single-transaction`, before
starting the API. All 12 existing migration-ledger entries were checked before
startup. Application tables were analyzed after restore; expected permission
warnings skipped Cloud SQL system catalogs. The local database was only read.

Cloud SQL on-demand backup **1789218184605** completed successfully after the
restore and before application launch. Daily backups and point-in-time recovery
are enabled; the instance and Cloud Run services have deletion protection.

Full migration receipts, local/cloud table fingerprints, image manifests,
cloud object metadata, restore helper, HTTP/browser check results, deployed
outputs and the final Terraform plan log are stored in the backup folder's
`receipts/` directory. The backup and receipts have restricted local permissions.
Disposable screenshots and test logs remain under `/tmp/artline-deploy-20260912/`.

## Deployment configuration

The organisation rejects public IAM grants to `allUsers`. Its policy was not
changed. Both Cloud Run services use the supported `invoker_iam_disabled` public
access setting. API editor operations retain application bearer authentication.

The image bucket is private with public access prevention and object versioning.
Only the web runtime receives object-reader access. A bounded image route streams
objects from GCS at their existing `/assets/...` paths, using short-lived runtime
credentials and browser caching. Production container uploads exclude local
images and environment files. The web runtime has no database or secret access.

A dedicated `artline-build` service account reads the regional build-source
bucket, writes Artline container images and emits Cloud Logging logs. The
build-source bucket expires staging objects after 30 days. An initial failed
Cloud Build submission also created the default `artline-508319_cloudbuild`
bucket; it contains build source, not catalogue backups or images.

Release tag: `20260912-1535`.

| Image | Digest | Cloud Build ID |
| --- | --- | --- |
| API | `sha256:e717d0803fdccb59686a20fcd76a9a78dfd24cf47240d618c8392f0e6baf2c3e` | `a4a61c0b-3408-4478-889f-55fecccd52d8` |
| Web | `sha256:c4160bb6c4fa0d55c91c9b103f434ed7d3c95de5b22610a8f5e813e7858a123c` | `ca0b95df-bdd0-46d4-a414-fbbfef7364cd` |

## Validation

- Terraform initialized and validated; final full plan: no differences.
- Both Cloud Build jobs succeeded; Next.js compiled and type-checked the image route.
- Existing 24 web unit tests passed; four additional storage-route tests passed.
- Live API health and database readiness endpoints returned 200.
- Anonymous catalogue and review-preview requests returned 401.
- Authenticated catalogue and Giotto preview requests returned 200.
- Chrome loaded 50 catalogue rows after entering the editor token, with no page
  errors. The token was cleared before closing the test browser.
- The public homepage settled to zero published painters with its review message.
- A 5,582,576-byte Giotto image served through the web endpoint matched the local
  SHA256 and loaded in Chrome. HEAD, ETag/304, missing-image 404 and non-image 404
  behavior also passed.
- The in-app browser connection was unavailable; a local headless Chrome session
  performed the page checks. No real catalogue fixture tests or test databases
  were created.

The initial database uses the existing `db-f1-micro` configuration. Full-history
scans took minutes on this small instance. Production traffic/load testing and
capacity tuning remain separate work; this deployment does not establish
performance at 20,000 painters / 10 million artworks.

## Owner access and later releases

Retrieve the editor token privately:

```sh
gcloud secrets versions access latest --secret=artline-editor-token --project=artline-508319
```

See `terraform/prod/README.md` for build, plan and apply commands. Do not rerun the
initial restore against this populated database. A future domain can be connected
without replacing the catalogue or image bucket.

References: [Cloud Run public access](https://docs.cloud.google.com/run/docs/authenticating/public),
[Cloud SQL restore guidance](https://docs.cloud.google.com/sql/docs/postgres/import-export/import-export-dmp),
[Cloud Build service accounts](https://docs.cloud.google.com/build/docs/securing-builds/configure-user-specified-service-accounts).
