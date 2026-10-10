# Random 5,000 artworks — museum matching at the approved 80% threshold

Completed 2026-10-07T10:53:56Z. Production assignments and a fresh final database audit are recorded below.

**909 museum connections added in production**, across 278 museums. 73 new museum authorities remain in review. Existing artwork publication states, dates, creator labels/relationships and images were preserved.

| Result | Fresh random 5,000 | Earlier 489 leads |
|---|---:|---:|
| collection lead below 80 after review | 2572 | 381 |
| duplicate or changed catalogue record | 14 | 0 |
| identified non museum collection | 107 | 0 |
| identified non museum site | 15 | 0 |
| museum already assigned since previous pass | 0 | 2 |
| museum assigned | 848 | 61 |
| museum assigned by concurrent catalogue work | 121 | 0 |
| no museum identified after research | 943 | 0 |
| object version or collection evidence below 80 | 77 | 45 |
| source reports private unknown or destroyed | 303 | 0 |

## Sampling and research

A fresh sample of 5,000 was drawn without weighting from 60,547 eligible production artworks, excluding all 10,000 artworks in the previous two samples. The random seed, complete UUID frame, query plan and baseline are preserved. The 489 still-unresolved original leads were added as a separate follow-up cohort.

All 5,000 new records received research: 795 initial exact-source reviews and 4,205 individual follow-up searches. All 489 older leads also received a new individual search. Exact cached WikiArt and Wikidata object captures, verified creator authorities, official museum catalogues, French and Italian object data and indexed primary sources are preserved with retrieval times and hashes.

## Decisions

The assistant made the matching decisions at the user-approved minimum 80% editorial confidence. Confidence is an assessment of the evidence, not a calibrated probability. Source object identity, creator and version checks remain mandatory; each accepted claim records its evidence and limitations.

Museum services were verified against official collection pages. Their collection administration is retained without guessing a specific venue or current display. The Atkinson historical gallery/library identity was reconciled to its current museum collection; a library label alone was not used as a reason to reject that art gallery. Other libraries, private collections and government bodies remain explicitly distinguished from museums.

Mixed WikiArt locations were examined individually. The Velázquez Emmaus painting matches the Irish version by title and dimensions; the James Ward mill is documented by the National Library of Wales. The Canaletto page lacks enough version evidence to choose between two museums. Duplicate source objects and shared inventories were checked before delivery.

Unassigned outcomes document non-museum collections, private/unknown whereabouts, insufficient object/version evidence or duplicate catalogue identities. No manual verification is requested from the user.

## Production verification

909 museum links were applied and verified across 278 museums. 121 assignments by concurrent catalogue work were observed separately and excluded from this pass’s write count. Twenty-one offline regression checks passed. Each applied artwork has a sourced accepted holding and citation; artwork metadata, creator relationships, dates, images and publication status were verified unchanged. No current-display claims were added.

Recovery backup 1791368481137 completed successfully. Pinned preimages are under `~/Library/Application Support/Artline/backups/random-5000-museums-round3-20261007/`. The local catalogue was not written. No artworks were ingested, images downloaded, commits made or deployment performed.

Source access failures and unresolved qualifications remain in the evidence. Queries were scoped to the sampled IDs and selected institutions. Sampling necessarily enumerated eligible UUIDs; details used bounded batches. The institution/accession check used the indexed bitmap path. The broader holding/source-URL audit used a parallel sequential scan; an indexed URL lookup and representative load testing remain necessary before routine use at ten-million-record scale.

## Per-artwork results

- [Fresh 5,000 decisions](new-5000-results.md) and [machine-readable ledger](new-5000-results.json.gz).
- [489 original unresolved leads](prior-489-leads-results.md) and [machine-readable ledger](prior-489-leads-results.json.gz).
- [Final database audit](final-audit.json).
- Pinned plans and verification receipts are in `delivery/`; exact source captures and reviews are retained alongside this report.
