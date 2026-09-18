# Expanded artwork research, round 12 — 13 September 2026

Completed and verified in local and production under the user's authorization to run another five rounds, 11–15. This round uses 426 official Rijksmuseum object records and 84 creator authority records, captured for another 80 previously unsearched creator names.

- Audited 77,187 retained unlinked artworks.
- Linked **176 artworks** to **15 new named painters** and **35 existing painters**.
- Enriched **176 artworks** with source-supported museum metadata.
- Remaining unlinked review artworks: **77,011**.
- No artwork rows were created or deleted; all accepted artworks remain `review` and `research_candidate=true`.

Source objects require exact full-name/title/museum/date matching, followed by creator authority or documented-name-and-biography reconciliation. Qualified attributions, uncertain identities and conflicting source objects are held. New painter lifespans require complete, unqualified museum birth/death evidence; unknown creation dates remain unknown. Original CSV records and supplied provenance are immutable. Museum presence is not promoted into a current-display claim. No images are downloaded by this metadata round.

The adjacent source-audit, source-match, hold and plan files preserve the decisions. Source captures and receipts are listed in `source-paths.json`. Plan SHA-256: `4b296d832b9cc2900dcda3f69c56e61959915d419e4c682556f14782a5627430`. Private plan/source archive: `gs://artline-508319-images/research/expanded-round12-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `523791c4ccb488e25f018216fbfb2f70f8a7fb9e80442072fbfea20db3c059da`. Its cloud size and MD5 were verified.

Fresh backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round12-20260913`. Local dump SHA-256 `228504ca6e0b6139228affecfdb27e1bb1b785f212d999133567a4c6a8336179` (356,349,031 bytes); archive directory checked. Managed production backup `1789306401030` completed successfully before writes.

Guarded serializable transactions apply at most 100 rows per batch. The shared writer and migration-0018 ledger are reused; historical citation field names retain their `round2_` prefix, while plan hashes distinguish rounds. Local and production preflight hashes matched. After applying, verification checked every planned attribution, metadata patch, provenance row, review status and unchanged unrelated fields, excluding independently managed media pointers and audit timestamps. Final selected-row SHA-256 matched in both databases: `aa9797422282fd4b57da67064874125109bfe11406aa6db09ec0bb5fc050fbbf`.

Live API checks are recorded in `live-verification.json`. Tests use offline metadata only; no fixtures or test databases were added to the real catalogue. These checks do not constitute a 10-million-row load test.

The source adapter encountered a list of conflicting creation periods and was corrected to hold multiple periods for review. Single-element lists can be read without changing their source wording. Offline tests cover this case, uncertain lifespan boundaries and qualified dates. No partial plan was applied before the correction. Official search documentation: https://data.rijksmuseum.nl/docs/search .
