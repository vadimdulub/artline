# Specification audit

Reviewed: 2026-09-08. Source: `/Users/vadimdulub/Downloads/CODEX_IMPLEMENTATION_SPEC.md` (1,595 lines, approved 2026-09-07). Both supplied screenshots are the same painter/artwork screen.

## Verdict

**The app does not implement all features in the specification and does not meet its definition of done.** It is a working discovery interface with a partial editor and a production infrastructure scaffold. A database table or placeholder route is not counted as an implemented workflow.

The user's explicit changes supersede the original architecture: Next.js + Go + PostgreSQL, local image assets, Markdown essays, Google Cloud, production only, no commit, and no Terraform apply. Vinext/D1/R2/Site-hosting requirements are therefore marked as adapted, not defects. The original downloaded document is unchanged.

### Current data, verified in local PostgreSQL

| Item | Actual | Specification baseline |
| --- | --- | --- |
| Painters | 11, all in review | 28 preserved, then source-checked |
| Artworks | 15, all in review; five for Giotto, one for each other painter | 140 preserved; 5–10 eligible works per published painter |
| Published painters / artworks | 0 / 0 | Populated published timeline |
| Countries / movements | 7 / 9 | 13 / 19 prototype baseline, with broader coverage later |
| Media | 15 local reproductions with rights/provenance metadata and checksum manifest | All permitted prototype media audited |
| Influence claims / external identifiers | 0 / 0 | Evidence-backed relationships and authority identity |
| Import jobs / editor accounts | 0 / 0 | Durable import review and authorized identities |
| Applied migrations | 5 | Append-only, reproducible schema and seed |

The missing prototype source and `SAMPLE_PAINTERS` export cannot be reconstructed faithfully from one screenshot. The illustrated selection is explicitly a research addition, not a recovered prototype export. No incomplete painter was promoted to published to hide this gap.

## Feature verification

Status meanings: **Implemented** = code and observable behavior exist; **Partial** = some required behavior exists; **Missing** = absent or schema/placeholder only; **Unverified** = cannot claim a tested result.

### Discovery and timeline — §§3, 5.1, 10, 12, 16

| Requirement | Status | Evidence / limitation |
| --- | --- | --- |
| Default timeline with horizontal 1100–2000 scale | Implemented | `components/TimelineExplorer.tsx`; browser test verifies initial local preview |
| Interval overlap, uncertain display dates, life/activity basis | Implemented | `internal/catalog/timeline.go`; dates may extend beyond the exploration window |
| Drag selected range; resize both ends; direct custom years | Implemented | Range-window pointer handling, two native range inputs, year fields |
| Full/century/50-year/25-year presets | Implemented | `lib/timeline.ts`; edge-clamping unit tests and browser preset test |
| Region, country, movement, work-type filtering | Implemented | Same SQL predicate for count, nodes, and bins; controls in timeline |
| Search names, aliases, movements, countries, places, artwork titles | Partial | Queries cover these fields; lowercase matching exists, full diacritic/transliteration folding does not |
| Nodes, life intervals, movement colors, semantic result list | Implemented | Nodes and accessible list; labels accompany colors |
| Hover/focus detail with country and work count | Partial | Accessible names and native title provide data; no complete rich hover card |
| Painter selection and URL-addressable sheet | Implemented | Native modal dialog, `artist`/work query state, canonical links |
| Shareable range/filter state; Back/Forward support | Implemented | `lib/url-state.ts`; browser tests cover selection/history and malformed bookmarks |
| Reset and empty state absent when results exist | Implemented | Browser regression tests |
| 300-node threshold and server density bins | Implemented | Transactional test with 305 artists; count/node/bin filters share one predicate |
| Density visualization and zoom action | Implemented | Resize-aware stacked Canvas and selectable semantic bin list |
| Synchronized individual painter list at density scale | Partial | Density mode provides bin summaries and zoom; no paginated individual painter list until zoomed |
| Public reads only published content | Implemented | API tests and direct anonymous HTTP checks; local preview requires a server-held token |
| Authenticated production draft-preview UX | Partial | Explicit local preview works; production has no signed-in preview session flow |

### Painter and artwork records — §§5.2–5.3, 6–7, 10

