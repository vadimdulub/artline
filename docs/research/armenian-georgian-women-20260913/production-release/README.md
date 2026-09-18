# Production release: Women artists, 13 September 2026

The user authorized the application release after completion of the research/import session. The API and web application now serve release `20260913-women-fef17155` with 100% traffic. Women artists appears before Only popular painters, and both filters can be combined independently.

[Open the production women-artists view](https://artline-web-lpuqqlugnq-ew.a.run.app/?women=true&popular=false).

## Release evidence

- Base commit: `b848edcbbf3deebba817fc40dc477dfc14503520`.
- Frozen source SHA-256: `fef171554eac46526c87e4ed414728d814b2b079947f2661ca44d3d38acf3b11`. The source manifest records the exact overlay files, including the previously live creator-slug compatibility fix. No commit was created.
- API build: `70ee6559-da48-40bc-8e23-f4a4e53cb99c`; revision `artline-api-00011-92d`; image digest `sha256:05277957852dbc8d8834b42736efb16a74d282d69536a5477b3b7a5280f6f8ee`.
- Web build: `6a402b54-d13d-4d2f-b8a8-3e764f7fa593`; revision `artline-web-00011-zkm`; image digest `sha256:62cd7e9bd15ac25cf4d0ba1cc0b3f26638d4d0d5a99ef5d14ab56f4a5771f97a`.
- Both Cloud Builds succeeded; running revision digests match those builds.
- Reviewed Terraform plan changed only the API and web container image fields. Applied the saved plan: 0 added, 2 changed, 0 destroyed. The final plan exited 0 with no drift. Private Terraform plans/state/configuration are excluded from this evidence folder.
- Migration `0019_artist_gender_evidence.sql` and 521 women identities were already present in production; verified read-only before deployment. This release performed no additional ingestion or publication. The 271 research artworks and 41 new artist profiles retain review status; 38 selected images remain available.

## Verification

Frozen-source Go catalogue and HTTP API tests passed. Both production browser tests passed (12.2 seconds), covering filter order, popularity intersection, counts, URL reload/back, reset/clear, and desktop/mobile widths of 1440, 390 and 320 pixels. The production mobile screenshot was visually inspected.

Live health and readiness endpoints returned 200. Women-only results contained 521 artists with popularity disabled and 5 with popularity enabled; combining Armenian country scope returned 2 women. Duplicate women query values returned HTTP 400 / INVALID_WOMEN for timeline, facets and painter options. The existing underscore-containing artist route returned 200.

Three representative Armenian/Georgian artwork routes and their live JPEG assets returned 200 after deployment. All image SHA-256 checksums matched the pinned research selections; receipts are in `live-artwork-verification.json`.

This verifies release behavior at current catalogue size; the previously documented 10-million-artwork load test remains outstanding.

## Rollback reference

Previous release tag: `20260913-creator-slugs-57a4f08a`. Previous ready revisions: API `artline-api-00010-98s`, web `artline-web-00010-5nl`. Before/after service receipts are retained here. No rollback was needed.

The original research completion archive and immutable application receipts remain unchanged. This folder documents the later authorized deployment.
