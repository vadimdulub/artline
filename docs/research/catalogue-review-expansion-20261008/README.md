# Catalogue review, one-way alignment and regional expansion — 8 October 2026

The user requested a repeat local → production alignment of all artworks, public access to records in review, and more museums/artworks in small countries, prioritising Cyprus and nearby countries. This pass adds source-backed records and browsing access while preserving publication states, existing populated production metadata and local database contents.

## Alignment

The initial comparison accounted for all 308,001 local artworks. Concurrent local collection work added another 291, then 121 records during this pass. Both batches were reviewed and delivered: **412 additional local artworks**, with their 412 accepted holding assertions, citations and native identifiers, plus two missing source records. All source fields were copied without overwriting existing artworks. The final fixed source snapshot contains **308,413 local artworks**, all represented in production through exact identity or the previously documented 201 duplicate-identity matches.

The final relationship comparison checks artist assignments, accepted museum holdings and primary images across that entire source snapshot. A raw institution-ID difference for *Bharat Mata* resolves through the existing Victoria Memorial alias to its canonical institution; source URL and evidence are identical. Production's 190 differing populated image choices were preserved. They are not missing images. See `relationship-audit-final-summary.json`, `institution-alias-crosswalk.json`, and `independent-data-verification-final.json`.

Two same-title candidates were explicitly kept distinct after primary-object review: Carrière's 1901 lithograph *Marguerite Carrière* (69.1.52 / M0416000035) versus the circa-1900 oil painting (69.1.5 / M0416000008), and the Wyld-workshop *Fête de Saint-Cloud* (607 / M0416000400) versus Bouchon's 1761 painting (2018.4 / M0416005405). The official French catalogue response is preserved in `sources/joconde-version-check.json`.

This is a point-in-time reconciliation, not a continuous replication service. Independent local imports can create later additions.

## Cyprus and nearby-country additions

| Country | Collection | New artworks | Museum record |
| --- | --- | ---: | --- |
| Cyprus | Pedoulas Byzantine Museum | 4 | Existing, previously empty |
| Cyprus | Ecclesiastical Museum, Koilani | 2 | Existing, previously empty |
| Lebanon | Sursock Museum, Beirut | 9 | New |
| Malta | MUŻA, Valletta | 5 | New |

Twenty selected artworks, two museums, two visitor venues, two places, Malta's country record, four artist links, four source records, 22 citations and 20 documented holdings were added. All new museums and artworks remain in review. No on-view claims or image attachments were created.

Pedoulas includes two dated medieval Virgin icons, an undated Saint George icon, and a silver Gospel cover dated 1778. The undated icon remains an explicit review candidate; no year or automatic pre-1970 eligibility was invented. Koilani's Mount Athos workshop attribution remains qualified.

Primary evidence:

