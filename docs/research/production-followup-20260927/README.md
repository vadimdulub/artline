# Production follow-up — 27 September 2026

User-authorized follow-up: reconcile 590 stale image records, correct broad
filter timeouts, add artwork images to All, and deploy the resulting code/data.

## Media reconciliation

All 590 files had intact, checksum-matching private copies. They had deliberately
been withdrawn: 440 for unverified original photograph provenance, 149 with
subsequent rights holds, and one for an incorrect Ivanov image identity. None
was linked as an artwork primary image, artist portrait, or artwork-media entry.

All 590 exact files are now verified in private object storage under
`research-holds/withdrawn-media/`. Bucket access is private, anonymous access
returns 403, and the web image route cannot serve that namespace. Both databases
retain the media records, original rights labels and withdrawal evidence, plus
archive paths, object generations and hashes. Their stale public delivery paths
are null and their storage kind is `placeholder`. No artwork record was deleted
or modified by this reconciliation, and no withdrawn image was republished.

`ops/archive-withdrawn-media-20260927.py` and the `withdrawn-archive-*` receipts
record planning, exact preimages, upload verification and both database commits.

The final full storage audit found **0 issues across 100,844 declared image
paths**, including **100,820 active primary-image/portrait references**. It
compared database sizes/SHA256, local file bytes, and GCS sizes/MD5. Remote,
on-demand book cover services are outside this asset audit.

## Additional art and data

42 new museum artworks and cleared images cover eight historical presets.
See [the object-selection report](../event-images-20260927/README.md). This
release also includes the completed [Decolonization research](../decolonization-20260927/README.md):
seven new records, two reconciliations, expanded exact selection, and one new
public-domain reproduction. This brings the transfer to **49 new artworks,
2 updated records and 43 new image objects**, with associated source/holding/
rights/geographic evidence. New records remain in review. No publication or
current-display assertion was introduced.

The immutable catalogue plan reconciles existing production identities and
checks exact locked preimages. Production-only records are preserved. Every
transferred record was checked before commit and again afterward. Every new
image was uploaded create-only and checked against the pinned database and
local-byte hashes. No production database drop was needed.

## Filter correction

A partial covering index contains eligible illustrated artwork IDs and dates.
Selective queries now bound native artwork IDs by date, creator, explicit picks
and highlights before evaluating geographic memberships and museum evidence.
Geographic sets are built from those candidates. Full unfiltered windows retain
the existing efficient holding/image join. Inactive checkbox defaults no longer
route a broad request through a slow selective query. Preset covers first bound
their explicit IDs before checking eligibility, including generic prepared plans.

Pre-maintenance same-snapshot production comparisons preserve exact counts, density and
bounded pages. Representative EXPLAIN ANALYZE execution times in this run:

| View | Before | After |
| --- | ---: | ---: |
| Renaissance, countries cleared | 4,266 ms | 131 ms |
| Civil rights, creators cleared | 1,036 ms | 788 ms |
| Industrial Revolution | 573 ms | 61 ms |
| Full illustrated view | 3,069 ms | 3,228 ms |

The last view keeps its unchanged SQL; small timing differences reflect runtime
variation. `query-plan-proof-r4.json` retains plans and exact-result comparisons.
No additional request-timeout increase or production instance resize was used.

The first browser round still found cold-cache timeouts. An index-only scan
returned 1,999 candidate rows but performed 55,919 heap visibility fetches.
Production statistics showed only 15,814 of 29,829 artwork pages marked
all-visible after catalogue changes. Nonblocking VACUUM (ANALYZE) of the
artwork, media and related indexed tables restores visibility information and
updates planner statistics. `maintenance-initial-statistics.json` and `maintenance.json` retain page
statistics; `ops/maintain-production-followup-20260927.py` is the explicit
post-ingestion maintenance step. No VACUUM FULL, data deletion, or blocking
table rewrite is used. Initial failed browser traces remain in `/tmp/` as
evidence; final status below reflects the post-maintenance runs.
These are current-catalogue measurements, not a 10-million-artwork load test.

Migration 0030 was installed concurrently and validated in both databases.
The index is about 10 MB. `atlas-index-delivery.json` pins its definition/hash.

## Recovery and verification

