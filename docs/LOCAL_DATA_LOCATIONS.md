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

### Japanese painters deep expansion — 17 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/japan-deep-20260917/`.
- The validated local pre-import dump is `local-before.dump` (SHA-256 `87e0631a01dea092a5cfee744ea7b357639ab6a9ebf421d3f83b2c8465fc2663`). Cloud SQL backup `1789640581717` completed successfully before delivery.
- Research, bounded discovery, authority evidence, visual review, per-record receipts, API smoke checks and public checksum verification: `docs/research/japan-deep-20260917/`.
- Delivered identically to local and production: 19 new named artist profiles, 27 new review paintings, 27 CC0 images, and source enrichment for eight existing Met objects. No records were published and no current-display claims were added.
