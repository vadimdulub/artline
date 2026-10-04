# Artists in the Account menu — 4 October 2026

Commit `9889729` removes Artists from the top navigation. The existing Account
sidebar and mobile drawer retain the Artists link. Account remains closed until
clicked, and the header remains sticky.

Committed, pushed and deployed from the exact Git source:

- Web revision: `artline-web-account-artists-1004`, serving 100% of traffic.
- Cloud Build: `23504137-a25f-47ab-999c-26d69364d3fe`.
- Image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:9bed2785dcdccee259292f7a7a398acb5c17fc63d02a73ec6f2531a1852d2c45`.
- Canonical site: <https://artlines.org>.

The source archive SHA-256 matches Cloud Build provenance. Targeted ESLint and
the existing desktop/mobile member-navigation checks passed. Browser verification
at 1440, 768, 390 and 320px confirms the top Artists link is absent and Account is
visible; the local API's real debug session confirms Artists appears when Account
opens. Candidate and live anonymous header checks passed without JavaScript errors.
The Account sidebar implementation is byte-identical to the previous deployed code.

Runtime configuration and instance sizes are unchanged. The API, database and
catalogue data were not changed. Only the ignored Terraform web image pin was
updated; no Terraform apply was performed. Previous web revision
`artline-web-artists4-1004` remains available for rollback.

Private source, service preimage, build and verification evidence:
`/Users/vadimdulub/Library/Application Support/Artline/backups/account-artists-20261004/`