- [Pedoulas Community Council's museum page](https://www.pedoulas.org.cy/index.php/en/culture-en/museums-en/byzantine-museum-of-pedoulas).
- [Cyprus Tourism Organisation, *Cyprus, Island of Saints*](https://www.visitcyprus.com/wp-content/uploads/files/cultural_routes/Cyprus_island_of_saints_EN.pdf), printed page 65, figures 109–110. This establishes historical documented holdings, not a fresh display report.
- [Sursock Museum's own collection captions](https://sursock.museum/content/modern-and-contemporary-art) and [visitor page](https://sursock.museum/content/plan-your-visit). Works after 1970, the 1962–85 range and captions lacking a definite title/date were excluded. Untitled (1966), a 120 × 90 cm upright panel, remains distinct from the existing landscape-format WikiArt Untitled (1965).
- [MUŻA museum identity](https://heritagemalta.mt/mt/explore/muza/) and Heritage Malta native object records [3661](https://emuseum.heritagemalta.mt/objects/3661), [1199](https://emuseum.heritagemalta.mt/objects/1199), [3663](https://emuseum.heritagemalta.mt/objects/3663), [3656](https://emuseum.heritagemalta.mt/objects/3656), [3674](https://emuseum.heritagemalta.mt/objects/3674). Captured object metadata explicitly identifies MUŻA. The Preti recto/verso drawing stays one sheet; Cafà's terracotta model is distinct from the final marble in Rome.

`regional-selection.json` contains the reviewed factual selection. HTML receipts and honest access-method notes are under `sources/`. No museum images were downloaded for attachment. Source rights labels have not been reclassified.

## Browsing implementation

- New `/artworks` route and bounded `GET /api/v1/artworks` endpoint include non-archived review records without requiring images, known dates, named artists, accepted holdings or creation-eligibility classification. Filters, pagination and counts run in Go/PostgreSQL. Artwork details use the existing source-aware drawer.
- Research museum browsing includes empty canonical museums and supports geography from an institution's recorded place as well as verified venues. Artist/selection/display filters still require matching works. Alias routes continue resolving to canonical institutions.
- Publication statuses and the explicit `preview=0` access boundary are preserved. The public website's recent cleanup remains intact: no internal review badges or missing-value placeholders were reintroduced.
- Directory pages select at most 61 IDs before enriching their cards. Scoped museum queries retain their existing bounded plans.
- Migration 0037 provides indexes for title pages, undated records, media membership and available local images; production indexes were built concurrently and verified valid. Migration 0038 maintains exact status/undated totals transactionally on artwork insert, delete and relevant updates. Initial totals and later read-only comparisons match source rows. Because the totals schema was installed manually before the release, its exact function, trigger definitions, columns, constraints and row totals were verified under the migration lock before registering `0038_artwork_directory_totals.sql` in the migration ledger; see `directory-totals-migration-registration.json`. Filtered title/image counts use indexed queries. A local database without the totals migration falls back to direct counts without any automatic local writes.
- Catalogue cache revision and preview scope invalidate and separate responses. This pass does not infer dates, museum ownership, current display or publication from visibility.

## Live result

The API and website are live on revisions `artline-api-catalogue-final-1008` and `artline-web-catalogue-final-1008`, each receiving 100% of traffic. The release preserves the concurrently deployed key-artwork API and painter-page changes using their verified Cloud Build source archives.

[Artworks](https://artlines.org/artworks) exposes **391,793 non-archived artworks**, including **391,576 review records** and **47,270 undated works**, at verification time. [Cyprus museums](https://artlines.org/museums?country=CY) returns 169 collections. Public museum-work endpoints return Pedoulas 4, Koilani 2, Sursock 9 and MUŻA 5. The published-only review query returns zero.

Production builds, API checks, artwork drawers, undated filtering, desktop/mobile layouts and the public museum pages passed. Desktop and 390px screenshots were inspected; 390px and 320px checks found no horizontal overflow. The in-app browser runtime was unavailable, so browser verification used standalone Playwright. Exact source hashes, build IDs, live traffic and HTTP/browser checks are recorded in [deployment.json](deployment.json).

## Verification and recovery

Cloud SQL backup **1791461266671** completed successfully before writes. All database operations were transactional and source plans were hash-pinned. Independent post-commit checks verify inserted values and preserved review states. No local catalogue writes, test fixtures, Git commits or Terraform apply were performed.

Read-only tests cover exact totals, review/published boundaries, missing-image/undated/unassigned artworks, keyset pages, invalid and mismatched cursors, empty museums, institution geography and anonymous Cyprus Museum holdings. Frontend tests exercise incomplete records, drawer opening and server-owned filtering. TypeScript and production builds pass. HTTP and browser release results are recorded in `deployment.json`.

The first candidate exposed a catalogue-wide count timeout under concurrent database activity. The final implementation uses the transactional totals projection and dedicated indexes. Query plans are preserved in this directory. Tests use the actual roughly 392,000-row production catalogue; **10-million-row load testing and DML fixture tests remain unperformed** under the real-database no-fixture constraint. Counts projections and broad image/title searches should be included in future ingestion/concurrency load tests.

Backups, exact source snapshots, immutable row plans, preimages, build/deployment receipts and browser screenshots are under:
`/Users/vadimdulub/Library/Application Support/Artline/backups/catalogue-review-expansion-20261008/`.

Implementation scripts: `ops/review-catalogue-20261008.py`, `ops/review-catalogue-followup-20261008.py`, `ops/expand-regional-museums-20261008.py`.
