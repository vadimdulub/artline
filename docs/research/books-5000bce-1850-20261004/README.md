# Books, 5000 BCE–1850 — 4 October 2026

Added 29 original-work records and 15 new creator profiles to both the real local catalogue and production. The batch uses 23 named creator identities; eight profiles already existed. The anonymous Sumerian *Lament for Ur* has no invented named author. All 29 records remain in review and are available through the existing research preview. Existing publication and Top 100 membership are unchanged.

| Target | Books before | Books after | Within requested interval after |
| --- | ---: | ---: | ---: |
| Local | 10,107 | 10,136 | 2,216 |
| Production | 10,069 | 10,098 | 2,216 |

The 38 unrelated local-only books were not synchronized. Exact book JSON, source checksums, creator profiles and creator links match across both targets for this batch. Both databases retain 34 published books and 256 highlights.

## Selected works

| Work | Date label | Image |
| --- | --- | --- |
| Lament for Ur | c. 2000 BCE | Original Artline text fallback |
| On the Sacred Disease | c. 400 BCE | Original Artline text fallback |
| De aquaeductu | c. 98 CE | Original Artline text fallback |
| Book of Roads and Kingdoms (Ibn Khordadbeh) | c. 870 | Original Artline text fallback |
| Mysterium Cosmographicum | 1596 | Historical title page |
| Uranometria | 1603 | Historical title page |
| Hesperides | 1648 | Historical title page |
| The Compleat Angler | 1653 | Historical title page |
| The Convent of Pleasure | 1668 | Original Artline text fallback |
| Ars Conjectandi | 1713 | Historical title page |
| Introductio in analysin infinitorum | 1748 | Historical title page |
| Institutiones calculi differentialis | 1748 | Historical title page |
| The Adventures of Peregrine Pickle | 1751 | Historical title page |
| The Adventures of Ferdinand, Count Fathom | 1753 | Original Artline text fallback |
| The Deserted Village | 1770 | Historical title page |
| The Man of Feeling | 1771 | Historical title page |
| The Expedition of Humphry Clinker | 1771 | Historical title page |
| The Village | 1783 | Original Artline text fallback |
| Mécanique analytique | 1788 | Historical title page |
| A Simple Story | 1791 | Historical title page |
| Nature and Art | 1796 | Original Artline text fallback |
| Traité de mécanique céleste | 1799–1825 | Historical title page |
| The Lay of the Last Minstrel | 1805 | Historical title page |
| Zofloya | 1806 | Historical title page |
| The Borough | 1810 | Original Artline text fallback |
| The Pilot: A Tale of the Sea | 1824 | Historical title page |
| On the Connexion of the Physical Sciences | 1834 | Historical title page |
| The Princess (Tennyson poem) | 1847 | Original Artline text fallback |
| The Prelude | 1798–1850 | Historical title page |

## Dates and identities

The requested limits are inclusive. No year zero or invented 5000 BCE record is introduced. The earliest new work is approximately 2000 BCE. Original work identity was checked against Wikidata and the matched article; people, disambiguation pages, translations/editions, unrelated image search results and existing book identities were excluded.

Composition, first publication, posthumous publication, and publication across multiple volumes remain distinguished in `dateBasis`. *The Prelude* retains its 1798–1850 development interval. *Institutiones calculi differentialis* records the sourced 1748 writing date while its selected title page is explicitly labelled 1755. The 1823 imprint on the image for *The Pilot* remains separate from the article’s 1824 publication date. *On the Sacred Disease* retains traditional attribution to Hippocrates.

