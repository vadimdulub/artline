# artlines.org activation — 28 September 2026

The owner requested connection of artlines.org and supplied a Cloudflare API
token. The token verified as active, accessed the artlines.org zone and created
the two records below. It was held in process memory, not saved in repository
files, shell arguments or configuration; the credential-handling process has
exited. No token value is included in this record.

Status: **live at https://artlines.org**. Both hostnames have valid HTTPS;
HTTP and www redirect to the HTTPS apex. The web canonical-origin revision
serves 100% of normal traffic, with the subsequent privacy release described
below. Final public checks passed again at 18:54 UTC.

## DNS

The zone had zero DNS records before this change. Nameservers remain
`amos.ns.cloudflare.com` and `teresa.ns.cloudflare.com`.

| Name | Type | Address | Proxy | TTL |
|---|---|---|---|---|
| `artlines.org` | A | `136.110.174.158` | DNS only | Auto |
| `www.artlines.org` | A | `136.110.174.158` | DNS only | Auto |

The two writes succeeded and a subsequent Cloudflare read returned exactly
these two records. Public resolvers `1.1.1.1` and `8.8.8.8` returned the address
for both names; the local resolver's earlier negative cache has also cleared.
There were no existing mail, verification or other records to modify.

## Google Cloud

Project `artline-508319`; Cloud Run region `europe-west1`.

The reviewed domain-only Terraform plan contained 12 creates, zero updates and
zero deletes. It enabled Compute Engine and provisioned the static IPv4,
serverless network endpoint group, backend service, managed TLS certificate,
TLS policy, HTTP/HTTPS URL maps, target proxies and forwarding rules.

The intended request path is Cloudflare DNS → global external Application Load
Balancer → existing `artline-web` service → existing API. The HTTPS URL map sends
the apex domain to the web backend and redirects www to the apex. The HTTP URL
map redirects to HTTPS at the apex. Redirects preserve paths and query strings.
TLS 1.2 is the minimum version, and Cloud CDN is disabled.

The infrastructure adds approximately US$18.25/month in base forwarding-rule
charges at the currently documented US$0.025/hour, plus traffic charges. It
does not change the existing Cloud Run, SQL or storage capacity settings.

## Web configuration

The domain revision `artline-web-domain-0928` was promoted at 18:51 UTC after
validation at zero normal traffic. It used the previous live web image:

`europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:057552791a18d14dcf3b7fac177599ae6be8ded43c323f8985ddff47be84273d`

The sole intended application setting change is
`ARTLINE_SITE_URL=https://artlines.org`. The candidate's `/about`, `/robots.txt`
and `/sitemap.xml` all returned 200 and used the new canonical origin. No source
image build, API deployment, catalogue change or database migration was needed.
Google member authentication remains a separate pending activation.

The subsequent live revision is **`artline-web-privacy-0928`**, serving 100% of
normal traffic from 18:54 UTC. Build `ef1006c0-53c6-42a7-8c7f-1b0bb680c8c2`
used the exact source archive of the previous production image, with only three
changed files: `app/privacy/page.tsx`, `app/layout.tsx` and
`components/MemberAccount.tsx`. It adds the privacy page and footer/sign-in links.
The operator and contact were explicitly confirmed as Vadim Dulub and
vadim@alingva.com. The current immutable image is:

`europe-west1-docker.pkg.dev/artline-508319/artline/web@sha256:87b101ebf9189a3dae6cd9413be352a645dee42eae574d4028812ae69523c23c`

Candidate and live HTTP checks passed. `/privacy` returns 200, includes the
confirmed contact details and uses `https://artlines.org/privacy` as its
canonical URL. The API and database configuration were unchanged. The
`web_image` pin in ignored tfvars was advanced to this verified image.

The existing image already serves `/account` (200), and `/api/auth/session`
returns `{"enabled":false,"user":null}`. The Google OAuth client secret is still
missing. At 18:46 UTC the random session-signing key was created directly in
Secret Manager as `artline-auth-cookie-key`, enabled version `1`. This did not
enable sign-in or change API configuration. A separate read-only production
schema check at 18:29 UTC confirmed
`0032_member_accounts.sql` in the migration ledger, both member tables, expected
columns and indexes. No account data was read or written, and no real Google
login has been verified.

`enable_custom_domain=true` and `site_url="https://artlines.org"` are persisted
in ignored production tfvars. A new
optional `web_image` variable pins the actual deployed immutable web image so
the domain configuration does not revert to an older shared `image_tag`.
Future web releases must update this pin or explicitly clear it.

## Verification and rollback

Eight public HTTPS, redirect and canonical-origin checks passed using ordinary
DNS resolution and certificate validation. Root, About, robots, the sitemap
index and page sitemap returned 200. HTTP apex, HTTP www and HTTPS www returned
301 redirects preserving paths and query strings. Root/About canonical links
and robots/sitemaps use `https://artlines.org`. Terraform formatting/validation
passed, and the live web image/settings comparison confirmed only the intended
site URL change.

Read the current certificate status without changing configuration:

```sh
gcloud compute ssl-certificates describe artline-web-certificate \
  --global --project=artline-508319 \
  --format='yaml(managed.status,managed.domainStatus,expireTime)'
```

Certificate provisioning began at 18:01:48 UTC; both DNS records were created
by 18:02:42 UTC. Google documents that issuance can take up to 60 minutes after
DNS and load-balancer propagation, and DNS caches can delay validation.
[Managed certificate guidance](https://docs.cloud.google.com/load-balancing/docs/ssl-certificates/google-managed-certs).

At 18:40 UTC both certificate domain statuses changed to `FAILED_NOT_VISIBLE`,
while the managed status remained `PROVISIONING`. A fresh check of both
authoritative nameservers, Cloudflare and Google public DNS returned the assigned
IPv4 for both hosts. No AAAA records, CAA restrictions or DNSSEC failures were
found. The HTTPS forwarding rule uses port 443, and its target proxy references
the correct certificate with no overriding certificate map. Google continues to
retry this state; it is not `PROVISIONING_FAILED_PERMANENTLY`.
[Certificate troubleshooting](https://docs.cloud.google.com/load-balancing/docs/ssl-certificates/troubleshooting).

Both domain validations recovered at 18:48 UTC without configuration changes.
The certificate became ACTIVE at 18:48:31 UTC and valid HTTPS responses were
verified at 18:50:40 UTC. Google manages renewal; keep both DNS records pointing
directly to the load balancer.

To roll back only the privacy release, restore traffic and the web image pin to
`artline-web-domain-0928`. The pre-domain revision is
`artline-web-deploy-0928`. If the canonical configuration needs rollback, restore
its traffic without changing the API or database, and restore the previous
`site_url` in ignored tfvars. Keep the domain
resources and DNS while investigating unless domain removal is explicitly
requested. Setting `enable_custom_domain=false` proposes infrastructure removal.

Private pre-change service configuration and candidate details are stored at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/domain-20260928/`

Disposable plans and test outputs are under `/tmp/artline-domain-*`.
No commit was made. Google OAuth was subsequently activated on 30 September;
see [the activation record](google-signin-activation.md). Statements above about
disabled sign-in describe the domain rollout on 28 September.
