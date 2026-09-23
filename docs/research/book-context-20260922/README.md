# Book and author context — 22 September 2026

Added sourced introductions to **9,594 existing books** and biographies to
**3,782 existing creators**, in both the local catalogue and production.
All **10,000 books** and **4,092 creator records** were checked before and after.
All books remain in review. The [170 language corrections](../book-languages-20260922/README.md)
are preserved, as are dates, original descriptions, creator credits, country and
region filters, women-author membership and editorial selections.

The detail panels show these introductions under “About this book” and the
creator biography, with a pinned Wikipedia link and CC BY-SA 4.0 attribution.
The standalone author panel uses the same biography. Three requested Books
timeline help texts were removed. Matching descriptions remain available for
records without a reliable introduction; no inferred replacement is generated.

## Sources and bounds

The capture contains 13,539 introductions requested through the Wikimedia
TextExtracts API: 9,714 book pages and 3,825 creator pages. Every accepted page's
Wikidata identity must match the existing work or creator ID. Redirects to other
entities, missing introductions and malformed/insufficient excerpts are held.
Book excerpts contain at most 220 words; biographies at most 140, and both at
most three paragraphs. They are introductory excerpts, not newly written
editorial interpretations. Empty pronunciation fragments produced by missing
audio/IPA markup are cleaned in the renderer.

406 books and 310 creators retain their earlier descriptions. Their individual
reasons are in `unresolved-overviews.json`. Unknown authorship, uncertain dates
and historical attributions remain unchanged.

## Retained artifacts

- `overview-plan.json`: accepted text, attribution, source revisions and evidence.
- `sources/`: immutable compressed API responses and retrieval receipts.
- `book-introductions/`, `creator-introductions/`, `creator-entities/`: matched
  source records, including held cases.
- `local-apply.json`, `production-apply.json`: exact update receipts and backup
  references.
- `local-verification.json`, `production-verification.json`: complete checks of
  records, relationships, projection checksums and preserved language corrections.
- `api-candidate-checks.json`: candidate API health, original-language filtering
  and book/creator overview checks.

Backups and release source archives live under
`/Users/vadimdulub/Library/Application Support/Artline/backups/book-context-20260922/`.
The two updates were atomic transactions using temporary staging tables for
existing records. No fixtures, new catalogue records, test databases or
publication changes were made. Existing invalidation triggers remained enabled;
affected discovery projections were restored from their locked preimages with
new source checksums and their prior memberships.

## Implementation and checks

`ops/enrich-books-20260922.py` captures sources with two workers and request
spacing. `ops/apply-book-context-20260922.py` prepares the pinned plan, performs
explicit target updates and verifies all records. `ops/book_context.py` contains
identity validation and excerpt bounds, with five offline regression checks.
The separate language parser has eight checks.

Go exposes the optional overview from existing JSON records; PostgreSQL still
owns filtering and pagination. There are no browser-side Wikipedia requests,
unbounded catalogue downloads or per-record network enrichment during reads.
Local read-only Go catalogue tests, Go book/HTTP tests, frontend lint, TypeScript
and an isolated production build passed. Desktop and 390-pixel mobile browser
checks verified both detail texts, pinned attribution, scrolling, no horizontal
overflow, removed help text and no JavaScript errors.

Production release sources were reconstructed from the actual 20 September
deployed archives and overlaid with only ten book-context files. Unrelated local
work was excluded. See `release.json` for the final deployed revisions and checks.

Final public verification passed after both services moved to 100% traffic on
`artline-api-books-0922` and `artline-web-books-0922`.
`browser-public-verification.json` records the public desktop/mobile checks;
`final-verification.json` confirms both catalogues still contain every one of
the 170 corrected language projections, 9,594 book overviews and 3,782 creator
biographies, with 10,000 valid discovery projections and zero errors.
