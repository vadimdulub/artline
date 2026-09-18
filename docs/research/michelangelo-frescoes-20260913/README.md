# Michelangelo frescoes — 13 September 2026

Added **12 new fresco records and 12 matching images** to local and production. Michelangelo (`Q5592`, `michelangelo-q5592`) now has **16 works** in each database. The painter record and all four preexisting artworks are unchanged. New artworks and the two chapel institutions remain in review.

Public profile: https://artline-web-lpuqqlugnq-ew.a.run.app/artists/michelangelo-q5592

## Selection and evidence

A bounded selection of the nine central Genesis scenes, The Last Judgment, and the two Pauline Chapel frescoes. This does not claim to catalogue every individual scene or figure Michelangelo painted. Vatican sources support authorship, location and dating; Wikidata supplies stable artwork identities. Commons file metadata, source revisions and original-image checksums document image identity and reuse rights.

| Fresco | Identity | Dating stored | Image licence |
|---|---|---|---|
| Separation of Light from Darkness | [Q3955636](https://www.wikidata.org/wiki/Q3955636) | 1508–1512 | [Public domain](https://commons.wikimedia.org/wiki/File:Dividing_Light_from_Darkness.jpg) |
| The Creation of the Sun, Moon and Plants | [Q3696827](https://www.wikidata.org/wiki/Q3696827) | 1508–1512 | [Public domain](https://commons.wikimedia.org/wiki/File:Michelangelo,_Creation_of_the_Sun,_Moon,_and_Plants_01.jpg) |
| The Separation of the Earth and Waters | [Q3955632](https://www.wikidata.org/wiki/Q3955632) | 1508–1512 | [Public domain](https://commons.wikimedia.org/wiki/File:Michelangelo,_Separation_of_the_Earth_from_the_Waters_00.jpg) |
| The Creation of Adam | [Q500242](https://www.wikidata.org/wiki/Q500242) | 1508–1512 | [Public domain](https://commons.wikimedia.org/wiki/File:Michelangelo,_Creation_of_Adam_01.jpg) |
| The Creation of Eve | [Q3696835](https://www.wikidata.org/wiki/Q3696835) | 1508–1512 | [Public domain](https://commons.wikimedia.org/wiki/File:Michelangelo,_Creation_of_Eve_01.jpg) |
| The Fall and Expulsion from Paradise | [Q3898510](https://www.wikidata.org/wiki/Q3898510) | 1508–1512 | [Public domain](https://commons.wikimedia.org/wiki/File:Michelangelo,_Fall_and_Expulsion_from_Garden_of_Eden_00.jpg) |
| The Sacrifice of Noah | [Q3944655](https://www.wikidata.org/wiki/Q3944655) | 1508–1512 | [Public domain](https://commons.wikimedia.org/wiki/File:Michelangelo,_Sacrifice_of_Noah_01.jpg) |
| The Deluge | [Q3707697](https://www.wikidata.org/wiki/Q3707697) | 1508–1512 | [Public domain](https://commons.wikimedia.org/wiki/File:El_Diluvio.jpg) |
| Drunkenness of Noah | [Q116621556](https://www.wikidata.org/wiki/Q116621556) | 1508–1512 | [Public domain](https://commons.wikimedia.org/wiki/File:Michelangelo_drunken_Noah.jpg) |
| The Last Judgment | [Q567861](https://www.wikidata.org/wiki/Q567861) | 1536–1541 | [Public domain](https://commons.wikimedia.org/wiki/File:Last_Judgement_(Michelangelo).jpg) |
| The Conversion of Saul | [Q2432043](https://www.wikidata.org/wiki/Q2432043) | 1542–1545 | [Public domain](https://commons.wikimedia.org/wiki/File:Michelangelo,_paolina,_conversione_di_saulo_01.jpg) |
| The Crucifixion of Saint Peter | [Q1886263](https://www.wikidata.org/wiki/Q1886263) | 1545–1550 | [CC BY 3.0](https://commons.wikimedia.org/wiki/File:Michelangelo,_crocifissione_di_san_pietro,_1546-50,_02.jpg) |

The nine ceiling scenes use the documented **1508–1512 ceiling campaign**, explicitly labelled as such; individual scene dates remain in review. The Pauline Chapel history specifically dates Saul to 1542–1545 and Peter to 1545–1550. Those Vatican dates take precedence over differing Commons filename/Wikidata dates. No exact creation year was invented. The Vatican title “Sun, Moon and Plants” is used, retaining the Wikidata English label as an alternate title.

The Peter photograph is by **Sailko**, reused under **CC BY 3.0** with photographer attribution, source link, licence link and resizing/compression notice. The other eleven files are documented as public domain. Images were visually checked as a contact sheet before insertion. Only these twelve selected originals were downloaded; all delivered JPEGs preserve the selected source frame and are at most 100,000 bytes. No generated artwork images were used.

Documented holdings were added for Sistine Chapel and Pauline Chapel as historic sites. No current on-view, public-access or fresh display assertion was created. Accession numbers and dimensions remain unset where not established.

## Verification

- Both databases: 12 new frescoes, all linked to Michelangelo Q5592, all with primary media, rights evidence, source citations and accepted source-backed holdings.
- Both databases: existing painter and four existing works match their pre-import snapshots exactly.
- Production: anonymous works endpoint returns all 16 works, including the 12 review records.
- All 12 public image URLs return HTTP 200 with matching SHA-256 and byte counts; local assets match the same hashes.
- Anonymous profile returns HTTP 200; protected editor coverage endpoint returns HTTP 401.
- Browser integration could not bootstrap because the tool reported a missing sandboxPolicy field. Visual image review and production HTTP verification completed; no browser-rendering test is claimed.
- No application code, infrastructure, publication status or existing record was changed. No deployment was required. These scoped checks do not establish 10-million-row load performance.

## Durable evidence and recovery

- `researched-records.json`, `prepared.json`, `captures/`, `image-receipts/` preserve primary evidence and selected image metadata.
- `visual-review.json` identifies the reviewed manifest by SHA-256.
- `local-applied.json`, `production-applied.json`, `verification.json` record application and verification.
- Source images and database preimages are under `/Users/vadimdulub/Library/Application Support/Artline/backups/michelangelo-frescoes-20260913/`.
- Successful managed Cloud SQL backup: `1789308907271` (before this import).
- Shared cloud images: `gs://artline-508319-images/assets/artworks/imported/michelangelo/`.
- Preparation/application entry point: `ops/import-michelangelo-frescoes.py`; read-only verifier: `ops/verify-michelangelo-frescoes.py`. The importer uses immutable evidence, conditional uploads, stable IDs, database transactions and conflict guards; it does not replace existing artwork identities.

Initial Wikimedia search responses containing `maxlag` errors are retained as failed retrieval evidence, not evidence that no artwork exists. Subsequent known-entity captures and explicit Commons file queries resolved the selected records.
