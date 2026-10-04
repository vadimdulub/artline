# Production catalogue release — 27 September 2026

User authorized uploading all local catalogue data and available images, then updating production code. The transfer preserves review/publication status and production-only records. It does not replicate local editor accounts, operational ingestion logs, or test fixtures.

The complete local/production catalogue comparison reconciled independent UUIDs by stable source identity. New records retain unknown fields and supplied provenance. Existing collection order is preserved; missing memberships are appended. Production evidence addenda and target-specific import receipts are retained. The separately completed Women’s rights publication is included and preserved.

## Catalogue delivery

| Table | Added | Updated |
| --- | ---: | ---: |
| `artist_aliases` | 61 | 0 |
| `artist_countries` | 54 | 0 |
| `artists` | 53 | 0 |
| `artwork_artists` | 1,453 | 0 |
| `artwork_location_assertions` | 2,811 | 0 |
| `artwork_media` | 129 | 0 |
| `artwork_places` | 318 | 0 |
| `artworks` | 3,156 | 5 |
| `book_creator_links` | 17 | 0 |
| `book_creators` | 15 | 0 |
| `book_discovery` | 19 | 93 |
| `book_discovery_terms` | 1 | 0 |
| `book_records` | 19 | 29 |
| `citations` | 3,300 | 0 |
| `countries` | 7 | 0 |
| `curated_collection_items` | 1,751 | 0 |
| `curated_collections` | 4 | 0 |
| `external_identifiers` | 3,160 | 119 |
| `institutions` | 7 | 0 |
| `media_assets` | 286 | 12 |
| `media_rights_evidence` | 255 | 12 |
| `places` | 26 | 0 |
| `research_resolutions` | 0 | 3 |
| `sources` | 24 | 0 |

The delivery is pinned to SHA256 `98715c12dc5d66b5b5736a313f54192b7da8c825d31905767a94c926289d6cde`. All affected preimages are checked and updated rows locked before writing. The existing book invalidation trigger is retained: 29 changed source records require their reviewed discovery projections to be recreated in the same transaction. The initial attempt rolled back on this trigger interaction. A second attempt also rolled back because the expected afterimage still contained old generated book dates. The final pinned plan reads generated expected values from the exact local source JSON and verifies them, while excluding generated columns from write assignments. Neither failed attempt committed partial catalogue changes.

Backup `1790509197914` completed before the transfer and includes the Women’s rights publication. Private source archives and service configurations are under `/Users/vadimdulub/Library/Application Support/Artline/backups/production-release-20260927/`.

## Images and schema

255 newly available, selected image files were uploaded create-only to `gs://artline-508319-images/assets/`. Local/DB SHA256 and size, GCS MD5/size, and all 255 public deliveries were checked. Rights/source metadata accompanies every new object. No museum images were newly crawled for this release.

590 older media records already lack files both locally and in storage. None is an active artwork primary image or artist portrait. These records remain preserved; missing files were not invented or silently removed.

Migrations 0028 and 0029 widen supported artwork types. Production’s small database required installing the final CHECK constraint with NOT VALID, committing the short exclusive-lock change, then validating under a weaker lock. Both migration ledger entries now correspond to the validated final schema.

## Production code

The full current local application was built, including the reviewed historical presets, richer Islamic/Arabic/Silk Road selections, individual book timeline marks, bounded 150-object responses, compact artwork labels, and crowded book covers.

Two preset references (French Revolution and Women’s rights) have different native UUIDs in the two databases. A bounded indexed stable-slug resolution now selects each database’s existing artwork, including context membership, without changing canonical cursor fingerprints.

- API build: `ec74f5c6-3fe0-48d4-8245-8d314926ffe7`
- API digest: `sha256:7c58e0c942186ce6b9973ee78ab104d5e97af1da65a401e9b8c5d07101cc7509`
- Web build: `822422e9-3d2d-47a0-9559-e0b9f4c0ab51`
- Web digest: `sha256:a47767093c7d2e8a37b99690d28d209f727c4d4278f121f128da61faee88f81e`
- Live revisions: `artline-api-release-0927-r6`, `artline-web-release-0927-r2`
- Rollback revisions: `artline-api-womens-0927`, `artline-web-womens-0927`

No Git commit or Terraform apply was performed. Production traffic and final browser verification receipts are recorded with this release.

## Verification

Go tests passed with ARTLINE_TEST_DATABASE_URL unset; web lint, 180 unit tests, and production build passed. All 31 presets passed read-only checks against the real local catalogue. Query plans were captured for representative presets; a 10-million-artwork load test remains outside this release.

Detailed JSON receipts in this directory retain the inventory, target-ID reconciliation, immutable transfer plan, image delivery hashes, builds, schema validation, and before/after checks. Raw research receipts are intentionally ignored by Git.


## Broad-view production performance correction

