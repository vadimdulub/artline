# Open-access image additions — 19 September 2026

This report describes the initial pass. [The subsequent continuation](../open-access-followup-20260919/README.md) added three more images and resumed the same append-only Met queue; its later event totals therefore exceed the initial counts below.

**9 new CC0 images uploaded and attached in both local and production catalogues, across 6 painters.** All nine images were visually inspected. Full-frame JPEGs total 844,168 bytes; every file is under 100 KB.

| Museum | Newly uploaded | Existing catalogue works with images after this pass |
| --- | ---: | ---: |
| Smithsonian (SAAM / Freer-Sackler catalogue links) | 8 | 3,663 |
| Metropolitan Museum of Art | 1 | 12,838 |
| Cleveland Museum of Art | 0 | 7,777 |

The existing-coverage column includes earlier work; it is **not** this session's upload count. It counts museum-linked artwork records, not unique image files or a new rights audit of all existing assets.

## Added images

- Gerald Ira D. Cassidy: *Antonio Concha, Old Man of Taos*; *Old Man of Zuni, High Priest (Cacique)*.
- William McGregor Paxton: *The Figurine*.
- Dwight William Tryon: *Midsummer Moonrise*; *November*.
- Morgan C. McIlhenney: *Nantucket Sand Dune*.
- Joseph Rodefer DeCamp: *Sir Robert Laird Borden*; *Sir General Arthur William Currie*.
- Honoré Daumier: *German unity, from News of the day, published in “L'Album du Siège”*.

Smithsonian creator-name variants were individually reconciled against exact object IDs, accessions, titles, creation dates and matching birth/death years. No artist names, biographies or alias tables were changed. The Met print uses the museum's working original image because its smaller derivative returns 404.

## Research scope and limits

- Screened 12,659 eligible Met gaps and 3,825 eligible Cleveland gaps against captured museum metadata. These indexes are selection leads, not current licensing authority; every download also required current object-specific rights and identity evidence.
- Refreshed 22 eligible Smithsonian gaps from 20 official metadata shards: 8 resolved name variants; 14 records still lacked a usable image.
- The broad, artist-balanced queue selected 2,329 works across 1,177 painters. Current source checks reached 1,534 works across 716 painters: 1,509 lacked an explicitly open downloadable image, 24 Met requests returned access errors, and 1 had a date conflict. The Met workers paused after repeated errors; 795 queued works were not individually requested in that queue.
- Separately checked all 20 Met public-domain metadata leads among the eligible gaps. Outcomes: 14 metadata/identity holds, 2 no longer supplied an open image, and 4 missing source/image URLs. One of those missing image derivatives was recovered from its exact official original URL and uploaded.
- Cleveland's captured CC0-image index produced no additional matches among its existing eligible gaps. All 1,129 Cleveland records in the broad queue also lacked a current explicitly open downloadable image.
- No exhaustive museum-image download or new-artwork import. Unknown dates, mismatches, qualified attributions and restricted images were not bypassed. This is a bounded gap-filling pass, not a claim that every possible museum image has been exhausted.

## Verification and preservation

- [Final preservation, image delivery and artwork API checks](final-verified-delivery.json): nine byte-exact public images and nine matching production artwork API responses.
- [Smithsonian local / production / storage / rights verification](smithsonian/delivery-verification.json).
- [Met local / production / storage / rights verification](../open-access-image-gaps-20260919-met-original/delivery-verification.json).
- Seven offline permission/identity regression tests pass; no test database or catalogue fixtures were created.
- Titles, creation dates, creator attributions, research-candidate flags and review statuses remain unchanged. The existing Smithsonian attachment workflow added eight exact, source-backed **collection holding** assertions and their derived institution links. No current-display claims were added.
- No status publication, deployment, Terraform changes or commit. Nine images were uploaded to the existing storage bucket.

Recovery snapshots are under `/Users/vadimdulub/Library/Application Support/Artline/backups/open-access-image-gaps-20260919/` and `open-access-image-gaps-20260919-met-pd/`. Checksums are retained in each run's `backups.json`.

The preliminary `final-preservation-and-delivery.json` and `preservation-detail-review.json` are retained for audit: their strict comparison flagged the eight expected Smithsonian institution links. The final verification checks those links against exact accepted collection assertions; it does not ignore arbitrary metadata differences. An initial manual artwork API probe used a local UUID against production and returned 404; all final probes use the correct production IDs and pass.

## Source policies

These programmes release designated assets, not every image in their catalogues. Exact object/image flags controlled every download: [Met Open Access](https://www.metmuseum.org/hubs/open-access), [Smithsonian Open Access](https://www.si.edu/openaccess/faq), [Cleveland Open Access API](https://www.clevelandart.org/open-access-api). No Pollock reproduction was uploaded without a verified reusable-image basis.
