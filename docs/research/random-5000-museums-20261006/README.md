# Random 5,000 artworks: museum research and production results

Completed 2026-10-06T18:59:09Z against the production catalogue. **492 artwork records now have a supported museum connection**, across **193 museums**. **13 further supported matches are held for duplicate-record reconciliation.** The other records retain explicit research outcomes and source leads; this report does not claim that every artwork belongs to a museum.

| Result | Count |
|---|---:|
| Randomly selected artworks with no institution or accepted holding | 5,000 |
| Eligible production population at selection | 60,482 |
| Supported source matches before duplicate checks | 505 |
| Museum assignments applied and verified | 492 |
| Duplicate or delivery conflicts retained for review | 13 |
| New institution authorities, all in review | 46 |
| Additional individual discovery queries | 4,631 |
| Source checks sufficient before that discovery pass | 369 |
| Complete artwork research coverage | 5,000 |

[All 5,000 outcomes and source links](results-5000.md) · [Machine-readable ledger](results-5000.json.gz) · [Final audit](final-audit.json) · [Frozen random sample](sample.json).

## What was researched

The sample is uniform and unweighted, drawn without replacement from all 60,482 eligible non-archived production records. The random seed, complete UUID sampling frame, query plan and initial snapshots are preserved. No weighting by artist, country, image availability or chance of a museum match was used.

The pass checked preserved WikiArt object pages for 2,495 artworks, 1,363 exact existing Wikidata artwork identities, supplied catalogue provenance, bounded official French and Italian object records, cached Finnish National Gallery and MoMA datasets, and 4,631 individual web queries. All 5,000 received either a sufficient exact-source check or an individual follow-up query. The queries produced leads for 3,237 artworks; those search hits were not treated as automatic assignments.

WikiArt is fully approved under the current project policy. Exact native artwork IDs, titles, creator variants, versions and explicit museum locations were still checked. Museum translations and cities were reconciled to existing authorities, including separate London, Oslo and Washington institutions. Unknown creators in icon and Fayum traditions were retained without inventing named artists. Prints without impression evidence, changed custody, private collections and incomplete museum identities remain visible in the ledger.

Official-source review excluded exhibition-history entries, related artworks, private loans and composite groups needing version checks. French records distinguish administering museum collections and documented incoming deposits from their separate deposit destinations and legal-owner fields. No current-display claim was created. The additional direct check of 71 selected primary pages preserved 64 successful responses, three HTTP 403 responses, two request failures and two skipped requests after a host failed; indexed primary-source captures remain separately identified.

## Outcomes for the full sample

| Outcome | Artworks |
|---|---:|
| collection lead requires verification | 1617 |
| no verified museum after bounded research | 2619 |
| museum assigned | 492 |
| source reports private unknown or destroyed | 172 |
| duplicate or delivery conflict requires reconciliation | 13 |
| specific print impression requires inventory or version evidence | 9 |
| documented non museum or unspecified collection body | 44 |
| documented non museum site or collection | 20 |
| historical or changed collection custody requires current authority review | 7 |
| institution identity requires individual review | 4 |
| museum department authority requires review | 1 |
| institution branch identity requires individual review | 1 |
| holding added by concurrent catalogue work | 1 |

Collection leads in the ledger are explicitly **review candidates**. They can name a museum, a public collection service or another holding body; Wikidata P195 and source excerpts alone were not used to invent accepted museum holdings. Unknown locations are not relabelled as private collections.

## Evidence, access limits and verification

Source pages, API responses, indexed captures, hashes, retrieval times, rejected candidates, pinned delivery plans and database receipts are retained in this directory. `primary-plans/`, `web-discovery/`, `primary-page-validation.json.gz`, `native-identity-preflight.json.gz` and `delivery/museum-holdings-03/` contain the main evidence. Earlier WikiArt plans and delivery wave 01 are superseded research drafts; no wave-01 writes occurred. The first wave-02 transaction rolled back because legacy capture receipts lacked a body-path field. Zero committed assertions were verified. All 500 final source bodies were then hash-verified, 162 legacy path mappings were normalized without inventing HTTP status, and fresh preimages were pinned for wave 03.

Wikidata fresh API access stopped after HTTP 429 at 400 entities; preserved entity captures covered the remaining existing identities. The Italian ArCo endpoint timed out after an initial bounded batch, so official indexed object records were used where available. Art UK and some primary hosts rejected direct access; no alternate endpoint, authentication or access-control bypass was attempted. Missing current records, version ambiguity, deposits, public agencies and unresolved authorities are retained as specific outcomes. One bounded pass is not proof that no further museum record exists.

Production changes add accepted holding assertions and citations and update only location/audit fields. Existing titles, dates, creator labels and relationships, identifiers, images and publication states were preserved against the locked preimages. Existing review assertions remain intact. All new institution authorities remain in review. No local database writes, new artwork imports, image downloads, publications, commits or deployments occurred.

Thirteen offline regression tests cover date/inventory confusion, creator and version collisions, museum cities, department mismatches, deposit roles, source URL migrations, reproducible sampling, legacy evidence-file validation and the production-only delivery guard. Database verification checks each applied holding, citation, revision and preserved relationship. This bounded research operation is not a 10-million-row performance benchmark.

Recovery backup: Cloud SQL **1791307556116**, verified `SUCCESSFUL`. Pinned row preimages and backup receipts are under `/Users/vadimdulub/Library/Application Support/Artline/backups/random-5000-museums-20261006/`.
