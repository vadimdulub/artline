# Artline implementation constraints

- Local collection workflow (11 September2026): audit the real local `artline`
  database using read-only queries. Do not create test databases or insert test
  fixtures into it. Do not point `ARTLINE_TEST_DATABASE_URL` at the real catalogue.
  Keep disposable proofs/test outputs out of Documents; preserve research evidence.
  Backups belong under `/Users/vadimdulub/Library/Application Support/Artline/backups/`,
  not scattered across Documents. See `docs/LOCAL_DATA_LOCATIONS.md` for relocated
  historical backups. Do not remove unrelated databases or real artwork assets.

- Explicit collection priority (10 September 2026): Russian icons, Greek
  artists, Byzantine and post-Byzantine art are first-class priorities, including
  works held outside their region of origin. See
  `docs/russian-greek-byzantine-priority.md`. Do not filter these traditions out
  merely because creators are anonymous, workshop-attributed, or not yet mapped
  to a named painter; support those cases explicitly before importing them.

- Capacity-planning scale: approximately 20,000 painters and 10 million artworks.
  This is engineering headroom, not a requirement to ingest/download that many.
- Confirmed content scope: artworks created in or before 1970, selected as
  masterpieces/highlights or supported by a documented museum connection.
  The cutoff is on artwork creation, not a painter's birth/death year.
- No exhaustive artwork/image downloading. Select eligible metadata first;
  download only selected, rights-cleared reproductions in an approved workflow.
  Personal masterpiece choices and museum designations must remain distinguishable.
- Treat museum holdings and currently-on-view status separately. Museum presence
  needs source evidence; an on-view claim also needs a fresh dated display record.
- Unknown dates or ranges crossing 1970 need editorial review, not an invented
  year or automatic eligibility. Do not delete existing records to apply this policy.
- Go/PostgreSQL own visibility, validation, filtering, date classification,
  grouping, counts, sorting and pagination. Next.js renders bounded responses
  and manages interaction state; do not load full collections into the browser.
- Scope artwork queries by painter/institution/IDs before enrichment. Do not reuse
  a global artwork CTE for a single-painter lookup without inspecting its plan.
- Prefer bounded keyset pages and indexed foreign-key lookups. Batch details for
  the returned IDs; avoid per-work requests or joins over the entire collection.
- Verify query plans with representative fixtures. Small-seed correctness tests
  are not evidence of 10-million-row performance. Document remaining load tests.
- Treat bulk ingestion, summary projections, search indexes and caching as
  explicit backend work with invalidation/review semantics, not client workarounds.
- No commits, Terraform apply, deployment or bulk ingestion unless requested.
- Existing records remain in review until explicitly validated/published. Never
  invent creation years or infer current display from a holding institution.
