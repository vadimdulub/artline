# Expanded artwork research, round 5 — 13 September 2026

Completed and verified in local and production under the user's authorization to continue through 5–10 research rounds. This round uses [the Walters Art Museum's official CC0 metadata](https://github.com/WaltersArtMuseum/api-thewalters-org), pinned at commit f7531ed751ac2c138eeb6f923a3b4fd325d78adf.

- Audited 81,627 retained unlinked artworks.
- Linked **691 artworks** to **135 new named painters** and **225 existing painters**.
- Enriched **691 artworks** with source-supported museum metadata.
- Remaining unlinked review artworks: **80,936**.
- No artwork rows were created or deleted; all accepted artworks remain `review` and `research_candidate=true`.

Source objects require exact full-name/title/museum/date matching, followed by creator authority or documented-name-and-biography reconciliation. Qualified attributions, uncertain identities and conflicting source objects are held. New painter lifespans require complete, unqualified museum birth/death evidence; unknown creation dates remain unknown. Original CSV records and supplied provenance are immutable. Museum presence is not promoted into a current-display claim. No images are downloaded by this metadata round.

The adjacent source-audit, source-match, hold and plan files preserve the decisions. Source captures and receipts are listed in `source-paths.json`. Plan SHA-256: `209c951e2c31a5d5e59e5dacb3ddbf52bba55eb49e5576759e662c06c252c5b6`. Private plan/source archive: `gs://artline-508319-images/research/expanded-round5-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `9779918f1ce0353aab045cbec17d070d63186d9351abd36af5b29647f5f2db0a`. Its cloud size and MD5 were verified.

Fresh backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round5-20260913`. Local dump SHA-256 `6a46c3ec87d5881abb4d0a0d29adf3835bf974a6f5531a3ea5ecdcd2da3309dd` (349,879,095 bytes); archive directory checked. Managed production backup `1789303270789` completed successfully before writes.

Guarded serializable transactions apply at most 100 rows per batch. The shared writer and migration-0018 ledger are reused; historical citation field names retain their `round2_` prefix, while plan hashes distinguish rounds. Local and production preflight hashes matched. After applying, verification checked every planned attribution, metadata patch, provenance row, review status and unchanged unrelated fields, excluding independently managed media pointers and audit timestamps. Final selected-row SHA-256 matched in both databases: `f8cb08137c2fc1258bdce9596d6d283ec904d09f26c241fc9babfdecf55ddf4d`.

Live API checks are recorded in `live-verification.json`. Tests use offline metadata only; no fixtures or test databases were added to the real catalogue. These checks do not constitute a 10-million-row load test.
