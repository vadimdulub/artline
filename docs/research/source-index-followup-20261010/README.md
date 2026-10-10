# Source-index image follow-up — 10 October 2026

Delivered **5 additional WikiArt images** to existing production records after checking 193 exact native objects from Belvedere and Detroit. All five passed visual inspection, strict decoding, public asset SHA-256 checks, database preservation checks and public artwork readback. No user review is pending.

The delivered works are Anton Romako's *On the Balcony* (1878) and *Girl Picking Apples* (1882), August von Pettenkofen's *Austrian Soldiers Crossing a Ford* (1851) and *Horse Market in Szolnok I* (1870–1880), and Jacob Jordaens's *Job* (1620). Each match has the same native creator, unique title, creation bounds and explicit museum holding. Historical catalogue dates, attribution, holdings and statuses remain unchanged. No creator links or catalogue records were invented.

Existing artist identifiers and previously captured Wikidata P6002 evidence supplied additional WikiArt profile bindings. The pass checked 34 unique creator profiles. Evidence, unresolved names and unmatched objects remain in `resolution-v2.json.gz`, `additional-artist-authorities.json.gz` and `native-v2/`. The earlier one-image resolution and contact sheet are preserved.

Version review excluded the Louvre's *Adoration of the Shepherds* and the National Gallery London's *The Market Cart*: their same-titled Detroit objects are different versions. *The Little Gardener* remains unmatched because WikiArt supplies neither a creation date nor a museum holding. The listed *Entombment of Christ* page lacked native artwork metadata. See `manual-version-review.json`.

Only the approved WikiArt images were uploaded. The selected native Belvedere photographs carry private/scientific or private-only wording; Detroit's selected native records have empty copyright fields. These do not establish image reuse under Artline's existing public-use policy. The exact policy captures are in the main batch's `additional-policy-review.json`; Japan E-Museum also restricts website republication. No permissions were requested from third parties and no access denial was bypassed.

Cloud SQL backup `1791631795709` predates both operations. Fresh follow-up row preimages and transaction postimages are under `~/Library/Application Support/Artline/backups/source-index-followup-20261010/`. Production changes ran in a separate bounded transaction using row locks, the curated-ingestion advisory lock and exact preimage equality. There were no local database writes, status changes, deployments or commits.

Follow-up plan SHA-256: `e37abeb675e6a9d6a4e7e91b8b2dafd6c0da9c50c6a29a3b07d4b52996dd36a3`. Receipts: `production-applied.json`, `production-verification.json`, `public-api-verification.json`, `uploads/`, `visual-review.json`, `strict-image-decode-check.json`.

The [combined delivery report](../source-index-delivery-20261010/README.md) covers both batches. Its `combined-delivery-summary.json`, `combined-source-ledger.json.gz` and `combined-artwork-ledger.json.gz` retain the latest totals without overwriting the original batch receipts.
