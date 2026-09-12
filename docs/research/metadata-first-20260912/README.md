# Museum artwork research dataset

## Results and files

Two source-backed research batches contain **20 distinct artwork records**, covering
**10 distinct named painters and six holding institutions**. These are staging
records, **not database additions**. Two artwork records are already present in
Artline. Eighteen others remain candidates; lack of an exact match does not prove
uniqueness. No artist, artwork, image or editorial row was changed.

- [First artwork batch: 16 rows](csv-v1/artworks.csv)
- [Theocharakis follow-up: four rows](theocharakis-csv-v1/artworks.csv)
- [Painter entries: 10 names](csv-v1/painters.csv)
- [First-batch source evidence](csv-v1/evidence.csv) and [follow-up evidence](theocharakis-csv-v1/evidence.csv)
- [First-batch deferrals](csv-v1/deferred.csv) and [follow-up deferrals](theocharakis-csv-v1/deferred.csv)
- [First-batch verification](csv-v1/verification.json) and [follow-up verification](theocharakis-csv-v1/verification.json)

The follow-up repeats Papaloukas's painter key intentionally: there are ten unique
painters, not eleven. Both batches use the same CSV headers. Every source-backed
claim in the artwork tables has an exact institutional URL; the evidence tables
contain 121 field-to-source references. This counts evidence fields, not 121
independent source pages.

The original four-row deferred file is a historical checkpoint. Its Theocharakis
self-portrait metadata lead is now resolved by the follow-up, leaving **six distinct
open deferred candidates** across the two files. Its image-rights question remains
open. Two approximate Parthenis dates in the main artwork file are separately
flagged for date mapping, rather than assigned invented numerical bounds.

## Coverage

| Painter | Artwork records | Institution | Outcome |
|---|---:|---|---|
| Konstantinos Parthenis | 3 | National Gallery Greece; Goulandris | Christ already present; Still Life and Harmony staged |
| Spyros Papaloukas | 7 | National Gallery Greece; Theocharakis | Boy with Suspenders already present; six other works staged |
| Ivan Aivazovsky | 3 | State Russian Museum | Three dated source-backed candidates; initial profile had zero linked works |
| Giorgio Morandi | 1 | GNAMC, Rome | Inventory 8535 staged; generic title is not a duplicate identity |
| José María Velasco | 1 | MUNAL | Cañada de Metlac, 1893 |
| Leandro Izaguirre | 1 | MUNAL | El suplicio de Cuauhtémoc, 1893 |
| Félix Parra | 1 | MUNAL | Fray Bartolomé de las Casas, 1875 |
| Juan Cordero | 1 | MUNAL | Cristóbal Colón en la corte de los Reyes Católicos, 1850 |
| Santiago Rebull | 1 | MUNAL | La muerte de Abel, 1851 |
| Manuel Ignacio Vázquez | 1 | MUNAL | Desnudo masculino, 1823 |

Holding-country distribution: Greece 10, Mexico six, Russia three, Italy one.
This is **not** an artist-nationality distribution. Aivazovsky's Armenian family
background and participation in Russian marine painting remain distinct.
The six Mexican painter entries have catalogue-backed names but still need
separate biographical and authority research. They are not completed profiles.

## Source findings

The Greek National Gallery lists 115 Parthenis works on its artist page, while the
initial Artline query found one linked work. That is an actionable coverage lead,
not 114 verified eligible additions: the website includes uncertain dates,
different media and possible catalogue relationships requiring individual review.[1]
Papaloukas's National Gallery artist page lists ten works; two were present in the
initial Artline query.[2]

The Russian Museum's Aivazovsky artist page lists 68 records in its own collection
and four under other museums. Those inventory totals are leads, not completed
object checks. The present batch verifies three paintings from individual
institutional records. Unstated accessions are left empty, and old gallery tours
are not treated as fresh on-view evidence.[3]

