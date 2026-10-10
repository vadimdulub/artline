# Painter influences — second research round

**Later research:** the [third round](../painter-influences-round3-20261009/README.md) added 324 relationships and 326 citations across 137 painter profiles. Production now contains 7,087 relationships and 8,140 influence citations. This report retains the second round's historical figures.

Completed 9 October 2026, Cyprus time (8 October UTC). The user requested another research round after approving production import and publication. This round added **374 relationships and 377 citations for 145 painters** to production. All 374 were verified in the public API responses for their target painters. The catalogue now contains **6,763 relationships and 7,814 influence citations**, including the preserved earlier records.

| New relationship type | Count |
|---|---:|
| Artistic influence | 291 |
| Teaching | 69 |
| Documented admiration | 14 |

The 291 artistic influences concern 120 target painters. Teaching and admiration are separate types; neither automatically establishes artistic influence. See [additions by painter](additions-by-painter.md) for the individual additions and sources.

Of the new relationships, **17 are documented by museum or foundation sources** and **357 retain medium-confidence editorial-inference labels** because they are explicit secondary-source assertions. Those biography assertions were read for names, direction and context; their underlying historical references were not independently verified. Publication does not remove these qualifications. No new low-confidence Wikidata-only assertions were imported.

## Research and decisions

This pass individually reviewed **141 additional biography passages**, producing 376 candidate assertions, plus **30 assertions from eight museum/foundation pages**. The selected primary material includes the National Gallery in Athens, the Russian Museum, the B. & M. Theocharakis Foundation, the Metropolitan Museum of Art and the National Gallery of Art in Washington.

The 406 interpreted assertions yielded 400 eligible canonical pairs after within-pass consolidation and two held targets. **26 already-recorded pairs were skipped**, preserving their earlier evidence, confidence, citations and publication history. The two held assertions concern Palamedes Palamedesz. and Jean Pierre François Lamorinière as targets whose identities could not be bound unambiguously to the pinned library roster. Other paragraph-level ambiguities and rejected readings remain in [reviews.jsonl](reviews.jsonl) and [primary-holds.json](primary-holds.json).

Examples of newly added museum-supported influences include Titian and Tintoretto → El Greco, Cézanne → Maleas and Parthenis, Picasso → Ghika, Kuindzhi → Rylov, and Kontoglou → Papaloukas. The citations preserve any work, medium or period qualification. Eight new claims retain named, authority-checked sources without linked painter profiles; no new profiles or placeholder biographies were created.

Identity checks use the original roster's source-backed bindings and fresh production identifiers. Conflicting authority IDs, archived endpoints, impossible chronology and posthumous personal teaching are excluded. Existing equivalent pairs are detected across supported shared identities and unlinked-source authority evidence. This round deliberately does not expand each new relationship to every duplicate catalogue profile or merge identities.

Cached Wikipedia passages were retrieved on 8 October during the first pass; this round records the later individual review and preserves the exact revision URL and original-wikitext paragraph hash. Wikipedia contributors are attributed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Primary pages were fetched separately. Direct HTTP access to the Met and NGA pages was blocked, but complete text was available through the web page reader; that access method is explicitly recorded. Blocked pages without adequate full-text access were not treated as independently read evidence.

Raw source captures are preserved under `/Users/vadimdulub/Library/Application Support/Artline/research/painter-influences-round2-20261008/primary/`; earlier biography contexts remain in the first run's private research directory. Used primary-capture hashes and all reviewed biography contexts were checked against their recorded hashes.

This is an additional research pass, not completion of every painter's historical research. **1,489 passages remain in this round's selected queue**, and **20,020 of the original discovered passages remain individually unreviewed**. These are leads, not accepted relationships. The [remaining queue](remaining-candidate-passages.jsonl) excludes all 141 passages reviewed here. Collective movements, shared exhibitions, friendships and simple resemblance were not expanded into individual influence pairs.

## Production delivery and verification

The [immutable production plan](production-plan-v1.json.gz) has SHA-256 `280d84ab220734d04d929be1b1d2e4147f06295cea4982e68bb472670f3e2bc1`. The [application receipt](production-plan-v1-applied.json) records the completed atomic transaction at 21:06:38 UTC. A scoped backup was created before the write at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/painter-influences-round2-20261008/production-plan-v1-before.json.gz`

The transaction inserted 374 published claims, 377 citations and one source-registry entry for the Theocharakis Foundation. **Every existing claim and influence citation was preserved**, as were all 3,878 checked painter rows, their historical statuses and external identifiers. No artworks, images, catalogue dates, biographies or factual review flags changed. The real local database was not modified. No application deployment or Git commit was performed in this round.

The unified catalogue was already live on API revision `artline-api-unified-catalogue-1008-1955`; review status no longer hides active painter profiles. This round therefore preserved painter statuses and required no publication rewrite. New relationships use the user's existing publication approval.

Six pure policy checks passed without a database or fixtures. The transaction verified exact row contents, existing preimages, active citations and audit inserts before commit; catalogue cache revision advanced from 839 to 840. A [fresh read-only database verification](production-plan-v1-verified.json) passed after commit. The largest incoming relationship count among affected painters was 14, within the API's 40-row bounded response.

The [public API verification](public-api-verification-passed.json) checked **all 145 target pages** and found **all 374 new incoming relationships**, matching their types, evidence labels, notes and citation URLs, with zero failures.

Delivery script: [apply-painter-influences-round2-20261008.py](../../../ops/apply-painter-influences-round2-20261008.py). Public verification: [verify-painter-influences-round2-api-20261008.py](../../../ops/verify-painter-influences-round2-api-20261008.py). The [first run](../painter-influences-20261008/README.md) and its pinned artifacts remain preserved.
