# Government Art Collection — 7 October 2026

The collection now has **203 linked artworks, including 200 with eligible creation dates**, with **203 distinct normalized inventories**. All remain in review. This campaign added **58 new paintings**, reconciled **123 existing holding links**, and filled **six previously unknown creation statements**. The 22 original linked records remain part of the total. The 72 existing illustrated records are unchanged; no images were added.

The collection’s database classification is unchanged. Its distributed embassy and government-building locations do not establish a single museum venue, physical custody or current display. Counts do not newly validate every legacy physical-object identity.

## Current evidence

- [Target verification](target-200-verification.json) checks the new records, both holding operations and the separate date enrichment.
- [58-work addition plan](gac-native-additions-001-plan.json.gz) and [applied receipt](gac-native-additions-001-applied.json): SHA-256 `2be8c75d7211175775d27d6a16cf54ba55fe2507c8f85d32c0fc924325e79c21`.
- [Six-date enrichment plan](gac-date-enrichment-001-plan.json.gz) and [applied receipt](gac-date-enrichment-001-applied.json): SHA-256 `a4c85616b479c535a14b12968c33080e1d6b1a36c66c1ca13f9dc68e5d6ef90d`.
- [New-object editorial decisions](new-artwork-editorial-003.json.gz) preserve 58 approvals and 42 held or deferred leads. Earlier review revisions remain evidence; the current revision corrects one acquisition-note transcription and records one failed native capture.
- [Latest campaign verification](../../verification-after-wave-31.json), [all added records](../../added-artworks-after-wave-31.csv), [holding reconciliations](../../reconciled-artworks-after-wave-31.csv), and [six date preimages/changes](../../gac-date-enrichments-after-wave-31.csv).

## New paintings

A bounded Wikidata discovery query supplied 150 dated painting leads: two already catalogued and 148 new source identities at that snapshot. The selected first 100 received current entity checks and official-page requests. **99 object pages succeeded; GAC 4996 returned 404.** The 58 approved additions represent 56 literal native creator names. All have distinct GAC numbers, explicit creation dates through 1970, dimensions, media and acquisition evidence. The native creator labels remain object-level labels; no artist links or biographies were invented.

Identity checks retained 75 artist IDs, 438 linked artwork rows, 1,018 surname-scoped unlinked labels, 1,034 exact-title matches and 17 bare-inventory matches. The selected 58 have no unresolved inventory collisions. Source URL and current Wikidata-ID checks exclude existing catalogue identities. The refreshed identity snapshot permits only the six documented date changes and their citations in the earlier scope.

Physical comparisons remain explicit. London Museum’s Bratby Blackheath 92.94 is 91.6 × 121.8 cm on canvas/wood; GAC 16935 is 122.5 × 150 cm on hardboard. Ceri Richards’ GAC 6686 is 26 × 36 cm, distinct from Tate’s 152.4cm-square Arabesque 3. Ian Stephenson’s four panels mounted on one board, GAC 9276, count as one work and retain their exact medium. Piper’s Sheffield Suburb is distinguished from the similarly sized Tate Forum through documented subjects; the Christie catalogue identifies Tate’s painting as a Roman subject. The Margaret Green Seaton Carew comparison remains unresolved; Art UK returned 403.

Kyffin Williams’ native GAC 13839 Date is 1970, despite the discovery index’s 1960. The native date supplies the new record; both source statements remain preserved. Bratby’s structured circa 1954–1956 range remains intact alongside the narrative’s 1954. Cornfields has inconsistent January/September 1956 acquisition statements; both are retained without choosing an invented month. Artist lifespans, acquisitions, depicted events and display histories never substitute for creation dates.

Source HTML, receipts, original fields, inscriptions, narrative, location labels and actual image rights remain in the evidence. No artwork image was downloaded or attached.

## Six separate date enrichments

| Existing object | Native creation statement | Result |
| --- | --- | --- |
| Egg, Feria at Seville,1883 | 1848–1860 | Date filled; holding accepted |
| Carlile, Lady Wearing an Oyster Satin Dress,18775 | 1650s | Full 1650–1659 range; holding accepted |
| Pettitt, Hilly Landscape with a Ruined Cottage,12551 | c.1850–1870 | Circa range; holding accepted |
| Youngman, King Street, Kingston,2372 | 1953 | Date filled; holding accepted |
| Vaux, Composition,4829 | 1957/1958 | Full1957–1958 range; holding accepted |
| Mynott, In the Conservatory,2295 | c.1952–1953 | Date filled; **no holding**, native record says missing |

The Carlile [primary PDF review](carlile-pdf-review-001.json) distinguishes the GAC canvas from the separately deattributed Ham House miniature and the Thirlestane miniature. The old Lely inscription and uncertain sitter remain source evidence. The structured 1650s date is not collapsed to a single guessed year. Only date_display, creation_year_start, creation_year_end and date_precision change; previous unknown values remain in backups and citations.

## Earlier 118 holding links

The [first holding plan](government-art-collection-existing-holdings-001-plan.json.gz), SHA-256 `c13bfe0ae06b93e5e845917cefe99445359938eec89683f3f8331ead78111a6b`, raised the collection from 22 linked/19 eligible to 140/137. It refreshed 135 eligible pending identities and captured 135 official GAC pages. The accepted 118 have matching object numbers, titles, creators, physical details and acquisition evidence, at 95% editorial confidence. Confidence is an editorial assessment, not a calibrated probability.

The [first editorial review](editorial-review-001.json) preserves 17 held cases involving creator qualifications, possible versions, a three-part screen, absent creation evidence or a canvas/stretcher ambiguity. Drummond14966 and1468 retain their distinct dimensions/acquisitions. Five native/imported artwork dates and 16 artist-lifespan differences remain unchanged, including Rose Bower’s native circa 1958–1959 versus imported 1926. Two records with “Origin uncertain” retain that unknown history. That holding-only operation did not rewrite catalogue dates or biographies.

The separate 88-page undated review found 81 blank creation fields, six explicit eligible statements now enriched, and one 1973 work. Blank fields and the 1973 record remain unchanged. The [eleven earlier web leads](new-native-discovery-001.json) remain research evidence, including one overlap with the later discovery pass. Two redirected print pages omit their former inventory numbers; impression/edition checks and other unresolved identities remain deferred.

## Verification and preservation

The date operation preserves all 242 scoped records except six four-field date patches and five institution links. It retains 604 older citations, 231 creator links, 80 media links and 242 identifiers, adding six citations and five accepted holdings. The missing-object pending assertion stays unchanged. The subsequent 58 additions preserve that complete 242-record baseline and add116 identifiers, 58 citations and 58 accepted holdings.

All 315 offline campaign tests passed, including 25 original GAC checks, 13 date-enrichment checks and 13 new-object checks. Both new operations passed zero-write replay. No database fixtures or test database were used. The [successor report adapter](../../../../../ops/museum-expansion-gac-target-report-20261007.py) verifies the prior 118 operation through the exact documented successor delta; its original strict pre-date verifier is retained as historical evidence.

Backups and preimages remain under `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-expansion-20261006/`. The shared importer and other campaign’s pinned scripts were not edited. A CSV report-header error occurred after database verification; its partial output is preserved in [report-attempt evidence](report-attempt-001.json). The corrected report handles both older and newer evidence columns. No database write depended on that failed report.

The preferred 200 eligible-date target is reached for this collection. Held candidates remain preserved for future identity or metadata research; quota completion is not permission to resolve unknowns automatically.
