# Random 5,000 artworks — museum matching at the approved 80% threshold

Completed 2026-10-06T20:34:27Z. Production assignments and a fresh final database audit are recorded below.

**2,250 museum connections added in production**, across 492 museums. 135 new museum authorities remain in review. Existing artwork publication states, dates, creator labels/relationships and images were preserved.

| Result | Fresh random 5,000 | Earlier 1,617 leads |
|---|---:|---:|
| collection lead below 80 after review | 1505 | 446 |
| duplicate or changed catalogue record | 13 | 0 |
| identified non museum collection | 130 | 181 |
| identified non museum site | 9 | 0 |
| museum assigned | 1303 | 947 |
| museum assigned by concurrent catalogue work | 48 | 0 |
| no museum identified after research | 1736 | 0 |
| object version or collection evidence below 80 | 50 | 43 |
| source reports private unknown or destroyed | 206 | 0 |

## Sampling and research

The new cohort was sampled without weighting from 63,667 eligible production artworks. All 5,000 records in the preceding sample were excluded. The cryptographic seed, full UUID frame, query plan and frozen source metadata are retained in `sample.json`, `sampling-frame.json.gz` and `baseline.json.gz`.

All 5,000 new records received research: 1,160 initial exact-source reviews and 3,840 individual follow-up searches. The first 1,617 leads were independently reassessed against exact source objects, creator authorities, museum identities, official catalogues and the earlier search evidence. The evidence includes 2,513 exact Wikidata artwork entities, captured WikiArt pages for 2,966 artworks, official French and Italian catalogues, selected cached Finnish National Gallery and MoMA data, 960 new indexed-search captures and direct primary-page checks.

## Decisions

The assistant made the matching decisions at the user-approved 80% editorial threshold. Each accepted claim records its source, confidence basis, retrieval time and limitations. Confidence values are editorial assessments rather than calibrated probabilities. Single active museum-collection statements with exact artwork and creator identity plus inventory/native catalogue evidence were accepted; verified unlinked creator labels were retained without creating artist relationships.

Museum ownership, collection administration, receiving-museum deposits and current display remain distinct. The Louvre/Versailles collection-role conflict was resolved using the explicit receiving-museum deposit. The Night Watch and Ingres’s The Source were checked against official catalogue records; another catalogue record already represents The Night Watch, so the duplicate was held. Shared accessions for distinct recto/verso or multipart records were reviewed and retained as separate catalogue objects.

Unassigned records have a recorded reason, including non-museum collections, private/unknown locations, ambiguous versions and duplicate catalogue identities.

## Production verification

The first delivery transaction stopped before writes after concurrent museum assignments changed its pinned records. Zero task assertions from that attempt were verified. A fresh plan preserved those other assignments; successful delivery batches and verification receipts are in `delivery/`. Only this pass’s writes are counted as added here.

Fifteen offline adversarial checks passed. Database verification confirmed one sourced accepted holding and citation per applied record, unchanged artwork metadata and relationships, unchanged images and publication states, and zero new display claims. Recovery backup 1791313987669 is successful; pinned preimages are under `~/Library/Application Support/Artline/backups/random-5000-museums-round2-20261006/`. No local catalogue writes, artwork ingestion, image changes, commits or deployment occurred.

The initial search rate limit was allowed to clear; all 3,840 follow-up searches subsequently completed at reduced concurrency. Direct HTTP 403 responses and request failures are retained honestly. Scoped duplicate-check query plans were inspected. The wide institution/source-URL audit chose a parallel scan; institution/inventory matching used an indexed bitmap plan. This bounded production research pass is not a 10-million-record performance test; an indexed source-URL path and representative load testing remain prerequisites for routine use at that scale.

## Per-artwork results

- [Fresh 5,000 decisions](new-5000-results.md) and [machine-readable ledger](new-5000-results.json.gz).
- [Earlier 1,617 decisions](prior-1617-leads-results.md) and [machine-readable ledger](prior-1617-leads-results.json.gz).
- [Final database audit](final-audit.json).
- Pinned source plans: `primary-plans/combined-80-reviewed.json.gz`, `primary-plans/delivery-80-verified.json.gz`, and `primary-plans/separate-parts-reviewed.json.gz`. Earlier assessment and delivery drafts remain preserved.
