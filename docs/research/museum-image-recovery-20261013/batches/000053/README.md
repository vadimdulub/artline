# Iteration 53

Checked ten distinct previously unchecked Cleveland Museum of Art holdings after cursor `1415be8b-da77-4e08-ab12-a0c9a5b78606`. All 520 prior IDs from 52 checked-artwork receipts were read and excluded. Prior completion pins and batch107 recovery evidence were verified. Batch107 is complete and not recounted. This iteration had no interrupted production writes to reconcile.

Three existing artworks received CC0 primary images: Baoyang Lake (1998.78.14), Daedalic Pendant with Potnia Theron (2001.157), and Album of Daoist and Buddhist Themes: Kings of Hells: Leaf 40 (2004.1.40). Seven remain held for rights. All ten official pages and ten API records returned HTTP 200 with matching native ID, accession and title, accessioned/non-loan status and creation ranges within scope. The seven copyrighted objects have page image routes although the open-access API supplies none; these are rights holds, not no-image findings. There were no museum-page-unavailable or no-image-at-checked-source outcomes and no paid search calls.

All three archived originals and all three prepared derivatives were individually viewed. Full source frames and proportions are preserved. Baoyang Lake and Kings of Hells are individual album leaves, not complete albums. The pendant is the exact 2001.157 frontal view, distinct from the nearly identical 1999.88 pendant referenced by the museum; its unseen reverse and necklace ensemble are not claimed. Derivative sizes are 99,582; 98,619; and 99,577 bytes. All three museum filesize values differ from actual downloads; exact native routes and decoded pixel dimensions agree, and both size values and actual SHA256 checksums are preserved.

The production proxy target and active transactions were inspected. Storage uploads used create-only generation preconditions. The transaction acquired the shared `artline-curated-ingestion` lock, locked all ten selected artwork rows, and rechecked null primary images before attaching three media records. Exact locked preimages and postimages preserve unrelated metadata, creators, holdings and editorial status. No concurrent-primary skips occurred. Independent read-only database verification matched three exact null-to-primary audit events, media/rights rows and search projections. Independent Storage downloads matched pinned checksums and generations. Three public images and three artwork API responses returned HTTP 200 with matching hashes, image paths and object identities. Seven held records are unchanged. This verifies API/public-asset delivery, not a browser UI audit.

Originals and receipts: `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000053/`. Recovery plans, baseline, locked preimages and precommit postimage: `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-image-recovery-20261013/batches/000053/`. These are affected-row backups, not a full database backup. No Cloud SQL backup was created.

No real-local catalogue connection, Translation, deletion, commit, push, deployment or infrastructure change occurred. Existing artwork/exhibition programmes and supervisor/prompt remain unchanged; no other workers were launched. Campaign coverage is 530 distinct checked IDs. Continue after Cleveland cursor `14412530-5399-5eec-8135-163521fcd731`, excluding all checked IDs and preserving recorded holds. This is one bounded iteration, not completion of all 1,000.

| Artwork ID | Native / accession | Title | Outcome |
| --- | --- | --- | --- |
| 141c1a04-10e1-5b46-8b3c-ce684bc3c1b6 | 160729 / 1998.78.14 | Baoyang Lake | attached-and-verified |
| 142535cc-9588-4c88-bfde-0189cfcc9099 | 134687 / 1957.205 | Kleine Welten:  IX Abstracte Komposition mit einem rautenförmig aufgeteilten Kreis | rights-deferred |
| 142c92fd-5b1c-40d8-bf0d-aaf4e32217a9 | 118517 / 1939.552 | Ambush | rights-deferred |
| 142e4917-319e-5751-8535-23ca0bf4fd20 | 161879 / 2001.157 | Daedalic Pendant with Potnia Theron (Mistress of the Animals) | attached-and-verified |
| 1431f34a-f183-47ec-a938-27e89b52deb4 | 126898 / 1949.231.31 | The Georgics of Virgil:  Vol. I, p. 123 | rights-deferred |
| 14324a1d-99a3-5281-8dcb-ed8a5dfa80d7 | 146858 / 1972.268 | Illustration for Oeuvre Poetique by Robert Ganzo | rights-deferred |
| 143d0904-7d03-5171-94d1-863e56dc860f | 134618 / 1957.149 | Nova Scotia Landscape, No. 2 | rights-deferred |
| 143d30b3-ea5e-4d53-9d51-a57359b66daf | 170929 / 2013.376.9 | Aberthaw Construction Company No. 9, Bulldozer at Foot of Hill | rights-deferred |
| 1440c0a2-4920-4f48-919b-29bddc200303 | 170956 / 2013.388 | Sprinters | rights-deferred |
| 14412530-5399-5eec-8135-163521fcd731 | 163140 / 2004.1.40 | Album of Daoist and Buddhist Themes: Kings of Hells: Leaf 40 | attached-and-verified |