| Requirement | Status | Evidence / limitation |
| --- | --- | --- |
| Painter name, dates, country names, movement, aliases | Implemented | `ArtistRecord.tsx` and expanded artist API; empty aliases stay absent |
| Multiple geographic/movement affiliations and portrait | Partial | Schema supports them; UI exposes countries and primary movement, no portrait or complete geography editor |
| Sourced biography and Markdown essay | Partial | Short database bio plus file essay; only Giotto currently has prose; essays respect publication state |
| Directional influence display with evidence/citations | Partial | Read query and UI exist; only cited published claims qualify; no actual claims or editing workflow |
| Intentionally ordered 5–10-work selection | Partial | Ordered strip and cap of 10; five Giotto works in review, ten other painters have one work each |
| Artwork selection, previous/next controls | Implemented | Browser-tested selected-work state and panel |
| Canonical painter and artwork routes | Implemented | `/artists/[slug]`, `/artists/[slug]/works/[artworkId]`; missing/archived/unpublished records return 404 |
| Date, medium, dimensions, creation place, current location | Implemented | Separate data fields and panel presentation; unknowns remain visible |
| Institution relationships, multi-place creation history | Partial | Schema only beyond current text presentation |
| Location check date and no implication of being on display | Implemented | Panel renders retrieval date and explains its meaning |
| Attribution role, image license/credit, object citations | Implemented | Expanded work API and artwork panel |
| Safe local image display and unavailable/restricted fallback | Implemented | Backend filters unverified/disallowed media; local paths validated, image errors fall back |
| Responsive image sizing, alt text, rights manifest | Implemented for 15 assets | Source-checked local collection, exact SHA-256 manifest and verifier; no generated replacements |
| Image upload and review interface | Missing | Local asset folder alone is not an editor workflow |
| Persisted unavailable-image state | Missing | Broken image falls back in UI but is not recorded in DB |

### Owner catalogue and publication — §§5.4, 6, 9–11, 14–15

| Requirement | Status | Evidence / limitation |
| --- | --- | --- |
| Dense readable table, search, status filter, sorting | Implemented | `CatalogueClient.tsx`; sort by name/date/updated |
| Bounded paging | Partial | Working 50-row offset paging; spec asks for cursor paging |
| Column show/hide, saved views, multiple simultaneous filters | Missing | Not implemented |
| Add/edit painter scalar fields and biography | Implemented | Persistent Go endpoints, structured form, expected revision |
| Inline scalar editing | Missing | Form editing exists; inline grid editing does not |
| Duplicate draft | Partial | Copies editable scalar fields into an unsaved draft; does not copy relationships or works |
| Archive/restore with conflict protection | Implemented | Expected revision required; archive is recoverable; stale requests tested |
| Unsaved/saving/saved/error states; preserve failed form | Partial | Dirty indicators, disabled save fields, inline errors, link-navigation/unload and form-switch warnings; durable draft recovery and a universal SPA Back guard are absent |
| Artwork, movement, influence, place, citation CRUD | Missing | Their schemas exist; no complete API/form workflow |
| Bulk selection and status changes | Missing | No bulk workflow |
| Complete publication issue report | Partial | Checks biography length, review states, citations, authority, work count/order, dates, locations, rights; structured duplicate/conflict review is missing |
| Atomic validation and publication | Implemented for current routes | Dependencies locked and revalidated in same transaction; stale revision rejected |
| Revalidate/demote published artists after dependency changes | Missing | Needs integration with future relationship/artwork editors and all maintenance paths |
| Unpublish to review | Implemented | Authenticated revision-checked endpoint |
| Stable slugs and redirects | Partial | Update trigger records former artist slugs and reads resolve them; complete cross-entity reserved-slug handling remains |
| Owner/editor/reviewer authorization | Missing | One Bearer token only; `editor_accounts` does not drive authorization |
| Sign-in/session identity | Missing | No identity provider, user bootstrap, session lifecycle, or role management |
| Mutation authorization | Implemented for existing endpoints | Strict Bearer parsing; no token means writes disabled; anonymous/raw/wrong-token API tests |
| Audit history with before/after values | Partial | DB triggers for artist/artwork/influence records; no authenticated actor attribution or audit UI |
| Explicit hard-delete maintenance with dependency preview | Missing | User-facing operations archive only |

### Imports, provenance, CSV, exports — §§5.5, 7–8, 10–11, 13, 15

| Requirement | Status | Evidence / limitation |
| --- | --- | --- |
| Import review route | Missing workflow | `/imports` clearly states it is unavailable; tables alone do not satisfy the requirement |
| Approved adapter interface and fixtures | Missing | No ingestion adapter implementation |
| Wikidata bounded discovery/checkpoints | Missing | No candidate registry or discovery jobs |
| Museum adapter end to end | Missing | Manual source-checking of Giotto is not an automated adapter |
| Source search, preview, field comparison, accept/reject/keep | Missing | No review UI or endpoints |
| External-ID matching, duplicate confidence, conflict resolution | Missing | Schema exists; matching/merging logic absent |
| Idempotent import commits and durable raw snapshots | Missing | Import-job uniqueness constraints are not an implemented ingestion pipeline |
| Safe fetch allowlists, redirect/IP/MIME/size/rate controls | Missing | No importer; arbitrary external fetching has not been exposed |
| Artist/artwork/influence CSV templates | Missing | No import templates or validators |
| CSV preview/commit and formula-safe export | Missing | No CSV flow |
| Full JSON/CSV/media-provenance recovery export | Missing | Cannot reconstruct the catalogue through an app export yet |
| Scheduled export and tested restore | Missing | Cloud SQL backups are configured, but no export/restore drill was performed |

