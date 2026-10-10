# Painter influences — third research round

Latest continuation: [fourth research round](../painter-influences-round4-20261009/README.md) adds more individually reviewed evidence and a complete production-profile research register. Counts below describe the third round at its completion.

Completed 9 October 2026. This round added **324 relationships and 326 citations across 137 painter profiles** to production. All 324 were verified through the public API. The catalogue now contains **7,087 relationships and 8,140 influence citations**.

| New relationship type | Count |
|---|---:|
| Artistic influence | 264 |
| Teaching | 56 |
| Documented admiration | 4 |

The artistic influences concern **127 target painters**; **116 target profiles gained their first recorded artistic influence**. These are profile-level counts, not deduplicated historical-person counts. Teaching and admiration do not automatically establish artistic influence. See [additions by painter](additions-by-painter.md) for every addition, evidence note and source.

**18 relationships are documented by museum sources; 306 retain medium-confidence editorial-inference labels.** The latter are explicit assertions in individually read secondary-source passages whose underlying historical references were not independently checked. Publication preserves these qualifications. No new low-confidence Wikidata-only assertions were imported.

## Research and source decisions

This pass reviewed **150 additional biography passages** (queue indices 141–290), yielding 326 assertions, and **30 assertions from 12 museum source pages**. None of the 150 passages overlap with the first round's 407 or second round's 141 reviewed passages. The 356 interpreted assertions produced 348 eligible canonical pairs after consolidation and two held assertions. **24 existing pairs were skipped**, preserving their existing evidence and history.

Selected museum evidence comes from the National Gallery in London and the National Gallery in Athens. Newly added examples include Monet and Renoir → Manet, Bellini and Raphael → Lotto, Caravaggio and Ludovico Carracci → Guercino, and Lazzarini → Tiepolo as a teacher. Each claim preserves the source's period or medium limits.

The [Moralis interview catalogue](https://www.nationalgallery.gr/wp-content/uploads/2021/10/moralis_both.pdf) was read as text and visually checked on PDF pages 20–21 (printed pages 19–20). It supports De Chirico's influence on a specific Cavafy woodcut, a temporary phase shaped by Kontoglou's methods through Tsarouchis, and Moralis's expressed admiration for El Greco. These are qualified individually; admiration and named comparisons were not automatically converted into influence.

Kontoglou's existing profile was reconciled for research using its native National Gallery identifier and the [museum biography](https://www.nationalgallery.gr/en/artist/kontoglou-fotis/). The museum's 1896 birth year and the authority's 1895 remain documented variants. This research-only binding changed no database identity, date or biography. Its evidence is in [supplemental-identity-bindings.json](supplemental-identity-bindings.json).

Seven new claims retain authority-checked named sources without linked painter profiles; no placeholder painter records were created. Two proposed targets, Kumashiro Yūhi and Kishi Ganku, lacked an unambiguous library identity and were held. Other held readings include speculative training, group-level claims, impossible early chronology, mere resemblance, explicit dislikes and names that are fellow students rather than teachers. See [reviews.jsonl](reviews.jsonl), [supplementary resolutions](supplementary-review-resolutions.json) and [primary holds](primary-holds.json).

Fresh primary-source receipts record 19 requests, including the additional identity biography: 18 HTTP 200 responses and one 404. A retrieved page is not automatically accepted relationship evidence. The 30 selected assertions use 12 sources. Museum HTML/PDF captures remain private under `/Users/vadimdulub/Library/Application Support/Artline/research/painter-influences-round3-20261009/primary/`.

Wikipedia passages were retrieved on 8 October in the first pass and individually reviewed in this round; they are not represented as fresh fetches. Citations preserve revision URLs, original-wikitext paragraph hashes, retrieval/review timestamps and attribution to Wikipedia contributors under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Used primary captures and every reviewed biography context were checked against their recorded hashes.

This completes another selected research pass, not every painter's historical research. **1,339 passages remain in the selected queue**, and **19,870 of the original 20,568 discovered passages remain individually unreviewed**. The [remaining queue](remaining-candidate-passages.jsonl) excludes all first/second/third-pass reviewed leads represented in it. These are research leads, not accepted relationships.

## Production delivery and verification

The [immutable production plan](production-plan-v1.json.gz) has SHA-256 `dc3a717e4afe7b37c0d304766e1d0c23ef5ef6647f59f1fe29beec5b989bc700`. The [application receipt](production-plan-v1-applied.json) records the completed atomic transaction at `2026-10-09T06:14:29.851324+00:00`. Its scoped backup is:

`/Users/vadimdulub/Library/Application Support/Artline/backups/painter-influences-round3-20261009/production-plan-v1-before.json.gz`

The transaction inserted 324 published relationships and 326 citations, reusing existing source registries. It preserved all **6,763 prior claims, 7,814 prior influence citations and 4,001 checked painter rows**, including statuses and identifiers. No artworks, images, biographies, dates or review flags changed. The real local database remained read-only. No deployment or Git commit was performed in this round.

The user's earlier publication approval applies to the new claims. The unified catalogue already exposes active records regardless of historical status, so no painter-status rewrite was needed.

Six pure policy checks passed without database fixtures. Before commit, the transaction checked exact new rows, protected preimages, audit inserts and active citations. Catalogue cache revision advanced from 1040 to 1041. A [fresh read-only database verification](production-plan-v1-verified.json) then passed. The maximum incoming relationship count among affected painters was 14, within the API's 40-row bound.

The [public API verification](public-api-verification-passed.json) checked **all 137 target pages and all 324 new relationships**, including direction, type, evidence label, note and citation URLs, with zero outstanding failures. One endpoint initially returned HTTP 503; only that page was retried and it passed. The [initial receipt](public-api-verification-failed.json) is preserved, and the final receipt retains each page's actual verification time. A separate final read-only query verified total claims by type/status and the influence citation count. Machine-readable results are in [summary.json](summary.json).

Scripts: [delivery](../../../ops/apply-painter-influences-round3-20261009.py), [public verification](../../../ops/verify-painter-influences-round3-api-20261009.py), [report generation](../../../ops/finalize-painter-influences-round3-20261009.py). Earlier evidence remains in the [first round](../painter-influences-20261008/README.md) and [second round](../painter-influences-round2-20261008/README.md).
