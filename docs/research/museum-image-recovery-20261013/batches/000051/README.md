# Iteration 51

Checked ten distinct previously unchecked Cleveland Museum of Art holdings after cursor `138561b3-a26a-569a-a958-1179e21a7f81`. All 500 prior IDs from 50 checked-artwork receipts were read and excluded. Prior completion pins and batch 107 recovery evidence were verified. Batch 107 is complete and not recounted. This iteration had no interrupted production writes to reconcile.

Six existing artworks received CC0 primary images. Four images remain rights-held: Hopi Corn, Trout Pond, Cleveland and Office Girls. Cleveland also retains a date hold for circa 1974 and structured bounds through 1976. All ten exact official pages and ten API records returned HTTP 200 with matching native ID, accession and title and accessioned/non-loan status. No museum-page-unavailable or no-image outcomes occurred. Image routes came from the exact museum objects; no search API was used.

All six archived originals and six prepared derivatives were individually viewed using the image-viewing tool. Full source composition and proportions are preserved. Exact print impressions and state labels remain distinct: Saint Christopher retains the literal source state IIe/Iie; The Risen Christ is I/II and The Early Plowman III/IX. Claude Lorrain's displayed circa-1630–33 date and broad structured 1620–1680 range remain unchanged. The Nativity drawing retains its questioned circa-1527/30 date; its complete drawn sheet is shown, but the larger secondary support and separate inscriptions are not. Rectos do not imply unseen versos. Derivative sizes are 99,037; 98,669; 98,481; 99,465; 98,634; and 98,084 bytes. All six museum filesize metadata values differ from actual downloads; exact native URLs and pixel dimensions agree, and both sizes and SHA256 hashes are retained.

Production proxy target and active transactions were inspected before use. No other active transactions were present at those checks. Storage uploads used create-only generation preconditions. The transaction acquired shared `artline-curated-ingestion`, locked the ten selected rows and rechecked missing primary images before attaching six media records. Exact locked preimages and postimages preserve unrelated metadata, creators, holdings and editorial status. There were no concurrent-primary skips. Independent read-only database verification matched six exact null-to-primary audit events and media/rights/search records. Separate Storage downloads matched pinned checksums and generations. Six public images and six artwork API responses returned HTTP 200 with matching image hashes and object identities. The four held records are unchanged.

Originals and receipts: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000051/`. Recovery plans, baseline, locked preimages and precommit postimage: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000051/`. These are affected-row backups, not a full database backup. No Cloud SQL backup was created.

No real-local catalogue connection, Translation, deletion, commit, push, deployment or infrastructure change occurred. Existing artwork/exhibition programmes and supervisor/prompt remain unchanged; no workers were launched. Campaign coverage is now 510 distinct checked IDs. Continue after Cleveland cursor `13b9c7e5-09e4-534a-8138-c0ef2cf3de48`, excluding all checked IDs and preserving recorded holds. This is one bounded iteration, not completion of all 1,000.

| Artwork ID | Native / accession | Title | Outcome |
| --- | --- | --- | --- |
| 1389c4cd-e688-4871-9506-d7a6a0b056c4 | 534877 / 2023.31 | Hopi Corn | rights-deferred |
| 138fd68d-3094-5cc5-8c74-3d28ddd1365b | 120644 / 1941.40 | Saint Christopher | attached-and-verified |
| 13916623-1410-5f89-90f3-cc0f899f07f0 | 151199 / 1983.11 | The Risen Christ | attached-and-verified |
| 139666a6-610e-4e86-8af3-ab65fe6cd2d1 | 160686 / 1998.48 | Trout Pond | rights-deferred |
| 13986109-455d-502b-87a2-172eb11d8fbc | 132103 / 1954.664 | Christ and His Disciples | attached-and-verified |
| 13a610c7-c87e-5d28-ae4f-57024b954fd5 | 148841 / 1976.81 | Cleveland | rights-deferred |
| 13a7d5e1-e7a7-4a64-a8f3-2b166734fa8c | 152811 / 1985.62 | Office Girls | rights-deferred |
| 13b35448-230b-502b-8873-ff7e5dcbf819 | 142374 / 1966.191 | The Early Plowman | attached-and-verified |
| 13b6e285-9f2f-54e8-8a02-f84e223c673a | 117799 / 1938.414 | Study of a Seated Woman and other Sketches | attached-and-verified |
| 13b9c7e5-09e4-534a-8138-c0ef2cf3de48 | 105920 / 1924.1003 | The Nativity with the Dream of Joseph | attached-and-verified |
