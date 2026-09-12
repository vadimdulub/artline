# Catalogue supplement — applied and verified

Completed 9 September 2026, local PostgreSQL `artline`. No commits, deployment,
infrastructure changes, image downloads or publication.

| Result | Count |
| --- | ---: |
| New artworks | 115 |
| Existing painter authorities represented | 24 |
| National Gallery / Orsay / Grenoble additions | 85 / 29 / 1 |
| New institutions / reused institutions | 1 / 2 |
| Added citations | 231 |
| Duplicate or enriched existing works | 0 |
| Whole catalogue artworks / institutions | 715 / 56 |
| Active painters / media assets, unchanged | 1,001 / 211 |

Every added artwork has a creation interval within the cutoff, material and
dimensions; all remain in review. No new museum highlights or owner selections.
No display assertions or published artworks. Grenoble is the one new institution.
Pissarro RF1979 9 is held in Grenoble under Orsay responsibility; Corot RF3745 is
at Orsay under Louvre responsibility. Both are `holding` claims with `loan` context,
not `display` claims. Ownership/assignment history remains in source notes.

## Changes and checks

- `cmd/research-ng -catalogue-v3 -out <new directory>` adds a bounded collection
  mode, explicit creator-name mappings and prior-accession exclusion. Sixteen
  same-day caches were reused; only two corrected-name responses were fetched.
  Old snapshots remain unchanged. A new directory is required; outputs are never
  silently overwritten. No collector writes to the DB or downloads images.
- Fixed Overall-measurement selection to skip empty display entries. NG6700 now
  has source-backed 96 x 121.2 cm. Its older alternative remains in notes.
- `cmd/assemble-catalogue` deterministically assembles the new offline evidence
  version, retaining raw response hashes, creator PIDs, catalogue references and
  per-object source notes. It excludes NG224's unresolved multi-stage date.
- `cmd/ingest-european -batch catalogue-v3` accepts only the pinned new inventory;
  default remains v1. No new SQL migration, frontend collection loading or global
  per-painter aggregation was introduced.
- `ARTLINE_TEST_DATABASE_URL=postgres://localhost/artline?sslmode=disable go test ./... -count=1`
  passes, as does `go vet ./...`. DB tests use isolated disposable schemas.
- New tests cover checksum/host/authority validation, creation cutoff, material
  and dimensions, rollback, old/new snapshot compatibility, existing editorial
  changes, replay, exact museum counts and two deposit contexts. Collector tests
  cover exact creator aliases and skipping empty/frame measurement entries.
- The existing identity query passes its opt-in 100,000-row fixture plan check
  with no sequential scan. This is not a 10-million-row throughput/load test.
- Dry run: planned 115 works/one museum/231 citations, with all 17 recorded public
  catalogue/audit counts unchanged. Apply: one serializable transaction, job
  `ad5fcf1d-a445-40ea-9126-881105f6fd41`, status `needs_review`, 118 import records:
  116 created (115 works + one institution) and two skipped/reused institutions.
- Applied replays of v3, v2 and v1 add zero works, citations or selections and
  leave all 17 counts, including audit rows, unchanged.
- Live authenticated API: National Gallery 143 local works, Orsay 32, Grenoble
  one. Grenoble's work resolves to Pissarro and has no image/display assertion.
  Caravaggio returns total 16, a five-item bounded page, cursor, dates and citations.
  Combined repeated `artist` and `country` filters for Monet/Pissarro and FR/GB
  return nine museums, correctly including Grenoble. Public listing total remains
  zero; anonymous preview returns 401.
- The PDF has 12 pages and 133 links; every artwork accession and official source
  URL passes structural checks. All pages were rendered and visually inspected.
  Available source modification dates were added to the catalogue, and the final
  one-record label was proofread. No clipping, overlap or missing glyphs observed.

### Selected current painter totals

Monet 49; Rembrandt 28; Van Gogh 27; Degas 19; Pissarro 19; Cézanne 17;
Caravaggio 16; Diego Velázquez 13. These are local catalogue counts, not complete
oeuvres. Orsay-sourced records remain private review material: website access is
not an established open licence for public/commercial reuse. One Courbet object
has indexed primary evidence with direct-access limitations explicitly preserved.

## Receipts and recovery

- [Applied receipt](../output/european-catalogue-applied.json)
- [Dry-run receipt](../output/european-catalogue-dry-run.json)
- [No-op replay](../output/european-catalogue-replay.json)
- [v2 compatibility replay](../output/european-v2-after-catalogue-replay.json)
- [v1 compatibility replay](../output/european-v1-after-catalogue-replay.json)
- [Before/after verification](../output/european-catalogue-verification.json)
- [Approved source inventory](research/european-catalogue-expansion/inventory.json)
- [Research report](../output/pdf/european-catalogue-expansion.pdf)

Inventory SHA-256:
`5f3fba58d4b3e736b8491252c55aa7244017e5109001d6e0b229e17580f83320`

Report SHA-256:
`fdec118a0f83b5a34e1e9bcab5714239641ff570855cb0ff3a8076bf9ae2cd68`

Private pre-import public-schema backup:
`/Users/vadimdulub/Documents/artline-catalogue-backup-20260909.KE0Qr5/before-catalogue-expansion.dump`

Backup SHA-256:
`fe13442de2d3cb4c669fea0c1f362c35fb8cc308873c240e108afffbad36fb0f`

Archive table of contents verified; full restore rehearsal not performed. Restore
into a separate database for comparison/recovery, not over later editorial work.

Final counts: artworks715, institutions56, places43, venues57, sources62,
holdings715, citations5119, audit5127, collections112, curated items391,
identifiers1894, import jobs11, import records3606, media211, active painters1001,
published artworks0, display assertions0. Both earlier approved inventory hashes
remain unchanged. All new implementation and data files remain uncommitted.
