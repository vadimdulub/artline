# Iteration 49

Checked ten distinct previously unchecked Cleveland Museum of Art holdings after cursor `12a68c74-61c4-5ee0-a401-067264d0469e`. All 480 prior checked IDs from 48 receipts were read and excluded. Prior completion pins and batch 107 recovery evidence were verified. Batch 107 is complete and is not recounted. No interrupted production writes existed for this iteration.

Three existing artworks received CC0 primary images: Quatrilobed Plaque (1932.537), Statuette of Osiris (1940.670) and Prince Shotoku at Age Two (1989.76). Seven museum images remain held for rights; Cleveland (1976.84), dated circa 1974, also has an explicit date hold. All ten direct official pages and ten API records returned HTTP 200 with matching native ID, accession and title and accessioned/non-loan status. No source-page-unavailable or no-image outcomes occurred. Image routes were taken from exact museum records; no paid search was used.

All three originals and three derivatives were individually viewed using the image-viewing tool. The full front views preserve complete object silhouettes and backgrounds, without claiming unseen rear or interior surfaces. The two Osiris objects in this and the previous iteration have distinct native IDs and accessions. Anonymous makers remain unknown. The museum's unreviewed Shotoku alt text calls the figure kneeling; posture was not inferred from that text and catalogue metadata was unchanged.

Derivatives preserve full source composition and proportions and measure 99,839; 99,856; and 95,985 bytes. All three museum filesize values differ from actual downloads while native routes and decoded pixel dimensions agree; both sizes and actual checksums are retained.

Production proxy target and active transactions were inspected before use. Storage uploads used create-only generation preconditions. The write transaction acquired the shared `artline-curated-ingestion` lock, locked all ten artworks, rechecked null primary images and preserved unrelated metadata, creators, holdings and editorial status. Three null-to-primary updates committed with no concurrent-image skips. Independent read-only database verification matched three exact audit events and media/rights/search records. Separate Storage downloads matched pinned hashes and generations. Three public images and three artwork API responses returned HTTP 200 with matching hashes and identities. The seven held artworks remained unchanged.

Originals and receipts: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000049/`. Recovery baseline, pinned plans, locked preimages and precommit postimage: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000049/`. These are affected-row backups, not a full database backup. No Cloud SQL backup was created.

No real-local catalogue connection, Translation, paid search, deletion, commit, push, deployment or infrastructure change occurred. Existing programmes and supervisor/prompt were unchanged; no workers were launched. Campaign coverage is 490 distinct IDs. Continue after Cleveland cursor `133f13f4-4de0-5698-8279-e0aea4f8341f`, excluding all checked IDs and preserving recorded holds. This is one bounded iteration, not completion of all 1,000.

The initial preflight interpreter lacked psycopg and failed before any database call; the established research environment then completed preflight. No ambiguous mutation was retried.

| Artwork ID | Native / accession | Title | Outcome |
| --- | --- | --- | --- |
| 12b2cf7e-b4e2-4887-ba7f-5e972f15c584 | 139921 / 1963.600 | Greek Robe | rights-deferred |
| 12ca5807-4ef2-5f43-bf1e-3cea1f6d8d61 | 148844 / 1976.84 | Cleveland | rights-deferred |
| 12db370c-e319-4620-9717-3d85ac407eb2 | 287535 / 2016.622 | A Suite of 27 Color Lithographs: Red-Orange over Blue (Rouge-Orange sur Bleu) | rights-deferred |
| 12e3d986-d461-47f6-a3e0-dc7576c11458 | 151142 / 1983.105 | Youth at a Grave | rights-deferred |
| 12edec8b-8927-4c10-a31e-fa63ee3c08d0 | 130865 / 1953.564 | Building a Babylon, Tudor City, NY | rights-deferred |
| 12f9ff9b-3354-40cd-b885-382b4c29c945 | 134134 / 1956.632 | The Farmer Dentist, Fourth Plate | rights-deferred |
| 1305cb1c-4a7e-5ba4-b8f0-e02d54de7005 | 113549 / 1932.537 | Quatrilobed Plaque | attached-and-verified |
| 13274a66-fc40-51b4-9d7f-85aadd451b7b | 119849 / 1940.670 | Statuette of Osiris | attached-and-verified |
| 132bbefc-8584-4919-8264-f4b9eba913b2 | 153113 / 1986.121 | Consume in Weaving | rights-deferred |
| 133f13f4-4de0-5698-8279-e0aea4f8341f | 155060 / 1989.76 | Prince Shōtoku at Age Two (Shōtoku Taishi) | attached-and-verified |
