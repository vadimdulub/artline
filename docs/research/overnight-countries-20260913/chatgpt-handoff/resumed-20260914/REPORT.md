# Artline research: production delivery completed

Snapshot: 2026-09-14T05:49:56Z. The Google Cloud sign-in issue was resolved and the queued deliveries completed. Twenty country research rounds each for the Netherlands, Greece, Russia, France, Italy, Spain, Germany, Austria, Belgium, Finland and Portugal now have verification receipts in both databases. The ledger also includes 20 additional Greek historical scopes: 240 country scopes in total. Earlier primary-museum and selected-image follow-ups remain part of the research evidence.

| Result | Local | Production |
|---|---:|---:|
| Gross added artwork rows | 2,778 | 2,778 |
| Gross added creator profiles | 628 | 628 |
| Verified selected image assets | 1,564 | 1,564 |
| Active primary images | 1,554 | 1,554 |
| Artwork duplicates consolidated | 438 | 438 |
| Artist duplicates consolidated | 60 | 60 |


All 2,767 active added works remain **In review**, as do all added creator profiles. Gross inserted rows include replacements of earlier placeholders and rows subsequently archived; they are not a count of newly discovered physical objects. See [row-level identity notes](new_row_identity_review.csv).

## Completed production catch-up

The previously queued one Antwerp panel and 29 selected Finnish/Antwerp images were delivered. Production also received 200 artwork consolidations, four painter consolidations, 235 Finnish primary metadata updates, 222 Russian Museum inventory/material/dimension updates, two Antwerp title corrections, two anonymous-master type corrections and Kuznetsov’s added Ukrainian affiliation. These categories overlap and are not additive counts of distinct objects. Each mutation used the reviewed source evidence and target-specific preimages; changes stopped on conflicting identities or relationships.

Portuguese research prepared 74 candidates across 20 scopes. Fresh plans applied 60 records in both databases and delivered 29 selected images; 14 candidates remain held. The [Portuguese delivery ledger](portugal_research_delivery.csv) records the actual outcomes and reasons, including any additional holds found by the fresh identity checks. Held source facts and images were preserved; no invented creator or museum identity was imported.

Fresh checks added six holds to the eight earlier holds: three eighteenth-century works conflict with the candidate creator Francisco Smith’s 1881–1961 lifespan, and three undated Simão Álvares works lack usable creator chronology in the prepared import. The latter are retained as metadata proposals for primary identity/activity research; no birth, death or creation dates were invented. These are distinct limitations, not a claim that every held record is a proven duplicate or has the wrong creator.

## Country and review status

All 628 added creator profiles have cultural-affiliation records. 2,765 active added works have qualified creator-country links. Two works retain only a rejected historical attribution to Isaac Walraven and intentionally have no inherited artwork country. The Rijksmuseum object authorities are [SK-A-5036](https://id.rijksmuseum.nl/200653393) and [SK-A-5035](https://id.rijksmuseum.nl/200653392). Painter country, birthplace, imperial citizenship and museum location remain distinct.

The catalogue-wide queue still has 3,589 active profiles without documented cultural affiliation. [Country evidence](country_source_evidence.csv) includes source wording and authority links; a review citation is not publication approval. Kuznetsov’s additional affiliation is supported by the [Simferopol Art Museum biography](https://simhm.ru/collection/picture/1199-ko-dnyu-rozhdeniya-nd-kuznecova.html), not inferred from birthplace. Artwork dates remain uncertain where no reliable creation date was available; no current-display claims were invented.

## Duplicate and image evidence

Confirmed duplicate rows were archived with canonical redirects, preserving sources, artwork relationships, images, rights and alternative assertions. Similar titles, shared acquisition registers, recto/verso depictions and whole-work/panel images were not automatically merged. The 170 individually reviewed same-title pairs include 166 distinct-object decisions, two distinct recto/verso decisions and two confirmed Pavia duplicates. See [the decisions](same_title_primary_pair_review.csv) and [consolidation ledger](confirmed_duplicate_consolidations.csv).

Finnish identity checks used exact object IDs, inventories and maker records from the [Finnish National Gallery metadata export](https://kokoelma.kansallisgalleria.fi/api/v1/objects). Numeric artwork IDs were not confused with legacy artist identifiers. Russian Museum inventories distinguished 222 objects in 111 same-title pairs. Later primary metadata enrichment preserved source wording and uncertain dates.

The image CSV retains per-file rights, source pages, credits, SHA-256, dimensions and delivery paths. Reproductions were selected individually, and served derivatives are no larger than 100,000 bytes. Retained duplicate-record assets explain the difference between image-asset and active-primary-image counts. Metadata licensing alone did not authorize image delivery.

## Verification and remaining research

Fresh read-only audits checked this session’s receipt membership, publication state, country coverage, creator links, selection evidence, creation eligibility, validated foreign keys and image-file integrity. [Semantic parity](SEMANTIC_PARITY.json) compared stable catalogue fields, creator roles, country relationships, authorities, redirects and selected image metadata between separately captured local and production snapshots. This is scoped delivery verification, not a claim that every unrelated database row is identical or that every possible duplicate has been found.

Public delivery checks fetched all 58 newly delivered image assets since the earlier handoff and matched their SHA-256 values to the reviewed derivatives. Dutch and Portuguese timelines, plus sampled artwork pages and their data endpoints, returned successful responses. [Public verification receipt](PUBLIC_DELIVERY_VERIFICATION.json)

69,441 older review works still lack creator links across 27,252 labels. Country gaps, Portuguese holds and remaining duplicate candidates are research queues. The [ChatGPT prompt](RESEARCH_PROMPT.md) requests sourced proposals, preserves uncertainty and forbids direct database mutation. The earlier pre-reauthentication archive remains unchanged as dated evidence. No application deployment or publication was needed for these data updates.
