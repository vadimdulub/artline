# SEO release — 20 September 2026

Deployed after the owner's explicit instruction, “deploy this is ok”.

Live website: <https://artline-web-lpuqqlugnq-ew.a.run.app>

Live sitemap: <https://artline-web-lpuqqlugnq-ew.a.run.app/sitemap.xml>

## Deployed revisions

Both services have 100% normal traffic on the tested SEO revision.

| Service | Revision | Image digest | Cloud Build |
| --- | --- | --- | --- |
| API | `artline-api-seo-0920` | `sha256:5aaa0bb084f2a5d0416344a6b49fb0e0ca13cab5270139724f07468ffc2b3252` | `e0c6d91f-3ab4-4c7f-8d52-79dd3357a75e` |
| Web | `artline-web-seo-0920` | `sha256:5682a36efdb86fbfcbbccc45588abfabd0207dc040f36a50ffb492a5337ef3a6` | `21d3eecd-68b9-47dc-87e1-847920943e2c` |

Images are under `europe-west1-docker.pkg.dev/artline-508319/artline`, tagged
`seo-20260920-1420`. Cloud Run revisions use the immutable digests.

Release contexts were reconstructed from the actual deployed Cloud Build source
archives, then overlaid with the SEO files recorded in `release-source.json`.
The API baseline was build `16cd40a2-3dc5-44bb-8c94-3b31a4d85d6d`
(`artline-api-images-0920`); the web baseline was build
`0cab5c35-36df-49dd-af94-8d7c07c3d6c1` (`artline-web-scale-0918`).
This preserves the already deployed image-visibility changes while excluding
unrelated unfinished Atlas, UI and research changes from the local workspace.
No commit was made.

Cloud Build uploads contained 296 API files and 122 web files. They excluded
local environment files, dependencies, build output, browser artifacts and
artwork images. Existing artwork assets were served from the current bucket;
no image or catalogue ingestion was performed for this deployment.

## Database and visibility

Cloud SQL backup **1789914194416**, “Before SEO deployment 20260920”, completed
successfully before the candidate API started its migration.

Only `0026_search_discovery_indexes.sql` was newly applied. All four indexes
were verified valid with read-only queries:

- `artists_published_seo_id_idx`
- `artists_published_seo_slug_idx`
- `artworks_published_seo_id_idx`
- `institutions_published_seo_id_idx`

Migration 0025 was already in the production ledger before this release; it was
not added to this release context or executed by this deployment.

The before/after production checks found zero published artists, artworks and
institutions. Public research preview remains enabled on both services. Review
pages and editorial tools carry `noindex`; the sitemap currently lists `/about`
and `/artists`. Approving and publishing catalogue records remains a separate
editorial action. No records were published or changed by this release.

`ARTLINE_SITE_URL` explicitly uses the existing Cloud Run origin until a custom
domain is purchased and connected. DNS, domain ownership and Google/Bing account
verification or sitemap submission have not been performed.

## Verification and rollout

- Isolated release: frontend lint, 56 unit tests and production build passed.
  This count excludes tests for unrelated unfinished workspace changes.
- Go catalogue, HTTP and Atlas test packages passed with
  `ARTLINE_TEST_DATABASE_URL` unset.
- Both Cloud Build jobs succeeded.
- API candidate at zero normal traffic: six HTTP checks passed, including
  health/readiness, published-only discovery, a bounded sitemap range and an
  existing review artist. The four new indexes and unchanged publication counts
  were verified through read-only database access.
- API traffic was promoted after those checks; its interface remains compatible
  with the previous web revision.
- Web candidate at zero normal traffic: four browser tests and four direct HTTP
  checks passed. The tests verify robots/sitemaps, canonical origin, review and
  editorial exclusions, complete artwork text with JavaScript disabled, a
  legacy-link redirect, missing-work 404, server-rendered museum identity, and
  artwork navigation with updated title/canonical metadata.
- Web traffic was promoted, and the same four browser checks passed on the
  public origin. Final service reads confirmed both revisions at 100% traffic.
  Public robots and sitemap documents returned 200 with valid XML and canonical
  URLs; the public discovery API still returned the empty published directory.
- Terraform formatting and validation passed. Local ignored image pins and the
  canonical origin were updated after release. No Terraform apply was run.

Recovery sources, before/after configuration, backup receipts, migration checks
and release manifests are retained under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/seo-release-20260920-1420/`

The configuration backups contain secrets and must remain private. Browser
artifacts are under `/tmp/artline-seo-release-20260920T142040Z/`; they are not
stored in Documents. Query-scale limitations and future publication/domain work
are documented in [the indexing guide](seo-indexing.md).

## Rollback

The immediately preceding production revisions remain available. Restore traffic
without deleting catalogue data or undoing additive indexes:

```sh
gcloud run services update-traffic artline-web --project=artline-508319 --region=europe-west1 --to-revisions=artline-web-scale-0918=100
gcloud run services update-traffic artline-api --project=artline-508319 --region=europe-west1 --to-revisions=artline-api-images-0920=100
```

Update local image pins if a rollback is performed. The prior API image is
`sha256:f762596ec37fa753c5d56ae0ce96634320ecdb1b4597e35ac00b4f03f8fb3350`;
the prior web image is
`sha256:d4a86e56b1001b2fff867e0c7aebeb1dc75cf470ab5b6ab0d62d521299efb234`.