Cloud SQL backup `1790533520479` succeeded before mutations. Validated local
dumps, exact database preimages, service configurations and frozen source
archives live under Library Application Support/Artline/backups/, including the
`production-followup-20260927` and `event-images-20260927` directories.

Go package tests, web lint and all 180 web unit tests passed. Read-only catalogue
checks passed for all 31 starting presets, independent discovery counts and
pagination, painter queries, cleared Renaissance/Civil rights filters, and
repeated prepared preset-cover queries. No test database or fixture was created.

Deployment and live browser verification receipts are recorded below. Both
services now serve the verified release. No Git commit or Terraform apply.

## Final geographic-set correction

After maintenance, Civil rights candidate selection performs **zero heap
visibility fetches** (previously 55,919); final production EXPLAIN execution was
77 ms. Renaissance was 113 ms, Industrial Revolution 62 ms. Results are unchanged;
`query-plan-proof-maintained.json` preserves the exact comparisons.

The larger Empire highlight view exposed another planner problem: an estimated
one-row highlight scope caused PostgreSQL to rescan a deduplicated country set
14,185 times. Its local EXPLAIN took 11.33 seconds and the production browser
request exceeded 20 seconds. Geographic membership now uses `IS TRUE` around the
uncorrelated IN set, retaining WHERE semantics while preventing that expensive
join transformation. Exact local count/density/page equality passed; the full
local request dropped from 8.37 seconds to 0.45 seconds. A read-only EXPLAIN
regression test rejects repeated large geographic sorts/deduplications. All
31 presets, discovery counts/pagination and cleared-filter checks pass locally.

The API source is frozen as `api-source-r2.tar.gz`; see `source-manifest-r2.json`.
Atlas/HTTP unit tests and the complete relevant read-only suite passed again.

## Rollout verification

Google Cloud authentication was renewed on 28 September. The final API build
`78dfccd8-5fef-4e50-9acc-5fcb78a1442a` succeeded from the hash-pinned r2 source.
Its digest is `sha256:859decdaf0ce55ca14e025dcb8a3b21fe82f9631d6dc79a3a040b2c5d843d55c`.
The unchanged web build is `707360ae-6773-4f29-943b-0bbead5b104c`, digest
`sha256:98e915d9bdfed3a8d9b272d9363b8eb98e0ae4defbdb0e6ee829355c8f642e24`.

The final Empire query was checked directly against production: 10,403 artworks,
with the country set sorted/deduplicated once. The first complete query took
8.46 seconds with cold reads; repeat EXPLAIN execution took 619 ms. Exact local
response equivalence and production count are recorded in
`empire-geography-hashed.json`. No timeout increase was needed.

Data, private archives, public images and migration 0030 are delivered and
verified. Earlier failed/interrupted runs are retained as diagnostic evidence.

The final API candidate passed all 45 HTTP checks, including all 31 presets and
three filter-broadening cases requested concurrently with geography, creators
and preset choices. Every preset contains illustrated artwork, respects the
1970 creation cutoff, and returns at most 150 objects per lane. The slowest
preset took 2.97 seconds. Cleared Renaissance countries took 1.11 seconds,
cleared Civil rights creators 0.92 seconds, and the broad 1700–2000 view took
3.87 seconds for 77,801 matching artworks with bounded pagination. See
`candidate-api-r2-smoke.json`; these are observed timings, not a load guarantee.

All four production browser tests passed in 1.7 minutes: the complete 31-preset
walkthrough with loaded artwork images and recommended filters; period
switching and deliberate clearing preserved on reload; and Civil rights
creator clearing on desktop (1440 px) and mobile (390 px). See
`browser-final-r2.log` and `browser-final-r2-evidence.json`.

Production traffic is now **100% API `artline-api-followup-0927-r2`** and
**100% web `artline-web-followup-0927`**. Both revisions are Ready and use the
verified build digests above. `production-final-services.json` records service
traffic and image identities. Local Terraform deployment pins were updated;
Terraform was not applied.

After promotion, `/all`, `/books` and preset discovery returned HTTP 200.
Three new image deliveries matched their pinned SHA256 bytes (all 43 had
already passed the complete delivery audit). A fresh mobile browser visit
verified loaded artwork images and no failing catalogue/image requests.
`production-live-smoke.json` and `production-live-browser.json` retain these
checks. The mobile screenshot was visually reviewed after image loading.
