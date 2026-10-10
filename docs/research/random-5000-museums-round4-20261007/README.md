# Fourth random 5,000 artworks: museum research

Completed 2026-10-07T17:01:22Z. **834 source-backed museum connections added in production**, across 278 museums. 39 new institution authorities remain in review.

| Outcome | Artworks |
|---|---:|
| collection lead below 80 after review | 2627 |
| duplicate or changed catalogue record | 12 |
| identified non museum collection | 89 |
| identified non museum site | 31 |
| museum assigned | 834 |
| no museum identified after research | 991 |
| object version or collection evidence below 80 | 65 |
| source reports private unknown or destroyed | 351 |

## Sampling and research

The fresh random sample contains 5,000 artworks selected without weighting from 63,122 eligible production records. It excludes all 15,000 records in the preceding three samples. The complete eligible UUID frame, seed, read-only repeatable-read snapshot and query plan are preserved.

All 5,000 received research: 783 initial exact-source reviews and 4,217 individual artwork searches. The exact query list and every response are retained. Captured WikiArt and Wikidata records were checked by native object identity, title and creator; selected museum catalogues, official national datasets and source indexes supplied additional evidence.

## Matching decisions

The user-approved minimum is 80% editorial confidence, an assessment of the evidence rather than a calibrated probability. Each accepted holding records its evidence, decision basis and limitations. Creator aliases were reconciled without changing creator labels or relationships. Museum services remain collection administrators; no branch, legal ownership or current display was inferred.

Translations and historical museum names were reconciled to existing institutions. Dealer labels including Brachot, Daniel Malingue and Normand were excluded from museum assignment. Private collections, libraries, civic bodies and historic sites are distinguished from museums. Photographic impressions, unidentified casts, conflicting locations and ambiguous versions remain unresolved unless exact-object evidence supports a decision.

Official object records corroborated selected sculptural versions and supplied accession numbers for duplicate checks. Repeated titles, studies, copies, prints, fragments and catalogued sets received additional review. Source dates and attributions remain visible even when they differ from the catalogue.

## Delivery and verification

All 834 writes passed production verification. 0 assignments made by concurrent catalogue work were observed separately and are excluded from this pass's write count. Twenty-three offline checks passed. Existing dates, images, creator labels/relationships and publication states were preserved. Each new holding has source evidence and a citation. No display assertions were added.

Recovery backup 1791386298193 completed successfully before delivery. Pinned plans and row preimages are retained under `~/Library/Application Support/Artline/backups/random-5000-museums-round4-20261007/`. The local catalogue was not written. No artworks or images were ingested; no commit or deployment was performed.

Research details were fetched in bounded batches scoped to sampled IDs. Native URL and institution/accession duplicate checks are preserved with query plans. This task does not establish ten-million-row performance; representative load testing and review of the broader holding-URL lookup remain outstanding engineering work. Access failures and unresolved source qualifications are retained in the evidence.

## Evidence

- [All 5,000 decisions](new-5000-results.md) and [machine-readable ledger](new-5000-results.json.gz).
- [Final production audit](final-audit.json) and [search coverage audit](search-completion-audit.json).
- [Additional version, attribution and dimension decisions](additional-editorial-decisions.json).
- Pinned delivery plans and verification receipts are under `delivery/`. Source captures, authority reviews and rejected-match reasons are preserved alongside this report.
