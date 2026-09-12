# Collection-first iteration — verified progress

## Latest verified state — 12 September 2026, 07:11 UTC

**106,350 artworks / 5,328 artists / 644 attached images.** All 644 local images
exist, fully decode, match their recorded hashes/bytes/dimensions, and have valid
primary artwork associations. Zero unlinked artwork raster files. Final audit:
`output/data-collection-20260911-2016/library-audit-v3/`.

This follow-up adds **4 paintings / 5 images** (Karlsruhe four, Athens one).
Collection-first cumulative additions: **11 artworks / 12 images**. Since the
earlier 18:52 baseline: 20 artworks / 23 images. These are distinct reporting
windows, not additive totals. No active-time claim includes the overnight gap.

The [Athens workshop icon](athens-icons.md) now has a 96,550-byte CC BY-SA photo,
with its photographer credited. Four additional API checks and full image decode,
served hash and visual full-frame check passed. No new anonymous artist profile.
Two more Athens icon image gaps were examined: a conflicting accession was
rejected, and incomplete rights/identity leads remain deferred.

Current gaps: 14,751 eligible paintings; 105,705 eligible artworks of all types.
Monet remains 300 records / 32 images. The browser visibility issue remains open.
Legacy exceptions unchanged: 161 oversized files and 15 missing structured
rights-evidence rows, not missing or corrupt files. No silent replacements.

Receipt audit v3: 206 successful metadata receipts, 107,745 exact source/row
assertions covering 106,189 distinct works, **zero failures**. Another 161 existing
records use legacy/other receipt formats; 11 origins have now been reconciled to
catalogue migrations, with the remaining 150 still queued. This does not claim
every captured candidate was imported. Tests for the four affected Go packages
passed with the fixture-database variable unset.

## Follow-up on 12 September — Karlsruhe completed

Added four paintings and four authentic images: two François Boucher works,
one Camille Pissarro and one Peter Paul Rubens, all held by Karlsruhe. No new
museum or artist profile was created. Latest completed Karlsruhe totals:
106,350 artworks / 643 images. This collection-first phase now adds 11 works /
11 images before the separate Athens icon follow-up. Do not count the overnight
gap between tool activity on 11 and 12 September as active work.

Checklists: [Boucher](francois-boucher.md), [Pissarro](camille-pissarro.md),
[Rubens](peter-paul-rubens.md). Four metadata details and two access checks passed;
14 image API checks, four full decodes, served hashes and manual composition
checks passed. Whole-database preservation passed; no highlights or publication.

New image sizes: 94,693; 89,872; 97,932; 97,303 bytes. Metadata manifest SHA256
`47d96daa160e8a18f0913627fa1aa05d415dac448f1394eb284a2001e0c8a262`;
image selection `a70a0eb3b191dad74f9a2ef1ecbdf53241cf0b48e3d5cd456870cb54ce14011b`.
Use `karlsruhe-next-v2`; v1 was never applied and had a stale batch-size sentence.
The first capture finished four pages but refused to replace the prior batch's
capture inventory. Eight new source/receipt files were relocated to their own
directory and the inventory completed from cache, without refetching pages.

Both backups are under the relocated `artline-popular-resume-20260911-backup.xM3Mcm`
folder: `before-karlsruhe-next.dump` SHA256
`4b1b43703138815053e86499bccb9f69f91c667829caace96e6b58022c90e363`;
`before-karlsruhe-next-images.dump` SHA256
`c681159bfc4c3f2f86e8e259c50399fd277ee3a8340a40b57585fdd83937edae`.
Archive tables of contents checked before mutation.

The eleven records without external IDs were traced to real catalogue migrations,
not disposable test data. See [legacy reconciliation](LEGACY_RECONCILIATION.md).
Their citations and existing images are preserved; no identifiers invented.

The historical snapshot below remains unchanged; newer results above supersede
its live totals, not its original measurements.

User redirected task at20:16:31UTC on11 September2026. Execute [the collection prompt](../../DATA_AND_IMAGE_COLLECTION_PROMPT.md). This is not a claim that the earlier4–5-hour window completed.

## Cleanup

- Real PostgreSQL contains only one Artline database, `artline`; no Artline test schema remained in it. No database dropped and no unrelated database touched.
-22 inspected backup directories containing36 custom-format dumps (6,887,312,797 bytes) moved out of Documents to `/Users/vadimdulub/Library/Application Support/Artline/backups/`. All hashes verified before/after; no backups deleted. See [locations](../../LOCAL_DATA_LOCATIONS.md) and relocation journal `output/data-collection-20260911-2016/backup-relocation.jsonl`. Moving backups clears clutter, not disk space.
-74 temporary PDF proof/contact-sheet files (11,029,094 bytes) and one browser-test state file moved to `/Users/vadimdulub/.Trash/artline-disposable-20260911-2024/`. Recoverable; no permanent deletion. Actual research reports, pinned source captures, imports, artwork assets and source-code tests preserved.