Conflicting secondary dates were checked against [ETH Library’s original 1788 Lagrange edition](https://www.e-rara.ch/zut/content/titleinfo/2488394), [Kyoto University’s 1799–1825 Laplace catalogue record](https://rmda.kulib.kyoto-u.ac.jp/en/item/rb00033955), [the Cambridge Frontinus edition](https://assets.cambridge.org/052183/2519/frontmatter/0521832519_frontmatter.htm), and [the University of Glasgow’s 1834 Somerville text](https://www.scottishcorpus.ac.uk/cmsw/document/?documentid=97). The Cambridge page was retained as an indexed publisher-page capture because direct retrieval timed out. Conflicting secondary overview text is omitted for the affected records. No geography is inferred from an author’s citizenship or a work’s setting.

## Images

Every selected book and named creator received a bounded image check. The result is 19 historical title-page images and 21 creator portraits, all with source, credit and licence fields. Ten books have no verified image and two named creators have no selected portrait. Exact coverage and reasons are retained in `image-coverage.json`. Johann Bayer’s search results were namesakes; the Ibn Khordadbeh candidate was an unverified modern depiction. Anonymous authors have no invented portraits.

A modern commercial Frontinus cover, unrelated compositions named Prelude, interior illustrations, source files with copyright warnings, and unrelated map or convent images were rejected. Alternate library portraits replaced several rejected first candidates. Hippocrates and Frontinus are explicitly labelled later depictions; Laplace’s posthumous portrait is also labelled. Book dates are independent of reproduced edition dates.

The 40 JPEGs preserve the full supplied frame, including source library scales, and use proportional resizing and compression. The largest is 96,209 bytes. Thirty-nine reproductions are marked Public domain; the Met title page for *Humphry Clinker* is CC0. Only selected source images were downloaded. Originals, URL receipts and hashes are retained under the designated Artline `source-images/books-5000bce-1850-20261004` directory.

The reviewed manifests are merged additively into `apps/server/internal/books/cover-selection.json` and `portrait-selection.json`. Existing selections are preserved. Assets are under `apps/web/public/images/{books,authors}/selected-20261004/`. The API continues to attach images through exact source identities after normal visibility checks; imported JSON cannot bypass image selection.

## Verification and recovery

The Go importer validated all 29 records without applying its generic import path. Existing books were checked for duplicate source identities and normalized titles. Guarded transactions required the pinned plan, successful recovery backups, exact preimages and unchanged dependencies. Fingerprints verified preservation of unselected books, discovery rows, creator profiles and links. No fixtures, test databases, migrations, bulk image download, publication changes or artwork mutations were performed.

Go books, atlas and HTTP API checks passed. Local HTTP verification checked all 29 records, 19 cover bindings, 21 portrait bindings and all 40 served image checksums through the frontend proxy. Local debug and all-feature access remain enabled on loopback, and the preview API connects with PostgreSQL read-only transactions. These are correctness and delivery checks, not a ten-million-row load test.

Local full recovery dump and exact local/production preimages are under `/Users/vadimdulub/Library/Application Support/Artline/backups/books-5000bce-1850-20261004/`. Cloud SQL backup `1791141438127` completed successfully before writes. The local dump archive directory was validated without restoring or creating a test database.

Database plan SHA-256: `a5f62d4edb574bc59076cd11c08fe937982c6c6e8768dd5e671ee25c260a31eb`. Image manifest SHA-256: `37b9449132630b277020c5dda770fd26e3f24c6b65f617b8faf9fc3f8637eb32`.

Database delivery receipts: `local-apply-receipt.json`, `cloud-apply-receipt.json`, `database-parity.json`. Image decisions, visual review, per-image hashes and missing-image reasons are retained alongside the source captures.

The image release is live at https://artlines.org. API revision `artline-api-books2-1004` and web revision `artline-web-books2-1004` each serve 100% of normal traffic. Public-site verification checked all 29 book records, their 23 creator identities and all 40 image checksums. Production Google sign-in remains enabled and local-debug access is disabled. Full results are in `release-verification.json` and `public-api-verification.json`. The image-only release is based on the currently serving application, preserving the currently serving account and reading changes. No commit or Terraform apply is part of this campaign.

Rollback references: the prior serving application revisions are `artline-api-account-reading-1004` and `artline-web-account-reading-1004`. Database rollback is separate and must use scoped preimages; do not restore over later catalogue or member changes. No records were deleted.
