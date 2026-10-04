# Compact undated-books panel — 3 October 2026

Deployed after the user's “push to prod” instruction. The release changes only `components/BooksGallery.css`, reconstructed from the exact previously deployed web source. Other workspace changes were excluded.

The undated list uses smaller labels and tighter spacing, with a 76-pixel height limit and vertical scrolling. It retains all eleven book entries and their date-uncertainty labels. Focus outlines remain visible inside the scroll area.

## Production release

- Service: `artline-web`, project `artline-508319`, region `europe-west1`.
- Revision: `artline-web-compact-1003`, ready and serving 100% of production traffic.
- Image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:8674a598a4221b77d8930742eff366d77a142bac444b432b39387e3e9fb5ea4e`.
- Cloud Build: `3b649364-b1e2-4dba-9ecf-1eecd8fae92d`, successful, including production compilation and TypeScript.
- Previous revision: `artline-web-public-1003`.

The candidate was staged without production traffic, checked, then promoted. Cloud Run runtime configuration was preserved apart from the web image/revision. The ignored local Terraform web image reference was synchronized; no Terraform apply, commits, API deployment or database writes were performed.

## Verification

Candidate and canonical-site checks passed at widths 1440, 390 and 320 pixels. At 1440 pixels, panel height fell from 143 to 67 pixels. At both mobile widths it was capped at 76 pixels, with scrolling and no horizontal overflow. All eleven books remained accessible. Opening the last book using the keyboard and returning focus after closing its details passed at each width. Screenshots were inspected.

Source archive, checksums, Cloud Run preimages and operations, screenshots and browser reports are stored outside Documents under `/Users/vadimdulub/Library/Application Support/Artline/backups/compact-panel-20261003/`. Uploaded source checksums match the isolated 217-file release snapshot; only the intended stylesheet differs from the previous production source.
