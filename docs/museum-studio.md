# Museum studio — local implementation, 12 October 2026

## Available locally

- `/account/museums`: find an existing institution and open its museum studio.
- `/account/museums/{slug}`: museum-scoped artwork, exhibition, guide and page
  editors, title search, bounded pages, draft/save/publish/unpublish controls.
- `/museums/{slug}`: public museum landing page, uncropped collection artwork,
  museum publications, visiting information and the existing historical collection.
- `/museums/{slug}/publications`: searchable museum-authored content by kind.
- `/museums/{slug}/publications/{id}`: public, read-only published document.

Contemporary artworks and current exhibitions are allowed here. They never enter
historical catalogue tables or their totals. Historical creation-date, medium,
source, attribution, image and review policies remain unchanged. Staff may enter
recorded dates, intervals or an explicit unknown date; exhibition opening dates
are required. Every editor labels required and optional fields. Artwork title and
recorded date are required; artist/attribution, year bounds, medium, dimensions,
inventory, descriptions and URLs are optional. Unknown dates remain explicit.
Images can be uploaded or linked by HTTPS, with required description and
credit/rights text. Images fit fully in their frames.

The museum studio's Guides tab also lists existing Artline editorial guides for
that institution, with **Read-only** labels and **Read guide** links. Staff cannot
edit, replace, publish or delete these prepared guides. Only museum-authored
publications enter the studio editor. The tab's search covers both groups;
results are filtered and bounded by Go. Prepared guides also appear on the
public museum page and keep their public language editions and PDF downloads.
New museum-authored publications are still listed on the museum's own page;
they are not added to the global editorial guide directory.

Guides and exhibitions have a text editor with bold, italic, heading, list, link
and preview controls. HTML and inline Markdown images are not rendered. Staff
can select up to 48 existing artworks, reorder them, and add notes beside each
one. Search offers the museum's historical collection, its own added artworks,
or the wider Artline catalogue, with an image filter for catalogue works and
24-item pages. A nested artwork editor can save or publish a new artwork without
losing the parent draft. Selected draft artworks must be published before the
guide/exhibition can publish.

Selections store IDs and notes, not copies of catalogue metadata. Public pages
resolve current public records in batches and preserve the selected reading
order. Saving a draft of an already published artwork does not expose the new
details or image through a guide. If staff unpublish a selected artwork, the
public guide shows an unavailable placeholder. References do not change holding
institutions, catalogue eligibility or current-display claims.

Museum record pages and works APIs are public. The museum directory, studies,
bookmarks and studio remain member-only. Saving catalogue bookmarks still
requires login. Empty catalogue institutions remain absent from the catalogue
museum directory; an institution can nevertheless have a public museum page once
it has published its own content. No placeholder catalogue records are created.

## Verification and authority

This version uses the existing Google sign-in. The verified ID token's `hd`
(Workspace/Cloud organization) claim must exactly match the verified email domain
and an active entry in `museum_staff_domains`. A typed email suffix or website
edit grants no access. See Google's [OpenID Connect documentation](https://developers.google.com/identity/openid-connect/openid-connect),
which distinguishes email-domain hints from the signed hosted-domain claim.

Operators approve domain-to-institution mappings with an institutional evidence
URL. Shared hosting, public email providers and domains unrelated to the museum
must not be registered. Multiple museums/domains are supported. Claims create
staff membership automatically; revoked memberships cannot self-reactivate.
Domain and staff revocation are checked on every private request and locked
again inside each write transaction. Museum staff cannot edit domain approvals,
other institutions' publications, existing historical catalogue records, or
other members' private studies. There is no public publishing endpoint.

Work addresses outside Google Workspace/Cloud Identity need a separate mailbox
verification delivery flow before they can qualify; this pass does not claim to
verify those addresses. Existing members must sign in again to capture `hd`.

## Persistence and publishing

Migration `0055_museum_studio.sql` prepares institutional domain/staff tables,
publications, scoped paging indexes and publication history. It also adds the
Google hosted-domain claim to member accounts. No migration has been applied to
the real local database or production by this task.

