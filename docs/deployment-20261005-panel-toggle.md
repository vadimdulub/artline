# Account panel control — 5 October 2026

The Account panel's show/hide arrow now sits at the bottom. Menu links scroll
above the control, keeping it visible in short windows. Desktop shows “Hide panel”
with the arrow; narrow screens and the collapsed panel show the arrow. Accessible
button names, keyboard behavior and Account navigation remain available.

## Release

- Application commit: `e2cae1151293e1344a25b5706f1ebbf1f46d5991`.
- Cloud Build: `e46c4e24-fdac-4ccf-b9b0-056045cac241`.
- Web revision: `artline-web-panel-toggle-1005`.
- Web image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:73ec0eec6e511377f4c5fb8733aa91b4ae8d23f90e22b31b586aca910dab738e`.

The build uses the exact application commit and preserves the 40 book and author
image assets from the preceding serving release. Source archive hashes were
verified against Cloud Build provenance. The candidate was checked before traffic
promotion. The ready revision serves 100% of web traffic; API, instance sizes and
runtime settings were unchanged. The local Terraform web image pin records the
serving digest; no Terraform apply was performed.

## Verification

- ESLint and TypeScript passed.
- All eight existing Account navigation browser checks passed locally.
- Local, candidate and live layout checks passed at 1440×900, 390×844, 768×360 and
  320×568. Checks cover the bottom position, menu scrolling, collapse/reopen and
  horizontal overflow. Screenshots were reviewed locally and on the candidate.
- All 40 retained image assets matched their source hashes on candidate and live.

Member UI checks use the real safeguarded local-debug API with the local database
in read-only mode and migrations skipped. Candidate/live browser checks intercept
only the session response inside the test browser using that local-debug response;
these are UI checks, not production Google sign-in checks. No account or catalogue
fixtures were created, and production authentication was not modified.

Private service snapshots, build provenance, source manifests, asset checks and
browser evidence are retained under
`~/Library/Application Support/Artline/backups/panel-toggle-20261005/`.
