# Iteration 48

Checked ten distinct previously unchecked Cleveland Museum of Art holdings after cursor `126f018a-c347-5e90-9a1a-3f615c50bded`. All 470 prior checked IDs from 47 receipts were read and excluded; previous completion pins and batch 107 recovery evidence were verified. Batch 107 is complete and is not recounted. There were no interrupted writes for this iteration.

Four existing artworks received CC0 primary images. Six museum images remain held for rights. All ten direct official pages and API records returned HTTP 200 and agreed on native ID, accession and title, with accessioned/non-loan status. Every selected source image is linked directly from the exact museum object page and API; no paid search was used.

All four originals and four derivatives were individually viewed. Statuette 1914.573 and relief 1920.1995 retain their qualified subject identifications. The jacket is shown fully from the front; its rear octopus face is not claimed visible. Drummer 1940.990.1 is the first individual sheet of a pentaptych, not the whole set or another impression. Its source physical size label (Each: 18.8 x 20.7 cm) conflicts with the portrait image dimensions (3052 x 3400 pixels). Exact component subject, native identity and download agree; the discrepancy is recorded without stretching the image or changing catalogue dimensions. The relief image shows the complete surviving fragment, without reconstruction.

Derivatives preserve full source composition and proportions and measure 98,333; 93,960; 99,277; and 99,687 bytes. All four museum filesize metadata values differ from actual downloads while native routes and decoded pixel dimensions agree. Both sizes and actual checksums are retained. No catalogue facts or editorial statuses were altered.

Production proxy target and active transactions were inspected before use. Storage uploads used create-only generation preconditions. The write transaction acquired the shared `artline-curated-ingestion` lock, locked all ten artworks, rechecked null primary images and preserved unrelated metadata, creators, holdings and editorial status. Four null-to-primary updates committed with no concurrent-image skips. Independent read-only database verification matched four exact audit events and media/rights/search records. Separate Storage downloads matched pinned hashes and generations. Four public images and four artwork API responses returned HTTP 200 with matching hashes and identities. The six held artworks remained unchanged.

Originals and receipts: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000048/`. Recovery baseline, pinned plans, locked preimages and precommit postimage: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000048/`. These are affected-row backups, not a full database backup. No Cloud SQL backup was created.

No real-local catalogue connection, Translation, paid search, deletion, commit, push, deployment or infrastructure change occurred. Existing programmes and supervisor/prompt were unchanged; no workers were launched. Campaign coverage is 480 distinct IDs. Continue after Cleveland cursor `12a68c74-61c4-5ee0-a401-067264d0469e`, excluding all checked IDs and preserving recorded holds. This is one bounded iteration, not completion of all 1,000.

| Artwork ID | Native / accession | Title | Outcome |
| --- | --- | --- | --- |
| 126f35a7-415e-4d5e-a595-09c99062b3bd | 108183 / 1925.804 | Simone Seated | rights-deferred |
| 12851264-1eba-504e-9847-8b4111f111e3 | 94001 / 1914.573 | Statuette of Seated God, probably Osiris-lah | attached-and-verified |
| 128cd635-4f6a-5b91-b893-a520906cc487 | 134635 / 1957.164 | Picnickers | rights-deferred |
| 128e9fc0-7906-4658-865f-af7a50335808 | 163898 / 2005.276 | Tree | rights-deferred |
| 12903107-9cea-505e-ac6d-517f7409a0d1 | 375948 / 2020.66 | Jacket with Octopus | attached-and-verified |
| 12903377-2d1f-5baf-9015-3ab73076c576 | 125838 / 1947.90 | In the Meadow | rights-deferred |
| 129c3c5c-2448-5185-a4d0-c7ea43752ab9 | 120231 / 1940.990.1 | Drummer from The Cave Door of Spring | attached-and-verified |
| 12a238c4-dc7c-42d9-93e3-32c519d1599d | 154235 / 1988.50 | The Kerosene Lamp | rights-deferred |
| 12a40f4b-4673-48a9-8e33-0f812fdf6e32 | 112053 / 1930.533 | Greetings from the House of Weyhe, 1929 | rights-deferred |
| 12a68c74-61c4-5ee0-a401-067264d0469e | 101382 / 1920.1995 | Relief of Hatshepsut or Tuthmosis III | attached-and-verified |