Each document has a draft and a separate published snapshot. Save updates only
the draft; publish copies the draft into the public snapshot; unpublish clears
the snapshot. Version checks reject stale edits. Each committed change records
its actor, action, version, document and time in the history table. Public
responses omit private versions and draft-change markers. All studio/publication
responses are uncached; publication routes are excluded from the catalogue cache.
The Next proxy forwards only validated session cookies and origin evidence,
bounds documents to 256 KiB and binary uploads to 10 MiB, and does not accept
asserted user/museum headers.

## Image uploads

The uploader accepts JPEG/PNG files up to 10 MiB and 20 million pixels. The API
checks decoded format and dimensions before decoding/re-encoding, applies JPEG
EXIF orientation, and strips metadata and appended/ancillary content. Two images
can process concurrently per API instance. Description and credit/rights are
required before an image-bearing document can save or publish.

Upload metadata is scoped to the museum in migration `0056_museum_uploads.sql`;
bytes live separately. Production requires `ARTLINE_MUSEUM_UPLOAD_BUCKET` set to
a dedicated private GCS bucket, public access prevention, and the API service
account's scoped object read/create permissions. Do not use the public catalogue
image bucket. The adapter uses Google's [media upload](https://docs.cloud.google.com/storage/docs/json_api/v1/objects/insert)
and [object read](https://docs.cloud.google.com/storage/docs/json_api/v1/objects/get)
endpoints, with generation-match zero to prevent overwriting objects. No cloud
bucket or production upload was created by this implementation.

`/api/museum-media/{slug}/{id}` checks whether any published snapshot in that
museum uses the image. Otherwise it requires current museum staff access.
Responses are uncached, use a decoded-image content type and `nosniff`, and never
redirect to a public storage URL. A replaced draft image stays private while the
old published image remains visible. After unpublishing the last reference,
future anonymous reads are denied. Previously downloaded public bytes cannot be
recalled. External image URLs retain their provider's access behavior.

Local-debug stores image bytes and metadata only in memory (128 MiB image limit)
and loses them when the API restarts. Unattached uploads remain private; no
automatic retention/deletion job is included. Before production rollout, define
retention for abandoned uploads and reconciliation of rare object-store writes
whose metadata transaction fails.

## Preview and verification

Preview: `http://127.0.0.1:3146/account/museums`.
API: `127.0.0.1:8146`, local-debug, `-skip-migrations`, database startup option
`default_transaction_read_only=on`. Museum identities and historical artworks
are read from the catalogue; access, publications and uploads are ephemeral in memory.
The preview has its own Next checkout under `/tmp/artline-museum-studio-20261012/`.

Verified:

- Go member and HTTP API tests, including race detection.
- Verified-domain mismatch rejection, anonymous/private access, cross-origin and
  non-loopback rejection, cross-museum isolation, draft/published snapshots,
  stale writes, unpublishing, date/URL/image-credit validation and keyset paging.
- Production Next.js build (webpack, isolated checkout), TypeScript and focused
  ESLint. 237 frontend tests cover guide content, auth/return paths, museum
  publication transport, image payload bounds and private image proxy behavior.
- Browser create/save/publish/edit/unpublish; contemporary date interval;
  exhibition, guide and profile publishing; search and anonymous public rendering.
- Browser layouts at 1440, 1024, 768, 390 and 320px; no horizontal document overflow.
  Editor Escape restores focus. Axe checks cover editor, studio and public page;
  one hover contrast issue was corrected and rechecked.
- Composer refinement: browser flows create a guide with historical references,
  reorder works, write notes, preview formatted text, upload an image in the
  nested artwork editor, save its draft, reject premature guide publication,
  publish the artwork, and publish/render the complete guide. Exhibition flow
  selects museum-added and global catalogue works and creates a new artwork.
- New dialogs and public guide checked at 1440, 390 and 320px, with no horizontal
  overflow, browser exceptions or Axe violations. Uploaded image preview was
  checked for successfully decoded pixels, not only a successful upload response.
- Additional Go tests cover artwork-reference isolation, published snapshots,
  parent/child unpublishing, independent document clones, upload ownership and
  private/public lifecycle, byte/pixel limits, JPEG EXIF orientation and metadata
  removal. No real catalogue/member fixtures were created.

Temporary screenshots, browser scripts and reports are in the preview directory.
Test publications were confined to the ephemeral API and cleared before handoff.

## Before production rollout

Deploy only after a separate production instruction. Run migration/integration
and representative-volume query-plan checks on an approved staging environment,
then apply migrations 0055 and 0056, configure the private upload bucket, and
establish evidence-backed museum domain mappings.
The real local catalogue remains read-only, so SQL persistence and query plans
for these new tables have not been executed here. The in-memory tests establish
behavior, not production SQL or ten-million-row performance. Institutional
queries are scoped before content retrieval and bounded to 24 items plus one
lookahead. Review authorization and revocation using real verified work accounts
in staging before enabling museum staff in production.

## Prepared-guide mapping — 12 October 2026

`content/articles/museum-guides/institution-links.json` explicitly maps all 86
existing museum guides to 88 institution slugs. It uses the original
`docs/research/museum-guides-80-20261011/selections/{guide}.json` institution
identities for the 80-guide expansion. The original six use their selected
catalogue evidence and exact institution lookups; the Munich guide links all
three named collections. No title/website similarity matching is performed at
runtime, and no guide edition or museum holding was changed.

The map is included in the immutable Go guide-search projection by
`ops/build-guide-search-index.py`. Run `--check` for releases; deploy the API
projection and web edition files together. `institution` is an exact validated
filter, bound into pagination cursors, counts and result scope. Public responses
are at most 24 guide summaries; no editor or mutation API exists for this index.

A read-only local check found 85 of the 88 institution slugs, none archived.
CVAR Nicosia, Museum Rietberg and Royal Museums of Fine Arts of Belgium are
present in the original production research snapshots but absent from this
local catalogue by both ID and slug. Their supported mappings are retained;
no local institution fixtures were inserted to make those previews appear.

Verification for prepared guides: Go guide/member/HTTP API tests pass, including
exact museum scope, combined search, invalid/cross-scope cursor rejection and
anonymous GET versus rejected POST/PUT/PATCH/DELETE. The isolated production
build, TypeScript and 192 focused frontend tests pass. Browser checks cover the
museum Guides tab, search/reset, read-only reading controls, signed-out museum
pages, French edition navigation and public PDF download. Screens at 1440, 390
and 320px have no horizontal overflow; Axe found no violations in the checked
studio/public guide sections. No editable preview publications were created.

## Museum page tabs — 12 October 2026

Collection, Exhibitions, Guides and Visit & about now show one panel at a time.
Tab links preserve collection filters and support browser history, keyboard
navigation and existing section/artwork anchors. The `tab` query parameter also
selects the server-rendered panel, with real links for navigation without JavaScript.

After the existing staff-access check succeeds, each panel offers its matching
action: Add artwork, Add exhibition, Add guide, and Add details (Edit details for
a published profile). Editors open directly on the museum page. Profile editing
loads any existing private draft first. Publishing refreshes the public content;
saving a draft confirms that it is private and links to the studio. Prepared
Artline guides retain their separate read-only reading links. Visitors and
members without staff access have no mutation controls.

Verification: production webpack build and focused ESLint pass; 191 focused
frontend tests cover tab/history behavior, preserved filters, staff access,
editor selection, profile reuse and guide/transport behavior. Browser checks
cover all four editors, nested artwork picker, Escape/focus restoration, old
anchors, signed-out reading and server-rendered tab navigation without
JavaScript. Screens at 1440, 390 and 320px have no horizontal overflow; Axe found
no violations across the checked panels and guide editor. No browser exceptions
or persistent database writes occurred. Preview publications were not changed.
