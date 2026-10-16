# Iteration 52

Checked ten distinct previously unchecked Cleveland Museum of Art holdings after cursor `13b9c7e5-09e4-534a-8138-c0ef2cf3de48`. All 510 prior IDs from 51 checked-artwork receipts were read and excluded. Prior completion pins and batch 107 recovery evidence were verified. Batch 107 is complete and not recounted. This iteration had no interrupted production writes to reconcile.

Three existing artworks received CC0 primary images. Seven images remain rights-held: The Garden at Tradate: Autumn, State Fair, Nude Child Seen from the Rear, Cathedral, An Eagle Ceremony at Tesuque Pueblo, Self-Portrait and La Punta. All ten exact official pages and ten API records returned HTTP 200 with matching native ID, accession and title and accessioned/non-loan status. All ten source creation ranges are within scope. No museum-page-unavailable or no-image outcomes occurred. The seven copyrighted objects have page image routes although the open-access API supplies no image routes; they are rights holds, not missing-image-source findings. No paid search API was used.

All three archived originals and three prepared derivatives were individually viewed using the image-viewing tool. Full source composition and proportions are preserved. Corot's exact 1942.878.b verso retains its faint graphite and source orientation despite upside-down annotations; the recto was not substituted. Kano Naonobu's 2015.481.2 image shows the complete six-panel winter screen, one of a pair. Hiroshige's 1930.180.a shows one entire sheet in the triptych, not all three sheets. These component distinctions are explicit in the attachment view labels and evidence. Derivative sizes are 95,175; 99,794; and 99,015 bytes. All three museum filesize metadata values differ from actual downloads; exact native URLs and decoded pixel dimensions agree, and both sizes and SHA256 hashes are retained.

Production proxy target and active transactions were inspected before use. Storage uploads used create-only generation preconditions. The transaction acquired shared `artline-curated-ingestion`, locked the ten selected rows and rechecked missing primary images before attaching three media records. Exact locked preimages and postimages preserve unrelated metadata, creators, holdings and editorial status. There were no concurrent-primary skips. Independent read-only database verification matched three exact null-to-primary audit events and media/rights/search records. Separate Storage downloads matched pinned checksums and generations. Three public images and three artwork API responses returned HTTP 200 with matching image hashes and object identities. The seven held records are unchanged. This verifies API/public-asset delivery, not a browser UI audit.

Originals and receipts: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000052/`. Recovery plans, baseline, locked preimages and precommit postimage: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000052/`. These are affected-row backups, not a full database backup. No Cloud SQL backup was created.

No real-local catalogue connection, Translation, deletion, commit, push, deployment or infrastructure change occurred. Existing artwork/exhibition programmes and supervisor/prompt remain unchanged; no workers were launched. Campaign coverage is now 520 distinct checked IDs. Continue after Cleveland cursor `1415be8b-da77-4e08-ab12-a0c9a5b78606`, excluding all checked IDs and preserving recorded holds. This is one bounded iteration, not completion of all 1,000.

| Artwork ID | Native / accession | Title | Outcome |
| --- | --- | --- | --- |
| 13bb2c33-2002-5248-99da-43e0b846d1d6 | 122630 / 1942.878.b | Sketch for a Landscape (verso) | attached-and-verified |
| 13c41659-5792-5ee4-8e16-c5021c5cf7e6 | 141211 / 1964.449 | The Garden at Tradate: Autumn | rights-deferred |
| 13daa3b3-5277-5343-bfac-ed861dfd57f3 | 86119 / 2015.481.2 | Summer and Winter Landscapes (one of a pair) | attached-and-verified |
| 13e12fd9-75ea-45c5-bbd8-19307274ee46 | 126062 / 1948.282 | State Fair | rights-deferred |
| 13e9a9c2-732e-4eae-8dbb-2845ea65d8c4 | 162723 / 2003.267 | Nude Child Seen from the Rear | rights-deferred |
| 13f009da-bd02-5881-95ab-c827519570d4 | 111644 / 1930.180.a | Mountain and River on the Kiso Road | attached-and-verified |
| 13f1ca91-b01b-5b1b-adda-e6ac92176dd4 | 128143 / 1951.138 | Cathedral | rights-deferred |
| 13f212e4-a081-48c0-a970-0eb2ddd6675a | 164332 / 2005.415 | An Eagle Ceremony at Tesuque Pueblo | rights-deferred |
| 13f5b469-6e93-5c4b-b6dd-6f7040f7d137 | 117927 / 1938.78 | Self-Portrait | rights-deferred |
| 1415be8b-da77-4e08-ab12-a0c9a5b78606 | 164902 / 2006.262 | La Punta | rights-deferred |
