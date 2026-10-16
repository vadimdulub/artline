# Batch 35 — National Museum Oslo primary images

Verified **six newly illustrated existing artworks**. No painters, artworks,
alternate images or museum links were added. The six images were individually
viewed using the image-viewing tool; originals were decoded and hash-checked,
but were not separately visually inspected. Served derivatives preserve the
complete supplied composition and are each at most 100,000 bytes.

The original 111-source registry, required policy files, previous checkpoint,
source queue and access holds were reconciled. Taiwan's open-data terms request
returned HTTP 403; no alternate-client retry or image request followed. Its 38
existing primary-image gaps all have unknown catalogue creation dates and need
source-specific date review when permitted access returns.

Institution reconciliation located the Norwegian native-object queue under
**National Museum, Oslo**, separate from a legacy institution record with four
already illustrated artworks. The main institution had 1,227 dated image gaps.
Twelve candidates were inspected: nine native pages succeeded, six images were
selected and delivered, two were held for object-specific copyright restrictions,
three need the recorded canonical underscore-URL correction, and one needs a
separate native identifier/title crosswalk. Neither institution record changed.

The selected first native photographs have no object copyright restriction.
The museum's current policy grants CC BY 4.0 reuse for this category. Photographer,
artist, original source title, museum, licence link and resizing notice were
preserved. Historical native export records, current inventories, creators,
dates and physical dimensions agree; translated titles retain their evidence.
No current-display assertion was made.

Production target `artline-508319:europe-west1:artline-postgres` was checked before
storage and database writes. The established helper used the shared
`artline-curated-ingestion` lock, create-only storage, an existing successful
Cloud SQL recovery backup, transaction preimages and audit history. Original
images and transaction backups are outside Documents. The real local catalogue
was never connected to.

[Independent verification](batch-verification-receipt.json) establishes all six
increments from null-primary transaction preimages, matching audit events and
persisted source/selection/review checksums. Each storage object and public image
was hash-verified, and all six public artwork API responses expose the attachment.
[An actual delivery rerun](independent-resume-verification.json) produced no
new rows or duplicate attachments. Existing artwork metadata, statuses, creators,
holdings, and all six held objects were preserved.

[Checkpoint](CHECKPOINT.json), [source queue verification](source-queue-update-verification.json)
and [milestone report](milestone-report.json) are persisted. The measured batch
runtime at checkpoint was 617.65 seconds; cumulative programme increments became
102 artworks, 315 newly illustrated artworks and 102 museum links. These are
programme increments, not a whole-catalogue census. The external supervisor owns
subsequent execution and reporting; its prompt, schema and LaunchAgent were not
modified, and no additional worker or schedule was launched.

Next: a bounded Te Papa primary-image gap review, with record-specific reusable
image rights and permitted access. Norway's remaining cursor and three URL
corrections remain in the source queue; all provider holds remain effective.

Resume using `/tmp/artline-cyprus-venv/bin/python`:

- `ops/continuous-norway-images-000035.py deliver` reconciles and safely resumes
  this exact selection.
- `ops/continuous-norway-images-000035-verify.py` independently rechecks delivery.
- `ops/continuous-norway-000035-finalize.py` records the checkpoint and queue update.

Completed 300,000-image campaign stop files remain unchanged. This batch uses
the separate `continuous-primary-images-20261011-b000035` campaign.
