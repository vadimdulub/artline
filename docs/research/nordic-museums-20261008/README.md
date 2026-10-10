# Denmark, Sweden and Norway museum coverage — 8 October 2026

The user requested an attempt to cover all Danish, Swedish and Norwegian museums and galleries. This completed bounded production pass adds **109 review artworks** and **40 institutions**, supplies additional evidence for **24 existing artworks**, and verifies geography/authority updates for **25 existing institutions**.

## Verified live country coverage

| Country | Browsable collections before | Browsable collections after | New artworks |
| --- | ---: | ---: | ---: |
| Denmark | 6 | 36 | 75 |
| Sweden | 1 | 11 | 20 |
| Norway | 1 | 19 | 14 |

Country pages were read with bounded keyset pagination. Every returned collection has a positive artwork count, correct country and unique identity. All 133 selected artwork states, 66 affected nonempty museum detail pages and 15 representative live artwork detail responses passed verification. Artwork API samples include the five direct museum objects, all selected unknown-date objects and a new/existing sample per country. New objects remain **review**, including 5 explicitly undated records. Existing dates, titles, creator links, images and publication states were preserved.

## Coverage and limits

The research directory contains 574 art-institution/collection leads found across targeted Wikidata museum, gallery and painting-collection indexes, plus a direct-source Vigeland Museum addition. Bounded indexes were checked for all 574 original leads; a first page is not an exhaustive collection catalogue. The broad Swedish general-museum discovery hit its row cap; targeted art-institution and collection discovery supplemented it. This is **not a complete national museum census**, and the represented collections do not have complete inventories.

The final selection contains 133 accepted objects after identity reconciliation. 1300 source object records and 8 additional database identity candidates remain unresolved or outside this selection. The gap ledger records empty source indexes, uncertain custody, unsupported references, later dates, qualified objects and ambiguous institutional identities. A missing Artline collection does not mean that a real museum has no artworks. No works were invented to make a museum visible.

## Evidence and identity

Actual catalogue sources are referenced Wikidata collection statements, explicitly reviewed Wikimedia Commons file-description metadata, and five directly verified museum catalogue entries/collection-guide objects from Vigeland and Millesgården. Commons fields were read as text; no reproduction files were downloaded. Unreferenced collection claims were withheld unless their exact object-specific collection evidence was reviewed. The Commons review accepted 45 corroborations and left 121 unresolved; an example rejection was a source caption describing an etching despite a painting classification.

Editorial holding confidence is 0.85 for accepted secondary-source evidence and 0.99 for the selected direct museum entries; these are assessments, not calibrated probabilities. Original source credits, collection names, native references and limitations are in the citations. Referenced pages are not described as independently fetched unless a capture exists. No current-display assertions were created.

Official museum pages establish Kode/Bergen, Kunstsilo/Sørlandet, Frederiksborg and Zorn institutional or collection continuity. The original collection identities remain in object evidence. Rasmus Meyer remains a distinct documented collection. Sweden's National Portrait Gallery and the Smithsonian National Portrait Gallery are different institutions; the initial name-only draft mapping was rejected before any database writes. The Danish and Swedish national museums were also distinguished despite a shared translated label. The obsolete Funen museum identity remains unresolved rather than creating a separate current collection.

Vigeland's four records identify the museum's original plaster versions (1889–1900), including the 1894 Rizpah version rather than its 1892 predecessor. Millesgården's record is the 68.5 cm bronze **M 119 B**, dated 1952–54 by the museum; it is not identified as the monumental outdoor cast. Missing painter authorities remain object-level creator labels. No artist biographies were invented.

## Verification and recovery

Eleven offline evidence/identity regression checks pass. Read-only identity checks used exact source identifiers, institution-scoped inventory matches and indexed title/creator lookups. Ambiguous versions were withheld. A broad initial inventory read timed out; the final procedure uses bounded institution groups and selected title/inventory filters. The retained execution plan describes the current production catalogue, not a 10-million-row load test.

Cloud SQL backup **1791475818698** succeeded before writes. Immutable final plan SHA-256: `abcbbe66930e997aefe080b6a58faf331af17f013f19bd1140b18f53aff1dc83`. Recovery plans, locked preimages and transaction postimages are under `/Users/vadimdulub/Library/Application Support/Artline/backups/nordic-museums-20261008`. Earlier superseded drafts and source captures remain as audit evidence. The real local database was queried read-only; no local catalogue writes, test databases or fixtures were created. No application deployment, Terraform apply or Git commit was made.

## Deliverables

- [Delivered artwork records](delivered-artworks.csv)
- [Complete coverage and gap ledger](coverage-and-gaps.csv)
- [Production application receipt](applied.json)
- [Database verification](database-verification.json)
- [Live API verification](api-verification.json)
- [Source and object decisions](held-source-records-v3.json)
- [Reviewed Commons corroborations](commons-reviewed.json)

Procedure: `ops/nordic-museums-20261008.py`. Tests: `ops/test_nordic_museums_20261008.py`.
