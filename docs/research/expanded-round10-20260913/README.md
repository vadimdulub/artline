# Expanded artwork research, round 10 — 13 September 2026

Completed and verified in local and production under the user's authorization to continue through 5–10 research rounds. This round uses fresh reconciliation against all pinned official object captures from rounds 2–8 and the painter identities established through round 9.

- Audited 77,663 retained unlinked artworks.
- Linked **164 artworks** to **0 new named painters** and **52 existing painters**.
- Enriched **159 artworks** with source-supported museum metadata.
- Remaining unlinked review artworks: **77,499**.
- No artwork rows were created or deleted; all accepted artworks remain `review` and `research_candidate=true`.

Source objects require exact full-name/title/museum/date matching, followed by creator authority or documented-name-and-biography reconciliation. Qualified attributions, uncertain identities and conflicting source objects are held. This round creates no painters and changes no existing painter biographies or activity intervals. Stable source-person identifiers allow additional works to link to previously established identities, including works with unknown creation dates. Unknown creation dates remain unknown. Original CSV records and supplied provenance are immutable. Museum presence is not promoted into a current-display claim. No images are downloaded by this metadata round.

The adjacent source-audit, source-match, hold and plan files preserve the decisions. Source captures and receipts are listed in `source-paths.json`. Plan SHA-256: `ae7525d50aeaa1714c85f9f045e2928a02ae022199486ec3fddc33f3a03b233a`. Private plan/source archive: `gs://artline-508319-images/research/expanded-round10-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `a3ad7e5eb9409aa12a3e2ae52eb81027ab261187e5ced2c4dd80a9715e245fc0`. Its cloud size and MD5 were verified.

Fresh backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round10-20260913`. Local dump SHA-256 `311c241056ca95bf1f9d28d65b29359591e0c9a1b6eb1259ba4c31413fabcb57` (355,538,369 bytes); archive directory checked. Managed production backup `1789305792431` completed successfully before writes.

Guarded serializable transactions apply at most 100 rows per batch. The shared writer and migration-0018 ledger are reused; historical citation field names retain their `round2_` prefix, while plan hashes distinguish rounds. Local and production preflight hashes matched. After applying, verification checked every planned attribution, metadata patch, provenance row, review status and unchanged unrelated fields, excluding independently managed media pointers and audit timestamps. Final selected-row SHA-256 matched in both databases: `3ecceec755ccb86993723c4faa3877f79d4d13dc04eaf06477cc115d1705f61c`.

Live API checks are recorded in `live-verification.json`. Tests use offline metadata only; no fixtures or test databases were added to the real catalogue. These checks do not constitute a 10-million-row load test.

The initial 224-link draft was reduced to 164 after 60 museum object identities were found on other existing artwork records (50 Lombardia and 10 Rijksmuseum records). The draft and per-record hold evidence remain preserved; no duplicate was merged or deleted. The final production object-identity audit found zero conflicts. Eighteen linked works still require date review; no creation date was invented.
