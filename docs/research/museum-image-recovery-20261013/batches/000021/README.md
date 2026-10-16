# Museum image recovery — iteration 21

Checked 10 previously unchecked existing Cleveland Museum of Art artworks missing primary images. All 200 prior campaign IDs were read and excluded; campaign coverage is now 210 distinct IDs. This completes iteration 21 only, not 1,000 iterations.

Three authentic CC0 images were attached and independently verified:

| Artwork | Native ID / accession | Internal ID | Derivative |
|---|---|---|---|
| [Black-Figure Loutrophoros-Amphora (Ritual Water Vessel): Prothesis (Laying out of Corpse), Mourners](https://clevelandart.org/art/1927.145) | 108979 / 1927.145 | `0a12f1ed-3497-5e49-990a-15c509b145f8` | 900 × 1400, 99,056 bytes |
| [Bowl](https://clevelandart.org/art/1963.478) | 139701 / 1963.478 | `0a139a94-d97d-5339-849f-eb752472faf1` | 1400 × 1082, 95,262 bytes |
| [Autumn Evening with Full Moon on Musashino Plain](https://clevelandart.org/art/2000.4.2) | 161673 / 2000.4.2 | `0a20b60a-7019-5d35-83ef-48436f52a09a` | 1400 × 686, 99,217 bytes |

All three originals and all three derivatives were individually viewed. Full source framing and proportions are preserved. Vessel images are complete primary viewpoints, not every physical surface. The screen is the exact six-panel component 2000.4.2, with its complete painted surface and border, not its sibling or the whole pair. Museum page/API native IDs, accessions, titles, creation dates and media support the exact physical objects. All three are accessioned and not on loan; no current-display assertion was added.

Seven other museum pages supply copyrighted reproductions and remain rights-deferred; no restricted files were downloaded. All ten exact museum pages and ten official API responses returned HTTP 200. No no-image, unavailable-page or access-hold outcome occurred. Previous campaign holds are retained through source-queue.json.

Museum reported print file sizes differ from the downloaded byte counts for all three images; actual original hashes, sizes and receipts are archived. All actual image dimensions match the selected print-route dimensions. The silver bowl structured museum data includes a 28.4 cm length omitted from its prose measurements; both remain in evidence, with catalogue facts unchanged.

Batch 107 reconciliation and saved evidence hashes were confirmed before selection; its earlier delivery is not counted again. Prior campaign completion pins passed. The production proxy target and active transactions were inspected before database use and before writing. The atomic write acquired artline-curated-ingestion, locked the selected rows, saved exact transaction preimages externally, and rechecked null primary images. Exactly three null-to-primary changes are supported by matching audit events; there were no concurrent skips.

Independent read-only database, image/evidence associations, search projection, Storage generation/download/checksum, public HTTP/image checksum/decode and public artwork API checks all passed. Artwork metadata, creator/holding links and editorial statuses are unchanged: both vessels remain published and the screen remains in review. The seven rights-held records are unchanged.

Originals: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000021/`.

Backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000021/`. These are exact affected-row snapshots and pinned plans, not a full database backup. No Cloud SQL backup was created.

The real local catalogue was not connected. No Translation, paid search, deletion, commit, push, deployment, infrastructure change, worker launch or supervisor/prompt modification occurred. Existing artwork and exhibition programmes are unchanged.

Continue after Cleveland cursor 0a2849b6-34bc-410b-89a7-474caccb8633 or switch museum; exclude all 210 checked campaign IDs. Inspect embedded page image_assets and official API; retain seven rights holds. Do not count repeat IDs.
