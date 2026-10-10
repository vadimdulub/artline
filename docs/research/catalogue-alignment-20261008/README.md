# Local to production catalogue alignment — 8 October 2026

Completed the user's instruction: **add data that production lacks from local, in that direction only**. The user separately approved deployment of the anonymous-museum visibility fix. The real local database was queried read-only throughout; no local fixtures, commits, Terraform changes or publication changes were made.

## Delivered

| Production additions | Count |
|---|---:|
| Review artworks | 6,200 |
| Review institutions | 108 |
| Accepted, documented holding assertions | 6,500 |
| Source citations | 6,609 |
| Native external identifiers | 6,692 |
| Source definitions | 109 |
| Artist links on new artworks | 39 |
| Venue records | 25 |
| Places | 69 |
| Countries | 6 |

The holdings comprise the 6,200 new artworks plus **300 existing artworks whose production holding was empty**. One existing institution's empty place was filled from local. Existing populated catalogue fields, images, source labels and publication states were preserved. All new artworks remain in review; fifteen retain unknown creation dates. Holdings do not establish current display.

[All added artworks](all-added-artworks.csv) lists every new object, creator label, museum, dates and native source identifier. Delivery happened in three guarded transactions:

1. **6,105 artworks across 122 institutions**, with 6,105 holdings/citations, 6,594 identifiers and 71 sources. Of the original 6,304 missing local slugs, 199 already represented production objects under other identities. Native identifiers, inventories, source URLs and individual version checks prevented duplicate imports.
2. The local [Africa expansion](../morocco-africa-20261008/README.md) arrived during the comparison. Its 97 local artworks became **95 production additions and two existing-object reuses**, together with 108 institutions, 69 places, six countries, two venues, 38 missing source definitions, 39 artist links, 207 citations and 98 identifiers/holdings. The source-definition count also includes twelve older, previously missing definitions. Three empty production artwork holdings and one empty institution place were filled.
3. A final relationship comparison found **297 additional accepted local holdings absent from production**, across eight museums. Their 297 new citations and assertions were copied, filling only empty production holdings. All 293 prior production assertions and the existing artworks' other fields were preserved exactly. Source qualifications remain intact, including the Armenian Wikidata assessments at 80% editorial confidence and their explicitly unverified legacy museum URLs.

The two additional same-work decisions concern Mahmoud Said/Saiid's *The Artist's Mother* and *My Friend in the Mixed Courts*. Visual comparison of the retained museum PDF against the existing WikiArt images confirmed identical compositions. The mother's dimension discrepancy remains in the evidence; neither production dimensions nor dates were replaced. Both existing images were preserved. See [the decisions](supplemental/title-review-decisions.json).

## Cyprus visibility

Production already contained **169 Cyprus institutions and 1,869 artwork holdings**. Missing venue geography excluded them from the country filter, and a separate API condition hid artworks with neither an artist link nor a creator label.

