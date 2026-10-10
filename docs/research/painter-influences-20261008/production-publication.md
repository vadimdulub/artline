# Approved production publication — 8 October 2026

**Follow-up completed:** after being told about the painter-profile visibility barrier, the user explicitly instructed “push them I aprrove evertyhing”. The [painter publication](production-painter-publication.md) published the remaining 3,723 linked profiles. All 6,379 approved relationships now pass the public visibility rules. The 22-visible/6,357-blocked figures below describe the earlier claim-only publication and are retained as history.

The user explicitly approved the imported relationship records with “just push them I appove them”. The publication transaction committed at **2026-10-08 18:35:05 UTC**. All **6,379** approved claims now have `published` status: **2,192 artistic influences, 4,179 teaching relationships and 8 documented-admiration relationships**.

Every claim retained its identity, relationship type, evidence note, evidence level and confidence. All **7,427 citations** were preserved exactly, including source qualifications and the historical import provenance. Publication approval is recorded here separately from the source evidence and does not upgrade the quality of historical verification. The 10 previously published claims and their citations were unchanged. All 3,745 referenced painter rows, their identifiers and the source registry were preserved.

**Public visibility:** the existing API requires both linked painter profiles to be published (or an unlinked source label). **22** approved relationships meet this condition. Read-only requests to all **12** affected target-painter API endpoints returned those 22 claim IDs with their expected relationship type, evidence level, evidence note and citations. The remaining **6,357** approved claims are published in the database but await publication of one or both linked painter profiles. Painter biographies and metadata were outside this relationship-publication change and retain their existing review states.

Only `status`, `updated_by` and `updated_at` changed on the exact claim IDs pinned by the original import plan. Before writing, fresh production preimages were backed up at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/painter-influences-20261008/production-publication-v1-before.json.gz`

Backup SHA-256: `934e604c19d4a4aa742879c46628c6804b24ca28b6c5fecc8d353c53cfd7d091`.

The [immutable publication plan](production-publication-v1.json.gz) has SHA-256 `23b336a22ffda7926ad4c4298892ab8851c03c85a09e51e87d818e648ab87e30`. It pins the publisher, original import plan, fresh backup, exact claim IDs and scope of approval. The original import plan and receipts remain unchanged.

The [publisher](../../../ops/publish-painter-influences-20261008.py) checked exact preimages under write-protecting locks, published the records in one transaction, and verified all changes before commit. Each of the 6,379 transitions has an audit record. The existing invalidation trigger advanced the catalogue cache revision from **832 to 833**. A fresh read-only database transaction verified every publication transition and all protected content; separate public HTTP requests verified the 22 currently visible relationships.

Verification records:

- [Commit receipt](production-publication-v1-applied.json).
- [Fresh database readback](production-publication-v1-verified.json).
- [Live public API verification](production-publication-v1-api-verified.json).

The transition checker also passed a valid-transition check and rejected six unsafe cases: confidence changes, evidence-note changes, changed source identity, updates to an unapproved claim, removed claims and claims left in review. This claim-only operation performed no application deployment, schema changes, painter publication, local-database writes or artwork changes. Its verifier checks the original painter preimages, so after the separately approved painter publication use `ops/publish-influence-painters-20261008.py verify` for the final state instead.
