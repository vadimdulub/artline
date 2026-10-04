# Logo and favicon release — 4 October 2026

Deployed after the user's “ok, deploy to prod” instruction. The compact
“Artlines” wordmark and matching serif “A” favicon are live at
<https://artlines.org/>.

## Release

- Service: `artline-web`, project `artline-508319`, region `europe-west1`.
- Revision: `artline-web-logo-1004`, ready and serving 100% of production traffic.
- Image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:0d27e24058a8417742a670ac5c92ae48e4f74498fb4856a8c6cdca0125ca3d4a`.
- Successful Cloud Build: `4b01e7ba-25d9-4f56-b481-1ef3624e25fe`.
- Previous revision: `artline-web-compact-1003`.

The 221-file source snapshot was reconstructed from the exact compact-panel
production archive. Seven files changed: the header, its logo styles, SVG/ICO
and Apple icons, the WebP wordmark, and its asset documentation. Uploaded source
hashes and Cloud Build provenance match the prepared snapshot. Other workspace
changes were excluded; the recent collection, SEO and compact-books releases
are preserved.

The candidate received zero normal traffic until verification passed. Cloud Run
runtime configuration was preserved apart from the image and revision. The
ignored Terraform web image pin was synchronized without Terraform apply.
No API deployment, database writes, publication changes or Git commit occurred.

## Verification

Production compilation, TypeScript and targeted header lint passed. Candidate
and canonical-domain browser checks passed at 1440, 768, 620, 390 and 320 pixels.
The desktop header remains 60 pixels high; the logo is 144 pixels wide on desktop
and 132 pixels on smaller screens, with no logo/navigation overlap or horizontal
header overflow. Desktop and mobile screenshots were inspected.

The wordmark (28,230 bytes), SVG icon (440 bytes), ICO (2,748 bytes) and Apple icon
(4,850 bytes) returned HTTP 200 and matched source checksums. Next.js icon links,
keyboard focus and the home link passed. Books, Events, All, Artists, Leonardo's
profile, the timeline guide and Account returned HTTP 200 with the new header.
Google verification, canonical metadata, homepage `noindex` and sitemap discovery
remain intact. No browser errors or ERROR-level revision logs were returned.

Private Cloud Run preimages, operations, source archive, manifests, browser
reports and screenshots are stored outside Documents at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/logo-20261004/`

The preceding revision remains available for a traffic rollback. Asset details
and the generation prompt are in `apps/web/public/brand/README.md`.
