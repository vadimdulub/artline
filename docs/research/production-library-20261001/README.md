# Production library release — 1 October 2026

Live at https://artlines.org. Both services serve 100% of traffic from the verified `library-20261001` release. All pending application changes at capture time were included; every captured application file still matched its SHA-256 after the build. No Git commit or Terraform apply was performed.

## Application images

| Service | Revision | Build | Immutable image |
| --- | --- | --- | --- |
| API | artline-api-library-1001 | 38f869f6-1fa2-4036-8693-516fad4741c0 | `europe-west1-docker.pkg.dev/artline-508319/artline/api@sha256:aadea2c9eb2fa438d5c6dd4726d69918e4c695780ee06fc206d10d08115022db` |
| Web | artline-web-library-1001 | 56626ed8-fcbf-41be-bd83-3427e19c861e | `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:207515480aa39765720ff01d6cc0385c4f78c9cb6386ddededc363994702d25d` |

API source archive SHA-256: `297aff1dbd3648aa14a2bf302584e93fb4c1bd9afb4bb053d5be0e224b7c90f5`. Web source archive SHA-256: `e990942cefbd515ab6bf0632d4c8ebed463af9dd4648c3fd95e4f5b0c9b93820`. Immutable archives, complete manifests, Cloud Build results, prior service configuration, promotion patches, screenshots, and verification receipts are retained privately under `/Users/vadimdulub/Library/Application Support/Artline/backups/production-library-20261001`. Builds used the existing `artline-build` service account.

## Catalogue and images

25 new books reached production: the 19-work [pre-1850 selection](../pre1850-books-20261001/README.md) and six [Byzantine works](../byzantine-books-20261001/README.md). Hexabiblos received its prepared date/highlight correction. Eleven creator records were added. Total books: 10,020 → 10,045; dated pre-1850 books: 2,123 → 2,148; highlights: 206 → 232. The highlighted author view returns all 192 creators. Book of the Eparch keeps its unknown date rather than inventing a composition year.

All new records remain in review and are visible through the existing public research preview. The 34 published books and all unselected book/discovery rows were preserved. Existing creator rows were not rewritten. Broad local/production projection-checksum differences were audited: only the seven prepared Byzantine changes differed semantically before this batch; timestamp/provenance differences elsewhere were preserved.

58 selected reproductions are now served: 17 book images, 25 author portraits, and 16 event illustrations. All live bytes match the selected local files, each under 100,000 bytes (largest 99,738). Date/edition labels, credits, source links, and public-domain declarations remain attached. See the [image research report](../library-illustrations-20261001/README.md).

## Verification

All Go package tests and 192 frontend tests passed. Both production container builds succeeded. Candidate browser checks covered 1440, 390, and 320 px layouts; close date ranges in Painters, Books, Events and All; pointer/keyboard input; touch preview/cancel/commit; complete highlight timelines; and source-linked images. Canonical-site checks repeated the mobile date controls, touch behavior, highlights and images without API interception. Artwork enlargement, isolation, scrolling, reset and overflow checks passed on the candidate and canonical site at all three widths.

Live API checks passed health/readiness, bounded normal book/author pages, dense/individual mode selection, all three All lanes, complete 232-book/192-author highlights, and every selected book’s identity, description and dates. No browser page errors were recorded, and Cloud Run returned no ERROR entries for the new revisions during verification. Production reports Google sign-in enabled, anonymous user, and no local debug/free access. Local debug previews still work on loopback.

Runtime templates and service settings are unchanged except the intended image/revision and traffic changes. The migrations match the preceding release; no new migration was required. Ignored Terraform image pins were updated to these digests. Representative catalogue checks are not a 10-million-artwork load test.

## Backup and rollback

Cloud SQL backup `1790869347953` completed successfully before catalogue writes. The production book transaction required exact preimages, a pinned plan hash, dependency checks, and a successful backup. Its receipt is retained in `books-apply-receipt.json`; the plan SHA-256 is `060a081da36d7b17001a0add4e187487eed44862f265c152a61785cb5109333a`. The reusable delivery script is `ops/deliver-library-books-20261001.py`.

The previous application revisions remain available. To roll back application traffic only:

```sh
gcloud run services update-traffic artline-api --to-revisions=artline-api-deploy-1001=100 --region=europe-west1 --project=artline-508319 --account=vadim@alingva.com
gcloud run services update-traffic artline-web --to-revisions=artline-web-deploy-1001=100 --region=europe-west1 --project=artline-508319 --account=vadim@alingva.com
```

The catalogue additions are compatible with the prior application. Database rollback is a separate, scoped operation using the retained preimages; do not overwrite later catalogue or member changes with a blind full-database restore.
