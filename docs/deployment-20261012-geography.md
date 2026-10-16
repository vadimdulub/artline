# Geography optimization deployment — 12 October 2026

Deployed and verified on `https://artlines.org`. The API sends 100% of
traffic to `artline-api-geography-1012-v1`. The web service was not redeployed.

Only the reviewed `internal/atlas/geography.go` and
`internal/atlas/repository.go` changes were added to the exact previous
release. The build verified both source preimages and the overlay hashes.
Unrelated workspace museum changes were excluded. Cloud Run resources,
pool/admission limits, secrets, scaling and access settings were preserved.

No schema migration, catalogue source changes, real local database access,
Terraform apply or commit was performed. The local Terraform API image pin
was updated to the deployed immutable digest.

## Live checks

The candidate returned identical complete responses to the old release
for nine selections, including Romanticism, selected Monet, broad All,
empty results and country/continent combinations. Japan and France also
matched on their next pages, with stable totals/density and no repeated IDs.
Painters, Books and Events returned 200; signed-out museums retained 401
and an invalid date range retained 400.

Observed HTTP response times in seconds. The first two columns used
150-item requests against the old/new API revisions; all listed requests
reported cache misses. Public verification used 149 items to obtain fresh
response-cache keys without flushing caches or changing the date range.
These samples include network/HTTP overhead and are not p95 or load tests.

| Selection | Previous API | New API | Public site | Public cache |
| --- | ---: | ---: | ---: | --- |
| Japan | 4.916 | 0.837 | 0.484 | MISS |
| France | 3.619 | 1.903 | 0.591 | MISS |
| Asia | 3.324 | 0.779 | 0.363 | MISS |
| Europe | 3.680 | 2.011 | 2.006 | MISS |
| Japan or France, intersect Asia | 3.486 | 0.812 | 0.788 | MISS |

Public checks also covered Romanticism and broad All, repeated requests
and country pagination. All public requests returned 200. The release log
query returned no error, HTTP 5xx or deferred-refresh entries at verification.
Europe remains the largest measured geographic case; the change does not
claim sub-second behavior for every selection. Presets, highlights and
narrower selections retain their existing query path.

## Release record

- Build: `6f095e8e-687a-4134-9592-0a3a8738f522`.
- Image: `europe-west1-docker.pkg.dev/artline-508319/artline/api@sha256:3ba760726eb30847be67a019184f263bc7793ca3c016f64044795e0db0ab9a45`.
- Previous/rollback revision: `artline-api-atlas-browse-1012-v1`.
- Verification: `2026-10-12T17:22:09.378674+00:00`.
- [Machine-readable release record](deployment-20261012-geography.json).
- [Implementation and prior tests](performance-20261012-geography-optimization.md).

The rollout was first checked on a tagged revision with no public traffic.
After successful comparison it was promoted to 100%, then checked through
the public web proxy. The previous revision remains available for rollback.

Detailed build inputs, hashes, service snapshots, HTTP responses/headers
and verification scripts are archived outside Documents at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/geography-deployment-20261012/`
