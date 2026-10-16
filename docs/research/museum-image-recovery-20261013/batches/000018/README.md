# Museum image recovery — iteration 18

Checked 10 previously unchecked, production museum-held works at the Cleveland Museum of Art. The preceding 170 campaign IDs were read from all prior checked-artwork receipts and excluded. Current campaign coverage is 180 distinct checked IDs; this is one bounded iteration, not completion of the 1,000-iteration request.

Delivered one new primary image: Ram-Head Drinking Vessel, internal ID `090037f9-495c-5e0c-907d-0cbbb8f6411b`, museum native ID `139702`, accession `1963.479`. The exact museum page and official API agree on identity, accession, silver medium, ca. 600 BCE date and CC0 rights. The museum record is accessioned and not a loan. The original and derivative were individually viewed; the complete primary viewpoint and original proportions are retained. The 1,400 × 1,017 JPEG is 99,647 bytes. This photograph shows one viewpoint, not every physical surface.

Nine objects have page image routes labelled Copyrighted and remain rights-deferred. None is recorded as a no-image or page-unavailable outcome. The Lion Brewery source title has a trailing line break; this formatting discrepancy is recorded and catalogue text is unchanged. The museum reports 668,653 bytes for the accepted original, while the downloaded file is 672,068 bytes; dimensions agree at 3,400 × 2,471, and both metadata and actual hash/bytes are retained.

Batch 107 reconciliation and the preceding completion pins were validated before selection. Production proxy target and active transactions were inspected. Delivery acquired `artline-curated-ingestion`, locked the selected records, saved exact preimages externally and rechecked the null primary image before attachment. One attributable audit event establishes this batch's new image. Editorial status, creators, holdings and unrelated metadata are preserved; the other nine records are unchanged. A separate read-only database connection, independent storage download, public image HTTP/checksum/decode and artwork API checks passed.

Originals: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000018/`.
Backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000018/` (exact affected rows and pinned plans, not a full database backup).

No real-local catalogue connection, Translation, paid search, deletion, deployment, infrastructure change, commit, push, worker launch or supervisor modification occurred. Existing programmes remain unchanged. Continue after Cleveland cursor `090037f9-495c-5e0c-907d-0cbbb8f6411b` or switch museum; exclude all 180 checked IDs and preserve prior holds. Per-object results and cursor/hold references are in `checked-artworks.json` and `source-queue.json`.
