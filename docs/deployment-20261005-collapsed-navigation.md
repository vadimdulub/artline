# Collapsed navigation icons — 5 October 2026

Collapsing the Account panel now leaves a 56px rail with all six navigation
icons. Links retain accessible names, hover labels and the current-page
highlight. The bottom arrow expands the panel, and collapsed navigation remains
available when moving between account pages.

## Release

- Cloud Build: `86654e4a-b037-413d-848f-4154a56cd566`.
- Web revision: `artline-web-collapsed-nav-1005`, ready and serving 100%.
- Web image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:2a6ae1967716a4ec196aa3bba13697919e17b6cb8206bfc1f8981cf463437299`.

The release uses the exact serving war-books/timeline source from Cloud Build
`10543d4b-2c0b-4fb7-82a4-9505cbf99dbe`. Only `MemberNavigation.tsx` and
`SiteNavigation.css` were overlaid. All 272 source files were checked against the
manifest; the 115 existing files under `public/images/` are preserved. The
submitted source archive was verified against the exact resolved Cloud Build
source generation using SHA-256.

The candidate passed verification before an etag-protected traffic promotion.
Runtime settings and prior revision tags were preserved. The API and database
were not changed. The ignored local Terraform web image pin records the serving
digest; no Terraform apply or Git commit was performed.

## Verification

- Focused ESLint and `git diff --check` passed; the production build passed.
- All eight local Account navigation tests passed, including keyboard navigation,
  expired sessions, accessibility checks, and desktop/mobile layouts.
- Candidate and public-site checks passed at 1440, 768, 390 and 320px. Checks
  cover all six icon links, labels, at least 44px targets, collapse/expand,
  current-page styling, keyboard navigation, content offsets and no horizontal
  overflow. Screenshots were reviewed on the candidate.
- Both production endpoints retain anonymous sessions without local-debug or
  all-features access. Public explorer tabs do not show the account panel.

Member UI verification forwards the real loopback API local-debug session only
inside an isolated test browser. These are UI checks, not production Google
sign-in checks. No account or catalogue fixtures were created, and production
authentication was not modified.

Private source archives, manifests, service snapshots, operation receipts and
browser evidence are retained under
`~/Library/Application Support/Artline/backups/collapsed-navigation-20261005/`.
