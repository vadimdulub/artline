# Deep European expansion — applied and verified

Completed 9 September 2026 in local PostgreSQL `artline`; no deployment or commit.
The original 59-record source snapshot and previous report are unchanged.

| Result | Count |
| --- | ---: |
| Researched paintings in this batch | 157 |
| Existing painter authorities represented | 41 |
| Museum collections represented / countries | 28 / 14 |
| New artworks / enriched existing artworks | 155 / 2 |
| New institutions / reused institutions | 19 / 9 |
| Added citations | 338 |
| Museum-designated highlights added | 17 |
| Whole catalogue artworks / institutions | 600 / 55 |
| Active painters / media assets (unchanged) | 1,001 / 211 |

Two existing records matched by National Gallery accession: *The Water-Lily Pond*
(NG4240) and *The Boulevard Montmartre at Night* (NG4119). Missing factual details
were filled without changing their titles/dates or nonempty values. Owner-created
must-see selections are untouched. Seventeen sourced museum selections were added
to review collections: ten Louvre, seven National Gallery of Ireland.

All 155 new artworks and 19 new institutions remain in review. No new media,
published records or display assertions. Raphael's *Madonna of the Goldfinch*
retains “Before February 1506” with unknown numerical bounds: the year-level
exclusive-before type cannot faithfully encode that month boundary. Other 156
source records are within the creation cutoff; circa/range/century precision is
preserved. Two records retain shared-author attribution notes, not sole authorship.

## Verification

- `ARTLINE_TEST_DATABASE_URL=... go test ./...` passes in isolated disposable
  schemas; `go vet ./...` passes. No tests insert fixtures into the public schema.
- Deep-batch tests validate all 157 records and exact source hashes/hosts; default
  dry-run rollback; v1/v2 accession matching; existing edits; later cleared fields;
  removed highlights; archived-record rejection; and museum API counts.
- Opt-in `TestEuropeanIdentityQueryPlan` passes with 100,000 unrelated artworks,
  identifiers and citations. Exact identity indexes are used, no sequential scan.
  This remains a 100k-row plan check, not proof of 10-million-row performance.
- The local final dry run leaves all 17 recorded catalogue/audit counts unchanged.
- Apply commits one serializable transaction. Job
  `e1cd69fe-6df6-417f-8e86-1fc8cd630aa7` is `needs_review`, with 185 ingestion records:
  174 created (155 works + 19 institutions), two updated, nine skipped/reused.
- Applied v2 replay reuses all 157 works / 28 collections, adds zero citations or
  selections, enriches zero works. Applied v1 replay still reuses its 59 works and
  changes nothing. Both leave the 17-count fingerprint, including audit rows, equal.
- Live authenticated API: Ireland 7 works / 7 highlights / 0 on-view; Louvre 13
  Artline works / 10 highlights / 0 on-view. Museum highlight filtering returns
  Ireland's seven sourced records. Combined Monet/Pissarro plus GB/IE/CH filters
  return six institutions. API filter keys are repeated singular `artist` and
  `country`, not plural keys; the corrected contract was verified.
- Raphael's undated API group returns Goldfinch with null years and `unknown`
  precision. Monet has 39 total artworks and one previously imported undated work.
- Public museum listing remains empty for the unpublished catalogue; anonymous
  preview returns HTTP 401. Existing authenticated research access still works.
- The 31-page PDF includes 244 source links. Text checks cover all 157 artwork
  titles; every page was rendered with Poppler and visually inspected, with a
  full-size check of dense narrative text. No clipping or missing glyphs found.

### Current selected painter totals

| Painter | Artline works |
| --- | ---: |
| Claude Monet | 39 |
| Vincent van Gogh | 22 |
| Camille Pissarro | 16 |
| Rembrandt van Rijn | 16 |
| El Greco | 16 |
| Hieronymus Bosch | 15 |
| Francisco Goya | 15 |
| Caravaggio | 13 |
| Diego Velázquez | 11 |

These are local coverage counts, not an artist's complete oeuvre or a museum's
total holdings. The broader report details source restrictions and unresolved gaps.

## Receipts and recovery

- [Applied receipt with local IDs](../output/european-deep-applied.json)
- [No-op replay receipt](../output/european-deep-replay.json)
- [Final dry-run receipt](../output/european-deep-final-dry-run.json)
- [Original-batch compatibility replay](../output/european-v1-after-deep-replay.json)
- [Complete new source inventory](research/european-deep-expansion/inventory.json)
- [Research report](../output/pdf/european-deep-expansion.pdf)

Pinned new snapshot SHA-256:
`1c871c57b9f02ac05977c0c5b5bcdcb0f20806df4c381ed1db4ab65973c4ca4a`

Pre-import public-schema custom-format backup:
`/Users/vadimdulub/Documents/artline-deep-backup-20260909.2JQfPK/before-deep-expansion.dump`

Backup SHA-256:
`d0d15e265c8e4b9e4102e586e31c258afe8cd1778eb1f42859669bd5342916d3`

Backup is in a private directory outside the repository; archive table of contents
verified. A full restore rehearsal was not performed. Restore into a separate
database for recovery/comparison; do not overwrite later editorial changes.

After apply/replays: artworks 600, institutions 55, media 211, places 42, venues 56,
sources 62, holdings 600, citations 4,888, audit rows 4,665, curated collections 110,
curated items 391, external identifiers 1,779, import jobs 10, import records 3,488,
active painters 1,001, published artworks 0, display assertions 0.

## Reproduction

From `apps/server`, `go run ./cmd/ingest-european -batch deep-v2` previews the pinned
offline inventory; `-apply` persists it locally. Default `-batch v1` remains the old
reviewed snapshot. Receipt paths are exclusive-create. `cmd/research-ng` is a
separate bounded metadata-only collector, not activated by importing. Its Louvre
mode uses eleven explicitly reviewed object IDs. Offline assembly is provided by
`cmd/assemble-european`; existing inventory outputs are never overwritten.

No migration was needed for the richer fields. Production-scale adapter scheduling,
throughput/load tests, asset licensing/downloading, genre taxonomy and publication
review remain separate work. Literal “all European museums” completeness is not
claimed.
