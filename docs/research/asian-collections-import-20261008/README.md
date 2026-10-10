# Chinese, Japanese and Manila production import — 8 October 2026

Imported 5,393 new review artworks, enriched 1,721 previously existing records and attached 1,062 images in production. The pass covers 30 museums, galleries and mural sites; 22 newly added institutions have country-level browsing links. No publication or current-display claims were added.

| Pass | New records | Existing enriched | New images | Collections |
|---|---:|---:|---:|---:|
| China | 2,973 | 413 | 486 | 17 |
| Japan | 2,177 | 1,309 | 575 | 10 |
| Manila | 243 | 0 | 1 | 7 |

## Evidence and verification

- [Delivery report](report.html)
- [Imported artwork register](imported-artworks.csv)
- [Production verification](verification.json)
- [Institution country links](institution-country-applied.json)
- Phase folders retain pinned plans, source captures, exclusions, preparation, visual review, upload receipts and applied receipts.

## Decisions and remaining gaps

- Coverage is substantial but incomplete. China has 17 represented collections/sites and Japan 10, with four institutions shared. Manila means Metro Manila and covers seven collections. The phase table counts records at the start of each phase: one Tokyo work added during China was enriched again during Japan, so the 1,722 phase enrichments cover 1,721 records that existed before this overall operation.

- China includes paintings, prints, calligraphy, mural fragments and nine named Dunhuang scenes. Nine source records remain held for blank titles, accession/component reconciliation or conflicting existing identities. Source inventory units include albums and leaves; counts are catalogue records, not necessarily independent compositions.

- Japan includes Cleveland, Chicago, Minneapolis, Tokyo/Kyoto/Nara/Kyushu national museums, Ōta, Adachi and the National Museum of Modern Art Kyoto. Two source records remain held. Tokyo modern-art access returned 403; no collection coverage is claimed for it.

- Manila: Lopez 61, Ayala 78, National Museum of Fine Arts 18, Vargas 44, BSP 38, UST 3 and Ateneo 1. Two duplicate title variants were reconciled into retained records; 53 explicitly later source entries were excluded. Six jewellery entries remain in research outside this pictorial/sculptural pass. Ayala loan/private-owner records were not assigned as museum-owned works.

- Ateneo’s collection URLs returned 404 and its homepage returned unrelated gambling content during retrieval. No data from that content was used. Its single addition is supported by the government NCCA inventory. Metropolitan Museum Manila and other collections without eligible object evidence remain coverage gaps.

- Chinese image downloads: 486 accepted and attached; three prepared images rejected as a closed album, blank backing and distant installation view. Chicago and Minneapolis denied selected image requests with HTTP 403 and further requests were stopped. Twenty-four narrow scroll previews failed the minimum-size filter. Japan: 575 attached; eight files failed preparation. Full preparation and access receipts are retained.

- Manila: WikiArt’s Spoliarium image was visually matched and attached with its actual Public domain label. WikiArt’s Amorsolo El Ciego and Bombing of the Intendencia images were held as different/private versions. Most Manila photographs still lack an established reusable source; metadata records remain available without invented images.

- Unknown creation dates, disputed source values and qualified maker labels remain explicit. Lopez pages showing an unlabelled current-year 2026 for historical works were recorded as unknown dates. No artist lifespan, excavation date or exhibition date became an artwork creation year.

- Country links identify only country-level geography; no city, coordinates, street address or current display was invented. Historical collection catalogues support holdings, not live display.

- Image originals are archived outside Documents. Application derivatives are complete source frames, resized proportionally, at most 100,000 bytes, with original source/rights labels and checksums. The production /assets/ route was used; obsolete pre-correction /media/ uploads remain unreferenced.

- All 7,114 distinct affected records were verified using scoped read-only production queries, with publication/metadata preservation checks. Museum browsing and one artwork detail per represented institution passed public API checks. Every newly attached image passed a public file checksum check. No application code, deployment or local database writes were required.

- The scoped museum query plan is retained in each plan. A separate limited exact-title check used a sequential scan; no broad title-only enrichment was performed. This catalogue operation is not a 10-million-row load test.

## Recovery and operation

Production backup: `1791478316451` (successful before imports). Row preimages and after-state evidence are under `/Users/vadimdulub/Library/Application Support/Artline/backups/asian-collections-import-20261008/`. Original images are under the corresponding `source-images` directory. Preserve both; no unrelated files or databases were removed.

Scripts: `ops/import-asian-collections-20261008.py`, `ops/images-asian-collections-20261008.py`, `ops/research-japan-import-20261008.py`, `ops/research-manila-import-20261008.py`, and `ops/verify-asian-collections-20261008.py`. The earlier [Chinese research](../chinese-art-20261008/README.md) remains a historical pre-import record.
