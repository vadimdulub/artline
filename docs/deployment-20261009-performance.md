# Performance deployment — 9 October 2026

API revision `artline-api-performance-1009-0730` serves 100% of production
traffic at https://artlines.org. It contains application commit `b48c888`
(including `e94325e`). The web revision remains
`artline-web-unified-catalogue-1008-1955`; its runtime and traffic are unchanged.

The release adds bounded catalogue work, revision-aware public record/facet
caching, batched influence citations, smaller public citation payloads, a compact
title-search projection, museum facet improvements and indexed artist holding
summaries. See [implementation details](performance-fixes-20261009.md).

All active records remain visible. Historical statuses, source links, qualified
attributions, unknown dates, archived exclusions and member controls retain
their semantics. No source records or real local catalogue data were rewritten.

## Release evidence

- Cloud Build: `07740c97-7c75-4720-a119-ee636a00042c`, successful on Go 1.24.
- API digest: `sha256:5842161a3ff832fed137a1cd0f31973e6712d1130d3f9ec92dd0bf4292ba43b5`.
- Prepared source SHA-256:
  `04cefe5c906aaf255fbebcba886d0aeb2c11d9bb7801ac46303380768078b06d`;
  verified against Cloud Build source provenance.
- Cloud SQL backup `1791528316434` completed successfully before migrations.
- Migrations 0040–0042 are applied. All six new indexes are valid. The search
  projection contains 414,699 records, including 414,213 active records; an
  exhaustive read-only field comparison found zero mismatches. Its foreign key
  and maintenance/invalidation triggers are enabled.
- The first projection installation attempt was cancelled and fully rolled
  back. The final installation completed in one transaction. The summary
  indexes were built concurrently; one invalid index from a lock-timeout
  attempt was removed and rebuilt successfully. Catalogue records were not
  used as test fixtures.
- Existing API environment, secrets, IAM, networking, scaling and resource
  settings were preserved. The ignored local Terraform API image pin was
  synchronized; no Terraform apply was run.

## Checks and measured results

All Go packages and the catalogue/HTTP race tests pass. Read-only local and
production comparisons verify results, pagination, museum choices, public
metadata and 40 batched influence citation sets. Forty candidate API checks
passed, including review-record visibility, SEO entries and anonymous access.

Browser follow-up verified the desktop/mobile artist gallery, loaded images,
legacy-parameter redirects and indexable metadata. Seven further checks passed
for the anonymous review artwork API, complete artwork rendering without
JavaScript, clean URLs, robots/sitemap delivery, artwork sitemap inclusion and
the anonymous session. Screenshots were inspected. These successful follow-ups
do not erase the intermittent failures recorded below.

| Observation | Before | After |
| --- | ---: | ---: |
| Public Rembrandt JSON, same production repository read | 391,368 bytes | 54,307 bytes |
| Met facet query sample | 4.77 s | 1.59 s |
| Artist collection-summary query sample | 11.49 s | 1.94 s |
| Candidate Rembrandt HTTP cache miss | previously unstable | 1.23 s |
| Candidate Madonna search, 2 results, cache miss | earlier 8 s failures | 0.67 s |

These are individual observations with different cache/load conditions, not
p50/p95 benchmarks or a capacity guarantee. The real local database was used
only through read-only connections and transactions. No 10-million-row fixture
or concurrent production load test was run.

## Remaining performance failures

Live verification is not an all-clear. It completed 36 successful checks before
stopping at an intermittent museum-directory timeout; earlier requests for the
same directory succeeded. An initial artist-page render also timed out. Cold
artist/museum requests can still exceed the eight-second budget despite faster
plans and successful candidate checks.
An artwork request through the web proxy also returned 503 during browser
verification; its follow-up succeeded in 0.21 seconds, and the subsequent
server-rendering/indexing checks passed.

The additional search probe passed Madonna, unknown-date and image-only cases,
then stopped at a cold `portrait` search timeout. Its exact count alone took
9.74 seconds / 1,293 disk reads in a subsequent plan. A book-author view timeout
was reproduced on both the previous serving revision and the candidate. These
failures are retained in the evidence and are not counted as passing checks.

Follow-up work should reduce cold count/summary reads, separate lightweight
artist identity from complete enrichment, and measure representative concurrency
and cache eviction on the current small database before a capacity decision.
This deployment does not establish that all production latency issues are solved.

Private plans, test logs, failed and successful checks, build provenance,
service snapshots and rollback information are retained under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/performance-fixes-20261009/`.

Runtime rollback can restore 100% traffic to
`artline-api-unified-catalogue-1008-1955`; the additive indexes and maintained
search projection are compatible with that version and need not be removed.
