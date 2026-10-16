# Account studies mockups

Revised 11 October 2026 using the user's supplied timeline screenshot. This is
an isolated design preview for **Account → Studies**, not a production change.

- [All revised mockups](overview.html)
- [Interactive timeline](index.html?screen=timeline)
- [Add your own link](index.html?screen=link)
- [Gallery](index.html?screen=gallery)
- [Artwork comparison](index.html?screen=compare)
- Screenshots: [Timeline](04-timeline.png), [Link entry](07-add-your-link.png),
  [Personal link card](08-own-link-card.png), [Gallery](01-research-set.png),
  [Record picker](02-add-artworks.png), [Compare](03-compare.png),
  [Mobile gallery](05-mobile-gallery.png), [Mobile record](06-mobile-record.png).

Preview server: http://127.0.0.1:8791/overview.html

## Changes following the reference

The study now uses the light paper chronology supplied by the user: named artist
or context rows on the left, dated cards in the middle, and a record inspector
on the right. Artworks, Books and Events have independent checkbox filters,
counts and labelled colours. Timeline is the desktop default; a first mobile
visit uses Gallery. The existing Artlines wordmark, header and account navigation
remain in the concept. The production painter-lifespan explorer is separate.

The timeline shows artwork creation dates, the book's first-edition date, and
the event's historical opening date. Date ranges remain visible; Seurat's painting
and later border are separate intervals. Compact titles retain their complete
values in accessible labels, inspection and export.

## Personal links

**Add your link** accepts a URL and a record type: artwork, book or event. Title,
creator/context and year are optional. The live card preview shows what will be
saved. A URL alone creates a card under **Undated links**; no creation/publication
year is invented. A supplied year positions the card on the timeline. Details
can be edited later. Out-of-range supplied years expand the preview range so
newly added dated cards remain visible.

Personal cards are explicitly labelled **Your link**, retain their original URL,
and open the external page in a new tab. The preview does not fetch external
page metadata or images. A URL-only card uses its hostname as the editable title.
User details remain personal study annotations and are not catalogue assertions.
Books and events do not enter artwork comparison. Personal artwork links can be
compared, using a link placeholder when no image exists.

HTTP/HTTPS links are accepted; executable schemes and URLs containing credentials
are rejected. Text is rendered literally. Browser-local persistence includes
personal cards, research-set membership, notes, selected artworks and workflow.
Previous v1 notes and selections are retained when the v2 preview first loads.
A repeated personal URL of the same type reuses its existing card. CSV exports
include types, source URLs, original date labels, personal/source origin and notes,
exclude image files, and neutralize formula-leading text.

## Fixtures and sources

The initial six records are four existing catalogue artworks plus two small
source-backed context fixtures. Authentic approved artwork images were copied
from the existing public assets, with source/rights evidence beside them.

| Record | Source | Date shown |
| --- | --- | --- |
| Caillebotte, Paris Street; Rainy Day | [Art Institute of Chicago](https://www.artic.edu/artworks/20684) | 1877 |
| Monet, Arrival of the Normandy Train, Gare Saint-Lazare | [Art Institute of Chicago](https://www.artic.edu/artworks/16571) | 1877 |
| Morisot, Woman at Her Toilette | [Art Institute of Chicago](https://www.artic.edu/artworks/11723) | 1875–80 |
| Seurat, A Sunday on La Grande Jatte — 1884 | [Art Institute of Chicago](https://www.artic.edu/artworks/27992) | 1884–86, border added 1888–89 |
| Zola, L’Assommoir | [BnF work reference](https://data.bnf.fr/ark:/12148/cb12001598m), [serial publication record](https://catalogue.bnf.fr/ark:/12148/cb31690619g) | 1877 · first book edition |
| First Impressionist exhibition opens | [Musée d’Orsay, Base Salons](https://salons.musee-orsay.fr/Detail/occurrences/83) | 15 April 1874 |

The BnF sources distinguish serial publication beginning in 1876 from the 1877
book edition. The event source records the actual 1874 exhibition; it is not a
modern reconstruction date. The illustrative personal card also uses the BnF
serial-publication URL and an example user-authored title. It is clearly a personal
reference, not a seventh source-backed catalogue object.

Morisot's conflicting museum API numeric start of 1870 remains in the saved
source evidence. The displayed 1875–80 date drives the preview, and the discrepancy
is disclosed. Holdings do not establish current display. Sources were reviewed
on 11 October 2026. The six fixtures are not a catalogue migration.

## Validation and boundaries

The first pass read `CODEX_TASK.txt`, repository and web `AGENTS.md`, design
principles, account and bookmark implementations, navigation, artwork contracts,
and repository commands. The companion JSON/PNG/SVG handoff files were not found.
The screenshot supplied in the revision is now the authoritative layout reference.

Screenshots are actual local Chrome captures of these HTML files. The in-app
Browser connection again failed before execution with a missing sandbox-policy
metadata error; the repository's installed Playwright/Chrome renderer was used.
Temporary automation lives in `/tmp/artline-account-studies-qa/`.

`verification-v2.json` records the revision's interaction and responsive checks;
`verification.json` preserves the first pass's checks. Checks cover mixed-record
filters/search, context inspection, link-only creation, reload persistence, adding
an optional year, separate date intervals, artwork-only comparison, personal-note
export, URL validation, Escape/focus, and layouts at 1440, 1280, 1024, 768, 390 and
320px. No application build was needed because application code did not change.

Only files in this design directory changed. No database records, account data,
production routes, catalogue statuses or production assets were changed. No commit,
production deployment or ingestion occurred. This preview uses browser-local
storage and a tiny fixture; it does not claim account sync or full catalogue search.

Production integration still needs account-owned studies/links/notes, Go-backed
bounded queries, source handling for personal URLs, real bookmark integration,
network/loading states and multiple recorded date intervals. Public-catalogue
eligibility and authentication rules remain unchanged. Automatic rich previews
for external links are not implemented by this concept.