### Coverage, reliability, and delivery — §§5.6, 8–9, 14–18

| Requirement | Status | Evidence / limitation |
| --- | --- | --- |
| Counts by draft/review/published/archived | Implemented | `CoverageClient.tsx`, authenticated summary API |
| Candidate count and known gaps | Missing | No candidate registry |
| 50-year, region, country, movement distributions | Missing | Filters/facets do not substitute for coverage reports |
| Dedicated Nordic coverage | Partial | Total exists; no separate Denmark/Sweden/Norway/Finland/Iceland review matrix |
| Asian coverage by region | Missing | Only a single Asian total exists |
| Missing five works and biography | Implemented | Current coverage quality queries |
| Missing dates/places/citations/licenses/alt, conflicts, duplicates | Missing dashboard | Some publication checks exist; no complete gap report |
| 150-painter balanced curated MVP | Missing | Eleven review records; no published cohort |
| App reads from own DB/assets, no live museum dependency | Implemented | Source fetches were one-time manual asset preparation |
| Prepared SQL and append-only migrations | Implemented | pgx placeholders, embedded migration ledger, advisory migration lock |
| Fresh-database replay/checksum verification | Unverified / partial | Incremental migrations run; no automated full clean-database replay or migration checksums |
| Request size limits and API timeout recovery | Implemented | Bounded JSON/Next proxy body; proxy returns structured 503 on upstream failure |
| Cache-Control, ETags, cache invalidation | Partial | Correctness uses no-store; published ETags/cache strategy absent |
| Keyboard, focus return, Escape, responsive width | Implemented for tested paths | Native dialog; desktop/mobile browser tests, screenshots |
| WCAG 2.2 AA and performance budgets | Unverified | Axe WCAG 2 A/AA + 2.1 AA scans pass on tested pages/dialogs; full screen-reader/WCAG 2.2 assessment and measured performance budgets remain |
| GCP prod-only infrastructure | Partial, adapted | Terraform source and containers exist; not initialized, provider-validated, planned, or deployed |
| Independent web/API privileges | Implemented in Terraform source | Web runtime has no DB or secret IAM; cloud behavior unverified |
| Automated CI, complete E2E/rollback/restore coverage | Partial | Local tests exist; no CI pipeline or full import/publish/export journey |

## Bugs fixed during this review

- Count, individual, and density queries had different search/movement behavior. One shared predicate now drives all three.
- Density bins could be offscreen and overwrite one another. Bins are clipped to the selected view and stacked by movement.
- Anonymous reads exposed draft/review records and private catalogue/coverage data. Public and editor reads are now separated.
- Raw tokens without the Bearer scheme were accepted. Strict parsing and endpoint authorization tests now cover this.
- Archive/restore could overwrite newer edits; ordinary edit could revive archived content. Both are protected.
- Invalid life dates were required to be clipped to 1100–2000. The API now accepts lifespans overlapping the exploration window.
- Publication validation could become stale before status mutation. It is re-run with dependency locks inside the write transaction.
- Slug changes lost canonical access, and writes had no audit trail. Append-only migrations add redirect/audit triggers.
- Draft essays could render on public pages. Content status is now enforced server-side.
- Missing records rendered a successful generic client shell. Canonical pages now resolve on the server and use 404/error boundaries.
- Selection requests raced, dialogs lacked native focus behavior, and Back/Forward did not restore selection. Replaced with URL-synchronized state and native dialog behavior.
- Presets near the upper timeline boundary shrank unexpectedly. Boundary-aware range functions preserve the requested span.
- Catalogue edits were unavailable; success messages vanished during reloads and failed requests could reject without feedback. Added a scalar editor, error retention, busy guards, draft duplication, and working pagination.
- Artwork cards were inert. They now select a detailed record, support next/previous, preserve work selection in URLs, and scroll to details on small screens.
- The Next proxy could read an unbounded request and throw a generic error when Go was unavailable. It now bounds bodies and returns actionable JSON errors.
- Cloud SQL lacked an explicit edition compatible with its shared-core tier, API startup could race DB/user creation, and web shared the DB-privileged service account. Terraform source is corrected; deployment remains unverified.

## Milestone checklist — §18

