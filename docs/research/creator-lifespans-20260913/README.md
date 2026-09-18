# Creator lifespan reconciliation — 13 September 2026

Completed in local and production: **4,743 artwork links to 699 existing painters**. This pass audited all 75,965 remaining unlinked review artworks. It found 9,511 creator labels ending in an explicit `(YYYY–YYYY)` lifespan; accepted links require a unique documented full-name variant and both matching painter lifespan boundaries.

Source facts and supplied CSV identities were rechecked before every write. Known biography conflicts, museum creator mismatches, ambiguous namesakes, attribution holds and impossible artwork/lifetime relationships were retained for review. Surname-first label normalization is used only with both independently documented lifespan boundaries. Activity ranges, approximate dates and qualified names are not parsed as closed lifespans.

Every selected artwork remains in review. Titles, artwork types, creation dates, museum fields, images, existing painter records and original CSV/source evidence were verified unchanged. **2,543 unknown creation dates and 4,743 unknown artwork types stayed unknown.** The creator's lifespan never becomes an artwork creation date.

Both databases passed preflight and all-link verification. The writer used 48 serializable batches per database, each at most 100 records, with existing ingestion advisory locks. Citations preserve the original label, parsed creator evidence, documented painter authorities and plan SHA-256 `220467132fca2f89867c56eaec032e0b2fe3ddbc8d493ca84a4fc866209d01e6`. Twenty-five public artwork detail checks plus painter options and timeline filters passed. Public research preview remains read-only; the protected editor endpoint returned 401.

Immediately after this pass, both databases had 71,222 unresolved artworks. The subsequent [Wikidata authority pass](../creator-authorities-20260913/README.md) reduces that count further.

Recovery: fresh local full dump, archive validation and checksum receipt under `/Users/vadimdulub/Library/Application Support/Artline/backups/creator-lifespans-20260913/`; successful Cloud SQL backup **1789324907514**. Both target preimages are retained there. No test databases, real-catalogue fixtures, images, deployments or commits were created for these identity passes.
