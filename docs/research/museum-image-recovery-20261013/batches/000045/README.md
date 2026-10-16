# Iteration 45

Checked ten distinct previously unchecked Cleveland Museum of Art holdings after cursor `11a4b934-2ed0-48bc-9471-f55e5fab60ed`. All 440 prior checked IDs from 44 receipts were read and excluded. Prior completion pins and batch 107 recovery evidence were validated; no interrupted writes existed in this batch and no previous delivery was recounted.

Seven existing museum-held artworks received primary images. All ten museum pages and corresponding official API records returned HTTP 200, with exact native/accession/title matches and accessioned, non-loan source status. Three page images remain copyright-held; no image files were downloaded for them. There were no unavailable-page or no-image-at-checked-source outcomes.

All seven CC0 originals and all seven derivatives were individually viewed with the image-viewing tool. Full source composition and proportions are preserved, including print borders, supplied margins and inscriptions; the Summer hanging scroll retains its entire mount, suspension and roller. The bowl, decorated cylinder and ancient statue retain explicit representative-view labels. The statue's missing head and damaged base are physical condition, not a crop. These are images for existing museum catalogue objects; no exhibition or main-artwork scope expansion occurred. All seven derivatives are 90,972–99,712 bytes. Original source filesize metadata differs from actual downloads; exact URLs and pixel dimensions agree, and both sizes and actual SHA256 values are retained.

Unknown physical print dimensions, states and editions remain unknown. Thomas Major retains printmaker authorship despite the inscription referring to a Monamy painting. Fresh Cranach structured page/API metadata gives 1487–1553; a separately inspected web-index text says Date unknown. No date or other catalogue fact was rewritten.

The production proxy target and active transactions were inspected before selection and again before writing. Images were uploaded create-only. The transaction acquired the shared `artline-curated-ingestion` advisory lock, locked all ten artwork rows, rechecked null primary images and preserved catalogue facts, creators, holdings and editorial states. Seven null-to-primary updates committed with no concurrent-image skips. Independent read-only database verification confirmed seven exact audit events, media/rights associations and search projections. Independent Storage downloads matched pinned SHA256 values and generations. All seven public images and artwork API responses returned HTTP 200 with the expected checksums, image paths, accessions and metadata. The three held records were verified unchanged.

Originals and download receipts: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000045/`. Recovery baseline, transaction preimages, pinned plans and precommit postimage: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000045/`. These are affected-row snapshots, not a full database backup; no Cloud SQL backup was created.

No real local catalogue connection, Translation, paid search, deletion, commit, push, deployment or infrastructure change occurred. Supervisor/prompt and existing artwork and exhibition programmes were not modified. No workers were launched.

Campaign coverage is now 450 distinct IDs (440 Cleveland and ten Städel). Continue after Cleveland cursor `11ed48cc-3d5b-5615-aa86-2fa8eda16ea9`, excluding all 450 IDs and preserving source-queue holds. This completes one bounded iteration, not all 1,000 requested iterations.

| Artwork ID | Museum native / accession | Title | Outcome |
| --- | --- | --- | --- |
| 11a9685c-07e0-5f63-a464-012f2a27298c | 105406 / 1923.526.9 | Martyrdom of St. Judas Thaddeus | attached-and-verified |
| 11b38f20-bd37-4a61-be5e-dca67d0fdae4 | 79073 / 2016.133 | Primavera | rights-deferred |
| 11d2d10f-a26a-5d23-881c-6324c5b8fc65 | 143960 / 1968.336 | Baiern, Markt und Ruinen des Schlosses Abach | attached-and-verified |
| 11db1fa5-532b-5cd6-8721-2104bbc97298 | 445185 / 2022.183 | Boat-Shaped Bowl with Plovers | attached-and-verified |
| 11def013-d698-48da-9340-c7196e3cf86c | 138566 / 1962.430.3 | Peace, New Year's Greetings; Nihil Humanum. Ex-Libris for Esther and Leonard Baskin | rights-deferred |
| 11e11384-43b9-568e-bf56-00534e31e4d4 | 108622 / 1926.314 | A View of the Sea by Moonlight | attached-and-verified |
| 11e1a09c-71d8-58ec-966a-6d5c74157eb2 | 154003 / 1988.13.1 | Seasonal Landscapes: Summer | attached-and-verified |
| 11e590c0-a981-5b29-9713-71be02d110ef | 152320 / 1985.182 | Decorated Cylinder | attached-and-verified |
| 11ebbc64-87c7-5b55-acd5-b59b3a765370 | 113186 / 1932.204 | Block Statue of the Royal Acquaintance, Horwedja | attached-and-verified |
| 11ed48cc-3d5b-5615-aa86-2fa8eda16ea9 | 148167 / 1975.165 | Figure | rights-deferred |
