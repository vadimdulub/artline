# Museum-directory API release — 17 September 2026

Final result: revision `artline-api-museum-directory-0917-v2` serves 100% of API
traffic. All 50 final live checks passed; API and web-proxy payload hashes match.
The temporary candidate tag was removed. See `release-summary.json`,
`final-api-public.json`, `final-web-public.json`, and `after.json`.

Scope: fix production museum-directory timeouts, including Dutch/German country
filters. No artwork/content writes, publication changes, web deployment, Git
commit/push, or Terraform apply are part of this release. One additive covering
index and its migration-ledger entry were applied separately from the API image.

## Cause and change

The old directory materialized membership across the artwork catalogue four
times per request. Country/name predicates did not bound that work. Selective
artist/movement/curation filters also started from holdings rather than selected
artwork IDs. Cards repeatedly read and checked the same museum works.

The new implementation:

- Uses correlated indexed existence checks for directory membership and facets.
- Resolves selected artwork IDs first for artist, movement, and curation filters.
- Builds cards only for the bounded institution page. Each card retains a narrow
  institution-scoped relation for counts and cover selection; only the chosen
  cover receives full artwork/media/creator enrichment.
- Keeps incoming loans separate from holdings, deduplicates card memberships,
  and retains existing creator visibility, rights, fresh display evidence,
  conflicts, active-source, preview, and publication policies.
- Keeps the eight-second request deadline and existing response schema.
- Adds `artworks_museum_card_covering_idx` (about 31 MiB at current scale) so
  large cards do not read wide artwork heap pages for the few fields they need.
  Index 0023 was created concurrently, verified valid/ready, and recorded in the
  migration ledger without running unrelated pending migrations. Ordinary
  `VACUUM (ANALYZE) artworks`, never `FULL`, refreshed the visibility map after
  recent imports so PostgreSQL can use index-only scans.

## Verification and evidence

- `baseline-public.json`: both single-museum searches returned HTTP 500 after
  about 8–9 seconds before deployment.
- `candidate-public.json`: the first candidate was **not promoted**. Specific
  Dutch/German searches passed, but broader views and filters still timed out.
- `candidate-1-*`: source/build evidence for that zero-traffic candidate.
- `production-api-public.json`, `production-web-public.json`: pre-index paired
  production checks. Both exposed one remaining highlights-plus-artist timeout;
  these failures are retained rather than overwritten by final verification.
- `index-local-applied.json`, `index-cloud-applied.json`: exact additive index
  definitions, validity/size, migration checksum, and maintenance receipts.
- `release-source.json`: final source manifest, compared file-for-file against
  the prior production release. Production code changes are confined to
  `apps/server/internal/catalog/museums.go`; the other changes are two tests.
- `local-baseline/`, `local-readonly/`: real-catalogue plans and complete-response
  comparisons. All database probes use read-only repeatable-read transactions;
  they do not use `ARTLINE_TEST_DATABASE_URL`, create fixtures, or write rows.
- `cloud-unfiltered/`, `cloud-maximum/`, `cloud-movement/`, `cloud-owner/`:
  read-only production query plans for default/maximum pages and selective filters.
- `cloud-selection-artist-indexed/`: the final combined-filter card plan uses
  `artworks_museum_card_covering_idx` with zero artwork heap fetches. The final
  live combined-filter request took approximately 1.2 seconds.
- `before.json`, `candidate.json`, and final snapshots: sanitized service images,
  traffic, and runtime-configuration fingerprints. No credentials are recorded.

The source starts from production commit
`f30681bffe477c948cdb1272c949ae4ba1dcf109` and retains the already-deployed
16 September artwork-detail fix. Unrelated books, frontend, ingestion and other
workspace changes are excluded. `museum-api-cumulative.patch` includes that
previous detail fix as well as this directory fix.

The additive index is delivered by
`apps/server/db/migrations/0023_museum_directory_covering_index.sql` and the
scoped `ops/apply-museum-directory-index.py` workflow, independently of the
unchanged final API image. A deployment rollback can retain this compatible
index; no catalogue-record rollback is necessary.

## Limits

These are bounded functional and query-plan checks against approximately 265,000
real artworks, not a 10-million-row or sustained-concurrency capacity test.
Fixture-writing integration tests remain opt-in and were not run against the
real catalogue. Existing live data has no accepted currently-on-view examples;
the retained evidence predicates are guarded by source-level regression tests,
but synthetic positive/conflicting-display fixtures were not inserted.
The heaviest final movement-filter request took approximately 5.4 seconds during
paired API/web checks; large-scale/concurrent performance is not claimed solved.

The first Cloud Build submission used the default staging bucket, which the
existing build service account could not read. Subsequent builds used the
project's configured `artline-508319-build-source` bucket. No IAM permissions
were broadened.
