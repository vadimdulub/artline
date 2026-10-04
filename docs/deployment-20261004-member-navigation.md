# Member navigation and desktop Full view — 4 October 2026

Deployed after the user's request to deploy Full view, replace the help icon for
signed-in users, and make collection categories accessible through left navigation.

Signed-in members now have an account icon in the upper-right corner and a
collapsible desktop sidebar with Artists, Museums, the art history guide,
collection coverage, sources and account links. Screens up to 1100 pixels use a
left drawer. Anonymous visitors retain the help link and existing public access.

Full view works on desktop and mobile in Painters, Books, Events and All. It
hides the header, filters and sidebar, with controls to reopen filters or exit.
Dates and selections remain intact across entry, exit and viewport changes.

The header and account page share the existing API session response. Session
visibility refreshes when the browser regains focus or becomes visible. Local
member previews continue to use the API's loopback-only debug mode; no catalogue
or member fixtures were created. Authentication, authorization and session
validation remain owned by the existing Go API.

## Production release

- Service: `artline-web`, project `artline-508319`, region `europe-west1`.
- Revision: `artline-web-member-nav-1004`, ready and serving 100% of traffic.
- Image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:4905f6d3a310301ae6101bafb60a5a58a732bfb247cfe2fe1b248dc76dad5b82`.
- Successful Cloud Build: `6ca3a017-24e1-4d70-85f3-2500ba637128`.
- Previous revision: `artline-web-fullview-1004`.

The 226-file source snapshot was reconstructed from the exact live mobile Full
view archive. Nine files changed: the layout, header, account component, shared
member session and navigation components/styles, and the three desktop Full
view files. Uploaded file checksums and Cloud Build source provenance matched.
Unrelated workspace changes were excluded.

The candidate received zero normal traffic until verification passed. Runtime
configuration was preserved apart from image and revision, including Google
verification and production debug safeguards. The ignored Terraform image pin
was synchronized; no Terraform apply, API deployment, database writes or Git
commit occurred. The previous revision remains available for traffic rollback.

## Verification

- Production compilation, TypeScript, focused lint and 21 authentication/SEO
  unit tests passed.
- Five member navigation checks passed locally using the API's real debug
  session. They cover account-session reuse, active links, collapsing, mobile
  drawers, keyboard focus, expired-session handling and Full view integration.
  Anonymous/expired responses were browser-only test stubs, with no database
  fixtures or authentication configuration changes. The member account view
  passed the WCAG A/AA accessibility scan.
- All twelve desktop/mobile Full view tests passed locally, on the candidate
  and on `https://artlines.org`, including nested artwork/book dialogs, filter
  preservation, popovers, keyboard shortcuts and index navigation.
- Member desktop/mobile screenshots were inspected. Canonical-site checks at
  1440, 768, 620, 390 and 320 pixels found no header overlap or overflow.
- Candidate and live anonymous session requests returned no member and did
  not enable local-debug/all-features access. These checks do not constitute
  a new Google sign-in round trip; signed-in UI behavior was verified with the
  actual local-debug session and the existing authentication proxy tests.
- Logo/icon checksums, page routes, canonical metadata, sitemap discovery and
  the existing Google verification token passed. No browser errors or
  ERROR-level revision logs were returned during verification.

Private runtime preimages, operations, source archive, manifests, browser
reports and screenshots are stored outside Documents at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/member-navigation-20261004/`
