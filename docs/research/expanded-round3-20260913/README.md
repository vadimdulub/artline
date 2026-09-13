# Expanded artwork research, round 3 — 13 September 2026

The user authorized further creator and artwork research in local and production, followed immediately by another round. This round selects museum-supported links for existing retained review artworks; it creates no artwork rows and publishes nothing.

## Reviewed result

- Audited 83,804 unlinked research artworks against the refreshed catalogue.
- Plan: 1,075 artwork links to 372 new and 254 existing named painters.
- 1,072 Minneapolis paintings gain source-backed type, date wording, medium, dimensions and accession metadata; two Joconde and one Tate work gain creator links with their existing metadata preserved.
- Plan SHA-256: `e16f41d7b87dd35a72a1a4a0fb3f125bf396cdf2e7cf6946833e34bbda764655`.
- All remain `review` and `research_candidate=true`. Unknown dates remain unknown. No holding is promoted into a current-display claim, and no image files are downloaded by this round.

## Source and selection

[Minneapolis Institute of Art's official metadata repository](https://github.com/artsmia/collection) publishes collection metadata under CC0. Captured its metadata archive at commit `790eb625934680f2eeccb262391618d2ca948486`, SHA-256 `752d5761774a3e0a1060b1b742d7ddc33f99e959b06ee66a8c4c70beb0bc0846`. The archive contains 196,079 JSON objects, 51 invalid JSON files and 77 non-object JSON values. Invalid/non-object records are skipped and counted. Images have separate terms and are not part of this workflow.

Object matching requires the supplied museum, full normalized creator name, title and literal date wording to match. It found 1,654 candidate matches before identity/type/conflict review. Museum archive member, complete selected source metadata and capture receipt are preserved for each match. Qualified, multiple and uncertain attributions are held. No fuzzy title or surname-only matching is used.

New painters require a complete, unqualified museum lifespan and no plausible existing identity collision. A review caught `1639 or later` and `1750s` in museum biographies; the final parser rejects these as exact lifespan boundaries. The initial draft and its preflight audits are preserved under `draft-v1/`; that draft was never applied. Regression tests cover these cases.

The shared planner now accepts a fresh output directory, a supplied source-match file, and a round slug; old defaults remain unchanged. It also rechecks older Joconde/Tate/SMK evidence against the refreshed painter catalogue. The shared guarded writer and generic migration-0018 enrichment ledger are reused; historical SQL citation field names retain their `round2_` prefix. The plan hash and evidence distinguish rounds.

## Recovery and verification

Fresh backups are under `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round3-20260913/`. The local dump is 346,202,028 bytes, SHA-256 `d7f29480b55d323305e26b1525b304e9d432e470ca2edfbb2de268873a3ed75a`; its archive directory was checked. Managed production backup `1789301962209` completed successfully; its receipt is stored alongside it.

Private evidence archive: `gs://artline-508319-images/research/expanded-round3-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `1b4067463b51ee2ab5d8046ce155d95167b766349997273cf87f06bdef3e4aa4`. Cloud size and MD5 match the local archive.

Before applying, all selected local/production rows had identical verification hashes. Transactions are serializable, guarded by original CSV, artwork values and source evidence, with 100-row batches. Each accepted row retains immutable source provenance in `research_artwork_enrichments`; replays are idempotent. Verification checks exact primary attribution, metadata, provenance and unchanged unrelated fields, excluding independently managed image pointers and audit timestamps. No test database or fixtures were created. Offline policy tests passed; large-scale performance testing remains separate work.

Final database and live checks are recorded in the adjacent verification JSON files.

Completed and verified in both databases: 1,075 additional links, 372 new painters, 1,072 metadata enrichments. Remaining unlinked review artworks: **82,729**. The selected-row verification SHA-256 is identical locally and in production: `7df7e2587f1035ade82e545545b8ded675d46f1e1e30d3bd84b23b647a1e35a0`. Live artwork-list checks passed for a precisely dated Zhang Geng work and a Morikawa Sobun work whose date remains unknown.
