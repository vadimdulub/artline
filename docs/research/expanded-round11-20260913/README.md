# Expanded artwork research, round 11 — 13 September 2026

Completed and verified in local and production under the user's authorization to run another five rounds, 11–15. This round uses 698 official Rijksmuseum object records and 88 creator authority records, captured for 80 previously unsearched creator names.

- Audited 77,499 retained unlinked artworks.
- Linked **312 artworks** to **17 new named painters** and **31 existing painters**.
- Enriched **312 artworks** with source-supported museum metadata.
- Remaining unlinked review artworks: **77,187**.
- No artwork rows were created or deleted; all accepted artworks remain `review` and `research_candidate=true`.

Source objects require exact full-name/title/museum/date matching, followed by creator authority or documented-name-and-biography reconciliation. Qualified attributions, uncertain identities and conflicting source objects are held. New painter lifespans require complete, unqualified museum birth/death evidence; unknown creation dates remain unknown. Original CSV records and supplied provenance are immutable. Museum presence is not promoted into a current-display claim. No images are downloaded by this metadata round.

The adjacent source-audit, source-match, hold and plan files preserve the decisions. Source captures and receipts are listed in `source-paths.json`. Plan SHA-256: `f6048d5e7ad7c1d27f5121ee9d0e3962aa362a473cfeafcc56409125bfaf5a94`. Private plan/source archive: `gs://artline-508319-images/research/expanded-round11-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `3c3d73dfd8ae4d6cdb7ed3f5385cbee652edc4f3192868d90700ddf79468dca6`. Its cloud size and MD5 were verified.

Fresh backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round11-20260913`. Local dump SHA-256 `c2d638e3a1e9b2a022df4d5dd354b952777edc77365dbc529afc6c25f849ec9b` (355,737,935 bytes); archive directory checked. Managed production backup `1789306231123` completed successfully before writes.

Guarded serializable transactions apply at most 100 rows per batch. The shared writer and migration-0018 ledger are reused; historical citation field names retain their `round2_` prefix, while plan hashes distinguish rounds. Local and production preflight hashes matched. After applying, verification checked every planned attribution, metadata patch, provenance row, review status and unchanged unrelated fields, excluding independently managed media pointers and audit timestamps. Final selected-row SHA-256 matched in both databases: `b319b1de5cc9b48aa33fb27abef151685572a7d4b25e3309cba27f5bf16b1c63`.

Live API checks are recorded in `live-verification.json`. Tests use offline metadata only; no fixtures or test databases were added to the real catalogue. These checks do not constitute a 10-million-row load test.

The first production backup request encountered an already-running Cloud SQL backup operation. No production writes occurred until the retry completed successfully. Official search documentation: https://data.rijksmuseum.nl/docs/search .
