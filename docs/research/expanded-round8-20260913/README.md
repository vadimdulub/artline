# Expanded artwork research, round 8 — 13 September 2026

Completed and verified in local and production under the user's authorization to continue through 5–10 research rounds. This round uses [the Finnish National Gallery's public collection metadata](https://kokoelma.kansallisgalleria.fi/en/api-sovelluskehittajille), additionally covering the State Art Commission and the Kiasma Helsinki organisation label.

- Audited 78,301 retained unlinked artworks.
- Linked **445 artworks** to **55 new named painters** and **102 existing painters**.
- Enriched **445 artworks** with source-supported museum metadata.
- Remaining unlinked review artworks: **77,856**.
- No artwork rows were created or deleted; all accepted artworks remain `review` and `research_candidate=true`.

Source objects require exact full-name/title/museum/date matching, followed by creator authority or documented-name-and-biography reconciliation. Qualified attributions, uncertain identities and conflicting source objects are held. New painter lifespans require complete, unqualified museum birth/death evidence; unknown creation dates remain unknown. Original CSV records and supplied provenance are immutable. Museum presence is not promoted into a current-display claim. No images are downloaded by this metadata round.

The adjacent source-audit, source-match, hold and plan files preserve the decisions. Source captures and receipts are listed in `source-paths.json`. Plan SHA-256: `f36bc6c6d9b14e9b8b11b61fac8f9357d8bd6c1415dd98903caaed2bf780ba6d`. Private plan/source archive: `gs://artline-508319-images/research/expanded-round8-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `4c58b896d030d5cf18d2c78b88643b25d057bc72cad50685d5d6cc0382a5b9ef`. Its cloud size and MD5 were verified.

Fresh backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round8-20260913`. Local dump SHA-256 `7da23c2f6391fa6fc95b7cec44ea8a578643f905e8e87c66c86c80dd95c4608b` (354,659,103 bytes); archive directory checked. Managed production backup `1789304661212` completed successfully before writes.

Guarded serializable transactions apply at most 100 rows per batch. The shared writer and migration-0018 ledger are reused; historical citation field names retain their `round2_` prefix, while plan hashes distinguish rounds. Local and production preflight hashes matched. After applying, verification checked every planned attribution, metadata patch, provenance row, review status and unchanged unrelated fields, excluding independently managed media pointers and audit timestamps. Final selected-row SHA-256 matched in both databases: `859f1150fff93409cf8ef33749aae87286b8f7953e1b7aba2863ff4a59aba2aa`.

Live API checks are recorded in `live-verification.json`. Tests use offline metadata only; no fixtures or test databases were added to the real catalogue. These checks do not constitute a 10-million-row load test.

The official gallery documents that the [Finnish State Art Commission operates under it](https://kansallisgalleria.fi/en/a-collection-for-everyone/). Its collection's placement in government institutions is kept separate from museum display. This pass examined 18,992 metadata records within the two additional organisation labels and matched 572 retained CSV candidates before painter/conflict checks. Every accepted creation date is within the cutoff. The original pinned museum package was reused without downloading any images.
