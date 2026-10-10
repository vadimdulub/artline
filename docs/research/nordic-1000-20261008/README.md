# Additional 1,000 Nordic artworks — 8 October 2026

The user requested “add more, 1000 artworks” following the Denmark, Sweden and Norway museum pass. **Exactly 1,000 new production artwork records** and 1,000 supported collection links were added across **12 existing institutions**. Existing records were not counted toward the target. All new records remain in review; no images, artist profiles or on-view assertions were created. The real local catalogue was not changed.

| Country | New artworks |
| --- | ---: |
| Denmark | 45 |
| Sweden | 597 |
| Norway | 358 |

## Collections expanded

| Collection | New artworks |
| --- | ---: |
| Nationalmuseum | 527 |
| National Museum, Oslo | 358 |
| Gothenburg Museum of Art, Gothenburg, Sweden | 38 |
| Hallwyl Museum | 32 |
| Skagens Museum | 16 |
| Ny Carlsberg Glyptotek | 15 |
| The Nivaagaard Collection | 4 |
| Hirschsprung Collection | 3 |
| David Collection | 2 |
| Kunstmuseum Brandts | 2 |
| Statens Museum for Kunst (SMK) | 2 |
| Ribe Kunstmuseum | 1 |

## Sources and decisions

- Referenced Wikidata object statements: 640 records. Exact source entities, collection references, creators, inventory numbers, title aliases and date precision were retained. Linked underlying references are not described as independently checked.
- [SMK's public catalogue API](https://api.smk.dk/api/v1/docs/): 2 records. A bounded 3,500-painting metadata selection was checked against the existing catalogue. Deposits, uncertain attributions, open-ended dates and apparent artist-career proxy ranges were withheld.
- [Nasjonalmuseet's own collection metadata](https://github.com/nasjonalmuseet/collection): 358 records, selected from one 2,465-record export fragment. The source dataset is dated **3 December 2020**, although retrieved in this pass. That source date and its limitations remain in each citation. Current native-page checks are samples, not a current inspection of every object. 7 of the eight refined samples corroborated inventory, title, creator and dates; the differing sample was withheld. Earlier unavailable sketchbook/verso samples prompted exclusion of sheet-side, part and version inventory codes. No current-display claim or ownership guarantee is inferred from the export.

All selected creation bounds end in or before 1970. Source ranges and circa labels are retained; no creation year was inferred from an artist's biography. New records include 880 paintings and 120 drawings. 282 records link to unique existing museum/Wikidata creator authorities; the remaining 718 preserve source creator labels without inventing artist profiles or resolving identity by name alone.

Exact identifiers and object URLs were checked globally; inventory matches were institution-scoped; possible title/creator/version matches and within-batch duplicate identities were withheld. The selection rotates countries and collections, using additional eligible records where a country's new-object queue is smaller. This expands existing collections and does not establish complete national museum or artwork coverage. The [earlier 575-lead gap ledger](../nordic-museums-20261008/coverage-and-gaps.csv) remains the institution research directory.

## Verification and recovery

All **1,000 database records** passed exact metadata, holding, creator, citation, source identity, review-state and image-absence checks. All 12 affected live museum responses and 33 representative artwork responses passed; samples span institutions, types, date precision and linked/unlinked creators. Country pages were checked with bounded pagination and positive collection counts. Thirteen offline source/identity regression tests pass.

Source evidence and the final plan are hashed and immutable. Final plan SHA-256: `22c564aacc1db1162958257304e3da395a0850f67b28478c2c2acc53bdc3618c`. Cloud SQL backup **1791482654794** completed before writes. Recovery plans, locked preimages and transaction postimages: `/Users/vadimdulub/Library/Application Support/Artline/backups/nordic-1000-20261008`. The insert transaction rechecked duplicate identities, locked the relevant institution and creator records, inserted all 1,000 records atomically and verified them before commit. Institution metadata remained unchanged. No existing artwork metadata, images or publication states were updated.

The retained query plan describes the current production catalogue, not a 10-million-row performance test. No test database, database fixtures, Git commit, application deployment or Terraform apply was used.

## Evidence

- [Delivered records](delivered-artworks.csv)
- [Production receipt](applied.json)
- [Database verification](database-verification.json)
- [Live API checks](api-verification.json)
- [Identity exclusions](identity-review.json.gz)
- [Wikidata exclusions](wd-held.json)
- [Norwegian source decisions](norway-held-v3.json)
- [SMK source decisions](smk-held-v2.json)
- [Current Norwegian page samples](norway-current-page-checks-v3.json)

Procedure: `ops/nordic-1000-20261008.py`. Regression tests: `ops/test_nordic_1000_20261008.py`.
