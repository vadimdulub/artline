# Third French museum pass — 8 October 2026

Added **73 real local artwork records**, all in review: 50 drawings, 13 prints, six paintings and four sculptures. Évreux and Tournus now exceed 100 eligible records. The other three museums still need evidence-backed additions.

| Museum | Added | Linked before → after | Eligible before → after |
| --- | ---: | ---: | ---: |
| musée Girodet — Montargis | 6 | 80 → 86 | 73 → 79 |
| musée d'art, histoire et archéologie d'Evreux — Evreux | 36 | 74 → 110 | 74 → 110 |
| bibliothèque-musée Inguimbertine — Carpentras | 1 | 82 → 83 | 75 → 76 |
| musée du château de Flers — Flers | 4 | 75 → 79 | 75 → 79 |
| musée Greuze - hôtel-Dieu — Tournus | 26 | 80 → 106 | 78 → 104 |

The verified September Joconde snapshot contained 1,796 rows for these museums, including 1,398 new source identities. Two bounded queues selected 123 complete current records, all returned with HTTP 200. Individual review approved 73 and held 50. Another 1,275 unique leads remain held or outside this selection. The supplemental 55 records supersede their initial exclusions; they are not counted twice.

Official Museofile context explicitly identifies Tournus's short museum name. Montargis's official operator supports its intercommunal public owner. These narrow parser adaptations preserve original location, legal labels and source fields. Deposit and missing-object exclusions remain in force. Optional Flers context capture ended with an incomplete-response transport error; it was not used to approve records, and the dependent optional Carpentras context capture was not reached.

The identity scope includes 36,894 existing artworks and 77,629 citations, with former Nevelson/Berliawsky and Janssens/Dietrich labels plus Schidone/Schedoni, Hondecoeter/Hondecooter and Del Marle variants. All 123 source facts and comparisons were recomputed against the final scope. Two Évreux Joconde references describe one Rome painting with an existing counterpart; neither became another artwork. An inventory shared across different museums is retained as a false-positive lead, not a match. Grouped and uncertain versions remain held. Girodet recto/verso drawings, multi-figure sheets and individually inventoried print impressions each count as one physical unit.

Creator labels and qualifications stay literal, including anonymous ancient sculpture and the Mayo/Milliarakis and Puni/Pougny aliases. The 1970 Alechinsky drawing is eligible. Represented historical years and sitter life dates do not replace creation dates. Current Maury chronology, a Leroy print mentioning Greuze's 1805 death despite eighteenth-century dating, books, casting dates, source medium conflicts and unresolved physical counterparts remain research holds. Missing dimensions, unknown lower date bounds and source dating differences remain explicit. Holdings do not establish current display.

The [plan](france-third-additions-001-plan.json.gz), [individual decisions](editorial-reviewed-001.json.gz), [application receipt](france-third-additions-001-applied.json) and [wave58 verification](../../verification-after-wave-58.json) document the additions. Readback verifies every new row, identifier, citation and holding assertion, preserving 3,046 scoped existing records and all 6,671 prior campaign records with associated data. The import uses the local loopback database only. No images, painter authorities, publication changes or display claims were added.

Twenty-two fresh offline checks passed; 904 historical checks remain pinned, for 926 cumulative verified checks. Historical tests were not all rerun; these checks are not a load-performance benchmark. Replay wrote nothing. Backups and execution logs are in Library, not scattered across Documents. The [delivery checkpoint](delivery-checkpoint-001.json) pins the evidence and the explicit root README supersession.

Campaign totals: **5,959 additions and 785 existing-record links across 169 expanded institutions**. Tournus and Montargis are newly expanded. All five museums were already included in source-pass totals, which remain 350 museums plus Barnes. A fresh audit has **1,184 canonical museum entries below 100 linked records** and **1,288 below 200**, with no unrelated coverage changes. The overall goal remains active. The separate minimum-100 job is terminal, unchanged and counted separately.
