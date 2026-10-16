# Iteration 47

Checked ten distinct previously unchecked Cleveland Museum of Art holdings after cursor `122ea5cf-c60a-4a36-9acd-e06b5a041f72`. Read and excluded all 460 prior checked IDs from 46 receipts; verified previous completion pins and batch 107 recovery evidence. Batch 107 is complete and is not recounted. There were no interrupted writes for this iteration.

Five existing artworks received CC0 primary images. Four museum images remain held for rights; one object has no primary, alternate, API or supported IIIF image route in its museum page metadata. All ten direct official pages and API records returned HTTP 200, agreeing on native ID, accession and title, with accessioned/non-loan status. Supplementary web-tool retrieval failed for the no-image object; this is recorded separately from its successful direct museum-page capture.

All five originals and all five derivatives were individually viewed. The lekythos retains its museum qualification of possible ancient origin with modern painting (source upper bound 1927). Rubens is the recto drawing, distinct from the Tomyris verso and finished paintings. The engraving preserves Giovanni Antonio da Brescia authorship after Andrea Mantegna. The vessel, mother-and-child figure and dish retain representative whole-object views; unseen surfaces are not claimed visible. No catalogue facts or editorial statuses were altered. Derivatives preserve full source proportions and are 98,609; 99,304; 97,634; 99,916; and 98,930 bytes. All five museum filesize metadata values differ from the actual downloads, while native routes and pixel dimensions agree. Both sizes and actual hashes are retained.

Production proxy target and active transactions were inspected before use. Create-only Storage uploads were verified. The write transaction acquired the shared `artline-curated-ingestion` lock, locked all ten artworks, rechecked null primary images and preserved unrelated metadata, creators, holdings and editorial status. Five null-to-primary updates committed, without concurrent-image skips. Independent read-only verification matched five exact audit events and media/rights/search records. Separate Storage downloads matched pinned hashes and generations. All five public images and artwork API responses returned HTTP 200 with matching hashes and identities. The five held artworks remained unchanged.

Originals and receipts: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000047/`. Recovery baseline, pinned plans, locked preimages and precommit postimage: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000047/`. These are affected-row backups, not a full database backup. No Cloud SQL backup was created.

No real-local catalogue connection, Translation, paid search, deletion, commit, push, deployment or infrastructure change occurred. Existing programmes and supervisor/prompt were not modified; no workers were launched. Campaign coverage is 470 distinct IDs. Continue after Cleveland cursor `126f018a-c347-5e90-9a1a-3f615c50bded`, excluding all checked IDs and preserving all holds. This is one bounded iteration, not completion of all 1,000.

| Artwork ID | Native / accession | Title | Outcome |
| --- | --- | --- | --- |
| 12316e4f-a9c8-4068-ba61-01439aafc288 | 160387 / 1998.225 | Untitled | rights-deferred |
| 123bab45-9a74-540c-bc7c-74ceb3a5fd90 | 109292 / 1927.434 | White-Ground Lekythos (Oil Vessel): Mourners at Tomb | attached-and-verified |
| 12436e2c-739e-5d1d-964a-dc5e1fde441f | 131584 / 1954.2.a | The Feast of Herod (recto) | attached-and-verified |
| 124b0a5a-5e39-569e-bd21-10eac5fe4378 | 139813 / 1963.572 | Le Moulin de la Galette | rights-deferred |
| 1252a5fb-21b4-451f-a6ce-31a3eaf222ab | 112656 / 1931.275 | City on a Rock | rights-deferred |
| 12548cbe-f0c4-5de4-87c5-1eeb75a4a5d2 | 112818 / 1931.426 | Mother-and-Child Figure | attached-and-verified |
| 125dca5a-5cf8-505d-98c0-7fb42ae342c8 | 140309 / 1964.271 | Dish with Reeds and Mist | attached-and-verified |
| 126888c9-104d-537d-8931-ed8353e56651 | 133136 / 1955.532 | Columbus Road Crossing | rights-deferred |
| 1269317c-2aae-5eff-a750-e3a2472e211f | 106116 / 1924.218 | Holy Family with St. Elizabeth and the Infant St. John the Baptist | attached-and-verified |
| 126f018a-c347-5e90-9a1a-3f615c50bded | 678659 / 2025.28 | Beauties with Bamboo and a Rose | no-image-at-checked-source |
