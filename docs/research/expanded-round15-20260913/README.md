# Expanded artwork research, round 15 — 13 September 2026

Completed and verified in local and production under the user's authorization to run another five rounds, 11–15. This round uses fresh reconciliation against all prior official captures and the painter identities established through round 14.

- Audited 76,868 retained unlinked artworks.
- Linked **53 artworks** to **0 new named painters** and **18 existing painters**.
- Enriched **53 artworks** with source-supported museum metadata.
- Remaining unlinked review artworks: **76,815**.
- No artwork rows were created or deleted; all accepted artworks remain `review` and `research_candidate=true`.

Source objects require exact full-name/title/museum/date matching, followed by creator authority or documented-name-and-biography reconciliation. Qualified attributions, uncertain identities and conflicting source objects are held. This round creates no painters and changes no existing biographies or activity intervals. Previously established museum creator identities support these further artwork links; unknown creation dates remain unknown. Original CSV records and supplied provenance are immutable. Museum presence is not promoted into a current-display claim. No images are downloaded by this metadata round.

The adjacent source-audit, source-match, hold and plan files preserve the decisions. Source captures and receipts are listed in `source-paths.json`. Plan SHA-256: `dcc350ef68427264fc5430e07dc1becd42cbf01a9b5d6dc99dea2ffd68d80c67`. Private plan/source archive: `gs://artline-508319-images/research/expanded-round15-20260913/plan-and-sources-v2.tar.gz`, SHA-256 `3cf642aa6ff3bc84d21f7fc82c3c81c1f5322b5200fe430b1fc2e73ca744f3c2`. Its cloud size and MD5 were verified.

Fresh backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round15-20260913`. Local dump SHA-256 `7cf7b5bee7f7ddaa7e2d93bd27b6f7e2abc9cf09d95ee3fcf56602f3f03c3253` (363,786,614 bytes); archive directory checked. Fresh complete preimages of all 53 planned artworks and related mutable/provenance records were verified before writes, SHA-256 `010aa85b764621d060360c14d4b96656d4a7c9961daa06486bbe972cb9438b12` (370,605 bytes). These scoped recovery records complement retained full managed backup 1789306647506; they are not a full database dump. Cloud SQL enforced its managed-backup frequency limit.

Guarded serializable transactions apply at most 100 rows per batch. The shared writer and migration-0018 ledger are reused; historical citation field names retain their `round2_` prefix, while plan hashes distinguish rounds. Local and production preflight hashes matched. After applying, verification checked every planned attribution, metadata patch, provenance row, review status and unchanged unrelated fields, excluding independently managed media pointers and audit timestamps. Final selected-row SHA-256 matched in both databases: `ff839e356748cfab6fc2400d30ef136412c787605862544ae2484689c3f4cc37`.

Live API checks are recorded in `live-verification.json`. Tests use offline metadata only; no fixtures or test databases were added to the real catalogue. These checks do not constitute a 10-million-row load test.

The initial plan held 65 duplicate museum object identities. Production preflight then held one Tate artwork whose painter, Konstantin Somov, had been created by a separate local import but was not yet present under that identity in production. The unapplied plans and original archive receipts are preserved in the draft directories; the final plan and source archive use version 2. No partial round-15 plan was applied before these checks.
