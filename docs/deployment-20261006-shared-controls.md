# Shared Artists and Museums controls — 6 October 2026

Artists and Museums now share search fields, searchable pickers, reset actions,
keyboard behavior and responsive filter layouts. Artist and museum artwork
views use the same search controls. The museum introduction and the “European
museums” / “All locations” shortcuts and explanatory prompt are removed.
Filtering, counts and bounded pagination remain owned by the existing Go API.

## Release

- Public site: https://artlines.org.
- Cloud Build: `3f119057-01e4-4ca5-bfc9-b23841cc8b2e`.
- Web revision: `artline-web-shared-controls-1006`, ready and serving 100%.
- Web image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:7d34a0e9fc11fc15e5baf57601c1cd9c5e192dfe4c01118ad046698c8ed84b2c`.
- Previous serving revision: `artline-web-museum-images-1005`; its tagged
  revision remains available.

The isolated release starts from the exact serving museum-gallery source from
Cloud Build `11cf3379-9476-4d70-a394-39beabfa402b`. It overlays 13 existing UI
files and adds `ArtistsIndex.tsx` and `AtlasSearchField.tsx`. All other source
files and all 121 public assets are preserved, including the previously
released museum image ordering and counts. Unrelated workspace changes are
excluded. The complete 274-file manifest and release patch are archived.

Both the baseline archive and the submitted archive were checked against Cloud
Build source provenance. Submitted archive SHA-256:
`b819190f5ee6d678a08f8e4f98d3991dabffb241f8ce22b49e5bd3315ad5499c`.

The candidate received no public traffic until verification passed. Promotion
used a Cloud Run v2 etag guard and preserved runtime configuration and existing
revision tags. The API and database were unchanged. The ignored local Terraform
web image pin records the serving digest; no Terraform apply or Git commit was
performed.

## Verification

- Production build and focused ESLint passed; local implementation checks also
  passed TypeScript, interaction tests and whitespace validation.
- All 17 candidate browser tests passed. Coverage includes directory search,
  country and movement pickers, reset/clear actions, keyboard focus, reversible
  pagination, server-rendered artist results with JavaScript disabled, artist
  workspaces, museum filters, large collections, painter previews and the
  shared Books filter bar.
- All seven directory-control tests passed again on https://artlines.org at
  1440, 390 and 320px, including server rendering without JavaScript.
- Supplemental candidate and public-site checks passed for member layouts at
  1440 and 390px, picker bounds, no horizontal overflow, Escape focus restoration,
  shared artwork controls, removed museum labels and no page errors. Candidate
  desktop and mobile screenshots were visually reviewed.
- Both endpoints retain anonymous sessions without local-debug or all-features
  access. Member layouts use the real loopback Go API debug response only inside
  an isolated test browser; these checks do not exercise production Google
  sign-in. No account or catalogue fixtures were created.

The in-app browser runtime was unavailable, so verification used standalone
Playwright. The local web preview stalled during supplemental setup; the same
checks then used the existing loopback Go API session directly, with a bounded
request timeout. No production authentication setting was changed.

Private source archives, manifests, service snapshots, operation receipts,
verification scripts, test reports and screenshots are retained under
`~/Library/Application Support/Artline/backups/shared-controls-20261006/`.
Disposable test output remains under `/tmp/artline-shared-controls-release-20261006/`.
