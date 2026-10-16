# Iteration 37

Checked 10 distinct previously unchecked Cleveland Museum of Art holdings after cursor `0f6a23b9-1643-5c4f-b8c8-ecbb9f73ba48`. All 360 prior checked IDs were read and excluded; prior completion pins and saved batch 107 reconciliation evidence were validated. No old delivery is counted again.

Added one independently verified primary image to Giovanni Battista Tiepolo's *Various Caprices: The Cavalier Mounting His Horse*, native ID 106513, accession 1924.575.11, internal ID `0f735ddd-c069-502e-bf2f-b82e9d08a167`. Exact museum page and official API agree on object identity and CC0 rights. The actual museum original and 99,393-byte derivative were individually viewed. The complete print, sheet margins and proportions are preserved. Museum source filesize differs from downloaded bytes; source date display and broader structured dates are retained without changing the catalogue.

Eight copyrighted images remain rights-held. Zeng Yandong's *Miniature Album with Figures and Landscape*, native ID 148076/accession 1975.11, remains held for an unsuitable pictorial view. The primary and all seven published alternates were downloaded and individually viewed: they show closed covers/cases, a box lid, decorated fabric, or calligraphy-only spreads. None depicts the album's figures or landscape. This is not a no-image-at-source outcome; the separate visual-review receipt preserves all eight views and their original checksums. No source page was unavailable, and no record lacked an image route.

The production proxy target and transactions were inspected. The write used `artline-curated-ingestion` plus row locks, rechecked null primary media inside the transaction, and saved exact preimages and checksum-pinned plans under the established external backup root. Independent database/audit, storage-download checksum, public-image checksum and artwork API verification passed. All nine held records remained unchanged. Artwork facts, creators, holdings and editorial states were preserved.

Originals: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000037/`.
Recovery snapshots: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000037/`.
These are affected-row backups, not a full database backup. No Cloud SQL backup was created. No real-local catalogue connection, worker launch, supervisor/programme modification, deployment, infrastructure change, deletion, commit or push occurred.

Campaign checked count: 370 distinct IDs. Next Cleveland cursor: `0fbfae45-977e-40fc-bf74-d48201dc1c2b`. Continue from source-queue.json, excluding all prior IDs and preserving holds. Museum rotation remains available. This receipt covers one bounded iteration, not completion of the 1,000-iteration target.
