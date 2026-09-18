# Expanded artwork research, round 9 — 13 September 2026

Completed and verified in local and production under the user's authorization to continue through 5–10 research rounds. This round uses stable creator authorities from the Finnish National Gallery, Walters, MoMA, Tate and Rijksmuseum, backed by documented artwork creation periods.

- Audited 77,856 retained unlinked artworks.
- Linked **193 artworks** to **193 new named painters** and **0 existing painters**.
- Enriched **177 artworks** with source-supported museum metadata.
- Remaining unlinked review artworks: **77,663**.
- No artwork rows were created or deleted; all accepted artworks remain `review` and `research_candidate=true`.

Source objects require exact full-name/title/museum/date matching, followed by creator authority or documented-name-and-biography reconciliation. Qualified attributions, uncertain identities and conflicting source objects are held. This round does not require a known lifespan: it requires a stable museum person ID and an eligible dated artwork. Missing birth/death boundaries remain NULL. Timeline and activity display explicitly describe a documented work period, not a lifespan. Unknown creation dates cannot establish a new activity anchor. Original CSV records and supplied provenance are immutable. Museum presence is not promoted into a current-display claim. No images are downloaded by this metadata round.

The adjacent source-audit, source-match, hold and plan files preserve the decisions. Source captures and receipts are listed in `source-paths.json`. Plan SHA-256: `e14e29eef986c5e5937adf09be50c7005fdfcc1f349d8c957f969dfceb7bec8f`. Private plan/source archive: `gs://artline-508319-images/research/expanded-round9-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `6f984bf8cf9a48ae050c3374e1f8782fd513aa5482826a310270599f1d770b63`. Its cloud size and MD5 were verified.

Fresh backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round9-20260913`. Local dump SHA-256 `377965b8a63d163c0844a775340ecd3037e0d73c59f56f2477ad553cab650206` (355,232,120 bytes); archive directory checked. Managed production backup `1789305018899` completed successfully before writes.

Guarded serializable transactions apply at most 100 rows per batch. The shared writer and migration-0018 ledger are reused; historical citation field names retain their `round2_` prefix, while plan hashes distinguish rounds. Local and production preflight hashes matched. After applying, verification checked every planned attribution, metadata patch, provenance row, review status and unchanged unrelated fields, excluding independently managed media pointers and audit timestamps. Final selected-row SHA-256 matched in both databases: `79da0c9261517227ca52237c66481285280519a24525c11df67897f50ccdcff9`.

Live API checks are recorded in `live-verification.json`. Tests use offline metadata only; no fixtures or test databases were added to the real catalogue. These checks do not constitute a 10-million-row load test.

One dated artwork establishes each authority. Additional works are deferred to round 10, so incomplete artwork dates can subsequently be linked to an already established museum identity. Existing matching names, shortened-name possibilities, known authority ownership and duplicate museum authority names are held; this does not use surname-only matching. Two anonymous Master labels, including a Finnish/Swedish catalogue formulation, were caught in the final name review and excluded. The unapplied draft is preserved under `draft-before-anonymous-name-review/`.

The dedicated activity writer validates in Python and PostgreSQL that each activity interval matches its source artwork, lies in or before 1970, and belongs to the stated museum creator ID. It never fills missing lifespan boundaries with activity years. A guarded first-record application proved the SQL path before completing the remaining local entries; every row then passed local and production metadata/timeline verification. Offline tests reject anonymous Master names, missing authority IDs, unknown work dates, post-cutoff anchors and unsupported expansion of activity dates.
