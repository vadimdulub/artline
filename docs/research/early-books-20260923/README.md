# Early books and highlights — 23 September 2026

Added **20 books** to the local Artline catalogue and **52 additional highlights**
(20 new records and 32 existing records). The selection contains 53 works because
*Muqaddimah* was already highlighted; its previously missing date was reviewed.
Twelve existing book date records were corrected or supplied. Fifteen new creator
records and one discovery term were added. All selected records remain in review.
No production upload, publication, deployment or image download was performed.

The requested period “0–1600” is represented as **1–1600 CE**, without inventing
a year zero. Every work newly selected here is wholly within that interval.

## Local outcome

| Measure | Before | After |
| --- | ---: | ---: |
| Stored book records | 10,000 | 10,020 |
| Books wholly dated within 1–1600 | 708 | 735 |
| Editorial highlights, all years | 154 | 206 |
| Highlights wholly dated within 1–1600 | 18 | 71 |
| Published books | 0 | 0 |

The [local 1–1600 highlights view](http://localhost:3000/books?start=1&end=1600&top100=true)
returns **72** works. It also includes the existing Bible record, whose recorded
range crosses from BCE into this interval. This is the existing overlap rule;
the Bible was not added or changed by this campaign.

The current Books display cutoff exposes 8,705 research records; the stored total
also includes records outside that display cutoff. Highlights remain an editorial
selection, not a claim of universal ranking. `top100` is the existing API/storage
field name, and does not impose a 100-work limit.

## New records

| Book | Recorded date | Creator |
| --- | --- | --- |
| [Christian Topography](https://www.wikidata.org/wiki/Q1216330) | c. 550 | Cosmas Indicopleustes |
| [De velitatione bellica](https://www.wikidata.org/wiki/Q5244989) | c. 970 | Creator not recorded |
| [The Book of Healing](https://www.wikidata.org/wiki/Q1030940) | c. 1014–1027 | Avicenna |
| [Canon of Medicine](https://www.wikidata.org/wiki/Q466060) | 1025 | Avicenna |
| [De humani corporis fabrica](https://www.wikidata.org/wiki/Q1233009) | 1543 | Andreas Vesalius |
| [Al-Tasrif](https://www.wikidata.org/wiki/Q2724312) | c. 1000 | Abu al-Qasim al-Zahrawi |
| [Al-Jabr (The Compendious Book on Calculation by Completion and Balancing)](https://www.wikidata.org/wiki/Q8369) | c. 820 | Muḥammad ibn Musa al-Khwarizmi |
| [Book of Optics](https://www.wikidata.org/wiki/Q264562) | c. 1021 | Ibn al-Haytham |
| [Tabula Rogeriana (The Book of Roger)](https://www.wikidata.org/wiki/Q1089336) | 1154 | Abu Abdullah Muhammad al-Idrisi al-Qurtubi al-Hasani as-Sabti |
| [Brāhmasphuṭasiddhānta](https://www.wikidata.org/wiki/Q1290001) | c. 628 | Brahmagupta |
| [The Book of Margery Kempe](https://www.wikidata.org/wiki/Q16210817) | 1430s | Margery Kempe |
| [De Re Metallica](https://www.wikidata.org/wiki/Q3193676) | 1556 | Georgius Agricola |
| [Revelations of Divine Love](https://www.wikidata.org/wiki/Q7317855) | 14th–15th century (composition) | Julian of Norwich |
| [The Treasure of the City of Ladies](https://www.wikidata.org/wiki/Q16765210) | 1405 | Christine de Pizan |
| [The Flowing Light of the Godhead](https://www.wikidata.org/wiki/Q139855844) | c. 1250–1282 | Mechthild of Magdeburg |
| [The Faerie Queene](https://www.wikidata.org/wiki/Q1813771) | 1590 (first publication) | Edmund Spenser |
| [The Lusiads (Os Lusíadas)](https://www.wikidata.org/wiki/Q781898) | 1572 | Luís Vaz de Camões |
| [The Sarashina Diary](https://www.wikidata.org/wiki/Q217955) | 11th century | Sugawara no Takasue no musume |
| [Digenes Akritas](https://www.wikidata.org/wiki/Q1129515) | 12th century | Creator not recorded |
| [The Life of St. Sava](https://www.wikidata.org/wiki/Q19569020) | 1254 | Domentijan |

## Research and date decisions

The bounded candidate pass retained 74 page results. Work IDs were reconciled
against existing source IDs before selection, including deduplication of alternate
page names. Redirects to people, genres, disambiguation pages, editions requiring
separate identity review, and works outside the period were excluded. Candidates
are research evidence; only the explicit selection was imported.

Each selected work has a documented editorial rationale. Matched Wikipedia
introductions and Wikidata metadata are retained with source revisions, retrieval
receipts and SHA-256 checksums. New book introductions are bounded excerpts with
pinned Wikipedia links and CC BY-SA 4.0 attribution. Creator records retain source
identity and unknown fields. Existing creators were not overwritten. Two missing
work-author links were reconciled through matching creator articles for Mechthild
of Magdeburg and Domentijan. No modern country was inferred from an author's name.

Date labels distinguish composition, completion, draft and first printing.
Examples include the 1578 draft and 1596 first printing of *Compendium of Materia
Medica*, the 1575 completion and 1581 first complete printing of *Jerusalem
Delivered*, and the 14th–15th century composition envelope of *Revelations of
Divine Love*, whose much later print date is not used as its composition date.
Approximate dates and broad source intervals stay approximate or broad.

Additional bibliographic checks:

- [Columbia University Libraries, De Re Metallica](https://exhibitions.library.columbia.edu/exhibits/show/jewels/item/11019): 1556 edition; direct source capture retained.
- [British Library, The Treasure of the City of Ladies](https://searcharchives.bl.uk/catalog/040-002024028): 1405 composition; direct source capture retained.
- [Library of Congress, The Lusiads](https://www.loc.gov/item/2021666936/): 1572 first edition. Direct download returned HTTP 403; the indexed catalogue text and corroborating pinned Wikipedia introduction were reviewed. The access limitation is recorded, not represented as a downloaded catalogue page.
- [Cambridge University Press, City of God chronology](https://assets.cambridge.org/97805214/68435/frontmatter/9780521468435_frontmatter.pdf): 413–426 composition. Direct download timed out; indexed publisher chronology was reviewed. The access limitation is retained in the review notes.

## Implementation and retained evidence

- `ops/curated-early-books-20260923.json`: explicit work selection and reviewed date decisions.
- `ops/research-early-books-20260923.py`: bounded source capture, without catalogue writes.
- `ops/expand-early-books-20260923.py`: read-only preparation and explicit local transactional application.
- `candidates.json`, `metadata.json`, `sources/`, `additional-source-reviews.json`: retained research and access notes.
- `plan.json`, `new-books.json`, `prepared-summary.json`: exact prepared records, projections, locked preimages and counts.
- `apply-receipt.json`: committed local result, plan checksum and backup reference.

Backup: `/Users/vadimdulub/Library/Application Support/Artline/backups/early-books-20260923/preimages.json`.
The applied plan checksum is `cd2b1d36f9a9a3a9155601bf82f74540bb1d4fb2436690a9146f22d1d3246ecf`.

The application checked source hashes and preimages, used an advisory lock and
one transaction, preserved publication status, and rebuilt affected discovery
projections after base-record invalidation. Unselected book records and discovery
projections were fingerprinted before and after and remained unchanged. Replaying
the application returns a no-change result. Re-preparation after a successful
application preserves the completed plan and its evidence.

Historical import/discovery scripts still represent their original 10,000-book
batch. Their precondition checks prevent silently overwriting these newer
projections. Any future full rebuild or production release must explicitly merge
this reviewed campaign with the existing context, language and date corrections;
do not replay an old snapshot as the current catalogue.

## Verification

- Go importer validation accepted all 20 distinct source-linked records without applying them again.
- Read-only Go audit traversed 8,705 visible records across 88 pages, checked period counts, creator data, facet intersections and publication gating.
- All 206 highlights were traversed at page sizes 200 and 100 with identical order and no gaps or duplicates; highlighted authors total 175.
- Thirteen browser checks passed across catalogue, filters, crowded periods and early-book details. Three existing checks were updated to expect the current filter controls instead of previously removed help text, then passed on rerun.
- Desktop and mobile checks confirmed all 53 selected works are reachable in the period view, correct date labels and source attribution, next-book navigation, no horizontal overflow, and retained review visibility. An unauthenticated direct API request for a new review record returned 404.
- Accessibility checks passed for the tested filters and crowded-period layouts at desktop and phone widths.
- Python compilation, TypeScript, targeted ESLint and whitespace checks passed.

Browser artifacts remain under `/private/tmp/artline-early-books-verified/` and
`/private/tmp/artline-early-books-crowded-verified/`. These checks exercise the real
local catalogue; no test database or fixtures were created. They are correctness
checks at current catalogue size, not evidence of ten-million-row load capacity.
