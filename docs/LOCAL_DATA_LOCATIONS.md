# Local Artline data

The real database is PostgreSQL `artline` on localhost. Read-only audits query it directly. Never point fixture/destructive integration tests at this database; never create a test database as part of the collection workflow.

Authentic artwork files remain in `apps/web/public/assets/artworks/`, with database media associations and source/rights evidence. Research captures, pinned selections and application receipts are real provenance, not disposable test data.

Larger source-image evidence, when retained separately from the <=100,000-byte
application derivative, belongs under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/`.
The first such archive is `athens-icon-20260912/`: one original photograph and
its capture receipt, both hash-verified after relocation. It is not a test image
or an extra served web asset.

## Backups moved out of Documents

On11 September2026, the22 individually inspected top-level `Documents/artline-…backup…` directories were relocated, not deleted, to:

`/Users/vadimdulub/Library/Application Support/Artline/backups/`

Each original folder name and dump filename is retained. Historical reports retain their original paths for audit: replace the leading `/Users/vadimdulub/Documents/` with the backup root above to find the same dump. The relocation journal contains original/new paths and before/after SHA256 verification:

`output/data-collection-20260911-2016/backup-relocation.jsonl`

Future backups go under this dedicated folder, never scattered at the top of Documents. Keep the pre-mutation safety requirement; these are recovery snapshots, not extra live databases. This relocation does not reclaim disk space, and no backup was deleted.

## First GCP migration backup (12 September 2026)

The PostgreSQL archive used to populate project `artline-508319` is retained at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/gcp-migration-20260912/artline.dump`

SHA256: `1100961ded54f74b8ddda765fc7bdb49b2f098e5c9eabbb8ca0bc475e9a45837`.

The local catalogue and 644 original application images remain in their existing
locations. Cloud Storage contains copies in `gs://artline-508319-images/assets/`.
This initial migration does not establish ongoing replication. See
`docs/deployment-20260912.md` for deployment and migration validation.

## Armenian/Georgian research and Women artists filter (13 September 2026)

Recovery dump, selected original reproductions and the verified completion archive:

`/Users/vadimdulub/Library/Application Support/Artline/backups/armenian-georgian-women-20260913/`

The pre-mutation local dump is `local-before.dump`; the successful Cloud SQL
backup is `1789326954000`. Research, application receipts, image credits and
verification are in `docs/research/armenian-georgian-women-20260913/`.
The completed pass added 271 review artworks, 41 artist profiles and 38 images
to both databases. No existing records, backups or artwork assets were removed.

## Overnight country research (13–14 September 2026)

Recovery dumps and per-change preimages:

`/Users/vadimdulub/Library/Application Support/Artline/backups/overnight-countries-20260913/`

The initial `local-before.dump` and final `local-after-20260914.dump` are retained.
Final dump SHA-256: `7d45f811ebee2d69fc322758916e19c52eeb6e77abdcc9d63503d303ee2e8d24`.
Its archive directory was verified without restoring it or creating a test database.
The successful pre-import Cloud SQL backup is `1789326339640`.

Selected originals are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/overnight-countries-20260913/`;
served derivatives remain in `apps/web/public/assets/artworks/`.

The report, exact receipt membership, CSV package and pending production differences
are documented in [the research index](research/overnight-countries-20260913/README.md).
Later local updates await Cloud reauthentication; this is not a fully synchronized
post-run production backup. Historical facts, archived duplicates and assets were preserved.

### Resumed production delivery — 14 September 2026

The post-delivery local recovery dump is `local-after-resumed-20260914.dump` under the overnight backup directory above (399,013,814 bytes; SHA-256 `e578e736fdd08a69689aa931deb0a41424ef1016dc15df2859bc99e0820adf59`). Its archive directory was validated without a restore. Post-delivery Cloud SQL backup `1789364642427` completed successfully. Both receipts are linked from [the current research index](research/overnight-countries-20260913/README.md); earlier backups and handoffs remain preserved.

## Cypriot painters (14 September 2026)

The pre-import local recovery dump, selected originals and completed research archive are retained under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/cypriot-painters-20260914/`

