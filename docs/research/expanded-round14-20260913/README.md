# Expanded artwork research, round 14 — 13 September 2026

Completed and verified in local and production under the user's authorization to run another five rounds, 11–15. This round uses stable Rijksmuseum creator IDs and dated artwork activity from the accumulated official captures.

- Audited 76,889 retained unlinked artworks.
- Linked **21 artworks** to **21 new named painters** and **0 existing painters**.
- Enriched **21 artworks** with source-supported museum metadata.
- Remaining unlinked review artworks: **76,868**.
- No artwork rows were created or deleted; all accepted artworks remain `review` and `research_candidate=true`.

Source objects require exact full-name/title/museum/date matching, followed by creator authority or documented-name-and-biography reconciliation. Qualified attributions, uncertain identities and conflicting source objects are held. This round establishes museum person identities from dated artwork activity. Unknown birth/death boundaries remain NULL; timeline displays explicitly describe documented work rather than a lifespan. Unknown creation dates cannot establish an activity anchor. Original CSV records and supplied provenance are immutable. Museum presence is not promoted into a current-display claim. No images are downloaded by this metadata round.

The adjacent source-audit, source-match, hold and plan files preserve the decisions. Source captures and receipts are listed in `source-paths.json`. Plan SHA-256: `74bde7a2ed9ef364c4cb7fb087e60e4be3ba5fd2fe5917c33e2e75a11a8bf513`. Private plan/source archive: `gs://artline-508319-images/research/expanded-round14-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `082a0165d198ae450e3abd630b86b0ccf65845cd6b5b61b089e850a76f5e002f`. Its cloud size and MD5 were verified.

Fresh backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round14-20260913`. Local dump SHA-256 `f1546d7630bf894793781557baf1180bf7c69069745dc497251c2309ec7bf592` (363,630,188 bytes); archive directory checked. Fresh complete preimages of all 21 planned artworks and related mutable/provenance records were verified before writes, SHA-256 `cc628002c979401780820b92444a3a138c16c57a44d981311aa2a934b51542e1` (118,771 bytes). These scoped recovery records complement retained full managed backup 1789306647506; they are not a full database dump. Cloud SQL enforced its managed-backup frequency limit.

Guarded serializable transactions apply at most 100 rows per batch. The shared writer and migration-0018 ledger are reused; historical citation field names retain their `round2_` prefix, while plan hashes distinguish rounds. Local and production preflight hashes matched. After applying, verification checked every planned attribution, metadata patch, provenance row, review status and unchanged unrelated fields, excluding independently managed media pointers and audit timestamps. Final selected-row SHA-256 matched in both databases: `c94f2fbd17e05e453976c2dd6738e9ad9a1592816a2c2c259fe2fa7d57410b43`.

Live API checks are recorded in `live-verification.json`. Tests use offline metadata only; no fixtures or test databases were added to the real catalogue. These checks do not constitute a 10-million-row load test.
