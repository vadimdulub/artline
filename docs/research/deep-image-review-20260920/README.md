# Deep image review — 20 September 2026

## Result

- **161 oversized images compressed and applied to both local and production catalogues.** Their combined size fell from 67,812,280 to 14,650,349 bytes. Every replacement is at most 99,896 bytes. Original files and recovery copies are preserved.
- **Final local audit: 88,138 image records; zero recorded oversize or unknown sizes.** All 87,548 existing image files were read and checked for size, SHA-256, dimensions and file validity. Largest file: exactly 100,000 bytes. No present-file mismatch remains.
- The remaining **590 missing-file records are unlinked** from artworks, artwork-media associations and artist portraits in the local catalogue. These were not restored, published or deleted. The missing-path set is identical before and after compression.
- **70 selected Cleveland artworks reviewed across 42 painters:** 13 already represented, 57 current museum sources verified. Downloaded **30 CC0 images across 30 painters**, totaling 2,734,637 bytes; maximum 99,666 bytes. All 30 passed file verification and were inspected on contact sheets.
- **Production delivery completed at 12:15 UTC on 20 September:** after credentials became available, all 161 replacements were uploaded and verified in both databases and through their public image URLs. Production has 88,018 image records, with zero recorded oversize or unknown sizes. [Delivery verification](size-limit/verification.json).

## Scope and preservation

The size audit covers all image media records, including unlinked records and artist portraits. It does not claim a fresh rights or visual-content audit of every historical image. The latest painter inventory contains **14,272 active artists**, including **10,016 with image gaps**. This is an inventory for continuing painter-by-painter research, not a claim that every painter and artwork has been individually researched.

The source-original archive is separate from application media and may contain larger originals. The 100 KB application limit means **100,000 bytes**, not 102,400. No original asset was deleted. The 161 updates in each catalogue changed only media-file fields, the compression change notice and update timestamps. Exact pre/post checks confirm unchanged rights-evidence rows, artworks, portraits and secondary image associations. Licences, credits, source links and existing publication states remain intact.

Other catalogue workflows ran during this task. Their additions account for the increase from 81,331 local image rows in the opening snapshot to 88,138 at the final audit; those additions are not counted as this review's downloads.

## New downloads: review only

The 30 Cleveland downloads are **not attached to new or existing artwork records**. Every selected record has a same-artist title collision requiring distinct-version/physical-object review. Current CC0 rights, accession, exact object/image identity, unqualified source creator and corroborating life date, museum ownership and source creation dates were checked before downloading. A verified image licence does not settle whether an existing catalogue record represents that same physical work.

[Contact sheet 1](cleveland-painter-review/contact-sheet-1.jpg) · [Contact sheet 2](cleveland-painter-review/contact-sheet-2.jpg) · [Per-image files, sources, licences and checksums](cleveland-painter-review/download-report.json) · [Painter-by-painter review ledger](cleveland-painter-review/painter-review.json) · [File verification](cleveland-painter-review/file-verification.json)

Contact sheets support visual inspection for gross image problems; they do not resolve catalogue collisions. The wide Bada Shanren scroll remains full-frame, including its margins; it was not cropped for a thumbnail. New artwork import, identity reconciliation and publication have not been performed in this batch.

## Evidence and recovery

- [Initial local / production / cloud-storage size audit](size-audit/size-audit.json).
- [Final local file audit](size-audit-local-final/size-audit.json), completed 20 September at 12:08 UTC.
- [Compression plan](size-limit/plan.json) and [local preservation / whole-database verification](size-limit/verification-local.json).
- [Missing-file reference review](size-audit/missing-file-review-local.json).
- [Latest complete painter inventory](size-audit-local-final/painter-inventory.json).

Backups are under `/Users/vadimdulub/Library/Application Support/Artline/backups/deep-image-review-20260920/size-limit/`, including both database preimages and all 161 original image copies. The pinned plan records their checksums. Old asset paths remain recoverable; new paths are content-hashed.

Twenty-five offline compression, metadata-preservation and Cleveland-clearance tests passed. No test databases or catalogue fixtures, commits, deployment, Terraform changes or schema migration were performed.

## Production delivery audit trail

The original delivery was paused by expired Google Cloud credentials. After authentication became available, these commands completed successfully using the pinned plan; already-applied local rows were recognized without changing their original recovery evidence.

```sh
/tmp/artline-popular-20260917-venv/bin/python ops/enforce-catalogue-image-size.py apply --run docs/research/deep-image-review-20260920/size-limit
/tmp/artline-popular-20260917-venv/bin/python ops/enforce-catalogue-image-size.py verify --run docs/research/deep-image-review-20260920/size-limit
```

These commands completed compression delivery only. The 30 newly downloaded Cleveland images still require version/duplicate review before attachment.
