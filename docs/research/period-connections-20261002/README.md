# Period connections and filter review — 2 October 2026

Reviewed all 31 existing All starting points against the real catalogue, then added **Baroque art and its world**, bringing the total to 32. The new view connects five selected painters, 1,530 eligible illustrated artworks, 14 books and three historical events. Its literature is explicitly cultural context, not a blanket Baroque style attribution.

## Filter changes

The compact filter bar retains its height. “Period or theme” now opens choices grouped by historical context, with dates and geographic or creative scope. Search also matches those descriptions, so a place such as Timbuktu can find the appropriate starting point. Selected values, keyboard navigation, Escape, reload and history remain supported.

Lane-specific artwork, book and event filters now have removable summary chips. “Clear filters” clears these fields as well as the common filters; it keeps the selected layers and manually chosen years. Choosing a period still clears editorial caps and fits the matching dates. Generic search and deliberate filters still turn off Top 100 / Highlights.

Design follows Artline’s existing paper (#f2efe8), ink (#1b1916), dark canvas (#12110f), muted text (#b5ad9f) and book accent (#c1a579), with serif group headings and familiar sans-serif controls. The open picker carries the extra context; the closed bar and timeline gain no extra guidance rows. Desktop choices form one left-aligned column; the mobile panel fits inside the viewport. No additional decorative card system was introduced.

## Researched connections

Forty-six book-to-period links were added, including fourteen for the new Baroque view. These mostly reuse recently researched catalogue records; they are not forty-six newly imported books. Default author choices were updated alongside the links so they do not hide the new selections.

| Starting point | Books before | Books after |
| --- | ---: | ---: |
| Byzantium | 5 | 11 |
| Scientific Revolution | 8 | 14 |
| Enlightenment | 8 | 14 |
| Women’s rights | 34 | 40 |
| French Revolution | 4 | 6 |
| Romanticism | 10 | 15 |
| West African trade and learning | 0 | 1 |
| Baroque art and its world | — | 14 |

The Byzantine additions cover law, agriculture, chronicles and romance. Science adds Harvey, Gilbert, Kepler and Kircher; the surrounding literary views add works concerned with women’s choices, education and social reform. Work identities, dates, original languages and source revisions come from the retained Byzantine and pre-1850 research campaigns. `connections.json` records the exact IDs and source links. No book dates, country associations or existing publication states were changed to fit a period.

The Baroque starting point draws on [The Met’s Baroque Rome essay](https://www.metmuseum.org/essays/baroque-rome), its [Northern European genre painting essay](https://www.metmuseum.org/essays/genre-painting-in-northern-europe), and the catalogue’s existing museum records. Its cover is Vermeer’s [Young Woman with a Water Pitcher](https://www.metmuseum.org/art/collection/search/437881). Six explicit artwork links retain portable slug identities across databases. All six existing reproductions are under 100,000 bytes (55,582–99,234 bytes); no duplicate artworks or new image downloads were required.

## One new book and author

Added **Tarikh al-Sudan** (Q13217999), the Arabic chronicle of Songhai and Timbuktu, dated **c. 1655**. The original work is distinguished from later manuscript copies and printed translations. The [reviewed Wikipedia revision](https://en.wikipedia.org/w/index.php?oldid=1336394489) supports the date, language and association; the [Library of Congress collection](https://www.loc.gov/collections/islamic-manuscripts-from-mali/articles-and-essays/timbuktu-an-islamic-cultural-center/) provides broader context for Timbuktu’s manuscript culture.

The author record preserves the reviewed birth year 1594 and open-ended death date “After 1655–1656”, rather than the less precise Wikidata values. The biography is attributed to the same article. No modern country is inferred. The older, undated Tarikh al-fattash remains untouched because its composite textual history needs separate work. The Book of the Eparch also remains undated; it was not assigned an invented interval to appear on the Byzantine timeline.

Local and production now have 10,069 books, 2,172 dated before 1850 (including ancient works), and 256 editorial highlights. All 34 previously published books remain published; the new book remains in review and is available through the existing public research preview.

Local plan SHA-256: `91cbb574ce9121d7cd85c677d2ee0b9d9c48c55b9e731a9483ebfeabdecd5f4d`.
Production plan SHA-256: `f569faf315ba09e4112a1d1fb5e7f7978083e2d9cc7b3b36254a1393d9b0a99a`.
Successful Cloud SQL backup: `1790963667418`.

The guarded import checked exact preimages and source captures, preserved all unselected books and discovery projections, and verified the committed result. Backups and source snapshots are under `/Users/vadimdulub/Library/Application Support/Artline/backups/period-connections-20261002-production/`.

## Validation

Go tests, 192 frontend unit tests, TypeScript and scoped ESLint pass. Chrome checks at 1440, 390 and 320 px cover grouped search, period selection, keyboard focus, WCAG 2 A/AA checks, reload/history and complete filter clearing. Five further discovery checks cover automatic date fitting and clearing editorial caps across Painters, Paintings, Books, Events and All.

Every starting point is queried in database-enforced read-only mode. The audit verifies bounded pages, dates, visibility, artwork cutoff, images, explicit book/event membership and retained context when country defaults apply. Representative EXPLAIN ANALYZE plans are retained in the release backup. These checks use the actual catalogue, not a 10-million-artwork load test; capacity testing at that scale remains outstanding.
