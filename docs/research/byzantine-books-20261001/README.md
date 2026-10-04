# Byzantine books — 1 October 2026

Six missing works were added to the local catalogue in review. The existing Hexabiblos record received a sourced composition date and highlight membership. None was published; the catalogue's published total remained 34.

| Work | Catalogue date | Original language retained | Source |
| --- | --- | --- | --- |
| Geoponica | 10th century | Ancient Greek, as recorded for the work | [Work article](https://en.wikipedia.org/wiki/Geoponica) |
| Chronicon Paschale | 7th century | Medieval Greek | [Work article](https://en.wikipedia.org/wiki/Chronicon_Paschale) |
| Basilika | c. 892 | Greek | [Work article](https://en.wikipedia.org/wiki/Basilika) |
| Book of the Eparch | Unestablished; layered compilation | Greek | [Work article](https://en.wikipedia.org/wiki/Book_of_the_Prefect) |
| Ecloga (Ekloge ton nomon) | 726 or 741 | Greek | [Work article](https://en.wikipedia.org/wiki/Ekloge_ton_nomon) |
| Belthandros and Chrysantza | 13th–14th century; later reworking | Medieval Greek | [Work article](https://en.wikipedia.org/wiki/Belthandros_and_Chrysantza) |
| Hexabiblos — existing record | 1344–1345 | Medieval Greek | [Author article](https://en.wikipedia.org/wiki/Constantine_Harmenopoulos), [work identity](https://www.wikidata.org/wiki/Q6649850) |

Unknown compilers remain unknown. Geoponica is not incorrectly attributed to Cassianus Bassus: the source explicitly distinguishes the tenth-century compilation from his earlier material. Imperial commissions are not treated as personal authorship. The Book of the Eparch has no invented closed date interval. Ecloga's two proposed dates are labelled as alternatives. Basilika's approximate completion date follows the reviewed article rather than the conflicting unreferenced Wikidata year. First printings, surviving manuscript dates and the events narrated in histories are not substituted for composition dates.

The six additions have descriptions and attributed, revision-linked Wikipedia excerpts. Byzantine Empire filter membership is tied to the work's historical context; no modern country is inferred. Languages without a work-level Wikidata claim are documented in the matched Greek-work article. Hexabiblos retains its existing creator and language projection.

## Audit and application

`ops/curated-byzantine-books-20261001.json` records editorial decisions. The bounded preparation/application workflow is `ops/expand-byzantine-books-20261001.py`; `candidates.json`, `sources/`, `metadata.json`, `plan.json`, `new-books.json` and the receipts preserve the research and exact changes locally.

The Go importer validated all six new source-linked review records before application. The transaction checked existing records against their prepared snapshots, preserved the previous catalogue data in `/Users/vadimdulub/Library/Application Support/Artline/backups/byzantine-books-20261001/preimages.json`, and verified that unselected book records and discovery projections did not change.

Local totals changed from 10,020 to 10,026 books and from 206 to 213 highlights. All seven selected records remain in review. Read-only API checks found the new works in Books and All; Book of the Eparch remains reachable in the undated list. No production database changes or deployment occurred.
