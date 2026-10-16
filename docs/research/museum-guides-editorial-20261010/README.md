# Museum guides editorial release — 10–11 October 2026

User requested a 100-museum programme, specifically naming the Louvre, Prado, Leventis Gallery, Munich, Le Havre and the National Gallery of Armenia. This first release has **six finished guides covering eight institutions**, **135 selected artwork entries**, **ten languages** and **60 illustrated PDFs**. It does not complete the 100-museum target and does not classify the remaining museums as lacking good guides. No placeholder guide pages are published.

The supplied editorial manual is preserved byte-for-byte at `apps/web/Art_Writing_Editorial_Manual_EN.md` and was read before drafting. Canonical publishable articles live in `apps/web/content/articles/museum-guides/<slug>/<locale>.json`; PDFs are generated from the same JSON by `ops/build-museum-guide-pdfs.mjs`. There is no CMS or runtime translation dependency.

| Guide | Works | Institutions | Artworks in dated All view |
|---|---:|---:|---:|
| Louvre | 20 | 1 | 20 |
| Prado | 20 | 1 | 19 |
| Leventis Gallery | 20 | 1 | 18 |
| National Gallery of Armenia | 25 | 1 | 25 |
| Munich museums | 30 | 3 | 30 |
| MuMa Le Havre | 20 | 1 | 19 |

All URLs carry exact artwork UUIDs. Artist lifespan links carry verified linked painter slugs; period books and events remain separate context rather than assertions of direct influence. Four works with catalogue date classifications that cannot be plotted remain fully illustrated in the guides. No catalogue date or status was changed to force timeline inclusion. Existing artist and individual-work access remains public; museum/member access is unchanged.

## Evidence and selection

`selected-catalogue.json` preserves the production snapshot used for the first five guides. `muma-image-selection.json` preserves the 20 selected museum objects and Commons file metadata. `sources/` contains captured museum/source pages, retrieval outcomes and compressed response bodies. Prado pages that returned HTTP 403 are retained as failed retrievals, not represented as successfully read pages; existing object/image evidence and source identifiers were retained. Official Louvre visitor trails, MuMa object commentaries and Pinakothek visitor information were checked separately.

All selected images were visually inspected on labelled contact sheets. Duplicate Louvre objects/versions were excluded. The watermarked Barque of Dante was omitted from the final Louvre selection. Leventis Composition follows the museum’s egg tempera and oil on hardboard description; its different catalogue medium is retained in the research snapshot. The Poor Poet uses the Munich museum’s 1839 date in guide copy and records the discrepancy with the imported 1837 date; the database was not rewritten. Leventis Harmony and Trellises and Shadows retain the reconciled dates from the preceding Leventis object review, whose source conflicts are documented in `../leventis-deep-20261008/README.md`.

Collection membership is not a current-display claim. Munich explicitly records the Neue Pinakothek renovation closure and tells readers to check individual locations. The Louvre and MuMa already provide official guides/commentaries; this release links them and never asserts they have no good guide. Further reading distinguishes freely readable books, publisher listings and official online resources. The Met’s Armenia volume is described as medieval context, not a catalogue of the selected modern paintings.

## Languages and PDFs

English is the authored original. Russian, Italian, German, Simplified Chinese, French, Spanish, Portuguese, Japanese and Arabic were translated using the official Google Cloud Translation API, enabled in the existing Artline project for this task. Content is static after generation; there are no visitor-triggered translation requests. Small visible AI-assisted translation labels appear on translated web and PDF editions. Titles and interface labels received an editorial pass, including correction of the Russian house-painter mistranslation and a misleading Chinese Armenia title. These are AI-assisted editions, not a claim of native-speaker review in every language.

Object IDs, source/image URLs, legal credits, licence labels, original catalogue titles, dates used for filters and painter links remain invariant across translations. Proper names and original book titles remain available in their source spelling. PDFs have selectable text, embedded images, source links, portal links, page numbers and a contents page. All 60 PDFs passed page-count checks: one cover, one contents page, one page per artwork, and one reading/visit page. Rendered Russian, Arabic, Chinese and Latin-script samples were inspected; translated-cover overflow was fixed before release.

## Selected production image delivery

Twenty previously unillustrated MuMa records received independently licensed Commons photographs or public-domain reproductions. No museum-supplied reproduction permission was inferred from the licence of a visitor’s photograph. Required photographer names, CC BY-SA links and change notices are retained. The complete source photograph, including frames where present, is preserved; derivatives are resized proportionally and JPEG-compressed to at most 100,000 bytes.

The Degas source records several campaigns, circa 1884–1886, 1890 and 1900; those all precede the cutoff. Image review accepted that documented scope without inventing an exact catalogue year. It remains outside the dated timeline until the catalogue’s date classification is reconciled separately.

`ops/deliver-museum-guide-images-20261010.py` stages plan, immutable upload, transactional attachment and verification. The transaction locks and compares preimages, adds media/rights/citations and changes only primary media plus revision/audit timestamps. Existing creator links, titles, dates, holdings and review statuses are checked unchanged. Recovery backup ID: 1791662970886. Preimages and the Cloud SQL backup receipt are under `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-guides-20261010/`. Source image renditions are under the corresponding Artline `source-images/museum-guides-20261010/` directory. The real local database remained untouched.

## Validation and scope limits

333 web unit tests pass, including full translation/object invariants and exact portal-filter propagation. Focused Go atlas tests and six read-only production guide audits pass. Captured query plans use scoped indexed artwork lookups; observed statement execution was roughly 100–120 ms on this production snapshot. This is not a ten-million-row load test. The broad Go suite is blocked in unrelated historical ingestion tests by pre-existing missing research inventory files; no fabricated inventories were added.

Browser checks cover all six guides, ten-language navigation, English PDF downloads, Russian/Chinese/Arabic editions, 320/390 px layouts, accessibility, invalid editions, the existing Guides navigation and actual Armenia All navigation. A slow Prado image request caused an initial load-wait timeout; the rerun waits for document readiness and passed. A broad alert assertion initially counted Next.js’s accessible route announcer; it was narrowed to actual main-content errors. Public production candidates are checked before traffic promotion.

The remaining 92 institutions in a 100-museum coverage target still need editorial selection, source/image review, complete original prose, translated editions and PDFs. No claim is made that this remaining writing is complete.

## Production delivery — 11 October 2026 (Cyprus)

The guides are live at https://artlines.org/guides. API revision `artline-api-museum-guides-1010-v1` and web revision `artline-web-museum-guides-1010-v1` each serve 100% of production traffic. Runtime settings were compared with the preceding revisions and preserved. Local Terraform image pins reflect the deployed digests; no Terraform apply or commit was made for this work.

All 60 page editions and all 60 downloadable PDFs passed checks on the deployed candidate and again on production. Each downloaded PDF matched the local reviewed file by SHA-256. Canonical URLs, language alternates, preview images, sitemap entries and invalid-edition 404s passed. All 11 candidate browser tests passed; the live Armenia All flow and translated mobile/accessibility checks also passed. The deployment receipt, exact image digests, rollback revisions and validation scope are recorded in `../../deployment-20261011-museum-guides.json`.