- Added **23 source-backed venue records for the 22 Cyprus institutions with artworks**. The State Gallery has separate SPEL and Majestic venues. Existing institution and artwork records were preserved.
- Removed the creator-label requirement for artworks without artist links. Existing artwork/artist publication checks and archive checks remain in force. No creator labels were invented.
- After the user's explicit deployment approval, built from the exact live API source and changed only the visibility predicate and its tests. Runtime environment, secrets references, resources and service settings were preserved. No unrelated working-tree changes were deployed.
- **Live verification:** [Cyprus collections](https://artlines.org/museums?country=CY) returns 22 collections. [Cyprus Museum](https://artlines.org/museums/cyprus-museum-nicosia) returns 102 works, including its anonymous objects, with bounded pagination. Institutions without artworks remain outside this collection directory.

Release: `artline-api-cyprus-visibility-1008`, receiving 100% of production traffic. Build `74a10e55-68f8-448c-b4de-f032ecb93be0`; image digest `sha256:7f257aa6c89f5c0300865110f6da50933b960c88a93e7d47cebc1ce7e25f5194`. The previous revision is `artline-api-loading-fixes-1007`.

## Verification and scope

- Complete inserted-row comparisons passed inside each transaction and independently afterward. Existing artwork preservation checks allow only the documented empty-holding fills. Museum, citation and previous-assertion preimages were also checked.
- The final identity snapshot covers artists, artworks, institutions, media, books, book creators, events, sources, places, movements, venues, curated collections and research snapshots. **No unresolved missing catalogue objects remain in that snapshot.** The 201 remaining local artwork slugs map to verified existing production objects, rather than additional physical works.
- All local artist links and primary-image attachments were represented in production. Of 154 absent local media UUIDs, 146 reuse identical existing production images; their checksums, sizes, rights, source pages, licences and attachments were checked. Eight unused placeholder rows have no image files or catalogue attachments and were not copied.
- The accepted-holding comparison's 297 gaps are resolved by the final independently verified transaction. This is catalogue identity and relationship alignment, not a byte-for-byte mirror of historical audit/import records or an overwrite of differing existing metadata.
- **24 live artwork API samples** passed across the three data deliveries. The deployed Cyprus country filter, museum count and seven-item pagination passed. Both public page URLs returned HTTP 200, and the Cyprus Museum page contained its title and museum content.
- Three focused museum directory tests passed. A read-only integration test verified the real Cyprus Museum's 102 anonymous holdings, 22 country-filter collections and the continued exclusion of review records from published-only browsing. The Linux API build passed. These checks make no claim of ten-million-row load testing.
- Browser automation could not start because the browser connection failed. Visual UI automation was therefore unavailable; HTTP page and live API verification succeeded. Initial API timeouts during a slow comparison query resolved after cancelling that read-only query; all subsequent samples passed. An unrelated broad comparison test was interrupted and is not reported as a passing test.

The working catalogue changed concurrently during the task. The first read contained 307,904 local artworks; the final identity snapshot contained 308,001. Production's final identity snapshot contained 391,820 artworks and 2,055 institutions, including other independently running production work. Those global count changes are not attributed entirely to this sync.

## Evidence and recovery

- Main: `delivery-plan-pin.json`, `delivery-applied.json`, `delivery-verification.json`, `version-decisions.json`, `public-artwork-recheck.json`.
- Supplement: `supplemental/delivery-plan-pin.json`, `supplemental/delivery-applied.json`, `supplemental/delivery-verification.json`, `supplemental/public-checks.json`.
- Holding relationships: `remaining-holdings-plan-pin.json`, `remaining-holdings-applied.json`, `remaining-holdings-verification.json`, `remaining-holdings-public-checks.json`.
- Cyprus: `venue-plan-pin.json`, `venues-applied.json`, `cyprus-geography-evidence.json`, `api-release-preflight.json`, `api-build.json`, `api-candidate-verification.json`, `api-production-verification.json`, `api-visibility.patch`.
- Final comparison: `final/presence-comparison.json`, `final/relationship-gaps.json` (pre-repair), `final/completed-alignment.json`; image evidence: `image-gap-verification.json`.

Cloud SQL recovery backup **1791456055193** completed successfully before writes. Scoped source packages, immutable delivery plans, production preimages, after-state evidence, service configurations and the local database snapshot are under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/catalogue-alignment-20261008/`

The earlier broad `inventory/` capture was abandoned in favour of narrow identity reads; its partial files are preliminary evidence, not the final comparison. Disposable release files and PDF review renders are in `/tmp`. Existing research captures and artwork assets were preserved.

Implementation: `ops/align-catalogues-20261008.py`, `ops/align-catalogues-supplement-20261008.py`, `ops/align-catalogue-holdings-20261008.py`. Each apply path protects the reviewed source and target state, uses the shared curated-ingestion advisory lock and commits transactionally. Applied receipts prevent replaying a delivery. Credentials and member/account data stay target-local.
