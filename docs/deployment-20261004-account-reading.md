# Account navigation and biographies — 4 October 2026

Account and the restored top-right avatar open `/artists`. Successful Google
sign-in redirects there. Artists, Museums and account resources keep the left menu
open, with an explicit hide/show button. Phones use a narrow labelled rail without
an overlay or scroll lock. Painters, Books, Events and All render no account panel.
The header stays at the top and its study-atlas tagline is removed.

Source biographies now honor single-newline paragraph boundaries. Long passages
break at sentence boundaries, with a lead paragraph, readable line measure and
serif spacing. Existing Markdown headings, emphasis, links and lists are retained.
Full artist pages show the complete biography; painter previews remain compact.
Attribution, revision links and licences remain. Empty optional sections and
editorial workflow notices are omitted. Stored biographies and facts are unchanged.

## Serving release

- Application commits: `dc8309a` and mobile CSS follow-up `d756681`, pushed.
- Web: `artline-web-account-books-1004`, ready and serving 100%.
- Web image: `europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:1f42a0055bbe092670484dd9bbffea683023b6bca5fdc7c8a8ae8eb56c3f69cd`.
- API: `artline-api-books2-1004`, ready and serving 100%.
- API image: `europe-west1-docker.pkg.dev/artline-508319/artline/api@sha256:5e5e5cb0e297db351ae9f1c5c332d909974f91397f044d97c32589a4a5ef2478`.
- Web application build: `1d35f62b-40e8-49b4-8b47-37266e0d8ec4`.
- Final web composition build: `3317580c-7750-467d-8977-abdec92dbbf6`.
- Serving API build: `8aa7f6b7-2028-4da1-a49b-f35ed0308a50`.

The Account API was first deployed as `artline-api-account-reading-1004`.
A concurrent book release then supplied the serving API above; its member handler
is byte-for-byte identical to `dc8309a`, including the `/artists` redirect.

The concurrent book web image initially used an older application base. The final
composition uses the exact `d756681` application image and preserves all 40 book
cover/author images from the concurrent build. Source archive SHA-256 and every
image asset were verified. Both the candidate and live assets match their source
bytes. Use the combined web digest above as the deployment target.

The concurrent book rollout completed before final promotion. Traffic was switched
to the already-tested combined revision using an etag-protected traffic-only
update. The service's latest-created template remains `artline-web-books2-1004`;
traffic is explicitly pinned to `artline-web-account-books-1004`. Instance sizes,
secrets and other runtime settings were retained. Terraform image pins match the
serving images; no Terraform apply was performed. Previous revisions are retained.

## Verification and limits

- All Go packages, ESLint, TypeScript and 209 frontend tests passed for this change.
  OAuth callback tests assert `/artists`; local-debug loopback/origin safeguards
  remain. No real Google login or member database fixture was used.
- Biography tests preserve every non-whitespace character across all 1,000 source
  profiles and exercise Markdown preservation and compact/full reading modes.
- Seventeen local browser checks passed. Eight account checks also passed against
  final source at 320, 390, 768, 1024 and 1440px, including navigation persistence,
  public-tab exclusion, the avatar, keyboard controls, layout and accessibility.
- Final candidate and live account/header checks passed at 1440, 390 and 320px,
  including full-width mobile navigation and sticky positioning. Production sign-in
  is enabled and local debug is disabled. All 40 concurrent image assets passed
  byte-for-byte checks on both the candidate and live site.
- Broader production catalogue checks were not all green: 6 of the initial 12
  candidate checks passed, including mobile biography reading and full Rembrandt
  catalogue interactions. Other checks and one reading retry encountered catalogue
  API timeouts. They are not counted as successful performance checks.

## Existing catalogue latency

Before promotion, both the previous API and candidate returned 8-second read
deadlines on artist discovery. Previous-revision logs also showed painter-detail
and chronology timeouts. A read-only activity snapshot showed long external-ID
research queries and concurrent location cataloguing work. These observations
establish that the failures predate this release, but not a complete root cause.
The API diff for this task changes only member handling and tests, with no catalogue
query changes. No other session/query was cancelled and this task made no catalogue
writes. Catalogue latency remains unresolved.

Private sources, manifests, service preimages, deployment operations, screenshots
and browser evidence are retained in the Artline backup directory under
`account-reading-20261004/`, `account-reading2-20261004/` and
`account-books-20261004/`. Unrelated uncommitted scripts and catalogue work remain
in the shared workspace.
