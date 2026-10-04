# Painter previews: pictures first — 4 October 2026

Commit `100d6db` makes the Painters pop-up open with a large artwork image,
caption, museum holding and previous/next controls. The image collection follows
in two columns. A single Filters button opens search, year, type, museum and
picture controls. Artwork metadata is expandable; biography and sources remain
available below the collection. Full artist pages retain their research layout.

The pop-up defaults to the existing server-side picture filter. Users can turn
it off to browse records without images; no catalogue records are removed or
published. The backend still returns bounded 24-work pages and scoped neighbours.
Artists remains in the Account menu only, as deployed in commit `9889729`.

## Production

- Web revision: `artline-web-picture-first-1004`, ready and serving 100% of traffic.
- Source commit: `100d6db`, pushed to `origin/master`.
- Cloud Build: `cd2d0407-7ac6-41bb-9d78-8b022d0b9850`.
- Immutable image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:e44a4ab92ce03d4c7ca7468dd8ebd541878b4e61958cd4ea0ab63ce8a1a581c2`.
- Example: <https://artlines.org/?artist=claude-monet>.

The build archive came from the exact Git commit and matches Cloud Build's
resolved-source SHA-256. Runtime configuration and instance sizes are unchanged.
The API and database were not deployed or modified. The ignored Terraform web
image pin was synchronized without a Terraform apply. The preceding revision
`artline-web-account-artists-1004` remains available for rollback.

## Verification

- ESLint, TypeScript and all 203 frontend unit tests passed.
- Twelve browser checks passed against the current local API: image-first preview,
  hidden/revealed filters, empty search/reset, retained records without images,
  keyboard/focus behavior, two-column thumbnails, image decoding and enlargement,
  previous/next across pages, and full artist-page regression coverage.
- Candidate checks reran the drawer, cross-page picture navigation and full artist
  workspace coverage against production data. Live checks reran the drawer and
  picture navigation at 1440, 390 and 320px. Accessibility checks passed at 390px.
- Opening and collection screenshots were inspected. Local validation used the
  real catalogue with enforced read-only access and no database fixtures. An
  initial run against an older local API could not exercise title search; the
  complete passing runs used the current API in an isolated preview.

Private source archives, manifests, service preimage, build results, deployment
operations, screenshots and browser evidence are retained under:
`/Users/vadimdulub/Library/Application Support/Artline/backups/picture-first-20261004/`
