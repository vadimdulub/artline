# Expanded artwork research, round 13 — 13 September 2026

Completed and verified in local and production under the user's authorization to run another five rounds, 11–15. This round uses new, bounded Rijksmuseum object and creator authority captures.

- Audited 77,011 retained unlinked artworks.
- Linked **122 artworks** to **20 new named painters** and **21 existing painters**.
- Enriched **122 artworks** with source-supported museum metadata.
- Remaining unlinked review artworks: **76,889**.
- No artwork rows were created or deleted; all accepted artworks remain `review` and `research_candidate=true`.

Source objects require exact full-name/title/museum/date matching, followed by creator authority or documented-name-and-biography reconciliation. Qualified attributions, uncertain identities and conflicting source objects are held. New painter lifespans require complete, unqualified museum birth/death evidence; unknown creation dates remain unknown. Original CSV records and supplied provenance are immutable. Museum presence is not promoted into a current-display claim. No images are downloaded by this metadata round.

The adjacent source-audit, source-match, hold and plan files preserve the decisions. Source captures and receipts are listed in `source-paths.json`. Plan SHA-256: `7dc90de83caaa1a3c3f52c4c9fc18e8fad15a222e1b5c306f40fc811aaa243eb`. Private plan/source archive: `gs://artline-508319-images/research/expanded-round13-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `04ddc15d52bfb18998c17aab0982d378a19967dba73615a49a1de88fd7d5ae21`. Its cloud size and MD5 were verified.

Fresh backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round13-20260913`. Local dump SHA-256 `496a9639a7ca2857e8e1b12f27a1432035a014378a53be129807342795fe1f07` (359,115,567 bytes); archive directory checked. Managed production backup `1789306647506` completed successfully before writes.

Guarded serializable transactions apply at most 100 rows per batch. The shared writer and migration-0018 ledger are reused; historical citation field names retain their `round2_` prefix, while plan hashes distinguish rounds. Local and production preflight hashes matched. After applying, verification checked every planned attribution, metadata patch, provenance row, review status and unchanged unrelated fields, excluding independently managed media pointers and audit timestamps. Final selected-row SHA-256 matched in both databases: `a1d03b7277b0f4bf079df0e99b75fd6ebc1e36fcbb6550b528a20852a17b7dbc`.

Live API checks are recorded in `live-verification.json`. Tests use offline metadata only; no fixtures or test databases were added to the real catalogue. These checks do not constitute a 10-million-row load test.

This round searched 80 previously unsearched Rijksmuseum creator names, selected from the largest remaining named-creator groups. Searches are scoped to painting metadata and limited to five pages per creator. Source captures include stable object/creator IDs and checksummed retrieval receipts. The source adapter holds qualified attributions and unsupported production structures.

Official API documentation: https://data.rijksmuseum.nl/docs/search .
