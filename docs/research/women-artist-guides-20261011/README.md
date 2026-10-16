# Three women artist guides — 11 October 2026

The user requested a few guides for women artists, continuing the established editorial approach, translated editions, downloadable PDFs and Artline selections. Publication and production deployment were already authorized in the guide conversation.

The selection contains 20 works each by Artemisia Gentileschi, Mary Cassatt and Frida Kahlo. These are editorial selections across collections, not museum rankings or current-display lists. All 60 artwork IDs already exist in production. No catalogue, account or local database writes were made for this task.

## Editorial evidence

- `selections/`: bounded production exports of the selected objects, creator relationships, source metadata and existing image credits.
- `copy/`: individually written English introductions, entries and reading notes. Descriptions follow visible details; importance explains a particular pictorial choice or documented context. The web editorial manual, version 1.1, governed the prose.
- `sources/`: retained source text and HTTP receipts. Museum records were preferred for particular object identifications and documented facts. Some museum sites returned 403 to automated requests; their indexed official records were checked with web research. A successful indexed lookup is not recorded as an HTTP 200 download.
- `article-field-overrides.json`: article-only corrections, with prior values and supporting sources. No silent changes to production metadata.
- `image-receipts/`: selected existing reproductions, hashes and image decoding checks. Contact sheets and enlarged images were examined. Existing WikiArt approval applies; actual source credits and rights labels remain visible.
- `translations/`, `translation-receipts/`, `translation-editorial-corrections.json`: Cloud Translation output, English input hashes and subsequent editorial corrections. This was assistant review, not independent native-speaker review. Non-English pages retain the small AI-assisted translation notice.

Artemisia's death is given as **1654 or later**, not a falsely precise year. The candidate Judith image identified in the initial export as a 1621–24 painting was excluded because creator/version identity remained uncertain. The selected Portrait of a Gonfaloniere is the 1622 work catalogued under the title Portrait of a Condottiero. The Allegory of Inclination entry distinguishes Artemisia's painting from the later covering drapery. Susanna and the Elders follows the Nivaagaard identification and date range.

Cassatt's colour prints refer to specific museum impressions, retaining their accession numbers. Twenty designs are represented; different impressions of one design do not inflate the selection. The Cup of Tea links to Met object 10388. The institutions cited in prose as the National Gallery are explicitly identified as the National Gallery of Art in Washington.

Kahlo's Fulang-Chang and I distinguishes the 1937 painted panel reproduced here from its later mirror assembly. The Frame uses the Pompidou's aluminium support and painted-glass surround rather than reducing the medium to glass. The Grandparents picture retains the museum's zinc support. The Cropped Hair reading link is labelled as a publisher sample, not a free complete book; MoMA blocks the automated HTTP check, while its official indexed publication record confirms the book.

## Portal behaviour

Each guide's **Artworks in context** link selects exactly its 20 artwork IDs; books and events use the selected works' date range. **Who lived when?** adds named contemporaries to make the comparison useful:

- Artemisia: Orazio Gentileschi, Caravaggio and Rubens.
- Cassatt: Berthe Morisot, Degas and Monet.
- Kahlo: Diego Rivera, Georgia O'Keeffe, Tarsila do Amaral and Remedios Varo.

Comparisons are stated as historical context, not claims of direct influence. Companion artists affect only the lifespan diagram; they do not broaden the 20-work selection. `api-verification.json` records exact painter sets and all 60 working artwork routes. `context-selection-verification.json` confirms that the live Atlas API returns exactly 20 selected artworks for each guide, plus populated book and event lanes (Cassatt: 7 books/3 events; Artemisia: 5/8; Kahlo: 27/13 at verification).

## Publication and validation

Content lives in `apps/web/content/articles/artist-guides/`, separate from museum content but using the same bounded guide routes and renderer. There are 30 editions: English, Russian, Italian, German, simplified Chinese, French, Spanish, Portuguese, Japanese and Arabic. Each has a 23-page PDF with the same text, source links, reading links and portal selections.

`pdf-validation.json` records all 30 PDFs and their hashes: 690 pages, with text, artwork images and source/book/portal links. All English pages were rendered for visual inspection; Russian, Chinese, Japanese and Arabic layouts were also inspected. Browser checks cover all 30 editions at 1440px or 320px, and candidate and production HTTP and interaction checks passed. All 30 public PDF downloads matched their frozen hashes; all 890 guide editions remain in the sitemap. All three exploration links were exercised in the browser, and the 4/4/5-painter comparisons rendered without errors. Three representative accessibility checks passed with no violations.

189 guide, metadata and sitemap unit tests passed. Scoped ESLint has no errors; existing raw-image warnings remain. The first whole-workspace TypeScript check encountered unrelated, in-progress BackNavigation changes; the isolated production build passed, including its TypeScript check. Release packaging uses an explicit allowlist and frozen predecessor hashes, preserving concurrent production changes and excluding unrelated local edits.

Release receipts and frozen archives belong under `~/Library/Application Support/Artline/backups/women-artist-guides-20261011/`. Browser/PDF previews are under `/tmp/artline-women-guides-20261011/`. No fixtures were written to a real database and no commits or Terraform apply were performed.

Published at 100% traffic as `artline-web-women-guides-1011-v1`, based on the deployed sharing release. See `docs/deployment-20261011-women-artist-guides.json` for the image digest, build ID, checks and rollback revision.
