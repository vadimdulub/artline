# Artline production infrastructure

Production project: `artline-508319`; region: `europe-west1`.
Public domain: https://artlines.org; www redirects to the HTTPS apex.
The Cloud Run HTTPS `run.app` URL remains available.

The optional `enable_custom_domain` configuration prepares HTTPS for
`artlines.org` and `www.artlines.org`. Optional `enable_google_signin` wires
member credentials from Secret Manager into the API. Both default to disabled;
production tfvars enables both the domain and Google sign-in as of 30 September 2026.
See [the setup and rollout guide](../../docs/google-auth-domain-setup.md) for
DNS, OAuth console values and costs, and [the activation record](../../docs/google-signin-activation.md)
for the live OAuth client, verified API revision and rollback details.

## Resources

- Cloud SQL PostgreSQL 17 Enterprise, with daily backups, point-in-time recovery,
  disk autoresize and deletion protection. The initial `db-f1-micro` tier is a
  starting configuration, not evidence of capacity for 10 million artworks.
- Separate Cloud Run API and web services, scaling from zero to three instances.
- Secret Manager stores the database URL, editor token, Google OAuth client secret
  and member cookie-signing key. Only the API runtime
  can read these secrets and connect to Cloud SQL.
- All artwork images are stored in the private, versioned
  `artline-508319-images` bucket. The web runtime has object-reader access.
  `/assets/artworks/...` and `/assets/artists/...` stream image objects through
  the web service, preserving database paths and local development behavior.
  Production build uploads exclude the image files and `.env` files.
- A dedicated build account can read the build-source bucket, push containers
  to the Artline Artifact Registry repository and write build logs.
- Private Terraform state is versioned in `artline-508319-terraform-state` at
  `artline/prod`. This bucket was bootstrapped separately so the stack cannot
  destroy its own state. Protect state and saved plans: they contain secrets.

The organisation restricts IAM membership, so public `allUsers` grants are not
used. Cloud Run uses `invoker_iam_disabled = true`, Google's supported public
access setting for domain-restricted projects. Image storage enforces public
access prevention; Cloud Run serves image bytes using its runtime identity.
No organisation policies were changed.

## Operate from this repository

The wrapper uses the active `gcloud` login without persisting an OAuth token:

```sh
sh ops/terraform_gcloud.sh init
sh ops/terraform_gcloud.sh plan -out=/tmp/artline.tfplan
sh ops/terraform_gcloud.sh apply /tmp/artline.tfplan
sh ops/terraform_gcloud.sh output
```

`terraform/prod/terraform.tfvars` holds the project, region, unique image tag and
random editor token. It is ignored by Git. The provider lockfile pins the
validated provider versions. An apply or deployment still requires an explicit
user request under the repository's AGENTS.md.

To build a new release, choose a fresh image tag, then:

```sh
sh ops/build_and_push.sh artline-508319 europe-west1 <unique-image-tag>
```

Set that tag in `terraform.tfvars`, and update or clear any `api_image` and
`web_image` overrides: a pinned image takes precedence over `image_tag` for its
service. Review the full saved plan, and apply it.
Build configurations use a dedicated service account and Cloud Logging. Both
images must exist before Cloud Run can create their revisions.

## Data and editorial access

The first migration restores a `pg_dump` custom archive into an empty cloud
database before starting the API, which runs schema migrations on startup.
The restore uses `--no-owner --no-acl --exit-on-error --single-transaction`.
Never restore over an existing catalogue without a separately reviewed plan.
Never use the real local or cloud database for fixtures or destructive tests.

The local database and local pictures are retained. This is a point-in-time
migration, not ongoing replication. Later local edits or new pictures require
an explicit subsequent migration; do not rerun the initial restore.

Catalogue browsing now includes every non-archived record. Historical status
values remain audit data and no longer restrict reads. The
`public_research_preview` option and its runtime environment settings have been
removed; member authentication and local-debug safeguards are unchanged. The
web service does not forward an editor credential to catalogue reads.
See [the unified catalogue change](../../docs/unified-catalogue.md).

Migration receipts and validation are recorded in `docs/deployment-20260912.md`.

References: [Cloud Run public access](https://docs.cloud.google.com/run/docs/authenticating/public),
[Cloud SQL restores](https://docs.cloud.google.com/sql/docs/postgres/import-export/import-export-dmp),
[Cloud Build accounts](https://docs.cloud.google.com/build/docs/securing-builds/configure-user-specified-service-accounts).
