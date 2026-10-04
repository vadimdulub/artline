# Google sign-in and artlines.org setup

Prepared 28 September and updated 30 September 2026. HTTPS, DNS and Google
sign-in are live at https://artlines.org. The OAuth app is External and In
production; a real Google login, session persistence and logout were verified
in the owner's v-test Chrome profile. The public privacy page is deployed.
See [the domain activation record](domain-activation-20260928.md) and
[the Google activation record](google-signin-activation.md) for current settings,
validation and rollback details. This setup did not run a database migration;
the existing production member schema was verified read-only on 28 September.

## Verified project and domain

| Setting | Value |
|---|---|
| Google Cloud project | `artline-508319` |
| Region | `europe-west1` |
| Existing web service | `artline-web` |
| Existing web URL | `https://artline-web-lpuqqlugnq-ew.a.run.app` |
| Existing API service | `artline-api` |
| Existing API URL | `https://artline-api-lpuqqlugnq-ew.a.run.app` |
| Canonical public URL | `https://artlines.org` |
| Secondary hostname | `www.artlines.org`, permanently redirected to `artlines.org` |
| Authoritative nameservers observed | `amos.ns.cloudflare.com`, `teresa.ns.cloudflare.com` |
| Root and www A records | `136.110.174.158`, DNS only |

The active Google Cloud login can read the Artline project. Secret Manager
contains the database and editor secrets plus
`artline-auth-cookie-key` and `artline-google-client-secret` (both enabled
version `1`). The Compute API was enabled during domain activation.
The owner supplied a Cloudflare API token, used successfully for the two DNS
records; no Cloudflare credential was persisted. The in-app browser connection
failed; Google Auth Platform was subsequently configured through the owner's
external Chrome profile. The existing production Web application client is
`995787188464-0omg2p07c40n3m4i56of59sla9ae7sr1.apps.googleusercontent.com`.
Do not create a duplicate client during routine maintenance.

## Implemented application behavior

- `/account` provides Google sign-in, current account and sign-out, with loading,
  unavailable and cancelled-login states. The Account link is visible on mobile.
- The Go API owns identity and sessions. The web app forwards only the supported
  authentication endpoints through `/api/auth/...`, preserving redirects and
  multiple cookies without exposing an editor bearer token.
- OAuth authorization-code flow uses state, nonce and PKCE S256. The OIDC library
  checks signatures, issuer, audience and expiry; Artline additionally checks
  nonce, verified email and the authorized party when present.
- Google `sub` is the unique account key. Email is profile information and is
  never used to merge identities or assign editorial authority.
- Sessions are random 256-bit tokens, with only SHA-256 hashes stored in
  PostgreSQL. Production cookies use `__Host-`, Secure, HttpOnly and SameSite=Lax.
  They expire after 30 days. Login replaces the browser's previous session;
  sign-out deletes the server session. No refresh/access tokens are persisted.
- Same-origin POST is required to start login and sign out. Authentication
  responses are private and never cached. Post-login redirects use the configured
  origin, not a request Host header or a user-supplied return URL.
- All member accounts are currently free. Billing, premium entitlements and
  account deletion UI remain future work. Editor-token authorization is separate.
- `0032_member_accounts.sql` adds member accounts and sessions. This setup work
  did not apply it to the real local catalogue or production. A pre-existing
  production release already serves the auth endpoints. A read-only production
  check at 18:29 UTC confirmed the migration ledger entry, both tables, their
  expected columns, identity uniqueness and session indexes. No account rows or
  tokens were read. API deployment runs pending migrations through the existing
  startup mechanism.