The Theocharakis collection introduction describes more than 600 works spanning
paintings, watercolours and drawings. Four individually inspected, dated paintings
are staged here. Two undated objects and a crayon drawing remain separate from
that painting-first selection.[4] The 1925 study for Boy with Suspenders is
34 × 27.5 cm and is distinct from the National Gallery painting, 60.5 × 51 cm.
Different collections and dimensions must not be collapsed because the subjects
are related.[2][5]

MUNAL's selected collection page supplies creator, title, year and medium for six
paintings. Missing accession numbers and dimensions remain blank. A single shared
page is distinguished by per-object textual locators; it must never become a
single object identifier reused for every work.[6]

GNAMC identifies Morandi's Natura morta as inventory 8535, dated 1918. That identity
must remain separate from his many other paintings titled Still Life or Natura
morta. The Lombardia lead for Natura morta con manichino could not be opened and
was not promoted from search-result discovery to verified metadata.[7]

## Database comparison and safeguards

Both exporters used repeatable-read, read-only transactions against the real local
`artline` database. Snapshot totals were **106350 artworks / 5328 artists**; a
separate read-only check also confirmed **644 media assets**. No test database,
fixture, backup or image binary was created in this task. No backup was needed
because there were no database mutations.

Across the two batches, automated outcomes were:

- 13 records with no match in the implemented exact checks;
- five with generic-title candidates requiring review;
- two with source/accession matches to existing Greek records.

The candidate ledgers retain 178 record-to-candidate matches. This is not 178
duplicates. A targeted manual database check resolved the obvious Harmony and
Wave collisions: existing Harmony is by Thomas Rowlandson; the two existing Wave
records are by Aristide Maillol and N. Krishna Reddy, not Parthenis or Aivazovsky.
Other generic-title candidates remain in the ledger for further reconciliation.

Checks cover exact source URLs, institutional accessions, title variants and
artist names/aliases across the live catalogue. They are **not** a completed
all-language, fuzzy-title or authority-ID reconciliation. Do not import a row
merely because `existing_catalogue_match` reports no match.

The staging CSV extends the earlier prompt's export-only match vocabulary with
`no_match_in_live_database_checks`, `possible_match_needs_review` and
`source_or_accession_match_needs_review`. These describe actual live read-only
checks, not an uploaded export. No automatic matching or publication is implied.

## Image outcomes and rights

**Zero images downloaded.** Metadata is the current priority. Existing images were
not re-audited or claimed repaired in this task. The previous Monet visibility
complaint remains open.

Image-page references are retained where encountered; they are not licences.
For Theocharakis's 1956 self-portrait, SearchCulture displays CC BY-SA 4.0, while
the institution's general terms distinguish personal/nonprofit research from
other reuse and warn about third-party rights. The record retains both leads;
publication or image downloading awaits reconciliation rather than assuming
either unrestricted reuse or that the specific licence is invalid.[8]

## Verification and implementation

`apps/server/cmd/research-csv` is a bounded Go staging exporter, not a production
CSV importer. It validates parent references, duplicate source identities,
explicit dates, source URLs and verification states, then serializes and reparses
every CSV record. It refuses to overwrite existing output files. It never fetches
remote resources, writes database records, creates schemas or downloads images.

Offline unit tests passed with `ARTLINE_TEST_DATABASE_URL` unset. Tests exercise
invalid dates, missing creators, duplicate objects, unsafe source URLs, shared
collection pages, Unicode, embedded quotes/newlines, accession leading zeros and
preserving existing evidence files. CSV row counts and SHA256 hashes are recorded
in each verification receipt. This is not a 10-million-row performance test.

To reproduce into a **new** directory whose parent exists, from `apps/server`:

```sh
env -u ARTLINE_TEST_DATABASE_URL DATABASE_URL='postgres://localhost/artline?sslmode=disable' go run ./cmd/research-csv -input ../../docs/research/metadata-first-20260912/facts.json -out ../../docs/research/metadata-first-20260912/csv-next
```

Use `theocharakis-facts.json` for the second batch. The original JSON and output
receipts are preserved. No commit, push, publication, deployment or Terraform run.

