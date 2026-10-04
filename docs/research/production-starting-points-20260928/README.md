# Production starting-point expansion — 28 September 2026

User-authorized local and production update. All 31 topics pass the 100-picture minimum and have a working representative cover. The smallest gallery is 104 works. Existing larger period collections remain available in pages of at most 150.

Deployed to the [production All tab](https://artline-web-lpuqqlugnq-ew.a.run.app/all). API revision `artline-api-starting-0928-r2` and web revision `artline-web-starting-0928` each receive 100% of service traffic. The matching local frontend/API remain running. Deployment image pins were updated locally; no Terraform apply or commit was performed.

## Data and images

Transferred **891 new artwork records and 883 stored image files**, comprising the [873-work starting-point expansion](../all-starting-points-expansion-20260928/README.md) and the separately completed [18-record decolonisation research batch](../decolonization-deep-20260928/README.md), including its ten image files and five existing selections. Also delivered the three source-backed US cultural-affiliation repairs and all bounded source, place, holding, media and collection dependencies: **6,930 inserted rows** in total. No existing production records were deleted or overwritten; all new records remain in review, with no new publication or on-view assertions.

The 873-image expansion contains 760 CC0 museum reproductions and 113 NASA photographs under its educational/informational permission. The decolonisation batch retains its original territorial public-domain, fair-use and unknown-rights labels and unverified status. Its delivery is not a new rights-clearance assertion. The image bucket remains private; the app retains its personal research preview configuration.

Image uploads used create-only generation preconditions and checked local SHA-256/size and stored MD5/size for every file. Catalogue inserts were pinned by plan SHA-256, checked against exact target absences, verified within one transaction, then verified again after commit. Existing target identities and production-only material were preserved; this explains small count differences in broader local and production galleries. No database replacement was necessary.

Cloud SQL recovery backup **1790597235330** completed before mutation. The local recovery dump and private service configurations are under `Library/Application Support/Artline/backups/`. Migration `0031_archive_institutions.sql` adds an archive institution kind, keeping NASA distinct from a physical museum. Catalogue records do not assign NASA a physical holding.

## Application and verification

Every starting-point entry now displays its selected picture, retaining the established featured cards and dark list. Small previews request small image sizes. Cover UUIDs are resolved through a bounded, indexed set of reviewed slug identities, since earlier independent imports sometimes assigned different local/production IDs. The gallery retains its compact title/creator presentation.

Go tests, 180 frontend unit tests, lint, real read-only catalogue/cover/pagination tests, and all six local and six production browser tests passed. The browser tests exercise all 31 topic selections, their filters, reset/reload behavior and accessibility at desktop/mobile sizes. All 31 covers decoded without errors or page overflow.

Production candidate API checks verified every topic's minimum count, image presence, artwork cutoff and bounded page size. Final topic requests completed within 1.56 seconds in this sample. Broader filter checks, requested alongside filter metadata, completed without timeouts: Renaissance with countries cleared 1.02 s; civil-rights context with creators cleared 2.34 s; the full illustrated 1700–2000 view 3.00 s. These are observed sample timings on the current production instance, not latency guarantees or a 10-million-row load benchmark. Post-ingestion VACUUM/ANALYZE and representative local EXPLAIN ANALYZE receipts are retained.

The first production browser run exposed a civil-rights clear/reload taking more than 20 seconds despite passing a standalone API sample. Migration `0032_atlas_image_evidence_indexes.sql` fixes the repeated large-row reads with a partial image-delivery index and a covering accepted-holding index. Both were installed concurrently in local and production databases. No query membership or data changed: four complete before/after local responses and SQL statements are identical. The production artwork query retains 9,154 results, takes 1,709 ms versus 7,108 ms before, and performs zero heap fetches for 9,158 image and 8,426 holding checks. The full production browser suite then passed, including desktop/mobile clearing and reload. The read-only regression test checks the actual covering-index plan on the real catalogue, with no test fixtures inserted.

## Verified artwork counts

| Starting point | Local | Production |
| --- | ---: | ---: |
| Writing and the first cities | 139 | 139 |
| The classical world | 202 | 202 |
| Buddhism and its early journeys | 279 | 279 |
| The Silk Roads | 331 | 331 |
| Byzantium | 122 | 122 |
| Islamic worlds and learning | 231 | 231 |
| Tang and Song China | 170 | 170 |
| West African trade and learning | 105 | 105 |
| The Mongol world | 168 | 168 |
| The Renaissance | 1664 | 1664 |
| Printing and the Reformation | 1956 | 1956 |
| 1492 and the Atlantic encounter | 451 | 451 |
| The Mughal world | 127 | 127 |
| Edo Japan | 2766 | 2766 |
| The Scientific Revolution | 1404 | 1404 |
| The Enlightenment | 2790 | 2791 |
| Women’s rights | 133 | 133 |
| The French Revolution | 253 | 253 |
| The Industrial Revolution | 214 | 214 |
| Romanticism | 2192 | 2192 |
| Empire and resistance | 10398 | 10428 |
| Modern life and modernism | 1681 | 1681 |
| The First World War | 122 | 122 |
| The Russian Revolution | 129 | 129 |
| Between the world wars | 199 | 199 |
| The Second World War | 126 | 127 |
| Decolonization | 104 | 104 |
| The Cold War | 112 | 113 |
| The US civil rights movement | 128 | 128 |
| The Space Age | 107 | 107 |
| The digital turn | 122 | 122 |

## Receipts

- `catalogue-plan.json` and `catalogue-plan-summary.json`: immutable bounded plan.
- `catalogue-applied.json` and `catalogue-verified.json`: exact write/read-back verification.
- `new-image-delivery.json`: all 883 verified object hashes and generations.
- `source-manifest.json`, `api-v3-source-manifest.json`, `*-build-verified.json`: sealed source and successful image builds; the API v3 receipt verifies Cloud Build's source SHA-256 against the local archive.
- `candidate-api-indexed-smoke.json`, `illustrated-counts.json`, `local-*-plan.json`: final API counts, timing and query evidence. Earlier candidate receipts are retained separately.
- `atlas-evidence-indexes.json`, `atlas-index-comparison.json`, `cloud-plan-*.json`: index delivery and unchanged-result performance proof.
- `production-final-services.json`, `e2e-production-final.log`: verified live revisions/traffic and passing full production browser suite.

Final canonical-URL checks also passed: all 31 cover images decoded at 1440 px and 390 px, the Space Age gallery loaded, and neither view had page overflow or browser/API/image errors. Desktop/mobile civil-rights clearing and reload passed again after both traffic switches. See `production-live-browser.json`, `e2e-live.log` and `final-readiness.json`.
