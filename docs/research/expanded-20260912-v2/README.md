# Expanded CSV review and database staging — 12 September 2026

The supplied CSV contains **285,090 rows**, including all **106,350 rows** from
the original export and exactly **178,740 additional rows**. This upload stores
research evidence; it does **not** create visible catalogue artists or artworks.
Catalogue promotion remains blocked by missing source object identities, source
links, artwork types and creator attribution/authority evidence.

| Additional-row outcome | CSV rows |
|---|---:|
| Unidentified creators excluded | 41,801 |
| Attribution, school, workshop, collective or geographic labels deferred | 27,622 |
| Other ambiguous creator identities deferred | 1,193 |
| Named candidates retained for research staging | 108,124 |
| Total additions | 178,740 |

The retained rows produce **104,984 distinct six-column entries**, covering
**32,259 creator labels**, in 21 checksum-pinned chunks. These are not verified
counts of unique physical objects or unique painters. The original record
numbers and multiplicities are retained in each staged row. Across all additions
there are 10,975 repeated rows; 3,140 of those repetitions occur in the retained
set. A title/date/museum collision cannot establish that two objects are the same.

Of the retained CSV rows, 64,564 have straightforward closed date strings within
the cutoff, and 43,560 require date interpretation/review. This classifier leaves
century wording, approximate dates and uncertain ranges unchanged. It does not
invent years or claim that a closed date alone validates an artwork for publication.

The user explicitly authorized uploading to both databases and excluding anonymous
creators for this batch. Existing anonymous records are preserved. No catalogue
artist, artwork, institution, editorial status, image or attribution is changed.
Every retained creator label has at least one supplied artwork row; no standalone
painter profiles are created from unverified names or artwork dates.

## Evidence and reproducibility

- Input: `/Users/vadimdulub/Downloads/artline-artworks-expanded-2026-09-12.csv`
- Input SHA256: `210a729ead48d12b0f228eb9e1fe0c5a6708750b196be38ddfbbb270aa1355c8`
- Baseline: `output/artline-artworks-2026-09-12.csv`
- Baseline SHA256: `3e89837f9ab91fbb9365a03c33ad6f9fd5b89c21a89b758615bcd2d9aefdc26b`
- Original CSV stored in the private bucket at
  `gs://artline-508319-images/research/expanded-20260912/210a729ead48d12b0f228eb9e1fe0c5a6708750b196be38ddfbbb270aa1355c8.csv`.
- [Review inventory](review.json), [excluded/deferred rows](deferred.json),
  `chunk-001.json` through `chunk-021.json` preserve local research evidence.
- The first review directory, `../expanded-20260912`, is an earlier audit only;
  v2 adds more multilingual attribution checks and is the applied inventory.

The CSV is the supplied source, not a substitute for primary museum evidence.
Its museum-country column stays in the raw payload; it is not an artist nationality.
`hasPicture` is retained as a supplied claim. The CSV has no image URLs, downloaded
image bytes or rights evidence, so **no images are acquired or attached**.

Build `apps/server/cmd/import-research-csv` to prepare a fresh review directory
with `-file`, `-baseline`, `-source-url` and `-out`. Preparation never opens a
database and refuses incomplete baselines or overwriting existing evidence.

Build `apps/server/cmd/stage-research`, then use `ops/stage-research-batches.py`
with the reviewed inventory, an explicit `DATABASE_URL`, `--target local` or
`--target cloud-sql-proxy`, a new receipt directory, and `--apply`.
The production proxy must be started explicitly for
`artline-508319:europe-west1:artline-postgres` at `127.0.0.1:55432`.
The runner verifies every chunk before the first transaction. Existing snapshot
SHA256 keys make replay idempotent; each chunk is atomic. Only `research_snapshots`
and `research_records` receive inserts.

## Backups and validation

Both local `artline` and production `artline` in `artline-508319` now contain all
104,984 staged entries, representing 108,124 supplied rows. Read-only verification
compared record counts, multiplicities and content hashes for all 21 chunks:
**all agree**. Both databases retain 5,328 artists and 106,350 artworks; research
rows increased from 10,324 to 115,308. Receipts are in `local-complete/` and
`production-applied/`; [database verification](database-verification.json) records
the per-chunk hashes. The earlier `local-applied/` contains the first successful
chunk before a receipt-format handling error was corrected; replay resumed the
batch without duplicating that chunk.

Backups are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-research-20260912/`:

- `local.dump`: complete local backup, SHA256
  `6e454cceab475110147b86665f2767c08aec04d0fc6449b11ab06f19db2afb02`.
- `production-research.dump`: both affected production research tables, SHA256
  `33d7725cc614fd4f849d273a96b1dc725bc38bf2ee73b099dc4e3f62c1d6fcf3`.
- Both archives passed `pg_restore --list`. The redundant full production transfer
  was stopped after the scoped backup was verified; `production.dump.incomplete`
  is explicitly incomplete and must not be used for restoration.

Offline Go tests cover multilingual unidentified/attribution labels, uncertain
dates, CSV quoting/newlines, incomplete baselines, preserving repeated records,
evidence overwrite refusal and explicit Cloud SQL target selection. Existing
ingestion and HTTP API unit tests pass with `ARTLINE_TEST_DATABASE_URL` unset.
No test database or catalogue fixture was created. Real-data replay of the first
local chunk returned `replayed=true` and did not duplicate records.

This validates this batch and its existing staging indexes; it does not establish
performance at ten million artworks. Promotion requires source-aware reconciliation
and representative query/load checks before adding new catalogue access paths.
