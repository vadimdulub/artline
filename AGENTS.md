# Artline implementation constraints

- Million-artwork goal (10 October 2026): the user explicitly requests continued
  production expansion of painters, artworks and authentic images until the
  catalogue reaches one million artworks. This authorizes source-backed bulk
  catalogue ingestion toward that goal. Continue metadata selection, duplicate
  and version reconciliation, source/date/attribution checks, review status,
  selected image preparation and verification; do not inflate totals with
  placeholders or duplicate objects. Existing date scope and image policies
  still apply. The real local database remains read-only. This is an actual
  catalogue goal; the separate ten-million-row figure remains capacity headroom.

- Member access and bookmarks (10 October 2026): the user clarified that artist
  and individual artwork pages are public without a login prompt. Museum
  browsing and saving artists/artworks to private bookmarks require login.
  Prompt when a signed-out visitor uses a star or a museum link; retain the
  selected destination through sign-in. Local-debug bookmarks are ephemeral
  and must not write account, session, bookmark or catalogue fixtures to the
  real local database. Publication status is unrelated to this access policy.

- Unified catalogue (8 October 2026): the user explicitly removed the
  research/review browsing distinction: “Always show all that we have.” All
  active records are available through one catalogue, regardless of legacy
  draft/review/published status. Remove preview flags, status-based visibility
  gates and the `catalogue=all` option. This supersedes earlier instructions
  that required publication before visibility or search eligibility. Preserve
  historical statuses as audit data, archived exclusions, factual uncertainty,
  source/image evidence, date-scope rules and unrelated member access controls.
  Do not bulk rewrite statuses or mutate the real local database for this work.

- Greek museum coverage (8 October 2026): the user instructed “let's cover all
  greek museums and upload pictures and artworks.” Continue nationwide research,
  selected source-backed production catalogue additions, museum links and authentic
  image delivery under the existing Greek museum/artist and WikiArt policies.
  Keep new artworks in review, unknown dates and qualified creator labels explicit,
  reconcile object/version duplicates, and distinguish holdings from current display.
  Do not create placeholder artworks to make a museum visible. Track every researched
  institution and remaining object-source gaps; directory coverage is not complete
  artwork coverage. The real local catalogue remains read-only for this pass.
  See `docs/research/greek-museums-20261008/README.md`.

- Museum browsing (8 October 2026): the user requests supported collection
  additions where possible and asks not to show museums with no catalogue items.
  Require at least one visible artwork for museum browsing, counts and choices;
  keep empty institution records for research. Anonymous, undated and unillustrated
  review works still count. Do not invent items just to make a museum visible.
  See `docs/research/nonempty-museums-20261008/README.md`.

- Local image delivery (7 October 2026): the user instructed “I don't want to
  approve, just uplaod them.” Complete matching, image review, local file
  preparation and database attachments directly; do not request per-image or
  batch approval. The assistant resolves research decisions within the existing
  source policies and preserves artwork/version identity, source labels,
  catalogue metadata and publication state. See `docs/ARTLINE_IMAGE_USE.md`.

- Museum matching confidence (6 October 2026): the user accepts museum
  assignments at at least 80% editorial confidence and asks the assistant to
  verify and decide, including the 1,617 leads from the first random-5,000 pass.
  Apply supported production museum links without requesting manual review of
  each match. Record the evidence, confidence basis and remaining uncertainty;
  confidence is an editorial assessment, not a calibrated probability. Preserve
  object/version checks, actual source labels, dates, images and publication
  states. Holdings remain distinct from current display. This applies to museum
  matching and does not change the separate image-matching threshold.

- Le Havre, Rouen and Cyprus collection request (6 October 2026): the user
  instructed “check havre museum and ruan museums and cyprus museums, find and
  upload data.” This authorizes selected, source-backed production catalogue
  additions and enrichment for this museum pass. Keep artworks in review,
  preserve unknown fields and qualified creator labels, reconcile duplicate
  object identities, and distinguish documented holdings from current display.
  Continue the existing WikiArt and Cyprus image-source approvals. See
  `docs/research/havre-rouen-cyprus-20261006/README.md`.

- Louvre painter-link continuation (6 October 2026): the user instructed
  “go ahead link more painters.” Reconcile supplied unlinked creator labels
  with verified existing painter records and WikiArt profiles using exact
  object/creator evidence. Preserve original labels in citations and audit
  history, qualified attributions, existing images, dates, holdings and review
  status. Record unresolved identities and duplicate painter conflicts. See
  `docs/research/louvre-painter-links-20261006/README.md`.

- WikiArt source approval (6 October 2026): the user explicitly confirms that
  WikiArt is a good source from all policy perspectives. Treat WikiArt as an
  approved source across Artline's collection, image-use, rights-review and
  public/commercial-display policies. Independent source/rights clearance or a
  missing public-domain label must not by itself block selected WikiArt images
  or prompt repeated approval requests. Preserve actual rights labels, credits
  and source evidence; record user approval separately. Continue artwork/version
  identity, catalogue-scope and review/publication checks. This instruction
  supersedes earlier project policy holds on WikiArt source acceptance. See
  `docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026`.

- WikiArt image-enrichment preference (6 October 2026): WikiArt is the source
  of truth for artwork image matching in this workflow. Use its artwork pages,
  creator identities, titles/translations, dates, versions and per-image rights
  labels as the reference. The user authorizes production image updates for
  matches with at least 90% confidence and wants as many supported matches as
  possible. This museum pass excludes the Louvre and Prado. Preserve source
  dates as evidence when imported dates differ or are missing; review the
  same-work identity against WikiArt before deciding whether to attach its image.
  Do not silently rewrite catalogue dates during an image-only update. Preserve
  evidence and unresolved ambiguities; image enrichment does not authorize
  changing catalogue metadata, holdings, display claims or publication status.

- Louvre source preference (6 October 2026): WikiArt is the source of truth
  for artwork metadata and images when a catalogue record has been securely
  matched to the same work. Prefer WikiArt's explicit creation dates over
  conflicting imported dates; a date discrepancy alone must not block adding
  its image. Preserve the previous values and source evidence in the audit
  trail. Resolve titles, versions, details, studies and copies before matching;
  source precedence does not make different artworks interchangeable. Retain
  per-image rights evidence, unknown fields and existing review/publication
  safeguards. A WikiArt holding label does not establish current display.

- Local debug preference (1 October 2026): all member and paid-feature previews
  must be available without Google login or a paid subscription. Use the API's
  local-debug access mode; keep its production and loopback safeguards intact.
  Do not create catalogue or member database fixtures to preview these features.

- Explicit incomplete-data preference (12 September 2026): retain named-creator
  artwork entries as actual database records in review even when additional
  research finds no details. Preserve supplied provenance and unknown fields;
  do not invent types, dates, artist biographies or accepted museum holdings.
  Unresolved named creators may remain object-level labels until reconciled.
  Anonymous/unknown creators and held attributions remain excluded from this
  expanded CSV import. Missing metadata does not authorize publication.

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
