# Production period and filter release — 2 October 2026

Live at https://artlines.org. Both services serve 100% of normal traffic from the verified release:

- API: `artline-api-periods-1002`, image `sha256:e9189fab50a7eaab70b656188bfef859b5a1d2fbae6f38ecd6507387345272c1`.
- Web: `artline-web-periods-1002`, image `sha256:062b9f61e2247c118a915a4ad1693a6639fa649b4704d0d26e4cc671caa2c2f4`.
- Builds: `da3008d5-bf5d-43a6-9e83-6666922c1d39` (API), `4adfaeb7-a2b0-400b-a6b8-924d30b82817` (web).

The [period review](../period-connections-20261002/README.md) describes the 32 starting points, grouped filter choices, complete filter clearing, 46 new book connections and the selected Timbuktu chronicle. Its guarded production database delivery completed before application traffic switched. No migrations or Terraform apply were needed.

Candidates were staged at zero normal traffic and tested against production data. All 32 API views returned the expected bounded counts and all newly connected books. Desktop and mobile Chrome checks at 1440, 390 and 320 px passed, including WCAG checks, search, dates, history and complete filter clearing. Six selected artwork assets matched local checksums and were below 100,000 bytes. Google sign-in remained enabled, anonymous users remained anonymous, and production local-debug/member-preview access remained disabled.

All 32 production starting points also passed direct database-enforced read-only checks and representative query-plan review. Thirty-seven connected book identities/checksums and six explicit artwork identities matched local records. Existing production-only artwork differences in four older views were preserved rather than overwritten from local. Counts were verified against the production catalogue for this release. These checks are not a 10-million-row capacity test.

Cloud Run template, ingress, access and scaling configuration were compared with the saved pre-release state. Only the image/revision and traffic were changed. Ignored local Terraform image pins now match the immutable release; no infrastructure apply was run.

Release archives and per-file hashes cover 343 API files and 215 web files, including pending application work present when the release was prepared. Separate SEO/guide-page edits appeared in the shared workspace after the build snapshot; those newer edits were not included in this verified release. No user edits were reverted and no Git commit or push was made.

Rollback targets remain the previous tagged revisions `artline-api-library-1001` and `artline-web-library-1001`. The new database record is backward-compatible with them. Exact service preimages, operations, source archives, build results, browser screenshots and verification receipts are under `/Users/vadimdulub/Library/Application Support/Artline/backups/production-periods-20261002/`. Database backup `1790963667418` completed successfully before the selected data addition.

Final canonical-site verification passed through https://artlines.org: all 32 period API views, the new Arabic-language book filter, all six selected images and six desktop/mobile browser scenarios. Receipts accompany this report.
