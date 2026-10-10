# Additional 2,000 Nordic artworks — 8 October 2026

The user requested “nice add more 1000 or 2000, don't ask my approve.” This continuation delivered **exactly 2,000 new production artworks** with documented collection links across **3 existing institutions**. The previous 1,000 records and all other existing records were excluded from the new-object count. New records retain review status as audit data and are available through the unified catalogue.

| Country | New artworks |
| --- | ---: |
| Denmark | 310 |
| Sweden | 773 |
| Norway | 917 |

The batch contains **1022 paintings** and **978 drawings**. All selected creation bounds end in or before 1970. Original ranges, circa qualifiers, titles, inventory numbers, materials and known dimensions are retained. No dates, creator biographies or images were invented.

## Collections expanded

| Collection | Added artworks |
| --- | ---: |
| National Museum, Oslo | 917 |
| Nationalmuseum | 773 |
| Statens Museum for Kunst (SMK) | 310 |

## Evidence

- **310 SMK drawings:** selected from the museum's [public catalogue API](https://api.smk.dk/api/v1/docs/), using bounded nationality-specific drawing searches, with at most 500 source records per requested group. Danish holdings include works by artists from other countries. The exact KKS inventory and museum creator authority IDs are retained. Deposits, uncertain creation bounds and qualified/multiple creator roles were withheld.
- **916 Norwegian objects:** selected from two bounded fragments of [Nasjonalmuseet's own metadata](https://github.com/nasjonalmuseet/collection), 20,000 source records in total, rather than the complete five-fragment dataset. The museum export is dated **3 December 2020**; that date remains explicit in every relevant citation. A current retrieval does not make its catalogue facts newly researched. Current museum-page samples corroborated 13 of 14 sampled records; the remaining sample decisions are held. Museum inventory ampersands remain unchanged, while object URLs use the museum's documented underscore format. Public collection links and the museum's own URL builder were captured to establish this format.
- **774 referenced Wikidata records:** continued beyond previously researched entities, scoped to the verified Nordic institutions. Every accepted row has exact object identity, a supported collection statement, eligible source date and retained creator/attribution evidence. Linked underlying reference pages were not described as independently fetched. Native Swedish object-page checks corroborated 9 of 10 samples; records with conflicting or unresolved primary fields were withheld.

Holding confidence remains an editorial assessment, not a calibrated probability. Holdings establish a source-backed collection connection, not current display or a legal-ownership guarantee. No current-display assertions were created. All raw source statements, receipts and limitations remain available in the hashed plan and citations.

**350** objects link to unique existing museum/Wikidata creator authorities. **1595** retain source creator labels without creating artist profiles or treating a matching name as proof of identity. **55** preserve an unknown creator explicitly. Names are used conservatively to flag possible pre-existing artwork versions even where a source creator has no linked profile.

Collection-qualified inventory numbers are accepted only when the qualifier names the exact museum. Forty-five SMK candidates with an explicit sheet-side identity or matching sheet family were held. Six Wikidata candidates with creation years conflicting with the source creator lifetime were held; lifetime evidence was used only to detect conflicts, never to invent a replacement creation date.

## Reconciliation and verification

The final duplicate review checked global source identifiers and object URLs, institution-scoped inventories, selected indexed title/creator candidates and within-batch object/version identities. It withheld 344 candidates and retained 105 additional eligible candidates outside the requested batch. Exact new IDs were absent before the transaction. Relevant institutions and creators were locked and compared with the pinned plan before insertion.

All **2,000 database records** passed metadata, source identity, holding, creator, citation, audit, review-state and image-absence checks. All **3 affected live museum responses** and **19 representative artwork responses** passed, with samples spanning institutions, work types, date precision and linked/unlinked creators. Country browsing was checked through bounded pagination, with positive collection counts. **28 offline regression checks passed** for source eligibility, attribution, date boundaries, version exclusions, collection-qualified inventories, identifier namespaces and duplicate candidates.

The Cloud SQL recovery backup **1791484855597** completed before production writes. Plan SHA-256: `74b4b18efa930f514e7b85564f5edc8c656451306d00f606e1cfce28c9a29946`. Recovery plans, locked preimages and transaction postimages are stored under `/Users/vadimdulub/Library/Application Support/Artline/backups/nordic-2000-20261008`. The complete batch was inserted atomically and verified before commit. Existing artwork, institution and creator metadata was not rewritten; existing images and publication states were preserved. No new images were downloaded or attached. The real local catalogue was unchanged.

The retained execution plan concerns the current production catalogue; it is not a 10-million-row load test. No application deployment, Terraform apply, test database, catalogue fixture or Git commit was used. Temporary test outputs are kept outside Documents.

This pass expands selected collection content. It does not establish complete national museum or artwork coverage. The [575-lead institution ledger](../nordic-museums-20261008/coverage-and-gaps.csv) and prior source gaps remain applicable.

## Delivery files

- [All 2,000 delivered records](delivered-artworks.csv)
- [Production receipt](applied.json)
- [Database verification](database-verification.json)
- [Live API checks](api-verification.json)
- [Source decisions](source-decisions.json.gz)
- [Identity exclusions](identity-review.json.gz)
- [Current native museum samples](current-native-samples.json)
- [Norwegian object URL evidence](native-url-evidence.json)

Procedure: `ops/nordic-2000-20261008.py`, using the shared insert/verification functions in `ops/nordic-1000-20261008.py`. Tests: `ops/test_nordic_2000_20261008.py` and `ops/test_nordic_1000_20261008.py`.
