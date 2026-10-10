# Account panel behavior — 5 October 2026

The Account panel follows Rondy's interaction pattern: desktop icons remain
stationary while labels collapse, the panel remembers its state across reloads
and navigation, and account controls sit at the bottom. The panel remains
limited to signed-in Account pages. Its visible group headings are removed, and
“Collection coverage” is shortened to “Coverage,” including accessible names and
collapsed-link tooltips.

## Release

- Cloud Build: `db3d0791-7b2b-4219-8a65-10692b4ba083`.
- Web revision: `artline-web-panel-rondy-1005`, ready and serving 100%.
- Web image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:55a681dcbfc045157839085428ccb5df3a46e350af3b31576ab5599858094fb6`.

The release uses the exact serving collapsed-panel source from Cloud Build
`86654e4a-b037-413d-848f-4154a56cd566`. Only `MemberNavigation.tsx`,
`SiteHeader.tsx` and `SiteNavigation.css` differ. The manifest covers all 272
source files and preserves the 115 existing files under `public/images/`.
Both baseline and submitted archives were verified against Cloud Build source
provenance using SHA-256.

The candidate passed checks before an etag-protected traffic promotion. Runtime
settings and prior revision tags were preserved. The API and database were not
changed. The ignored local Terraform web image pin records the serving digest;
no Terraform apply or Git commit was performed.

## Verification

- All 10 local navigation checks passed after the wording change, covering
  Account-only visibility, desktop/mobile sizing, accessibility, keyboard
  navigation, storage failures, saved preferences and reduced motion.
- TypeScript passed during implementation; focused ESLint and the production
  build passed. A local animation check sampled 23 frames without icon movement.
- Candidate and live browser checks passed at 1440, 768, 390 and 320px. Checks
  cover all six icon links and tooltips, minimum 44px targets, collapse/expand,
  current-page styling, keyboard navigation, content offsets, no horizontal
  overflow, removed wording and preference persistence across reloads and public
  tab navigation. Candidate desktop/mobile screenshots were reviewed.
- Production anonymous sessions retain no local-debug or all-features access.

Member UI checks use the real loopback API local-debug response only inside an
isolated test browser. These are UI checks, not a production Google sign-in
round trip. No account/catalogue fixtures were created and production
authentication was not modified.

Private source archives, manifests, service snapshots, build receipts and browser
evidence are retained under
`~/Library/Application Support/Artline/backups/panel-rondy-20261005/`.
