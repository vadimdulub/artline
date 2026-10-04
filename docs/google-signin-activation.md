# Enable Google sign-in for Artline

Activated and verified on **30 September 2026** at **https://artlines.org/account**. Google Auth Platform now reports **In production**, with an **External** audience. The anonymous session endpoint returns `{"enabled":true,"user":null}`.

## Live configuration and validation

| Setting | Active value |
| --- | --- |
| Project | `artline-508319` |
| Web OAuth client | `Artline web production` |
| Client ID (public) | `995787188464-0omg2p07c40n3m4i56of59sla9ae7sr1.apps.googleusercontent.com` |
| JavaScript origin | `https://artlines.org` |
| Redirect URI | `https://artlines.org/api/auth/google/callback` |
| Scopes | `openid`, `email`, `profile` only |
| OAuth secret | `artline-google-client-secret`, enabled version `1` |
| Cookie-signing secret | `artline-auth-cookie-key`, enabled version `1` |
| Runtime identity | `artline-runtime@artline-508319.iam.gserviceaccount.com` |
| Serving API revision | `artline-api-google-0930` — 100% of normal traffic |
| Previous API revision | `artline-api-deploy-0928` |

The client secret was transferred directly into Secret Manager. Secret values are absent from this guide and repository configuration. Terraform granted the runtime access to the two individual authentication secrets: two IAM additions, no updates or deletions. The ignored production tfvars now enables sign-in, records the public client ID and pins both secret versions.

Activation reused the existing API image, `europe-west1-docker.pkg.dev/artline-508319/artline/api@sha256:85944159f1559a68fae79445b3b4fed06caa0497d3cb95494db3a74de03d0ee9`. It added only the four authentication environment settings. No application rebuild or web deployment was needed. The Google CLI rejected an existing project-ID secret annotation; the supported Cloud Run v2 PATCH API applied the same prepared change, with an etag conflict check and an explicit field mask. The candidate initially received no normal traffic. Its complete template was compared against the previous configuration before promotion at **16:55 UTC**.

Checks passed on the candidate: API health, enabled anonymous session with no-store, the exact Google client/callback/scopes, PKCE S256, secure HttpOnly host-only OAuth cookie, rejection of missing/foreign/cross-site origins, and invalid callback rejection without a member session. The public session endpoint was then verified.

A real login using `vadim@alingva.com` in the owner's **v-test Chrome profile** completed Google consent and returned to Artline with the correct name and email. Reload preserved the session; sign-out and another reload restored the signed-out view. This exercised production account/session writes for the owner's real account, without inserting test fixtures. The browser was left signed out of Artline. Server-side token revocation is covered by the existing automated tests; this browser check did not export or replay a session token.

Google's Verification centre confirms that data-access verification is **not required** for these scopes. Custom branding remains unverified: the observed Google consent screen identifies the app as **artlines.org**, rather than displaying the configured Artline brand. Search Console domain verification and optional brand verification have not been completed. They do not block the verified basic sign-in flow.

Private deployment snapshots and the activation receipt are under `~/Library/Application Support/Artline/backups/google-auth-20260930/`. To roll back activation, use Cloud Run's **Manage traffic** to route 100% to `artline-api-deploy-0928`; that revision has sign-in disabled. Review the resulting service state and adjust the ignored Terraform settings before a later deployment. Do not reuse saved plans from this activation.

The following sections remain the setup and maintenance runbook; the creation and activation steps above are already complete.

## 1. Open the correct Google project