Browser verification exposed timeouts in broad illustrated windows on the
`db-f1-micro` production instance. An EXPLAIN ANALYZE on the complete catalogue
returned 100,089 eligible illustrated artworks in 19.04 seconds. Its nested
lookups evaluated 237,093 holding assertions and 199,351 image references.
The final query joins native images and accepted current holdings before the
unchanged eligibility checks, and returned the same 100,089 artworks in 3.85
seconds. The existing unique accepted-current-holding index prevents duplicate
works. The optimization applies only to broad unfiltered artwork windows;
selected creators, geography, facets, search, highlights and picked IDs retain
their selective paths.

Focused Go atlas/HTTP tests passed. Existing read-only discovery tests compare
independent eligibility counts, density, bounded pages and cursor order against
the real local catalogue; both full-all and full-all-images-false passed.
The before/after production plans are retained in `production-query-plans/`.
These measurements describe the current catalogue, not a 10-million-row proof.

Fresh post-commit verification checked every transferred record. All 100,777
active primary/portrait media references resolve to the audited inventory and
verified image delivery. The API passed all 31 presets; Books highlights contain
206 records with 150 entries on the first page. Some historical artwork counts
are slightly greater than local counts because production’s 37 earlier UK
collection memberships are preserved (see the 21 September synchronization
entry in LOCAL_DATA_LOCATIONS.md).

The optimized candidate also passed the exact previously failing HTTP requests:
the 1700–2000 illustrated view returned 77,798 artworks, 6,119 books and 6,813
events in 5.05 seconds; the Renaissance returned 1,664/12/7 in 3.17 seconds;
Civil rights with creators deliberately cleared returned 411/4/4 in 2.24 seconds.
All responses remain bounded to at most 150 records per lane.

Cold simultaneous filter requests on the shared-core database still exhausted
the previous 10-second atlas deadline after the broad-query improvement. The
final application retains cancellation and bounded pages while allowing atlas
timelines 20 seconds, creator/geography choices 10 seconds, and atlas GET proxy
requests 25 seconds (below the HTTP server’s 30-second write deadline). Other
proxy requests, including writes, retain their 12-second deadline. The existing
abandoned-read cancellation regression test passed, as did atlas/HTTP tests.
This provides headroom for the current instance; it is not a substitute for
future large-scale projections or capacity testing.


## Filter-query performance correction

A second production plan showed the Industrial Revolution's five selected
painters still using a whole-artwork-table scan before country/focus matching.
The creator-native relation is now materialized from indexed artist/artwork
links before those broader predicates. On the complete production catalogue,
the old and new queries returned exactly the same count (214 artworks), density,
and bounded detail page. EXPLAIN ANALYZE improved from 2.92 seconds to 0.64
seconds; the artwork access changed from parallel sequential scans to 545
primary-key lookups. `creator-scope-proof.json` records both plans. All 31
existing starting-point read-only checks passed against the real local
catalogue after this change, as did atlas/HTTP unit tests.

Country choices now derive visible book country keys in one pass instead of a
correlated per-country probe. Exact output equivalence was checked for both
research preview (742 choices) and published-only visibility (76 choices).
The measured requests improved from 1.66 to 0.11 seconds; repeat plan execution
improved from 145 to 34 ms. `geography-query-proof.json` retains the evidence.

Earlier browser rounds exposed variable shared-instance latency: the isolated
Civil rights desktop/mobile cases passed, but cycling through periods still
occasionally exceeded the 20-second UI test wait. These failures are preserved
in `/tmp/artline-release-20260927/` rather than being treated as passing checks.
The final release status below records verification after the last correction.


## Final production delivery

Both services now send 100% of production traffic to the revisions above.
`production-final-services.json` pins their deployed image digests and traffic;
private complete configuration snapshots and the exact final source archive
(`release-source-r6.tar.gz`) are in the release backup directory. Local ignored
Terraform image pins match these releases; Terraform was not applied.

The final API candidate returned Industrial Revolution 214/10/4 in 1.55 seconds,
Renaissance 1,664/12/7 in 3.46 seconds, and Civil rights 18/4/4 in 0.53 seconds.
The production All/Books pages, 31-preset endpoint, and three representative
new images passed live checks; each image matched its recorded SHA256.
See `api-r6-smoke.json` and `production-live-smoke.json`.

No production database drop was necessary. All catalogue inserts/corrections
and selected available images were reconciled in place, with existing review
states and production-only evidence preserved.


The final live browser run passed the complete 31-preset walkthrough, including
recommended filters, all three lanes, and an actually loaded artwork image in
every preset. Three additional interaction cases remain failing: clearing the
Renaissance country defaults, and the Civil rights creator-clearing flows at
desktop/mobile widths exceed the 20-second readiness wait. Their traces and
screenshots are retained in `/tmp/artline-release-20260927/browser-results-live/`;
`production-browser-final.json` records this limitation. The earlier isolated
Civil rights run passed, so broad-filter latency remains variable on the current
shared database. This release does not claim those interaction checks passed.
The data/image transfer and production code rollout are complete; broader
query/capacity work remains separate from this verified delivery.
