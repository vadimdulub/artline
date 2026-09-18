# Expanded artwork research, round 6 — 13 September 2026

Completed and verified in local and production under the user's authorization to continue through 5–10 research rounds. This round uses [Smithsonian Open Access](https://github.com/Smithsonian/OpenAccess), restricted to the SAAM metadata unit and matched against the supplied CSV.

- Audited 80,936 retained unlinked artworks.
- Linked **2,128 artworks** to **147 new named painters** and **160 existing painters**.
- Enriched **2,128 artworks** with source-supported museum metadata.
- Remaining unlinked review artworks: **78,808**.
- No artwork rows were created or deleted; all accepted artworks remain `review` and `research_candidate=true`.

Source objects require exact full-name/title/museum/date matching, followed by creator authority or documented-name-and-biography reconciliation. Qualified attributions, uncertain identities and conflicting source objects are held. New painter lifespans require complete, unqualified museum birth/death evidence; unknown creation dates remain unknown. Original CSV records and supplied provenance are immutable. Museum presence is not promoted into a current-display claim. No images are downloaded by this metadata round.

The adjacent source-audit, source-match, hold and plan files preserve the decisions. Source captures and receipts are listed in `source-paths.json`. Plan SHA-256: `c0297ff768595f99a4d08e0f8dceeeb0e440d14c74dcc04b0f4faffe08229711`. Private plan/source archive: `gs://artline-508319-images/research/expanded-round6-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `1f1bc18922aea5f48d287dd395dd2f2d788fac3ae2c6554e7ab8661048d1b6b5`. Its cloud size and MD5 were verified.

Fresh backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round6-20260913`. Local dump SHA-256 `1071ac5b0967bc2ffa2d84b1f1f96f71c387163cd765725a80aad7ad517518f2` (351,079,821 bytes); archive directory checked. Managed production backup `1789303637514` completed successfully before writes.

Guarded serializable transactions apply at most 100 rows per batch. The shared writer and migration-0018 ledger are reused; historical citation field names retain their `round2_` prefix, while plan hashes distinguish rounds. Local and production preflight hashes matched. After applying, verification checked every planned attribution, metadata patch, provenance row, review status and unchanged unrelated fields, excluding independently managed media pointers and audit timestamps. Final selected-row SHA-256 matched in both databases: `0b7f34c8be82642a93b2d9074dc99f2398ed3927b45e07fd96a414f0f4da9d50`.

Live API checks are recorded in `live-verification.json`. Tests use offline metadata only; no fixtures or test databases were added to the real catalogue. These checks do not constitute a 10-million-row load test.

The capture contains 256 SAAM metadata partitions (16,569 records). The CSV's creator column often preserves the entire museum name-and-biography string. Object matching therefore checks that exact original source label before extracting the named creator and its explicitly labelled birth/death years. An initial zero-link draft, preserved under `draft-raw-creator-label-review/`, exposed this input format and was never applied. Indexed decade arrays were not used as creation dates because they can reflect artist lifespans. Museum date wording is retained directly.
