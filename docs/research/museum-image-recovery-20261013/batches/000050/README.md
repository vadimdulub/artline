# Iteration 50

Checked ten distinct previously unchecked Cleveland Museum of Art holdings after cursor `133f13f4-4de0-5698-8279-e0aea4f8341f`. All 490 prior checked IDs from 49 receipts were read and excluded. Prior completion pins and batch 107 recovery evidence were verified. Batch 107 is complete and is not recounted. No interrupted production writes existed for this iteration.

Seven existing artworks received CC0 primary images. Three images remain held for rights: Prometheus Unchained, Fountain of Youth and Picture of Dorian Gray: Basil at the Theater. All ten direct official pages and ten API records returned HTTP 200 with matching native ID, accession and title and accessioned/non-loan status. All ten source creation dates are within scope. No source-page-unavailable or no-image outcomes occurred. Image routes came from the exact museum records; no paid search was used.

All seven originals and seven derivatives were individually viewed using the image-viewing tool. Leaf 16 retains its own native accession and anonymous maker. The full mounted handscroll is preserved at 3400 x 114 pixels, including painting, title and colophons, without claiming legibility of small writing. The Cruyl drawing has a museum sheet-dimension orientation discrepancy: the actual native view, inscription and title are horizontal; neither image orientation nor catalogue dimensions were changed. The Daumier image preserves the complete printed composition but does not show the wider blank sheet margins or marginal edition marks. Its exact 1920 impression, 1863 design, state II/II and Daumier/Maurand/Schmied roles remain distinct. The sculpture view shows the complete mourner, not the whole tomb or unseen surfaces.

Derivatives preserve full source composition and proportions and measure 99,533; 99,886; 98,176; 99,962; 98,490; 99,141; and 98,671 bytes. All seven museum filesize values differ from actual downloads while native routes and decoded pixel dimensions agree; both sizes and actual checksums are retained.

Production proxy target and active transactions were inspected before use. Other observed transactions were read queries and were left alone. Storage uploads used create-only generation preconditions. The write transaction acquired the shared `artline-curated-ingestion` lock, locked all ten artworks, rechecked null primary images and preserved unrelated metadata, creators, holdings and editorial status. Seven null-to-primary updates committed with no concurrent-image skips. Independent read-only database verification matched seven exact audit events and media/rights/search records. Separate Storage downloads matched pinned hashes and generations. Seven public images and seven artwork API responses returned HTTP 200 with matching hashes and identities. The three held artworks remained unchanged.

Originals and receipts: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000050/`. Recovery baseline, pinned plans, locked preimages and precommit postimage: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000050/`. These are affected-row backups, not a full database backup. No Cloud SQL backup was created.

No real-local catalogue connection, Translation, paid search, deletion, commit, push, deployment or infrastructure change occurred. Existing programmes and supervisor/prompt were unchanged; no workers were launched. Campaign coverage is 500 distinct IDs. Continue after Cleveland cursor `138561b3-a26a-569a-a958-1179e21a7f81`, excluding all checked IDs and preserving recorded holds. This is one bounded iteration, not completion of all 1,000.

| Artwork ID | Native / accession | Title | Outcome |
| --- | --- | --- | --- |
| 13408261-777a-4868-87db-4a45e8f8727f | 120760 / 1941.492 | Prometheus Unchained | rights-deferred |
| 1343c115-1f66-4b90-8710-62f08e70e60d | 110595 / 1929.16 | Fountain of Youth | rights-deferred |
| 134a8dcc-5649-5416-8953-7be0f62e4cd9 | 123011 / 1943.269 | Eighteen Views of Rome: The Ponte Rotto | attached-and-verified |
| 1352d74c-1775-58ee-beb3-c7414ff48500 | 135539 / 1958.67 | Mourner from the Tomb of Philip the Bold, Duke of Burgundy (1364–1404) | attached-and-verified |
| 1353c6a5-b6c6-53b7-9459-e93dff68074f | 163113 / 2004.1.16 | Album of Daoist and Buddhist Themes: Procession of Daoist Deities: Leaf 16 | attached-and-verified |
| 1358d91d-5935-54a4-bd6e-0661060616f8 | 106760 / 1924.78 | James MacNeill Whistler | attached-and-verified |
| 135aac56-5954-52da-b5f0-2f3f5c40fa01 | 150840 / 1982.246 | Flowers in a Vase | attached-and-verified |
| 135ee6f0-a438-4e09-9eb3-20aec4906a91 | 157264 / 1994.136 | Picture of Dorian Gray:  Basil at the Theater | rights-deferred |
| 137f945e-dabf-5c54-9318-a4c2d40c90bb | 165736 / 2008.108 | Spring Rain Thatched Hut | attached-and-verified |
| 138561b3-a26a-569a-a958-1179e21a7f81 | 102865 / 1921.1498 | A Street at Midnight: Coming out of a drama. Coming out of a variety show | attached-and-verified |
