# Museum artwork detail performance release — 16 September 2026

Museum artwork details previously enriched all candidates in a collection before selecting the requested work. On the current catalogue, the sampled NGA and Met requests took 5.1 and 6.6 seconds and had previously timed out during ingestion. The API now resolves the artwork UUID first, preserving the complete response, holding checks, image rights and review visibility.

The API revision `artline-api-museum-detail-0916` receives **100% of production traffic**. The web service, database schema and editorial states were unchanged.

| Museum | Before: API, seconds | After: API median | After: live-site median |
| --- | ---: | ---: | ---: |
| nationalmuseum-stockholm | 1.196 | 0.173 | 0.177 |
| national-gallery-of-art | 5.118 | 0.090 | 0.111 |
| the-met | 6.552 | 0.089 | 0.105 |
| smithsonian-american-art-museum | 0.823 | 0.087 | 0.103 |

Measurements use one baseline request and three post-release requests per museum. These are bounded verification samples, not load-test results.

Release evidence:

- [Release summary](research/api-museum-detail-deploy-20260916/release-summary.json)
- [Exact source patch](research/api-museum-detail-deploy-20260916/museum-detail.patch)
- [Source manifest](research/api-museum-detail-deploy-20260916/release-source.json)
- [Test and Linux-build evidence](research/api-museum-detail-deploy-20260916/validation.json)
- [Production API checks](research/api-museum-detail-deploy-20260916/production-api-public-check.json)
- [Live-site checks](research/api-museum-detail-deploy-20260916/production-web-public-check.json)
- [Final traffic and configuration](research/api-museum-detail-deploy-20260916/production-final.json)
- [Terraform plan summary](research/api-museum-detail-deploy-20260916/terraform-plan-summary.json)
- [Release error-log check](research/api-museum-detail-deploy-20260916/post-release-error-check.json)
- [Cloud Build](https://console.cloud.google.com/cloud-build/builds/e688bc31-7f0e-458a-ab6c-8310af48e1a5?project=995787188464)

The release used an isolated archive of production commit `f30681bffe477c948cdb1272c949ae4ba1dcf109`, plus the previously reviewed museum detail patch and its read-only test. Unrelated workspace changes were excluded. No commit or push was made.

Image digest: `europe-west1-docker.pkg.dev/artline-508319/artline/api@sha256:14ba419993809d3276ddc9264d4d3a57b87d8afec83657bacbaa56595a866098`.

Validation passed: catalog and HTTP API tests, full-response equivalence in a read-only local transaction for Met/NGA/SAAM, UUID-index query plans, 24 repeated repository calls, a Linux build, 16 staged requests and 30 production requests. Invalid UUIDs and an unrelated museum correctly return 404. The real catalogue received no test fixtures or writes. The initial broad test attempt could not run ingestion tests in the isolated server export because their external research fixtures were not included; it is not reported as a passing full-server suite.

The optional `api_image` Terraform variable now supports an API-only digest pin while retaining `image_tag` as the backward-compatible fallback. Local production variables pin this release; the web remains on `20260915-f30681b`. Terraform formatting and validation passed. A read-only plan confirms both image choices; remaining proposed changes only normalize CLI client/revision metadata. No Terraform apply was performed.

The pre-release Terraform variables backup is under `~/Library/Application Support/Artline/backups/api-museum-detail-deploy-20260916/`. Temporary builds, test logs and the sensitive Terraform plan remain outside the repository.

Immediate traffic rollback:

```sh
gcloud run services update-traffic artline-api \
  --project artline-508319 --region europe-west1 \
  --to-revisions artline-api-00013-8hw=100
```

After a rollback, also restore the previous API image pin before any future Terraform apply. The previous image digest is recorded in the source manifest. The previous revision was retained; the temporary staging tag was removed after successful production checks.
