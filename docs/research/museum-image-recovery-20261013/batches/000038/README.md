# Iteration 38

Checked 10 distinct previously unchecked Cleveland Museum of Art holdings after cursor `0fbfae45-977e-40fc-bf74-d48201dc1c2b`. All 370 prior checked IDs were read and excluded. Prior completion pins and saved batch 107 reconciliation evidence passed verification; no previous delivery is counted again.

Two existing artworks received independently verified CC0 primary images:

- Hua Yan, *Album of Landscape Paintings Illustrating Old Poems: Boy Tending a Water Buffalo*, 1745. Native ID 151028, accession 1982.68.12, internal ID `0fd26255-5cd0-5843-9a48-50593fcef634`. Derivative: 98,742 bytes, 1400 × 1167 pixels.
- Song Xu, *Xiaomei*, c. 1588. Native ID 160733, accession 1998.78.18, internal ID `0fdfdce7-a457-5b3f-beb7-74cc91623f80`. Derivative: 99,238 bytes, 1000 × 924 pixels.

Exact museum object pages and official API records agree on native ID, accession, title and CC0 rights. Both originals and both derivatives were individually viewed. They show the specific painted leaves with the complete supplied frames, inscriptions, seals and sheet edges preserved. No cropping or proportion changes were applied. Museum filesize metadata differs from actual original bytes by 3,417 bytes for each image; exact native routes and decoded dimensions match, and actual bytes and checksums are retained.

Eight other records remain rights-held: their museum pages supply images but label them Copyrighted, with no reusable licence established. No museum page was unavailable and no checked record lacked an image route. These outcomes are separate from delivery and retained per object in `checked-artworks.json`.

The production proxy target and active transactions were inspected before use. The atomic write acquired `artline-curated-ingestion` and artwork row locks, rechecked null primary media, saved exact transaction preimages and used a checksum-pinned plan. Independent database/audit, search projection, storage download checksum, public image checksum and artwork API checks passed for both additions. All eight held records, artwork facts, creators, holdings and editorial states remained unchanged.

Originals: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000038/`.

Recovery snapshots: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000038/`. These are affected-row backups, not a full database backup. No Cloud SQL backup was created.

No real-local catalogue connection, additional worker launch, supervisor/programme modification, deployment, infrastructure change, deletion, commit or push occurred.

Campaign checked count: 380 distinct IDs. Next Cleveland cursor: `0ffdf5f4-be6d-48b7-8f76-f5cd0115aed0`. Continue from `source-queue.json`, excluding all prior IDs and preserving holds. This receipt covers one bounded iteration, not completion of the 1,000-iteration target.
