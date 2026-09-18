# Expanded artwork research, round 7 — 13 September 2026

Completed and verified in local and production under the user's authorization to continue through 5–10 research rounds. This round uses [Rijksmuseum Data Services](https://data.rijksmuseum.nl/docs/search), scoped to the 40 largest unresolved painter groups and their linked creator authorities.

- Audited 78,808 retained unlinked artworks.
- Linked **507 artworks** to **14 new named painters** and **22 existing painters**.
- Enriched **507 artworks** with source-supported museum metadata.
- Remaining unlinked review artworks: **78,301**.
- No artwork rows were created or deleted; all accepted artworks remain `review` and `research_candidate=true`.

Source objects require exact full-name/title/museum/date matching, followed by creator authority or documented-name-and-biography reconciliation. Qualified attributions, uncertain identities and conflicting source objects are held. New painter lifespans require complete, unqualified museum birth/death evidence; unknown creation dates remain unknown. Original CSV records and supplied provenance are immutable. Museum presence is not promoted into a current-display claim. No images are downloaded by this metadata round.

The adjacent source-audit, source-match, hold and plan files preserve the decisions. Source captures and receipts are listed in `source-paths.json`. Plan SHA-256: `3377d67cc2145f52d0d076c0cc5e2c131d6e8e2cccc54034d7e12b8cdd6390f8`. Private plan/source archive: `gs://artline-508319-images/research/expanded-round7-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `ec862eaae4b187cf7fdbffcbe487af10dc88ce7bb785b703ffde7aa8a4d11318`. Its cloud size and MD5 were verified.

Fresh backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round7-20260913`. Local dump SHA-256 `47306d34fb520f92bd99722558c8efd157f0c6c1a185569c11d337be40969e59` (353,776,456 bytes); archive directory checked. Managed production backup `1789304350579` completed successfully before writes.

Guarded serializable transactions apply at most 100 rows per batch. The shared writer and migration-0018 ledger are reused; historical citation field names retain their `round2_` prefix, while plan hashes distinguish rounds. Local and production preflight hashes matched. After applying, verification checked every planned attribution, metadata patch, provenance row, review status and unchanged unrelated fields, excluding independently managed media pointers and audit timestamps. Final selected-row SHA-256 matched in both databases: `bdad4ecbfdefbe300bdc9d3fc286c400227676027c8e18626c9cd7ce12389bf0`.

Live API checks are recorded in `live-verification.json`. Tests use offline metadata only; no fixtures or test databases were added to the real catalogue. These checks do not constitute a 10-million-row load test.

Captured 848 painting records and 46 museum creator authority records. The search is partial-keyword discovery only; acceptance requires exact documented creator name variants, title and literal date wording, followed by authority/biography review. Qualified productions and multiple production parts remain held. Birth/death boundaries are used only when the museum supplies an unqualified year or calendar date. Ten objects already owned by other catalogue rows were held; the unapplied draft and counterpart audit are preserved. Live painter-scoped detail checks covered Richard Nicolaüs Roland Holst, George Hendrik Breitner and Cornelis Troost.
