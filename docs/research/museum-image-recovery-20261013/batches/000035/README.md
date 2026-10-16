# Museum image recovery — iteration 35

Checked 10 previously unchecked museum-held artworks. Added one primary image to production, independently verified through the database, exact audit event, storage generation and bytes, public image checksum and artwork API. Eight rights holds and one no-image outcome remain. Campaign coverage is 350 distinct IDs; this is iteration 35 of 1,000.

The accepted image is Kano Tan’yū’s The Four Seasons, accession 1992.394 / native ID 156808. The exact CC0 original and derivative were individually viewed. Both complete six-panel screens, all twelve panels, borders and signatures remain in the museum-supplied stacked composite. This counts as one illustrated existing artwork. The uncropped proportional derivative is 1200 × 1151 pixels, 99,391 bytes. Source filesize metadata is empty; actual downloaded bytes and hashes are retained. Physical screen dimensions do not describe the stacked reproduction.

All ten official object pages and APIs were captured; native ID, accession and title agree. All ten are accessioned museum objects, not loans. A Hurricane has no primary/alternate image, API image or conservation/ArtLens media. This no-image outcome is separate from an unavailable page. Eight copyrighted page images have no established reusable licence and were not downloaded.

| Artwork | Accession / native ID | Outcome |
|---|---|---|
| The Fighting Yank, Marne | 1920.112 / 100733 | rights-deferred |
| Banyan Tree | 1998.353 / 160576 | rights-deferred |
| The Four Seasons | 1992.394 / 156808 | attached-and-verified |
| A Hurricane | 1942.1440 / 121608 | no-image-at-checked-source |
| Twelve Men | 1938.70 / 117919 | rights-deferred |
| Horse | 1954.353 / 131778 | rights-deferred |
| Los Basureros | 1954.13.4 / 131344 | rights-deferred |
| Hampstead, North Carolina | 1945.52 / 124532 | rights-deferred |
| The Georgics of Virgil:  Volume II, p. 73 | 1949.231.70 / 126945 | rights-deferred |
| Nina Schishin | 1953.613 / 130922 | rights-deferred |

Batch 107’s completed checkpoint and saved verification pins passed. All 340 prior checked IDs were excluded; prior completion pins and source holds retained. No interrupted write receipts existed for this batch. The production proxy and active transactions were inspected. The transaction acquired `artline-curated-ingestion`, locked all ten records, saved exact row preimages and rechecked the accepted record’s null primary image. One attachment committed, with no concurrent skip. Editorial statuses, other metadata, creators, holdings and prior media were preserved; nine held records are unchanged.

Originals and receipts: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000035/`.
Recovery snapshots and pinned plans: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000035/`. This is an affected-row recovery backup, not a full database backup; no Cloud SQL backup was created. Backup JSON values match exactly; selection/baseline backup files add only a final newline, recorded in final-check.json.

No real local catalogue connections, supervisor/other-programme modifications, paid search, Translation, deletion, commits, pushes, deployment or infrastructure changes occurred. Initial preflight stopped for missing psycopg before any connection; the established research virtualenv completed the work.

Continue after Cleveland cursor 0f0fd43d-221a-453d-9d71-5c358086d37f or switch museum; exclude all 350 checked campaign IDs and preserve prior holds. Eight new rights holds and one no-image outcome remain. Do not count repeat IDs.
