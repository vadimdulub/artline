# Resume the pending Artline deliveries

The active Google Cloud account, `vadim@alingva.com`, required interactive reauthentication during the run. Normal token refresh failed. This is the reason later production writes stopped; it was not a deployment failure or a database-content rejection.

Sign in normally:

```sh
gcloud auth login vadim@alingva.com
```

From `/Users/vadimdulub/Documents/vadim-dulub-git/artline`, inspect the ordered work:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/artline-images-venv/bin/python ops/resume-overnight-production.py
```

Then execute the already-authorized, guarded delivery:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/artline-images-venv/bin/python ops/resume-overnight-production.py --execute
```

The existing Cloud SQL proxy must be available on `127.0.0.1:55432`. The connection helper uses this project's configured Terraform state and does not persist or print database credentials. If the proxy or research Python environment is no longer present, restore that local connection setup before running the command. The tool does not change the active account, apply Terraform, deploy code, publish records, or hard-delete assets.

The ordered steps are:

1. Apply the two anonymous-master corrections and Kuznetsov's additional Ukrainian affiliation in production.
2. Consolidate the two Pavia objects, the SMK self-portrait, 184 Finnish placeholders and nine cross-country Finnish objects.
3. Reconcile four painter identities, then their four exact duplicate artwork pairs.
4. Apply 235 Finnish primary metadata updates, then upload and attach 26 Finnish images.
5. Apply the Antwerp panel corrections and missing panel, then upload and attach three images.
6. Fill 222 Russian Museum inventories/materials/dimensions from the reviewed source captures.
7. Run fresh local and production identity plans for all 20 Portuguese research rounds, apply eligible reviewed decisions and verify each round.

Each production plan uses its own current UUIDs and preimages. Duplicate plans must match the individually reviewed local identities and complete primary evidence. Changed relationships, conflicting authority ownership or changed artwork fields stop the affected step. Do not bypass a failed guard or blindly replay an old SQL snapshot. Completed steps have receipts so the workflow can resume after interruption.

After successful delivery, regenerate session membership and both database audits, then export under a **new phase name**. Keep this package as the dated pre-reauthentication snapshot. `session-application-index-final.json` currently records 2,718 local versus 2,717 production inserted rows; it must be refreshed for the newly delivered panel and any Portuguese additions before computing new totals. Preserve its original bytes and hash as evidence before replacing the working index or add an explicit new-index option to the exporter.

The existing local and production preimages are in the dedicated Artline backup directory. The final local recovery dump is described in `FINAL_LOCAL_BACKUP.json`; no restore is part of this resume procedure. Fresh final production verification remains required—the public UUID inventory alone does not establish complete database parity.