## Exact continuation

1. Reconcile all generic-title matches using creator, date, dimensions and holding.
   Keep the two already-present Greek records rather than importing again.
2. Resolve the six Mexican painter authorities from primary biographies, including
   missing dates and documented aliases. Reconcile institution identity for MUNAL,
   GNAMC and Theocharakis before creating any new institution.
3. Convert validated candidates into the existing pinned Go import format. These
   CSV files are not yet accepted for direct mutation. Back up the real DB in the
   approved Library location before any subsequent import; retain review status.
4. Rotate to Aivazovsky's individually linked collection records and regional
   holdings (Stavropol, Omsk and Pskov are catalogue leads, not checked holdings).
   Then continue Parthenis's catalogue and another Mexican or Italian institution.
5. Theocharakis has further unreviewed object links. Do not count its collection
   size as painting coverage, and do not assign dates to χ.χ. records.
6. Keep anonymous Greek/Byzantine and Russian icon work in the broader queue.
   The preceding Athens Michael/Marina Commons API captures remain unimported
   image leads under `content/imports/data-collection-20260912/athens-followup/`.
7. After metadata selection, resolve rights and physical-object image identity,
   download permitted full compositions <=100000 bytes, and verify attachments
   and HTTP delivery. Do not claim the Monet UI issue fixed from image counts.

## Sources

1. National Gallery Greece. [Konstantinos Parthenis](https://www.nationalgallery.gr/en/artist/parthenis-konstantinos/), accessed 12 September 2026. [Goulandris Harmony record](https://goulandris.gr/en/artwork/parthenis-constantinos-harmony) provides an additional collection and a differing birth-year statement.
2. National Gallery Greece. [Spyros Papaloukas](https://www.nationalgallery.gr/en/artist/papaloukas-spyros/) and [Boy with Suspenders](https://www.nationalgallery.gr/en/artwork/boy-with-suspenders/), accessed 12 September 2026.
3. State Russian Museum. [Aivazovsky authority and collection index](https://rusmuseumvrm.ru/reference/classifier/author/ayvazovsky_ik/index.php), [The Ninth Wave](https://rusmuseumvrm.ru/data/collections/painting/18_19/zh_2202/?lang=ru), [Wave](https://virtual.rusmuseumvrm.ru/mikh_palace/collection/russkoe_iskusstvo_vtoroy_polovini_xix_veka/volna/index.php), [Odessa](https://virtual.rusmuseumvrm.ru/mikh_palace/collection/russkoe_iskusstvo_pervoy_polovini_xix_veka/vid_odessi_v_lunnuyu_noch/index.php), accessed 12 September 2026.
4. Theocharakis Foundation. [Collection](https://exhibition.thfdigital.gr/%CF%83%CF%85%CE%BB%CE%BB%CE%BF%CE%B3%CE%AE/), accessed 12 September 2026.
5. Theocharakis Foundation. [Study for Boy with Suspenders](https://exhibition.thfdigital.gr/projects/111655/), accessed 12 September 2026. Other exact object URLs are in the follow-up CSV.
6. Museo Nacional de Arte. [Tesoros del MUNAL](https://munal.mx/es/tesoros-del-munal), accessed 12 September 2026. Only selected factual object fields retained, not catalogue essays.
7. Galleria Nazionale d'Arte Moderna e Contemporanea. [Morandi, Natura morta, inventory 8535](https://gnamc.cultura.gov.it/opera/natura-morta/), accessed 12 September 2026.
8. SearchCulture. [Papaloukas self-portrait record](https://www.searchculture.gr/aggregator/edm/theocharakis/000163-103449?language=en); Theocharakis Foundation, [original object](https://exhibition.thfdigital.gr/projects/103449/) and [terms](https://exhibition.thfdigital.gr/%CF%8C%CF%81%CE%BF%CE%B9-%CF%87%CF%81%CE%AE%CF%83%CE%B7%CF%82-2/), accessed 12 September 2026.
