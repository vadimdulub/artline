# Artline production infrastructure

Production project: `artline-508319`; region: `europe-west1`.
No domain is required: the web service uses its HTTPS `run.app` URL.

## Resources

- Cloud SQL PostgreSQL 17 Enterprise, with daily backups, point-in-time recovery,
  disk autoresize and deletion protection. The initial `db-f1-micro` tier is a
  starting configuration, not evidence of capacity for 10 million artworks.
- Separate Cloud Run API and web services, scaling from zero to three instances.
- Secret Manager stores the database URL and editor token. Only the API runtime
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

Set that tag in `terraform.tfvars`, review the full saved plan, and apply it.
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

Review records remain in review. `public_research_preview = true` is enabled
for this deployment, allowing anonymous browsing of non-archived research records
in the timeline, painter pages and museums. The Go API owns this visibility
decision; the web service renders the research labels. Public preview does not
grant editor privileges or give the web runtime an editor secret. Set the
Terraform flag to `false` to restore published-only browsing. Open `/catalogue`
and provide the editor token for editorial operations.
To retrieve the token privately on your own terminal:

```sh
gcloud secrets versions access latest --secret=artline-editor-token --project=artline-508319
```

Do not paste the token into tickets, logs, or source files. Editing still requires
API bearer authentication; deploying never publishes review records.

Migration receipts and validation are recorded in `docs/deployment-20260912.md`.

References: [Cloud Run public access](https://docs.cloud.google.com/run/docs/authenticating/public),
[Cloud SQL restores](https://docs.cloud.google.com/sql/docs/postgres/import-export/import-export-dmp),
[Cloud Build accounts](https://docs.cloud.google.com/build/docs/securing-builds/configure-user-specified-service-accounts).
