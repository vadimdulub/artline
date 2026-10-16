# Museum image recovery — iteration 19

Checked 10 previously unchecked museum-held production artworks at the Cleveland Museum of Art. All 180 earlier checked IDs were read from campaign receipts and excluded. Campaign coverage is now 190 distinct IDs; this receipt completes only iteration 19 of the requested 1,000.

Two existing artworks received authentic CC0 primary images:

- Orange-Lily, internal ID `0948799c-a1bb-5a91-a1cb-905c48e75c37`, native `132620`, accession `1955.144`: 1,200 × 1,004 JPEG, 99,956 bytes.
- Finial, internal ID `0955714e-fb2a-56f5-9d29-d410f9aeb22a`, native `112307`, accession `1930.730`: 841 × 1,400 JPEG, 97,758 bytes.

Exact object pages and official API metadata agree on native IDs, accessions, titles, media, dates and CC0 labels. Both objects are accessioned, not loans. Each original and each derivative was individually viewed. Full supplied compositions and proportions are retained. The finial photograph documents one complete primary viewpoint, not every physical surface.

The Orange-Lily image includes plate no. 1018 and a May 1, 1807 publication imprint. The source's Thomas Curtis lifespan (1846–1920) conflicts with that date. This is preserved as an unresolved source-attribution discrepancy in research and production image evidence; existing creator links, dates and catalogue metadata were not changed. The source's unreviewed alt text describes vertical orientation, while the actual reproduction is landscape; its actual proportions are preserved. Both downloaded originals are 3,415 bytes larger than the museum's filesize metadata; actual dimensions match, and actual files and checksums are archived.

Eight further exact museum pages have primary image routes labelled Copyrighted. They remain rights-deferred, distinct from page-unavailable and no-image outcomes, both of which number zero in this iteration. No restricted images were downloaded.

Batch 107 reconciliation and prior completion pins were validated before selection. The production proxy target and active transactions were inspected before database use and again before delivery. The transaction acquired `artline-curated-ingestion`, locked all ten selected rows, saved exact preimages externally, rechecked null primary images and preserved unrelated metadata, editorial status, holdings and creator links. Two exact audit events establish attributable null-to-primary changes. The other eight records are unchanged.

Independent read-only database, search-projection, Storage-generation/download/checksum, public image HTTP/checksum/decode and artwork API checks passed for both attachments. Pinned plans, source captures, download receipts, transaction snapshots and final outcomes are retained in this directory.

Originals: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000019/`.

Backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000019/` — exact affected-row snapshots and pinned plans, not a full database backup. No Cloud SQL backup was created.

No real-local catalogue connection, Translation, paid search, deletion, deployment, infrastructure change, commit, push, worker launch or supervisor/prompt change occurred. Existing artwork and exhibition programmes remain unchanged.

Continue after Cleveland cursor `0955714e-fb2a-56f5-9d29-d410f9aeb22a` or switch museum. Exclude all 190 checked IDs and retain all earlier holds. See `checked-artworks.json`, `source-queue.json` and `independent-verification.json`.
