# Museum image recovery — iteration 20

Checked 10 previously unchecked museum-held production artworks at the Cleveland Museum of Art. All 190 prior campaign IDs were read and excluded before selection. Campaign coverage is now 200 distinct IDs. This completes iteration 20 only, not the requested 1,000.

One existing artwork received an authentic CC0 primary image: **One-Handled Bowl**, internal ID `09ab0818-0af6-54bc-87ce-d737d6e1ed92`, museum native ID `96282`, accession `1916.1995`. The 1,400 × 880 JPEG is 98,148 bytes. Exact museum page and official API evidence agree on accession, native ID, title, date c. 1450–1200 BCE, white slip ware, Cyprus cultural context and measurements. The object is accessioned and not on loan. Its existing published status and unknown creator remain unchanged.

The source original and derivative were individually viewed. The entire bowl, rim, handle, base edge and source margins are preserved. This is one complete primary viewpoint, not every physical surface. The source print metadata reports 3,598,852 bytes; the actual download is 3,602,266 bytes. Actual dimensions agree at 3,400 × 2,137. The difference and inconsistent small-thumbnail dimensions are recorded; only the inspected print route was used.

Nine other exact museum pages expose images labelled Copyrighted. These are rights-deferred, not unavailable-page or no-image outcomes. Restricted images were not downloaded. All ten pages and ten official API requests returned HTTP 200; no access or Retry-After hold was encountered.

Batch 107's completed reconciliation and saved verification hashes were confirmed before selection. Prior campaign completion pins passed. The production proxy target and active transactions were inspected before database use and before delivery. The write transaction acquired `artline-curated-ingestion`, locked all ten selected artworks, saved exact preimages externally, and rechecked null primary images. One attributable null-to-primary change is confirmed by its exact audit event. All unrelated artwork metadata, editorial status, holdings and creator links were preserved; the other nine records are unchanged.

Independent read-only database, media/evidence association, search projection, Storage generation/download/checksum, public image HTTP/checksum/decode, and public artwork API verification passed. See `independent-verification.json`. The checksum-pinned plan and completion receipts preserve exact results separately from earlier research decisions.

Original: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000020/96282.jpg`.

Backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000020/`. These are exact affected-row snapshots and pinned plans, not a full database backup. No Cloud SQL backup was created.

No real-local catalogue connection, Translation, paid search, deletion, commit, push, deployment, infrastructure change, worker launch or supervisor/prompt change occurred. Existing artwork and exhibition programmes remain unchanged.

Continue after Cleveland cursor `09eaea6c-37be-40fa-a5f5-f780a96f439c` or switch museums. Exclude all 200 campaign checked IDs and retain every prior hold through `source-queue.json`.
