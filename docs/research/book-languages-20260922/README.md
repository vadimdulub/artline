# Original book-language audit — 22 September 2026

Audited all **10,000 existing books** against fresh Wikidata responses and captured **9,714 linked English Wikipedia pages**. Applied **170 supported language corrections** to **local and production**, including **98 formerly empty values**. Both complete catalogue verifications passed with **zero errors**; all 10,000 records remain in review. **442 books still have no confirmed language.**

Original composition is distinct from translation availability, the language of first publication, the language of a title, a fictional language within the story, or an author's nationality. Wikipedia infoboxes are checked against article introductions and work identity; they can themselves describe translated editions. Dialect/historical-language precision and unresolved multilingual works are retained for review.

Examples: *Critique of Pure Reason* → German; *For Bread Alone* → Arabic; *Nineteen Eighty-Four* → English; *Sarah’s Key* → English; *The Manipulated Man* → German. *War and Peace* retains its Russian/French projection. Explicit prose supplied K’iche’ for *Popol Vuh*, Sanskrit for *Yoga Vasistha*, and both Hebrew and Aramaic for the *Talmud*.

- `correction-plan.json`: all exact before/after values, decision reasons, pinned Wikipedia revisions and retained Wikidata claims.
- `review-index.json`: one result for each of 10,000 books, including unresolved cases and contradictory infoboxes. A capture or unchanged Wikidata statement is not a claim that original composition is confirmed.
- `local-verification.json` / `production-verification.json`: complete before/after checks. Dates, creators, country/region filters, highlights, publication states and base records were unchanged by this language-only operation.
- `applications/`: transaction receipts and references to exact rollback preimages.
- `sources/`, `entities/`, `wikipedia/`, `language-entities/`: immutable response archives, receipts and source records.

Backups: `/Users/vadimdulub/Library/Application Support/Artline/backups/book-languages-20260922/`. No test database or fixtures were used.

The parser has eight offline regression checks, including translation qualifiers, conflicting editions, unrelated redirects, original-title codes, reference stripping and genuine multilingual fields. Production writes used bounded transactions of at most 50 existing projections, preserving original claims in evidence.

The subsequent requested book/author overview enrichment is tracked separately in `../book-context-20260922/`; it may update base checksums while preserving these corrected languages.
