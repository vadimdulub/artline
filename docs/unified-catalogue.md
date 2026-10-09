# Unified catalogue — 8 October 2026

The owner requested removal of research/review browsing: “Always show all that
we have.” Catalogue reads now include every active record, independently of
legacy draft, review or published values. This supersedes older publication
requirements for browsing and search eligibility.

## Behaviour

- Artists, artworks, museums, books, events, counts, filter choices and related
  records use the same catalogue scope. Unknown dates, unnamed creators and
  missing images do not hide a work from the artwork directory.
- `catalogue=all` is no longer generated. Existing artist and artwork links
  redirect to their ordinary path while retaining supported artwork filters.
- The API ignores obsolete `preview` and `status` parameters. No token or
  research-preview environment variable is needed to read the catalogue.
- Sitemaps and catalogue metadata no longer restrict visibility by editorial
  status. Museum sitemap entries use the same nonempty-collection and
  holding/display rules as museum browsing.
- Page sizes, keyset pagination and server-side filtering remain bounded.
  Cursors from the removed visibility scopes need a fresh first page;
  legacy artist links restart pagination while retaining the actual filters.

Archived records remain excluded. Historical statuses and publication dates
remain audit data; this change does not rewrite them or claim that incomplete
facts have been verified. Sources, image credits, qualified attributions,
unknown dates and the distinction between holdings and current display remain.
Date ranges, image filters, selections and other reader-selected filters still
apply. A timeline cannot assign an invented year to an undated work.

## Access and search

The production release preserves existing public painter and artwork pages.
Active review records now receive ordinary indexable metadata and sitemap
entries. Member accounts and local-debug safeguards remain unchanged. Separate
in-progress member-page guards in the local workspace were excluded when the
release was assembled from the exact serving production sources. Google decides
whether to index an eligible page.

API JSON, account pages and internal routes keep their separate indexing rules.
Source and image-use evidence is unchanged. No bulk publication or ingestion was performed. The user subsequently requested
production deployment; see [the release receipt](deployment-20261008-unified-catalogue.json).

## Configuration and database

The web research-preview helper and credential forwarding are removed, along
with the Terraform public-research-preview option. Obsolete research-preview
and editor-token environment settings were removed from production. Existing
local environment values no longer affect runtime visibility. The historical editor
secret resources are retained in Terraform to avoid destroying managed secrets
as part of a browsing change; runtime no longer reads that credential.

Migration `0039_active_search_discovery.sql` adds partial indexes for bounded
active-record sitemap scans. It changes no catalogue records. The real local
catalogue remains read-only. The production indexes were created concurrently,
validated, and recorded in the migration ledger after a successful Cloud SQL
backup. No artwork, artist, museum, book, event, or publication status was rewritten.

## Verification

The dedicated `TestUnifiedCatalogueReadOnly` audit connects with PostgreSQL
`default_transaction_read_only=on`. It exercises ordinary API routes, legacy
parameters, counts and keyset pages against existing records. It creates no
fixture schema, data or database. Unit tests cover URL normalization, unchanged
member access, search metadata, sitemap errors and cache invalidation.

Validation completed on 8 October 2026:

- Go unit suite with the fixture database variable unset.
- 282 frontend tests, TypeScript, ESLint and the production Next.js build.
- Read-only API checks across catalogue routes, counts, old visibility flags,
  entity filters and each sitemap kind.
- Real-catalogue audits for artist pagination, anonymous and undated artworks,
  museum summaries, indexed artwork lookups and atlas/native filter agreement.
- Complete bounded page walks for 8,821 eligible books and 10,026 active events,
  including mixed historical review and published statuses.
- Browser verification of normal artist/artwork pages, legacy link redirects,
  preserved artwork filters and removal of the separate full-catalogue link.
  The temporary API enforced PostgreSQL read-only mode and skipped migrations.

Representative local query checks are not proof of performance at ten million
artworks. Load testing at that scale remains future performance work. The
indexes were subsequently applied during the production release below.

## Production verification

Both API and web revisions `unified-catalogue-1008-1955` serve 100% of traffic.
The staged and live APIs each passed 41 checks. Staged and live browser checks
verified public painter/artwork pages, legacy links, preserved filters, loaded
images, mobile layout, HTML without JavaScript, sitemaps and anonymous sessions.
Live responses included 405,287 active artworks and 1,399 Rembrandt works.
Build source checksums and image digests were verified. Unrelated live changes,
public assets, member authentication, secrets, ingress and scaling were preserved.
The only runtime configuration removals were obsolete catalogue credentials
and preview switches. No Terraform apply or Git commit was made during deployment.
The verified production sources were subsequently committed and pushed as
`fc89398`; see [the 9 October performance audit](performance-20261009.md).