Open [Google Auth Platform](https://console.cloud.google.com/auth/overview?project=artline-508319) and confirm the project is **artline-508319**.

If the platform is not configured, click **Get started**. Enter `Artline` as the app name, choose the support address, select **External**, and supply the developer contact. If it is already configured, use the Branding and Audience pages to review the existing values. [Google setup instructions](https://developers.google.com/workspace/guides/configure-oauth-consent).

## 2. Complete Branding and domain verification

Use these values in [Branding](https://console.cloud.google.com/auth/branding?project=artline-508319):

| Field | Value |
| --- | --- |
| App name | `Artline` |
| User support email | `vadim@alingva.com`, if available in the selector |
| Developer contact email | `vadim@alingva.com` |
| Application home page | `https://artlines.org` |
| Privacy policy | `https://artlines.org/privacy` |
| Authorized domain | `artlines.org` |

The operator and support address above match the deployed privacy page. If the support address is unavailable, use an eligible address you control or configure the appropriate Google account/group. Leave the optional terms-of-service field empty until a real terms page exists.

If domain ownership has not been verified, open [Google Search Console](https://search.google.com/search-console/welcome), add the **Domain** property `artlines.org`, and copy its TXT verification value. In Cloudflare → artlines.org → DNS, add that exact value as a TXT record at `@`, then return to Google and click Verify. Retain the TXT record. Use an account associated with this Google Cloud project. This does not require changing the existing A records. [Google domain and branding requirements](https://developers.google.com/identity/verification/authentication-verification).

## 3. Set the audience and identity scopes

In [Audience](https://console.cloud.google.com/auth/audience?project=artline-508319), choose **External** so ordinary Google accounts can sign in. You can leave the publishing status at Testing during setup.

In [Data Access](https://console.cloud.google.com/auth/scopes?project=artline-508319), use **Add or remove scopes** and select only:

| Console scope | Requested by Artline as |
| --- | --- |
| `openid` | `openid` |
| `https://www.googleapis.com/auth/userinfo.email` | `email` |
| `https://www.googleapis.com/auth/userinfo.profile` | `profile` |

These match the application. Gmail, Drive, Calendar and Contacts permissions are unnecessary.

Google exempts requests using only these basic identity scopes from its usual testing-user allowlist and seven-day authorization expiry. **Testing is therefore not a private-access gate for Artline.** You may add your account under Test users, but this does not restrict other accounts for this flow. [Google audience rules](https://support.google.com/cloud/answer/15549945?hl=en).

## 4. Create or update the Web application OAuth client

Open [Clients](https://console.cloud.google.com/auth/clients?project=artline-508319). Check for an existing Artline production client first. If none exists, click **Create client**, choose **Web application**, and name it `Artline web production`.

Set the **Authorized redirect URI** to exactly:

```text
https://artlines.org/api/auth/google/callback
```

No trailing slash. This is the web application's callback; the API's internal `/api/v1/auth/...` route is not the browser callback. The current server redirect flow does not require a JavaScript origin. If you populate that field, use `https://artlines.org` with no path.

Save the client. Keep its **Client ID** and **Client secret**. The client ID is a public identifier; store the secret in the next step. Do not paste the secret into chat, source files or Terraform variables. Google requires an exact redirect-URI match. [OAuth client settings](https://support.google.com/cloud/answer/15549257?hl=en), [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect).

## 5. Store the client secret and grant API access

Open [Secret Manager](https://console.cloud.google.com/security/secret-manager?project=artline-508319).

1. Create a secret named `artline-google-client-secret`, or add a new version if it already exists.
2. Paste only the OAuth **Client secret** as its value, not the downloaded JSON document or Client ID.
3. Record its enabled numeric version, for example `1`.
4. Reuse `artline-auth-cookie-key`, enabled version `1`; do not regenerate it for this setup.
5. On each of these two secrets, open **Permissions → Grant access** and grant **Secret Manager Secret Accessor** to:

```text
artline-runtime@artline-508319.iam.gserviceaccount.com
```

Grant this role on the two individual secrets. This is the existing API runtime identity. [Cloud Run secret access](https://docs.cloud.google.com/run/docs/configuring/services/secrets).

## 6. Configure and deploy the API revision

Open [Cloud Run](https://console.cloud.google.com/run?project=artline-508319), select **artline-api** in **europe-west1**, and choose **Edit & deploy new revision** (the UI may show **View diff & redeploy**).

Under the container's variables and secrets, add these two ordinary environment variables:

| Variable | Value |
| --- | --- |
| `ARTLINE_GOOGLE_CLIENT_ID` | Your complete Client ID, ending in `.apps.googleusercontent.com` |
| `ARTLINE_AUTH_ORIGIN` | `https://artlines.org` |

Add these two **secret references**, exposed as environment variables:

| Variable | Secret | Version |
| --- | --- | --- |
| `ARTLINE_GOOGLE_CLIENT_SECRET` | `artline-google-client-secret` | Actual enabled version from step 5 |
| `ARTLINE_AUTH_COOKIE_KEY` | `artline-auth-cookie-key` | `1` |

All four settings must be added together: the API rejects partial configuration. Keep the existing database/editor secret references, image, runtime identity and other settings. Deploy the configuration and route 100% of API traffic to the new ready revision. The currently deployed application already supports this feature; no new source build or web deployment is required. Configuring Cloud Run secrets creates a new revision. [Google's deployment instructions](https://docs.cloud.google.com/run/docs/configuring/services/secrets).

Record the previously serving API revision before deploying so you can restore its traffic if activation fails. The previous revision from this check is `artline-api-deploy-0928`; recheck that value at activation time.

## 7. Test on the canonical domain

Open [the session endpoint](https://artlines.org/api/auth/session) in a fresh private browser window. Before signing in, expect:

```json
{"enabled":true,"user":null}
```

Then open [Your account](https://artlines.org/account):

1. Confirm the Google sign-in button replaces the coming-soon message.
2. Click the button and sign in with your own Google account.
3. Confirm Google returns you to `https://artlines.org/account`, displaying your name and email.
4. Reload and confirm the account stays signed in.
5. Sign out and reload; confirm the signed-out view returns.

This creates a real member account, not an editor account. Begin the flow on `artlines.org`: the cookies are host-only, and the fallback `run.app` domain is a separate host.

## 8. Publish the OAuth app and preserve the configuration

For the public launch, open **Audience → Publish app** to move to production. Follow **Branding / Verification Center** prompts to verify and publish the Artline name/logo. Basic identity scopes do not require sensitive-scope verification; brand verification is a separate process for displaying the app's identity. Google notes that verified branding edits need to be published before appearing to users. [Audience publishing](https://support.google.com/cloud/answer/15549945?hl=en), [brand verification](https://developers.google.com/identity/verification/authentication-verification).

After console activation, synchronize these existing variables in the ignored `terraform/prod/terraform.tfvars` so a future Terraform deployment preserves sign-in:

```hcl
enable_custom_domain       = true
site_url                   = "https://artlines.org"
enable_google_signin       = true
google_oauth_client_id     = "YOUR_ACTUAL_CLIENT_ID.apps.googleusercontent.com"
google_oauth_secret_version = "1" # Replace with the actual numeric version.
auth_cookie_key_version    = "1"
```

Edit the existing assignments instead of adding duplicates. Keep both currently deployed image pins. Secret values do not belong in this file. Review a fresh full Terraform plan before any later apply; the existing `member-auth.tf` configuration already defines these settings and the secret access grants. This guide does not require running Terraform to complete the console activation.

## If something fails

| Symptom | What to check |
| --- | --- |
| `redirect_uri_mismatch` | Client settings contain exactly `https://artlines.org/api/auth/google/callback`; the configured Client ID belongs to that client. |
| Button still says coming soon | The API revision receiving traffic has all four variables; reload `/api/auth/session`. |
| New API revision does not start | Both secret versions are enabled, the API runtime can read them, and all four variables are present. Restore traffic to the previous revision while fixing configuration. |
| “This request must come from Artline” | Open `https://artlines.org/account`; `ARTLINE_AUTH_ORIGIN` must be exactly `https://artlines.org`. |
| Google returns to a sign-in error | Restart from `/account`; verify the client secret/version and cookies. A callback opened directly has no valid login state. |
| `org_internal` | Change Audience to External if public Google accounts should be allowed. |

The earlier [domain and authentication setup record](google-auth-domain-setup.md) contains implementation details and prior deployment evidence.