Cloud SQL backup `1789369991390` completed successfully before import. The bounded pass added 7 painter profiles (6 Cypriot, plus one explicitly active in Cyprus), 36 review artworks and 3 verified images to both databases. See the [research report and verification receipts](research/cypriot-painters-20260914/README.md). No existing catalogue records or artwork assets were deleted.

## Cypriot expansion (14 September 2026)

The next selected pass added 13 artist profiles, 31 review artworks and 19 licensed images to local and production. Recovery dump, selected originals and completed research archive are under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/cypriot-expansion-20260914/`

Cloud SQL backup `1789372089497` completed before delivery. Combined Cyprus coverage is 20 artists, 67 artworks and 22 images. See the [expansion report and verification receipts](research/cypriot-expansion-20260914/README.md), including the preserved date disagreement and superseded image selection.


### Cypriot further expansion — 14 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/cypriot-more-20260914/`.
- Contains validated local pre-import dump, selected image originals (including two rejected Venice views), cloud backup request and completed research archive.
- Cloud SQL pre-import backup: `1789376146123` (successful).
- Evidence and receipts: `docs/research/cypriot-more-20260914/`.
- Delivered to local and production: 7 new artists, 26 artworks, 11 licensed images. Existing Minas and Goul identities reused; all new records remain in review.


### Cypriot and Greek artist portraits — 14 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/cyprus-greece-portraits-20260914/`.
- Validated local pre-import dump, target-specific artist preimages, selected source originals and completed evidence archive.
- Cloud SQL pre-import backup: `1789379855575` (successful).
- Research, coverage inventory, gallery and verification: `docs/research/cyprus-greece-portraits-20260914/`.
- 22 artist portraits stored locally in `apps/web/public/assets/artists/imported/cyprus-greece/` and in GCS `artline-508319-images` under matching asset keys; attached in both databases. Private bucket access preserved; public images delivered through Artline.

### Spanish painters deep expansion — 17 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/spain-deep-20260916/`.
- Contains a validated pre-import local dump, exact preimages for the 74 existing artworks enriched in each target, and the successful pre-import Cloud SQL backup receipt.
- Research, selection, rights review, transaction receipts, post-delivery audit and verification: `docs/research/spain-deep-20260916/`.
- Delivered identically to local and production: 69 new artist profiles, 906 new review artwork records, evidence enrichment for 74 existing artworks, and 79 licensed images. All 79 served image files were checksum-verified; no records were published and no current-display claims were added.

### Spanish paintings image follow-up — 17 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/spain-images-followup-20260917/`; selected source originals are under the corresponding `source-images` directory.
- Cloud SQL pre-attachment backup `1789632648328` completed successfully. The local full dump and exact target preimages were validated before delivery.
- Evidence, visual review, transaction receipts, API smoke checks and public-file verification: `docs/research/spain-images-followup-20260917/`.
- Attached 27 additional licensed images to the same records in local and production. Twelve prepared alternatives were held because an existing primary image was present; no existing media or catalogue metadata was replaced.

### Japanese painters deep expansion — 17 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/japan-deep-20260917/`.
- The validated local pre-import dump is `local-before.dump` (SHA-256 `87e0631a01dea092a5cfee744ea7b357639ab6a9ebf421d3f83b2c8465fc2663`). Cloud SQL backup `1789640581717` completed successfully before delivery.
- Research, bounded discovery, authority evidence, visual review, per-record receipts, API smoke checks and public checksum verification: `docs/research/japan-deep-20260917/`.
- Delivered identically to local and production: 19 new named artist profiles, 27 new review paintings, 27 CC0 images, and source enrichment for eight existing Met objects. No records were published and no current-display claims were added.
