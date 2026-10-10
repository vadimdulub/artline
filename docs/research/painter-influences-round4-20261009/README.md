# Painter influences — fourth research round

Completed 9 October 2026. Added **451 relationships and 455 citations across 209 painter profiles** to production. All additions were verified through the public API. Production now contains **7,538 relationships and 8,595 influence citations**.

| New relationship type | Count |
|---|---:|
| Artistic influence | 305 |
| Teaching | 137 |
| Documented admiration | 9 |

**160 profiles gained their first recorded artistic influence**. All additions, notes and source links appear in [additions by painter](additions-by-painter.md). Teaching and admiration remain separate from artistic influence. Counts refer to catalogue profiles; unresolved duplicate historical persons are not silently merged.

## Whole-library coverage

The research register covers all **23,769 active profiles** in the production snapshot of `2026-10-09T08:57:39.366940+00:00`. Every profile has a recorded lookup attempt across the research rounds. The initial discovery pass freshly searched the **170 newcomers** absent from the original register, retained 95 supported research-only identity bindings, and retrieved 92 identity-checked biographies in seven languages. All 62 keyword passages discovered in that initial discovery were individually reviewed. Identity matches do not by themselves establish influence, and no database identities were rewritten.

The final count found 100 additional active profiles absent from the pinned import snapshot. A separate [read-only catalogue catch-up](catalogue-catchup/production-snapshot.json) searched all of them and collected 24 further biography passages. Those passages remain research leads for individual review; no extra claims were automatically published. The original import snapshot, immutable plan and earlier summary were preserved. This brings the register to the current snapshot total shown above.

After this import, **1,447 profiles have at least one recorded artistic influence**, and **3,518 have at least one influence, teacher or admiration relationship**. **22,322 still have no recorded artistic influence.** All-painter historical research remains incomplete. A failed lookup or absence of evidence in checked sources does not mean the painter had no influences.

| Current research state | Profiles |
|---|---:|
| artistic influence recorded | 1,447 |
| biography passages require review | 5,868 |
| further source research needed | 2 |
| identity unresolved after lookup | 3,345 |
| no relationship in checked sources | 11,036 |
| teaching or admiration only | 2,071 |

The [complete painter register](painter-research-register.json.gz) records identity IDs, lookup evidence, relationship counts, reviewed passages and remaining lead IDs per profile. The [remaining painter research list](remaining-painter-research.json.gz) contains all profiles without an artistic influence, prioritizing those with unreviewed biography leads. The state label is a next-action classification, not a statement that all historical literature has been examined.

Across the rounds, **960 passages have been individually reviewed**; **19,694 discovered passages remain unreviewed**. The narrower [selected queue](remaining-candidate-passages.jsonl) has 1,139 passages remaining and is not the whole-library backlog. The final read-only count found 23,769 active production profiles; snapshot coverage is anchored to its recorded time.

## Evidence reviewed this round

Reviewed **262 new biography passages**: 200 previously retrieved passages at queue indices 291–490 and all 62 fresh newcomer passages at indices 1630–1691. None overlap earlier individually reviewed leads. The older passages retain their original retrieval dates; they are not represented as fresh fetches. Revision URLs, original-wikitext hashes, review times, source attribution and [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) licensing are retained.

Selected **49 assertions from 19 museum biography pages**. Source captures include 12 London National Gallery requests and 20 Athens National Gallery requests. Five London requests returned 404; four successful HTTP responses had no usable substantive biography. HTTP success alone was not evidence. All accepted source captures and reviewed biography contexts passed hash checks.

Examples of source-backed museum readings include [Mantegna and Francesco Morone → Gerolamo dai Libri](https://www.nationalgallery.org.uk/artists/gerolamo-dai-libri), [Corot → Volanakis, specifically landscapes](https://www.nationalgallery.gr/en/artist/volanakis-konstantinos/), [Lipparini → Tsokos](https://www.nationalgallery.gr/en/artist/tsokos-dionysios/), and the artists whose work shaped [Vryzakis’s style and historical subjects](https://www.nationalgallery.gr/en/artist/vryzakis-theodoros/). These museum assertions may consolidate with biography claims or be skipped where a relationship already exists.

The 531 interpreted assertions consolidated into 488 eligible canonical pairs; 37 existing pairs were skipped. Existing claims and citations were preserved, including their prior qualifications. New claims comprise **39 documented/high-confidence relationships** and **412 qualified editorial-inference/medium-confidence relationships**. Secondary biographies contain explicit relationship statements, but their underlying historical references were not independently verified. No Wikidata-only influence statement was imported automatically.

Fresh article/authority lookups resolved selected named sources. [Supplementary resolutions](supplementary-review-resolutions.json) preserve those decisions and a corrected QID transcription caught before planning. Held examples include a historian mistaken for a similarly named painter, a footballer mistaken for an artist’s brother, conflicting authority labels, speculative tuition, impossible chronology, group-level traditions, mere resemblance, and social acquaintance. No placeholder painter profiles were created. 58 new claims retain a checked source name without a linked painter profile.

Import guard holds:

- source painting practice not established by checked authority occupations: 8 assertions.
- target has no unambiguous identity in the research roster or fresh production Wikidata identifiers: 25 assertions.
- teacher died before pupil was born: 1 assertions.

See [individual reviews](reviews.jsonl), [museum decisions](primary-decisions.json), [museum holds](primary-holds.json), [named-source lookup receipts](named-source-resolution-receipts.json.gz) and [name-search identity decisions](name-search-identity-decisions.json.gz). Private raw evidence remains under `/Users/vadimdulub/Library/Application Support/Artline/research/painter-influences-round4-20261009/`.

## Production verification

The [immutable plan](production-plan-v1.json.gz) has SHA-256 `8c1a36016e8fa1d28d1b27f3ac757a7e6be9070496ebdf6b873aebc1e7f77a33`. The [application receipt](production-plan-v1-applied.json) records the completed atomic transaction at `2026-10-09T08:49:41.843034+00:00`. Scoped backup:

`/Users/vadimdulub/Library/Application Support/Artline/backups/painter-influences-round4-20261009/production-plan-v1-before.json.gz`

The transaction preserved **7,087 existing relationships, 8,140 influence citations and 4,193 checked painter rows**, including identifiers, dates and statuses. The real local database was not modified. No deployment or Git commit was performed. Earlier publication approval covers the new relationships; unified catalogue visibility required no painter-status changes.

Six pure policy/evidence tests passed without database fixtures. The atomic transaction checked new rows, protected preimages, audit inserts and active source citations before committing. Catalogue cache revision advanced from 1082 to 1083. [Fresh read-only database verification](production-plan-v1-verified.json) passed; the maximum incoming relationship count on affected targets was 9, within the API’s 40-row bound.

[Public API verification](public-api-verification-passed.json) checked **all 209 affected target pages and all 451 additions**, including direction, type, evidence label, note and citation URLs. There are zero outstanding failures; 38 pages required a separate retry pass. Final read-only queries independently checked relationship totals by type/status and the influence citation total. Machine-readable results: [current summary](summary-catalogue-catchup.json).

Scripts: [research register](../../../ops/research-painter-influences-round4-20261009.py), [delivery](../../../ops/apply-painter-influences-round4-20261009.py), [public verification](../../../ops/verify-painter-influences-round4-api-20261009.py), [report generation](../../../ops/finalize-painter-influences-round4-20261009.py). Earlier evidence: [round 3](../painter-influences-round3-20261009/README.md).