The Google button is an unmodified, pre-approved PNG from the
[official branding asset bundle](https://developers.google.com/identity/branding-guidelines).
The authentication flow follows [Google's OpenID Connect documentation](https://developers.google.com/identity/openid-connect/openid-connect).

## 1. Connect the domain

The prepared route is Cloudflare DNS → Google global external Application Load
Balancer → existing `artline-web` Cloud Run service → existing API. Keep the API
behind the same web-origin proxy for browser requests. An `api.artlines.org`
hostname is unnecessary for this setup.

Google recommends a global external Application Load Balancer for production
custom domains; direct Cloud Run domain mappings remain preview and are not
recommended for production. [Google custom-domain guidance](https://docs.cloud.google.com/run/docs/mapping-custom-domains).

Budget approximately **US$18.25/month base** for the first five global forwarding
rules combined (`$0.025 × 730 hours`), plus traffic processing, egress and the
existing Cloud Run/SQL/storage charges. This setup uses two forwarding rules.
The static IP attached to the forwarding rules has no separate IP charge.
Prices checked 28 September 2026; actual currency, tax and usage change the bill.
[Load balancer pricing](https://cloud.google.com/load-balancing/pricing),
[external IP pricing](https://cloud.google.com/vpc/network-pricing#ipaddress).

Prepared infrastructure in `terraform/prod/domain.tf` includes a reserved IPv4,
serverless backend, managed certificate for both hostnames, TLS 1.2 minimum,
HTTP→HTTPS redirects and www→apex redirects preserving path/query. CDN caching
is disabled. It is opt-in (`enable_custom_domain = false` by default).

Before activation, review a fresh full Terraform plan and the existing deployed
image versions. Do not apply an old plan or use an unreviewed image tag: this
workspace also contains other ongoing work.

```sh
sh ops/terraform_gcloud.sh plan \
  -var=enable_custom_domain=true \
  -target=google_compute_global_forwarding_rule.web_http \
  -target=google_compute_global_forwarding_rule.web_https \
  -out=/tmp/artline-domain.tfplan
# After reviewing and authorizing the concrete plan:
sh ops/terraform_gcloud.sh apply /tmp/artline-domain.tfplan
sh ops/terraform_gcloud.sh output -raw artlines_dns_ipv4
```

The one-time domain provisioning plan is explicitly scoped to the two entry
points and their infrastructure dependencies. This avoids rolling out unrelated
Cloud Run image/configuration changes from the current working tfvars. A fresh
full plan was inspected and also proposed updating both existing services;
those updates are outside the domain-only step. Use a full reviewed plan for
the subsequent application release. Terraform targeting is intentional for this
staged setup, not the default for routine maintenance.

Persist `enable_custom_domain = true` in the ignored production tfvars before
subsequent plans, so the next deployment does not propose removing the domain
resources. Leave sign-in disabled and the existing canonical site URL unchanged
until DNS and HTTPS are working.

In Cloudflare, open **artlines.org → DNS → Records** and add:

| Type | Name | Content | Proxy | TTL |
|---|---|---|---|---|
| A | `@` | Exact `artlines_dns_ipv4` output | DNS only / grey cloud | Auto |
| A | `www` | Same `artlines_dns_ipv4` output | DNS only / grey cloud | Auto |

The assigned IP is now **136.110.174.158**, and both records are configured.
Do not enter the `run.app` URL as an A record,
or assume a CNAME to it configures Cloud Run for this hostname. Check for
conflicting A/AAAA/CNAME records at these two names; preserve mail and other
unrelated records. Nameservers already point to Cloudflare and need no change.

Keep these records DNS-only for this certificate design, including renewal.
Cloudflare proxying and “Cache Everything” rules are not part of this setup.
If proxying is introduced later, configure certificate validation deliberately,
use Full (strict), and bypass caching for authentication/account responses.
[Cloudflare Full (strict)](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/).

Wait until `artline-web-certificate` is ACTIVE and both HTTPS names work. If
certificate provisioning stalls, check both DNS records, old AAAA records and
any restrictive CAA policy. Google documents the supported certificate issuers
and troubleshooting in its [managed-certificate guide](https://docs.cloud.google.com/load-balancing/docs/ssl-certificates/google-managed-certs).

## 2. Create the Google Web application client

Open [Google Auth Platform](https://console.cloud.google.com/auth/overview?project=artline-508319).
Use this setup sheet:

| Google setting | Value |
|---|---|
| Application name | `Artline` |
| Public operator | `Vadim Dulub` — explicitly confirmed by the owner on 28 September 2026 |
| Audience | External, for ordinary Google-account users |
| Support / developer contact | `vadim@alingva.com` — explicitly confirmed by the owner on 28 September 2026 |
| Homepage | `https://artlines.org` |
| Privacy policy | `https://artlines.org/privacy` — deployed and verified |
| Authorized domain | `artlines.org` |
| Client type | Web application |
| Suggested client name | `Artline web production` |
| Authorized redirect URI | `https://artlines.org/api/auth/google/callback` |
| Authorized JavaScript origin | `https://artlines.org` if required by the console; the server redirect flow does not use a browser SDK |
| Requested scopes | `openid`, `email`, `profile` only |

The callback must match **exactly**; do not add a trailing slash or use the API's
`run.app` address. The canonical origin is the apex domain, so no www callback is
needed. Users must begin sign-in on `artlines.org`; cookies are host-only and are
not shared with the fallback `run.app` domain.

Verify ownership of `artlines.org` in [Google Search Console](https://search.google.com/search-console/welcome).
For a Domain property, Google supplies a unique `google-site-verification=...`
TXT value. Add that exact TXT record at `@` in Cloudflare, then Verify. This token
is generated by Google and has not been invented or created in this session.
Domain TXT verification does not require the app's HTML-verification variable.

For testing, use the console's Testing audience and add the owner/testers when
applicable. For public launch, complete the production publishing/branding steps
shown by Google. Provide a real privacy policy with the operator's identity,
contact and data practices; terms of service are optional for Google's branding
requirements. The owner confirmed **Vadim Dulub** and **vadim@alingva.com** as
the public operator/contact. `/privacy` is deployed and linked from
the footer and sign-in screen. It describes the current identity fields, session
cookies, hosting, retention limits and email requests. Its separate, narrowly
scoped web release passed build, candidate and public URL checks at 18:54 UTC.
Terms of service are not included.

Google's [production-readiness guidance](https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification)
describes domain and branding requirements. Basic sign-in does not need access
to users' Gmail, Drive, calendar or contacts.

Create a separate development client if local interactive login is needed:

- Origin: `http://localhost:3000`
- Redirect: `http://localhost:3000/api/auth/google/callback`
- API `ARTLINE_AUTH_ORIGIN`: `http://localhost:3000`
- Use `localhost` consistently; `127.0.0.1` has a different cookie host.

## 3. Store credentials and deploy the prepared code

Keep the client secret and cookie key in Google Secret Manager. Do not paste
secrets into chat, source, Terraform variables or command arguments. The client
ID is public and can be placed in ignored production tfvars.

Create `artline-google-client-secret` in
[Secret Manager](https://console.cloud.google.com/security/secret-manager?project=artline-508319),
containing only the OAuth client secret, not the entire downloaded JSON.
`artline-auth-cookie-key` was generated directly into Secret Manager at 18:46 UTC,
using 48 cryptographically random bytes encoded as URL-safe text. Its enabled
version is `1`; do not replace it during routine setup. The value was passed on
stdin, with no local file, shell argument or tool output containing the key.
Record the OAuth secret's numeric version ID as well. The prepared Terraform
grants read access only to the API runtime identity when sign-in is enabled;
neither secret is passed to Next.js.

Once the domain, owner policy pages and client are ready, configure:

```hcl
enable_custom_domain        = true
site_url                    = "https://artlines.org"
enable_google_signin        = true
google_oauth_client_id      = "THE_REAL_CLIENT_ID.apps.googleusercontent.com"
google_oauth_secret_version = "1" # Use the actual version number.
auth_cookie_key_version     = "1" # Use the actual version number.
```

The current production images already contain the authentication endpoints and
the member migration is recorded as applied. Reuse the verified API image for
credential activation. The privacy page is already deployed from the previous
production source plus exactly three intended page/link changes. Its current
image is pinned in `web_image`; no further web build is needed for credentials.
Recheck both live images and pin them explicitly before reviewing the plan; the
working tfvars may still contain an older API override. For later source releases,
clear or update both image overrides as appropriate.

Review the deployment plan. The API receives:

| API environment | Value |
|---|---|
| `ARTLINE_GOOGLE_CLIENT_ID` | Real client ID |
| `ARTLINE_GOOGLE_CLIENT_SECRET` | Secret Manager reference |
| `ARTLINE_AUTH_COOKIE_KEY` | Secret Manager reference |
| `ARTLINE_AUTH_ORIGIN` | `https://artlines.org` |

The web service receives `ARTLINE_SITE_URL=https://artlines.org` for canonical
URLs, sitemap links and metadata. OAuth redirects use the explicit API origin
above. Keep the existing private API-to-database and web-to-image permissions.

For local setup, copy the values from `apps/server/.env.example` into the ignored
server environment using the existing startup workflow. This change does not
automatically load `.env` in the Go process. Any database-migration verification
must respect AGENTS.md: do not use the real catalogue for test fixtures or create
test databases for this task.

## 4. Acceptance checks before public launch

1. `http://artlines.org/...` and both www variants redirect to the same HTTPS apex
   path and query; certificate validation succeeds on both hosts.
2. Canonical links, robots and sitemap URLs use `https://artlines.org`; review
   records retain their existing visibility and indexing rules.
3. A real Google account completes consent and returns to `/account`. Reloading
   preserves the session; signing out makes the old session unusable.
4. Cancelled consent, missing cookies, invalid state and upstream failures recover
   without issuing a session or displaying raw provider errors.
5. Google login alone cannot write catalogue records or unlock paid features.
6. Authentication endpoints and account pages are not cached. Confirm secrets,
   ID tokens and raw session tokens never appear in application logs.
7. Establish a support/account-deletion process before collecting public accounts.
   Schedule bounded cleanup of expired member sessions (index on `expires_at`);
   login currently removes expired sessions only for the returning member.

## Verification and limits

Local tests cover signed-token rejection, state/nonce/PKCE, origin validation,
cookie flags, session rotation/revocation, unavailable service states and proxy
redirect/cookie handling. PostgreSQL is represented by an in-memory test store;
the migration and SQL writes were not exercised by these local tests. A separate
read-only check confirmed the existing production schema and migration ledger;
it did not exercise account/session writes.
No claim of large-member-load validation is made. Session reads use a primary-key
lookup and a member-ID join, independent of catalogue size.

Passed on 28 September 2026:

- `go test -race ./internal/member ./internal/config ./internal/httpapi`
- API compilation, four web authentication-proxy tests, TypeScript checking and
  ESLint on the changed web code.
- Browser checks at 1440, 390 and 320 pixels: disabled sign-in, enabled sign-in,
  cancelled sign-in and a signed-in account. These browser account states were
  mocked; no real Google session or database account was created. No horizontal
  overflow or JavaScript errors was observed.
- The real local API, started with migrations disabled, returned
  `{"enabled":false,"user":null}`. The account page emits noindex metadata.
- Terraform configuration validation and a refreshed production planning pass.
- The privacy page rendered locally with the confirmed operator/contact and a
  footer link; TypeScript and ESLint passed for the privacy additions. The
  isolated production build, candidate checks and live privacy URL checks also
  passed. This is separate from the earlier account-flow browser checks.

The refreshed domain activation plan was applied: **12 creates, zero updates and
zero deletes**. It contained the Compute API enablement and domain resources
only. Both `enable_custom_domain=true` and `enable_google_signin=true` are now
persisted in production tfvars. Do not reuse the earlier saved plans.

On 30 September, API revision `artline-api-google-0930` activated the credentials
using the existing image. Real Google consent and production account/session
writes were verified with the owner's account, followed by reload and logout
checks. Google reports In production and no required data-access verification.
Custom brand verification remains optional and incomplete; the Google consent
screen currently displays artlines.org. Detailed evidence is in the activation
record linked above. No member-load test was performed.