## Applied batch

Seven Karlsruhe artworks (six paintings and one Klee drawing), six painters, one museum; seven authentic CC0 images,72,956–99,122 bytes. This phase adds **7 artworks /7 images**. Earlier resumed phase9works/11images remains separate; combined since18:52baseline16works/18images.

| Painter | New works/images | Checklist |
|---|---:|---|
| Paul Klee | 2/2 | [Review](paul-klee.md) |
| Caspar David Friedrich | 1/1 | [Review](caspar-david-friedrich.md) |
| Paul Gauguin | 1/1 | [Review](paul-gauguin.md) |
| Paul Cézanne | 1/1 | [Review](paul-cezanne.md) |
| Edgar Degas | 1/1 | [Review](edgar-degas.md) |
| Claude Monet | 1/1 | [Review](claude-monet.md) |

Metadata7 object-detail/2 access checks passed. Image23 API checks,7 complete JPEG decodes, served hashes and visual full-composition checks passed. Whole-DB preservation passed. No highlights, publication or prior editorial changes.

Metadata manifest SHA256 `46b6825d12ba204c94459093ca6e4e9a54df6e4c926cb291de4a215b53949a8b`; image selection `2a9bd13987bfa3c2880b8a6195903a6a57ea9d5581590db12e403f78204fc67b`. Initial metadata preview was safely rejected for missing museum allowlist mapping; mapping corrected and a new preview passed before application. Tests pass with fixture database environment unset.

Before-images backup `before-karlsruhe-images.dump` SHA256 `fa0a03900af7906e5dde8854846c7a9faeff40d6809455d3b6d055037773064e`, in the relocated `artline-popular-resume-20260911-backup.xM3Mcm` folder. Archive table of contents checked. Metadata backup hash recorded in previous checkpoint.

## Real database and disk audit

Snapshot20:29:24UTC: **106,346 artworks,5,328 artists,639 media assets**. All639 local raster files exist, fully decode, and match recorded size/hash/dimensions. Zero raster files without a media row. No missing/corrupt files found.

-15,259 paintings:506 with primary images;14,752 eligible painting-image gaps; one additional painting needs date review.
-58,981 prints and32,101 drawings account for most of the larger queue. Five frescoes all have images.
-105,706 eligible image gaps across all existing work types, exported in bounded500-row primary-key pages to `output/data-collection-20260911-2016/library-audit-v2/eligible-missing-image-queue.jsonl`. These are inventory gaps, not105,706 completed source searches. Reconcile prior deferred states before downloading.
-161 older files exceed100,000 bytes;15 older files lack structured `media_rights_evidence` rows. All have source and licence fields, but this is not enough to mark source-backed rights review complete. No silent replacement or invented evidence.477 pass all automated checks.
-Monet:300 database artworks/32 primary images. Their existence does NOT establish correct rendering in the right panel; the requested UI audit remains queued.

See `output/data-collection-20260911-2016/library-audit-v2/AUDIT.md`, `summary.json` and per-media JSONL. The raw statistic `primary_media_missing_artwork_media_link=639` means primary images are not duplicated into the separate gallery relation; primary foreign-key associations are valid. It is not evidence of639 broken image links, and no gallery rows were invented.

First audit attempt was read-only and stopped on an incorrect institution-country column; v2 uses the actual places relation and completed. No schema/database fixture created. Unit file fixtures live in automatic OS temporary directories and are cleaned by Go tests.

## Import receipt reconciliation

205 recognized successful metadata receipts:107,741 receipt-work assertions covering106,185 distinct artworks checked against the live DB and exact source identifiers/citations; **zero failed assertions**.258 successful receipt files found in total; other formats (images, directory/creator operations) listed separately, not misrepresented as metadata checks.

161 current artworks lie outside that receipt format:73 Met,29 Chicago,18 National Gallery Greece,11 Prado,9 Cleveland,9 Uffizi,1 MAM and11 without external identifiers. They are present in the DB; they are NOT161 missing imports. Their legacy/other-format evidence requires separate reconciliation, especially the11 without identifiers.

Full results and the explicit161-row follow-up list: `output/data-collection-20260911-2016/receipt-audit-v2/`. Captured leads and rejected/deferred source records are not claimed imported.

## Query and verification limits

The first eligible-filter-inside-keyset query chose a full sequential scan per page. Changed the read-only exporter to materialize a500-row primary-key page first, then classify eligibility and build source/creator details within that page. Representative live plan uses `artworks_pkey`,500 rows,~9.6ms in the observed run. This is not a10-million-row benchmark. Database counts scan once; no frontend payload or new DB index was introduced.

This iteration does not claim all pictures are obtainable, all data sources exhausted, or browser visibility repaired. Collection-first prompt is saved and has been executed for cleanup, reconciliation, imports and image verification; the next batch remains below.
