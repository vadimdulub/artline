# Artist workspace release — 4 October 2026

The Artists directory is now a searchable, filterable entry point into the catalogue.
Every artist profile uses the same biography, paginated artwork browser, documented
museum holdings and source sections. The release also includes the requested Account
menu toggle and sticky header. Production is <https://artlines.org/artists>.

## Committed production source

Feature commit `3b7f575` adds the workspace and 1,000 source-attributed reference
biographies. Commit `c69e074` adds the explicitly verified production identity for
Domenichino. Commit `920c75f` corrects filter reset and tablet navigation spacing.
Commit `e160a4e` disables automatic prefetch of linked museum catalogues.
All are pushed to `origin/master`.

| Service | Source commit | Revision | Cloud Build |
| --- | --- | --- | --- |
| API | `c69e074` | `artline-api-artists2-1004` | `d5710f22-3ce4-4cac-91fc-ee3e03f9e85d` |
| Web | `e160a4e` | `artline-web-artists4-1004` | `03bf7a43-5d5a-4fa4-a71d-1bebb3c073ea` |

- API image: `europe-west1-docker.pkg.dev/artline-508319/artline/api@sha256:c8cb0c5b010d37183be3007a38fb80475cd6e38114d4468771cb7443ae20821c`.
- Web image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:e3a6097dd50adadcd73bb7d24e8b2c00acd035cda94002f62a41f3513eced6d0`.

Both revisions are ready and receive 100% of normal traffic. Build contexts came
from the specified Git commits; Cloud Build's resolved-source SHA-256 values match
the private source manifests. Failed candidate checks were corrected before the
website received traffic. The previous `artline-api-gallery-git-1004` and
`artline-web-gallery-git-1004` revisions remain available for rollback.

## Data and access

The directory filters name/aliases, country, movement, top-1,000 cohort and women
artists, with popularity/alphabetical ordering and bounded server pages. Artist
catalogues filter title/accession, year, work type, museum and image availability.
PostgreSQL owns counts, filters and pagination; the browser receives 24 works at a
time. Museums are documented holdings, not claims of current display.

Production checks confirm Rembrandt has 1,386 recorded works across 23 collections
and Van Gogh has 126 across 17. Each still has five published works. The complete
recorded views use the existing public research preview at `?catalogue=all`, remain
noindex, and are linked from the directory and canonical artist pages. Existing
publication state and canonical published visibility remain intact.

All 1,000 biography entries match production artist identities. The bundle is
reproducible from retained source captures, preserves substantial editorial
biographies, and credits Wikipedia contributors with CC BY-SA 4.0 and exact source
revisions. One reviewed additional database UUID for Domenichino accounts for the
local/production identity difference; the source evidence and exact binding are
retained. No artist biographies or catalogue records were overwritten in the DB.

## Validation and operational limits

- All Go package tests, 203 frontend unit tests, lint and TypeScript checks passed.
  Both production builds passed. Targeted checks passed after release corrections.
- Actual local catalogue checks ran in enforced read-only transactions. Scoped
  artwork query plans use the attribution index and artwork primary keys. This is
  not a ten-million-row or concurrent-load benchmark; those tests remain pending.
- Candidate and live API checks covered all 1,000 biography identity bindings,
  Rembrandt/Van Gogh counts, published visibility, paging, title/type/museum
  filters and the additional Domenichino binding.
- Six artist workspace browser checks passed on the final candidate and live site:
  directory reset/filter/paging, full works at 1440/390/320px, source disclosure,
  museum filtering, image viewer, accessibility, and direct artwork links without
  JavaScript. Actual displayed artwork images decoded successfully.
- Ten header widths (320–1440px), sticky positioning, brand asset byte checks,
  seven route responses, canonical metadata, Google verification, sitemap
  discovery and anonymous session safeguards passed. No browser JavaScript errors
  occurred in those smoke checks. A new Google sign-in round trip was not performed.
  Layout/asset smoke checks preceded the final prefetch-only correction; the full
  artist suite was rerun on the final candidate and live revision.

CPU, memory, min/max instances, concurrency, environment, secrets, ingress and
session configuration are unchanged. Both services retain 1 CPU, 512 MiB,
concurrency 80 and min 0 / max 3 instances. The database tier is unchanged. Ignored
Terraform image pins were synchronized without a Terraform apply. No catalogue
writes, new schema migrations, bulk ingestion or publication changes were made.

Live log review found museum-detail timeouts (Met, NGA, SMK and AIC).
The prior release already documented Met/NGA timeouts. Museum
links now disable automatic prefetch, and browser tests verify that opening and
filtering an artist does not request linked museum pages. The new artist
workspace’s collection counts and Browse works filters pass independently;
opening an affected museum’s separate detail page can still time out. No error
entries appeared for the serving revisions during the final browser verification
window after the prefetch correction.

Private preimages, build manifests/results, source captures, operations, reports
and screenshots are retained under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/artist-workspace-20261004/`