| Milestone | Status | Exit criterion still missing |
| --- | --- | --- |
| 0: Preserve/export prototype | Blocked on unavailable original data | Original 28/140 export and provenance; existing Site identity not applicable to requested local/GCP project |
| 1: Full-stack shell | Partial | Full original workflow parity and original data are not present |
| 2: Schema/seed | Partial, adapted | PostgreSQL exists, but original baseline counts and complete clean replay are not verified |
| 3: Durable catalogue | Partial | Roles, related-entity CRUD, structured editorial workflow, attributed audit |
| 4: Media | Partial, adapted | 15 permitted local images; complete review/upload/asset management and raw source snapshots absent |
| 5: Imports/CSV/provenance | Missing | End-to-end preview, commit, dedup, CSV, and export |
| 6: Coverage expansion | Missing | Balanced published cohort, Nordic/Asian regional review, distribution reports |
| 7: Scale/accessibility/hardening | Partial | Dense rendering works; complete accessibility, performance, importer security, exports, recovery remain |

## Definition of done — §19, item by item

| # | Requirement | Result |
| --- | --- | --- |
| 1 | Initial timeline shows published painters | **Fail** — local preview shows 11 review painters; zero published |
| 2 | Sourced painter information and 5–10 works | **Partial** — functional viewer, one five-work research selection |
| 3 | Separate date/creation/current-location modeling | **Pass for current schema/UI** |
| 4 | Cited, directional, honestly labeled influences | **Partial** — model/read display exists, claims/editor missing |
| 5 | Manage/import/validate/publish without code | **Fail** — painter scalar editing only; related workflows missing |
| 6 | Durable database persistence | **Pass, adapted to PostgreSQL** |
| 7 | Permitted media and raw snapshots persisted | **Partial, adapted** — local image/provenance, no raw import snapshots |
| 8 | Ordinary browsing independent of external APIs | **Pass** |
| 9 | Reconstruct catalogue from CSV/JSON export | **Fail** |
| 10 | Nordic and Asian coverage measured independently | **Partial** — totals only, no required regional breakdowns |
| 11 | Reject sculpture/architecture | **Pass for schema and existing filter validation** |
| 12 | Authorization/injection/fetch/conflict/regression tests | **Partial** — existing-route tests pass; importer/export security tests absent |
| 13 | Keyboard/touch/reduced-motion/accessible alternative | **Partial** — core paths tested; full WCAG/screen-reader assessment not complete |
| 14 | Preserve original identity/data/design intent | **Partial** — screenshot design restored; original data and Site checkout unavailable |

## Verification evidence

- `go test ./...`: passes, including existing-route anonymous/wrong-token authorization and input validation.
- PostgreSQL integration tests: pass; 305-artist density totals, public draft exclusion, stale updates, slug redirects, stale archive rejection, restore, publication rejection, and audit records. Fixture changes are rolled back.
- Frontend lint, TypeScript production build, and five unit tests: pass.
- Six browser scenarios: pass against local preview (right-side painter drawer with independent scrolling, focus trap and mobile layout; compact integrated focus controls with range dragging/keyboard interaction; timeline/filter/history/dialog; canonical artwork/mobile layout; bookmark/empty recovery; editor validation/failed-save retention).
- Desktop/mobile screenshots: `docs/screenshots/`, inspected visually.
- Terraform formatting: passes. No init, provider validation, plan, apply, deployment, or cloud restore test.
- No commit or GitHub write.

## Next implementation order

1. Add identity-backed authorization and the structured editor for artworks, citations, movements, affiliations, media, and influences. A curator must be able to satisfy every publication rule using the UI.
2. Implement one bounded museum adapter with preview, conflict handling, explicit rights review, idempotent commit, and fixtures; then CSV and full recovery export.
3. Recover the original prototype dataset if available, or curate a new clearly documented baseline. Publish only after factual review.
4. Complete coverage distributions, geographic gap reports, accessibility/performance measurement, and production recovery tests.

## Sources consulted for the limited new research data and cloud correction

- [National Gallery: Giotto](https://www.nationalgallery.org.uk/artists/giotto) — biography and approximate birth date.
- [Scrovegni Chapel](https://cappelladegliscrovegni.it/index.php/en/la-cappella-di-giotto) — cycle dates and place.
- [Chapel overview](https://www.cappelladegliscrovegni.it/index.php/en/?start=0) — named narrative scenes.
- [Wikimedia file record](https://commons.wikimedia.org/wiki/File:Giotto_-_Scrovegni_-_-31-_-_Kiss_of_Judas.jpg) — image rights and provenance; conflicting object date retained as a research note.
- [Cloud SQL instance settings](https://docs.cloud.google.com/sql/docs/postgres/instance-settings) — edition selection for PostgreSQL 17.
