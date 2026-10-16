# Broad geography optimization — 12 October 2026

Implemented the selective country/continent query from
[research round 3](performance-20261012-round3.md). Broad geographic browsing
now finds artwork IDs through indexed creator countries and production places,
without constructing geography for the entire illustrated collection first.
The fast existing query for selected creators and presets is preserved.

The implementation was first verified locally with read-only production queries,
then [deployed and checked on the public site](deployment-20261012-geography.md)
at the user's request. No schema migration, catalogue source change or commit
was made. The real local catalogue was not accessed. Synthetic tests used only
the guarded disposable PostgreSQL cluster under `/tmp`.

## Scope of the change

- [Geography strategy](../apps/server/internal/atlas/geography.go): enable direct
  indexed membership only for the full All date range, with countries and/or
  continents, no highlights, preset, selected creators, text search, legacy
  region, artwork picks or neighbor lookup.
- Native artwork filters retain the existing scoped query. The accepted no-op
  options `image_only` and explicitly disabled `popular`/`women` do not disable
  the optimization. Filters belonging to books/events remain independent.
- [Repository](../apps/server/internal/atlas/repository.go): select the existing
  indexed geography predicate for that broad case. All other cases keep the
  shared geography CTE. Existing projection eligibility, pending-row fallback,
  aggregate cache, bounded detail lookup and cursor ordering are unchanged.
- [Regression tests](../apps/server/internal/atlas/geography_browse_test.go):
  protect query routing and geographic behavior with pending and clean rows.

No additional index, cache layer, global memory setting or frontend change is
needed. The separate refresh-worker capacity recommendation remains future work.

## Measurements on current production data

Baseline and candidate test executables generated the actual repository queries.
Each request ran through a read-only connection; plans were captured sequentially
with `EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON)`. The country/continent
requests used the normal 150-item browser settings, including
`selection=true&highlights=false&artwork_popular=false&artwork_image_only=true`.

Times below sum database execution for the aggregate, first page and bounded
image lookup. They exclude planning, network, HTTP processing and browser work.

| Selection | Previous SQL | New SQL | Reduction |
| --- | ---: | ---: | ---: |
| Japan | 3.216 s | 0.125 s | 96% |
| France | 3.610 s | 0.445 s | 88% |
| Asia | 3.331 s | 0.183 s | 95% |
| Europe | 3.733 s | 1.862 s | 50% |
| Japan or France, intersect Asia | 5.104 s | 0.502 s | 90% |
| Missing country, empty result | 1.729 s | 0.058 s | 97% |

The next-page statement itself dropped from 1.740 s to 0.026 s for Japan and
from 1.812 s to 0.168 s for France. These numbers exclude the aggregate: normal
next-page requests can reuse the existing aggregate cache. The test harness
deliberately ran uncached repository instances and captured both statements.

Japan, France, Asia and the combined case no longer wrote temporary blocks in
their main query plans. Europe still wrote 2,836 temporary blocks per main
statement and remains the largest measured geographic case. These are samples
on the current catalogue, not p95, concurrent-load or ten-million-row results.
Live HTTP measurements are recorded separately in the deployment report.

Romanticism's complete generated SQL and arguments were identical before/after;
its measured execution was 0.234/0.171 s. Broad All without geography, highlights,
narrow dates, selected Monet and the native artwork-type facet also generated
identical SQL. Timing variation for these unchanged queries is not attributed
to this patch.

## Verification

All **14 scenarios / 50 statement-result comparisons** passed a second replay
inside read-only repeatable-read snapshots. This compared every returned column
and row, including full density results, page JSON, identity resolution and
image enrichment. Complete captured API representations also matched. Japan
and France's second pages retained totals/density and did not repeat first-page
IDs. The final replay observed catalogue revision 4,194 and an empty pending
queue; no synthetic production markers were inserted.

The disposable database test additionally checked anonymous production places,
mixed active/archived creators, duplicate geographic evidence, independent
country/continent memberships, holdings versus production origin, missing
images, the 1970 cutoff, empty matches, cursor pages, pending updates, projection
refresh and live production-place changes. All fixture writes rolled back.
The existing concurrent-refresh and snapshot/cache tests passed as well.

Validation results:

- Workspace Atlas tests passed with the race detector.
- Guarded disposable PostgreSQL tests passed with the race detector.
- An isolated copy of the deployed API source, its hash-verified browsing
  projection overlay and this patch passed Atlas/API race tests and API build.
  Current book-limit assertions were used because the older source archive's
  test still expected a 150-item limit despite the already-deployed 300-item
  summary limit. No book implementation was changed.
- The broader shared-workspace check could not compile unrelated in-progress
  museum code (`MuseumUpload`, `MuseumStudioOptions`, `registerMuseumUploads`
  and `museumDocumentImageURL` were undefined). Those files were not edited.
- Changed files passed formatting and whitespace checks.

## Evidence and release boundary

The implementation modifies two production Go files and adds one test file.
Source preimages, the isolated-release input manifest, complete traces/plans,
same-snapshot comparisons and test logs are archived at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/geography-optimization-20261012/`

Key artifacts: `capture-summary.json`, `parity-summary.json`, `fixture.log`,
`release-check-final.log`, `release-httpapi-final.log`, `release-check-inputs.json`,
and the `baseline/` / `candidate/` query directories. The release isolated these
files from unrelated workspace work and required no schema migration. Its
separate deployment record contains the image digest and rollback revision.
