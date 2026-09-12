# US / Europe discovery and NGA import verification

2026-09-09. No commits, deployment, image downloads or publication. This is a completed ingestion/research pass, not completion of every US/European museum catalogue.

## Actual database changes

- Catalogue: 715 -> 2,223 artworks. Added 1,508 NGA paintings; reused two existing NGA works without replacing editorial fields. 356 existing painter authorities represented by 1,510 selected records. Active painter count stays 1,001.
- Catalogue institutions remain 56. Discovery candidates are deliberately not promoted to institutions. Media stays 211; published artworks and display assertions stay zero; curated selections stay 391.
- Added 3,021 citations and 1,508 holding assertions. NGA import job `a869ca3a-95e9-474f-bf10-6c9ce12f3bac`.
- New immutable research storage: 10,324 source records in two snapshots. The source evidence contains factual data and source texts; it is not exposed through the public app.
- Museum directory snapshot: 4,542 distinct Wikidata candidate identities, 1,216 Muséofile records and the supplied 111-source registry = 5,869 source rows. These sets overlap; never call their sum a unique museum count. 940 Wikidata candidates have a US country claim. 57/58 country/territory partitions retrieved; Italy failed after one bounded retry. Zero-result partitions and geopolitical boundary scopes are retained explicitly.
- NGA staging: all 4,455 painting-classified source records, including selected rows and excluded/deferred evidence. Only 1,510 passed all catalogue gates. This count is not 4,455 additional catalogue artworks.

## Safeguards and evidence

Fresh pre-change backup: `/Users/vadimdulub/Documents/artline-us-europe-backup-20260909.GXhXuL/before-us-europe-expansion.dump`.
SHA256 `ecd970bd30b9747bde038f7f82f4955f463a2215710088decd7fa45a82f59426`.
Archive table of contents verified; no full restore test claimed. Migration 0011 is additive and stores discovery separately from existing catalogue tables.

NGA official Git revision: `f088836026d09d0d25001814fba0f84d757ebe62` (2026-09-09T10:00:45Z). Six metadata files plus documentation downloaded with URL, UTC retrieval time, byte size and SHA manifests. No image file or image metadata dump downloaded. CSV parsing streams records, including quoted newlines. `objects.csv` contains 145,707 object records, of which 4,455 classify as Painting.

Approved catalogue SHA: `1bb0735af4f17696c341b7e8324b39c4afc1668548abce4714d60d26e22d148f`.
NGA staging SHA: `0e1b2fa336649cb41a24faa512e93d3fe227e28995e095735aee1ffca1806b88`.
Directory staging SHA: `5ded3ffda695eb3a50a6f83057dff0e973e77a0b96fa1ca4263caecc28797862`.

The initial exploratory NGA selection was retained under `docs/research/nga-catalogue-expansion/`; only the `reviewed/` subdirectory is the approved import. Reviewing source roles found that both `artist` and `painter` can identify the sole current creator of a Painting. The earlier overly restrictive analysis was not applied to the database.

Dates require meaningful literal creation dates consistent with source search bounds. Blank display dates must not inherit artist lifespan. Numeric conflicts, open/disjunctive dates and ranges crossing 1970 remain staged. Missing/ambiguous identities are not fuzzy-matched. Source roles and qualifications are preserved; inseparable child records and virtual covers are deferred, while separable physical panels are retained. Existing archival/review states, titles, dates, cleared fields, holdings and personal/museum selections are preserved.

## Checks

- `ARTLINE_TEST_DATABASE_URL='postgres://localhost/artline?sslmode=disable' go test ./... -count=1` passes, using isolated disposable schemas.
- `go vet ./...` passes.
- New tests exercise date traps, pipe-delimited quoted-newline CSVs, staging validation, rollback, duplicate identity, full pinned NGA import/replay and unchanged owner edits.
- Scoped identity query tested against 100,000 unrelated artworks, identifiers and citations: indexes used, no sequential scan. This is not a 10-million-row benchmark.
- Research review keyset query uses `research_review_page_idx`: observed 50 rows, ~2.4 ms execution on the local 10,324-row evidence store, not a production-scale performance claim.
- Live API: NGA `work_count=1510`, `on_view_count=0`; works page returns five rows plus cursor. New records retain the existing preview/review visibility boundary.
- Direct database unsafe-new-row check returns zero: review status, creation bounds <=1970, no media or publication attached. Catalogue and staging replays are no-ops.

## Reproduction commands

Run from `apps/server`. Read-only collectors do not touch PostgreSQL except the offline assembler's read-only authority lookup. Existing verified source snapshots are reused; changed or unmanifested files require review. HTTP sources are allowlisted, redirects rejected, requests/bytes bounded, 403/429 pauses the source. Collection queries preserve failed country coverage; no persistent retry loop.

```sh
go run ./cmd/research-coverage -mode nga -out ../../content/imports/nga-catalogue-20260909
go run ./cmd/research-coverage -mode france -out ../../content/imports/museofile-20260909
go run ./cmd/ingest-european -batch nga-v1
go run ./cmd/stage-research -file ../../docs/research/nga-catalogue-expansion/reviewed/staging.json -sha 0e1b2fa336649cb41a24faa512e93d3fe227e28995e095735aee1ffca1806b88 -name nga-painting-catalogue-2026-09-09
```

The import/staging commands default to transaction rollback; `-apply` is needed for a local write. `-report` requires an unused receipt filename. The CLI retains its legacy `ingest-european` name, but `nga-v1` has its own source, version and checksum.

## Querying the museum list and review backlog

Use backend keyset pages; do not transfer the full registry or catalogue to Next.js. Candidate names may refer to sites/buildings, inactive institutions or duplicate institutions across national directories. Full raw evidence and original websites are retained in `raw_json`.

```sql
SELECT source_record_id, display_name, country_code, source_url, decision
FROM research_records
WHERE source_key='wikidata' AND record_kind='museum_candidate'
  AND country_code='US' AND source_record_id > ''
ORDER BY source_record_id, snapshot_id LIMIT 50;

SELECT source_record_id, display_name, source_url
FROM research_records
WHERE source_key='nga' AND record_kind='catalogue_object'
  AND decision='creator_authority_requires_review'
  AND source_record_id > ''
ORDER BY source_record_id, snapshot_id LIMIT 50;
```

Future multi-snapshot cursors must include `(source_record_id,snapshot_id)` to avoid ties. No automatic refresh schedule, fully normalized provenance UI, discovery-to-institution promotion endpoint or complete US/Europe census has been implemented. Next work is authority reconciliation and documented Louvre/Rijksmuseum/Met/Chicago harvesting, with per-source checkpoints and reconciliation—not blind page scraping.

## Delivered report QA

`output/pdf/us-europe-museum-research.pdf`: seven pages, 32 hyperlinks, 118,493 bytes.
SHA256 `d24382ff361ba5b1debe67fded7f621a356507aac7edcd701f7d908f99ea0d6a`.
All seven final rendered pages visually inspected. All canonical source links exist in PDF annotations, and key totals/country-gap labels are structurally checked. A first proof with nearly empty continuation pages was retained under task-specific `tmp/pdfs/`; the final report corrects those page breaks. No full-list census claim or unverified bulk-import claim is made.
