# Museum image recovery — iteration 34

Checked 10 previously unchecked museum-held artworks. Added 3 primary images to production and independently verified each database attachment, audit event, storage object, public image checksum and artwork API response. Seven works retain rights holds. Campaign coverage is now 340 distinct IDs; this is iteration 34 of the requested 1,000.

All ten exact Cleveland museum object pages and API records were captured. Native IDs, accessions and titles agree; all ten are accessioned museum objects, not loans. Seven copyrighted page images have no established reusable licence and were not downloaded. Three CC0 originals and their three derivatives were individually viewed. All derivatives preserve the source frame and are below 100,000 bytes.

| Artwork | Museum accession / native ID | Outcome |
|---|---|---|
| Washington Square, New York City, No. 1 | 1941.481 / 120748 | rights-deferred |
| Rider | 1977.41 / 149110 | attached-and-verified |
| Differential Complex | 2001.123 / 161786 | rights-deferred |
| Wisteria | 1962.13 / 137171 | rights-deferred |
| Qur'an Manuscript Folio (recto) | 1933.480.a / 114236 | attached-and-verified |
| The Horse of Ostend | 1958.166 / 135132 | rights-deferred |
| Young Woman Combing Her Hair | 1964.354 / 140410 | rights-deferred |
| Caesar's Palace | 2010.588 / 168908 | rights-deferred |
| Bodhisattva Guanyin of the South Sea | 1950.579 / 127950 | attached-and-verified |
| Die Eroberung von Mexico:  Illustration | 1963.335 / 139542 | rights-deferred |

Rider and Guanyin retain the museum primary whole-object views, including the rider's ancient losses; the images do not claim to show every side. The Qur'an folio is the exact recto record 1933.480.a, preserving its full sheet, calligraphy and rosettes. This existing museum drawing is not a substitute for another pictorial scene and creates no exhibition claim. Original museum-reported file sizes differ from actual CDN downloads; both values and exact original checksums are retained.

Batch 107's completed recovery checkpoint and all saved verification pins were checked before selection. All 330 prior checked IDs were excluded; prior batch completion pins and source holds were retained. Production proxy identity and active transactions were inspected before use. The image-only transaction acquired `artline-curated-ingestion`, locked all ten rows, saved exact preimages, and rechecked null primary images. All three attachments are attributable to this operation, with no concurrent skips. Editorial status, metadata, creators, holdings and prior media associations were preserved.

Originals are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/museum-image-recovery-20261013/batches/000034/`. Exact affected-row recovery snapshots and pinned plans are under the matching `backups/museum-image-recovery-20261013/batches/000034/` directory. This is not a full database backup; no Cloud SQL backup was created.

No real local catalogue connections, other-programme/supervisor modifications, paid search, Translation, deletion, commits, pushes, deployment or infrastructure changes occurred.

Continue after Cleveland cursor 0eab6436-c93a-4331-a1c5-251cf7d74abb or switch museum; exclude all 340 checked campaign IDs and preserve prior holds. Seven new rights holds remain. Do not count repeat IDs.
