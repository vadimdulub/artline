# Mobile Full view release — 4 October 2026

Deployed after the user's “deploydeploy” instruction. Mobile users can enter
Full view on Painters, Books, Events and All. A compact toolbar keeps filters
and exit available, paintings grow larger, and filter selections and record
navigation remain intact. Resizing to desktop exits this mobile mode.

## Production release

- Service: `artline-web`, project `artline-508319`, region `europe-west1`.
- Revision: `artline-web-fullview-1004`, ready and serving 100% of production traffic.
- Image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:c175186c4d8d94a34889290e6957aa40dd4bb82593cec89468b6fd29912c4055`.
- Cloud Build: `b5ecf4e6-f58f-4f26-8589-8ada04b41a0b`, successful, including production compilation and TypeScript.
- Previous revision: `artline-web-logo-1004`.

The 223-file source snapshot was reconstructed from the exact deployed logo
release archive. Nine component files changed: the shared frame and stylesheet,
filters and popover Escape handling, and the four explorer integrations. Source
checksums match the uploaded Cloud Build archive. The logo, SEO, collection and
compact-books releases are preserved.

The candidate was staged without normal traffic and promoted after its checks
passed. Cloud Run runtime configuration was preserved apart from image and
revision. The ignored local Terraform web image pin was synchronized without
Terraform apply. No API deployment, database writes or Git commit occurred.

## Verification

All eight release browser tests passed on `https://artlines.org`. Checks cover
390-pixel and 320-pixel phones, 740-pixel landscape, resizing to 1440-pixel
desktop, opening filters, preserved selections, keyboard focus, nested book and
artwork dialogs, index navigation, popover Escape handling and image loading.
The filter view also passed the WCAG A/AA accessibility scan. Screenshots were
inspected, and no ERROR-level revision logs were returned during verification.

An initial candidate check reached its five-second assertion timeout while the
catalogue was loading; the gallery checks passed with a 20-second network wait.
Concurrent local desktop Full view work changed the shared test expectations
during deployment. Final verification used an isolated copy matching this mobile
release; those desktop edits were preserved locally and excluded from this build.

Private service preimages, operations, source archive, manifests, test reports,
screenshots and the isolated release test are stored outside Documents at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/mobile-full-view-20261004/`

The previous revision remains available for a traffic rollback.
