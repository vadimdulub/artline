# Artline catalogue expansion

Audience: Artline owner and maintainer. Date: 10 September 2026, Asia/Nicosia. Scope: approved local museum-data expansion, with an artwork-creation cutoff of 1970. Source captures and import evidence are dated 9 September UTC. No commits or cloud changes.

## 63,073 works in the local database

Added 28,809 museum-connected artworks to the verified baseline of 34,264. The 50,000 lower target is reached; 100,000 is not. These are persisted PostgreSQL counts, confirmed by import receipts and unchanged replay fingerprints, not projected catalogue totals.

| Source | New works | What was imported |
|---|---:|---|
| France - Joconde | 26,295 | 15,852 drawings, 5,364 paintings, 5,079 prints; 213 new institution/collection rows. |
| Italy - Milan SIRBeC | 2,075 | 1,722 drawings, 331 paintings, 22 prints; 10 new institution/collection rows. |
| Russia - Pushkin KAMIS | 439 | Paintings; another 33 source records matched existing works instead of creating duplicates. |
| Total added | 28,809 | Descriptions and source provenance; no new image downloads. |

Official metadata sources: [Collections des musees de France: base Joconde](https://www.data.gouv.fr/datasets/collections-des-musees-de-france-base-joconde), French Ministry of Culture, updated 9 September 2026; [Opere d'Arte conservate nei Musei nel Comune di Milano](https://dati.comune.milano.it/dataset/ds617_opere_darte_conservate_nei_musei_nel_comune_di_milano), Regione Lombardia, source rows updated 7 September 2026; and the [Pushkin electronic collection, painting fund](https://collection.pushkinmuseum.art/entity/OBJECT?fund=13), accessed 9 September 2026 UTC.

New coverage includes 5,285 works associated with Musee Gustave Moreau, 3,185 with Musee Ingres Bourdelle, and 2,771 with Musee National Picasso-Paris. In Milan, additions include 1,094 Castello Sforzesco graphic-collection works, 609 Academy of Brera works and 121 Ambrosiana works. Pushkin now has 488 records. These are imported counts, not the museums' complete holdings.

The whole database contains 9,985 paintings, 24,133 drawings, 28,950 prints and 5 frescoes. Artist records remain 5,315; media assets remain 230. The 280 institution/collection rows include departments, so they are not necessarily 280 distinct physical museums.

All new works remain in review, with no new masterpiece designations, publication or current-display claims. Every new work passes the creation policy. Across the entire database, 63,071 pass and two preexisting records still require date review. This is broader museum coverage, not a claim that every imported work is an independently validated masterpiece.

## Verification, rights and next step

Identity safeguards. Imports map only to existing creator authorities using full normalized name/alias equality and conflict checks, not fuzzy surnames. Qualified authorship, multiple creators, grouped objects and conflicting or unresolved dates are deferred. This is a machine-assisted crosswalk awaiting editorial review, not individual art-historical authentication. Conservative date ranges preserve source uncertainty; artist lifespans never supply missing creation years.

One concrete duplicate avoided: Monet's Luncheon on the Grass, accession Ж-3307, remains one work with both the legacy and KAMIS source IDs. The museum's [1866 object record](https://collection.pushkinmuseum.art/entity/OBJECT/78221) supports the match (Pushkin Museum; accessed 9 September 2026 UTC). Academy of Brera collections remain distinct from Pinacoteca di Brera. France's already-used primary museum catalogues retain priority: 2,721 overlapping national records were deferred pending accession and holding reconciliation.

Reproduction rights. France's downloadable metadata is reusable with attribution, but images and protected material require separate checks: [POP data reuse](https://pop.culture.gouv.fr/donnees-ouvertes), Ministry of Culture, accessed 9 September 2026 UTC, and [Licence Ouverte 2.0](https://www.data.gouv.fr/pages/legal/licences/etalab-2.0), Etalab, version 2.0. Milan's [dataset metadata and field dictionary](https://www.dati.lombardia.it/api/views/5gfm-gsfr.json) declares CC0 for the dataset, not a blanket photo licence (Regione Lombardia; rows updated 7 September 2026). Pushkin's [materials-use policy](https://pushkinmuseum.art/usage_policy/index.php?lang=ru), approved 30 December 2014 and checked this pass, imposes separate permissions. Its new app descriptions contain factual metadata, not protected museum essays or photographs. No new images were added.

Persistence and API checks. All 59 bounded, atomic chunks passed rollback preview, apply and replay. Fourteen table fingerprints prove preview and replay changed no persistent rows. Existing artist, image, rights and curated-item data were preserved. The full Go suite with PostgreSQL integration checks and go vet passed. Twenty-six API requests checked museum counts, keyset pages, details, artist chronology, Monet-or-Pissarro filtering and private/public visibility. No frontend changes or browser QA were performed in this pass.

Performance evidence is limited. A museum-scoped query passed on 100,000 temporary works in 2.870 ms. A separate identity test used 100,000 unrelated works, identifiers and citations and verified all three identity indexes without sequential scans. Actual local museum first pages took 116-361 ms; next pages reached 425 ms. These are sampled local observations, not concurrent production or 10-million-row benchmarks. A pre-import database backup has a verified checksum and readable archive catalogue, but has not been restore-tested.

Next bounded expansion: the [regional Lombardia parent feed](https://www.dati.lombardia.it/resource/ay8b-p38f.json), Regione Lombardia, rows updated 7 September 2026, exposes 54,484 painting/drawing/print candidates. It includes the Milan subset, so this count is not additive and is not an eligible import forecast. Expand incrementally with the same identity, date and museum checks. This pass did not harvest the Russian Museum, Hermitage or Tretyakov, nor complete a census of European museums. Prioritize those evidence gaps and selected rights-cleared images alongside continued editorial review.
