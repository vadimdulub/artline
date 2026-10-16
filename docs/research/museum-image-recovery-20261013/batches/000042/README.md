# Iteration 42

Checked 10 distinct previously unchecked Cleveland Museum of Art holdings after cursor `11071d6b-0186-5d67-a0a0-e64db2b98cae`. All 410 prior checked IDs across 41 campaign receipts were read and excluded. Prior completion pins and saved production batch 107 reconciliation receipts were validated before selection; earlier deliveries were not counted again. No interrupted writes existed in this iteration directory.

Two existing artworks received independently verified CC0 primary images:

| Internal artwork ID | Museum native ID / accession | Title | Derivative bytes |
| --- | --- | --- | ---: |
| 110e71ca-7d82-555e-9797-67bc3b9c154a | 132883 / 1955.340 | Phytanthoza iconographia:  No. 1017 | 98,720 |
| 11169366-2347-545d-87c0-e21c2c9f820f | 104079 / 1922.246 | A Tournament | 99,539 |

All ten official museum object pages and corresponding official API records returned HTTP 200. Native IDs, accessions and titles agree. Eight other works have museum-page images but Copyrighted labels without established reusable licences and remain held. These are rights holds, not missing museum images or unavailable pages. No source access restriction was bypassed and no search API was used.

Both originals and both derivatives were individually viewed using the available image viewer. Complete source frames, margins and proportions are preserved. Botanical plate 1017 retains the museum's broad 1698–1741 date range and unknown physical measurements; publisher Weinmann and engraver Seutter roles are preserved separately. The Tournament remains the exact accession's impression, with museum state II/II recorded as source evidence rather than an independent visual state determination. Its dense detail required an 800 × 563 derivative to meet the byte limit; the full original is archived. Museum filesize metadata differs from actual bytes for both original downloads; native image routes and pixel dimensions agree. Actual byte sizes and SHA256 hashes are retained.

Originals and download receipts are archived under `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000042/`. Transaction preimages, baseline and checksum-pinned plans are backed up under `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000042/`. These are exact affected-row backups, not a full database backup. No Cloud SQL backup was created.

The production proxy target and active transactions were inspected before selection and again before writing. Create-only storage uploads preceded the database transaction. The transaction acquired the shared `artline-curated-ingestion` advisory lock, locked all selected rows and rechecked null primary images. Two attributable null-to-primary updates committed with no concurrent-image skips. Independent verification checked exact audit events, media and rights associations, search projections, creator links, holdings and editorial-state preservation. Independently downloaded storage bytes matched pinned checksums and upload generations. Both public images and artwork API records passed identity, byte-size and checksum checks.

The real local catalogue was never connected to or changed. No Translation, paid search API, deletion, commit, push, deployment or infrastructure change occurred. Other programmes and supervisor/prompt files remain unchanged. No additional workers were launched.

Campaign coverage is now 420 distinct IDs: 410 Cleveland and 10 Städel. Continue after Cleveland cursor `112d8ceb-38f1-400a-bc8e-3da78f945166`, exclude all 420 checked IDs and preserve the holds in `source-queue.json`. This completes one bounded iteration, not all 1,000 requested iterations.
