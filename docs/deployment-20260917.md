# Museum-directory production release — 17 September 2026

Production API revision `artline-api-museum-directory-0917-v2` serves 100% of
traffic. Dutch and German museum listings return successfully: 9 Dutch and 22
German catalogue institutions. This is current catalogue coverage, not a claim
of exhaustive national coverage.

The release scopes membership/filter work before enrichment and reuses narrow,
institution-scoped data for museum card counts and covers. A concurrently built
covering index removes wide artwork-row reads. Ordinary `VACUUM ANALYZE` enabled
index-only scans after recent imports. The eight-second API deadline is unchanged.

## Verification

- 34 complete old/new response comparisons passed, including filters, facets,
  counts, preview visibility, 24/60-item pages, and keyset pagination.
- Catalogue and HTTP API package tests passed. Read-only artwork-detail
  regressions for the Met, NGA, and SAAM passed.
- 25 no-traffic candidate HTTP checks and 50 final live API/website checks passed.
- The paired checks initially exposed an additional combined-filter timeout;
  after the index fix that request returned in approximately 1.2 seconds.
- Read-only production plans confirm the large-card query uses the covering
  index with zero artwork heap fetches. Broad movement filters can still take
  several seconds; sustained-load and 10-million-row tests remain outstanding.

## Release identity and scope

- Image: `europe-west1-docker.pkg.dev/artline-508319/artline/api@sha256:0a9c95ba704c3d224a9044aa9d3c47e4c9077fd0a8756d692e8d5fd52fa2356e`
- Cloud Build: `420b0a9d-b02f-4853-aa41-f1d614de54a0`.
- Source: production commit `f30681bffe477c948cdb1272c949ae4ba1dcf109`, retaining
  the previously deployed artwork-detail fix, plus the reviewed directory patch.
  Unrelated workspace changes were excluded from the isolated build.
- Additive migration `0023_museum_directory_covering_index.sql` was applied
  independently, concurrently, to local/production databases. Only this index
  and its migration-ledger entry were added; unrelated migrations were not run.
- Artwork data and publication states are unchanged. No test fixtures or test
  databases were created. Web deployment and runtime settings are unchanged.
- The local Terraform API image pin was updated; web keeps `20260915-f30681b`.
  Terraform validation/format checks passed; no Terraform apply was run.
- No Git commit or push was performed for this release.

Evidence, including earlier failed checks, is retained in
[the release audit](research/api-museum-directory-deploy-20260917/README.md).
The variables backup is under
`/Users/vadimdulub/Library/Application Support/Artline/backups/api-museum-directory-deploy-20260917/`.

## Rollback

Route API traffic back to the prior production revision:

```sh
gcloud run services update-traffic artline-api --project artline-508319 --region europe-west1 --to-revisions artline-api-museum-detail-0916=100
```

The additive index is backward-compatible and can remain in place. If rolling
back, also restore the prior API image pin from the variables backup, preserving
any subsequent unrelated configuration changes. No catalogue-content rollback
is needed.
