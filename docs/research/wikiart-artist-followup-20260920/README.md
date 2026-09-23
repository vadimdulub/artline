# WikiArt artist follow-up — 20 September 2026

Completed in both the local and production catalogues: **2,144 additional image attachments**, including **2,119 new review artwork records** and 25 existing image gaps, across **1,904 artists/source groups**. All 2,119 new records belong to the personal owner collection. No new artist authorities were invented. All preparation, upload, attachment, selection and verification workers finished successfully.

After Google Cloud authentication was renewed, delivery reused the completed local receipts and finished with **zero held attachments in this pass**. Another **23 images from the earlier passes** were linked to their existing production artwork identities. Public file and API verification passed.

## Selection and image delivery

This continuation reuses the completed WikiArt A–Z survey and excludes all 5,110 previously processed source object IDs. It selects one further featured work per reconciled artist, up to three for Russian/Greek/Byzantine priorities. It is a bounded highlight pass, not an exhaustive image crawl. The selection includes 363 priority images, 40 works with object-level creator labels and nine explicitly dated BCE works.

All selected creation dates end by 1955. Explicit ranges, approximations and creator/cultural labels remain intact. New works retain unknown work type and review status, with no invented biography, museum holding or current-display assertion. Personal collection membership is separate from museum designation and does not publish the editorial record.

The JPEGs total **136,576,251 bytes**, with a largest file of **99,994 bytes**. Each uses proportional resizing and compression without cropping or generated content. Source originals remain separately archived. Source labels are 1,691 public-domain labels and 453 copyright-protected labels retained as `restricted`; artwork age was not converted into a licence. All attached images and source links are publicly available through Artline, including images carrying restricted source labels, as explicitly requested by the owner.

Across the three WikiArt passes, **7,254 files have been uploaded**, with **7,253 local image attachments** and **7,219 production attachments**, including the 23 reconciled earlier attachments. Thirty-four earlier local artwork identities still lack a confirmed production match; their uploaded files remain public and their local attachments are preserved. One earlier Crespi source variant remains a duplicate candidate without a second artwork attachment. These counts are recorded in [the completion summary](completed-delivery-summary.json).

## Main collection coverage

A final audit of existing artwork attachments found 133 local and 129 production artworks whose images were available on artist pages but whose records lacked selection evidence for the main atlas. They now belong to the personal owner collection, with their WikiArt source URL, capture date and explicit owner-selection reason. Existing artwork metadata, publication status and museum claims were preserved. The separate new-record selection counts above remain 2,119 per database.

[Collection coverage verification](existing-selection-coverage/verification.json) checked the unchanged artwork records, membership and all 129 production atlas detail responses, including image paths and source links. None of the eligible existing image attachments in the audited scope remains without selection evidence.

## Identity review

Two same-title pairs were visually distinguished and attached: Serebriakova’s *Reclining Nude* compositions and Serov’s portrait studies of P. I. Scherbatova. Symmetric resolutions allow either delivery order while preserving separate source IDs and compositions. Earlier held receipts remain in `title-resolution-history/`.

All 2,144 source IDs and prepared hashes are distinct within this pass. Comparison with earlier passes found two exact image overlaps:

- Altamouras: *Ship on shore* and *Boat at the beach*, both dated 1874, have different WikiArt IDs but the same image. These are probable duplicate source records, not a newly discovered distinct composition.
- *Case din Via Ripetta / Via Ripetta Houses* (1921) appears under both Jean Alexandru Steriadi and Lucian Grigorescu with the same image. This is an unresolved source attribution conflict, not a reason to merge the artists or accept either attribution.

Both supplied source records remain in review. Explicit identity-conflict citations were added to all four affected artwork records in both databases; [production citation verification](cloud-identity-review-delivered.json) passed. Original claims, images and preimages remain preserved in `cross-source-identity-review/` and its history; no publication state was changed. Counts above describe records and image attachments, not a guarantee of distinct compositions.

The current pass also reconciled Gwen John's *A Lady Reading* across different local and production UUIDs using matching artwork metadata, creator and Tate object N03174. The original hold and exact preimages are retained in `target-identity-history/` and `target-identity-resolutions/`. The 23 earlier attachment reconciliations likewise required matching metadata, creators and shared official object URLs; [their database and public API checks](earlier-target-verification.json) passed. No replacement production artwork or invented holding was needed.

## Verification

[Final local verification](verification-local-2144-1789887994.json) passed with zero errors. It checks all 2,144 file hashes and sizes, attachment metadata, recovery preimage hashes, source labels and links, exact artwork state, review status, absence of invented holdings/display claims and personal collection membership.

[Final production verification](verification-2144-1789899020.json) also passed with zero errors: all 2,144 local and public-file SHA-256 checks, both databases' attachment states, all 2,119 new-record owner memberships per database, and public artwork API checks including every object-level creator example.

The final read-only database audit found **zero recorded oversized images and zero unknown byte sizes** among **88,138 registered local images** and **88,018 production images**, with a maximum of 100,000 bytes. Archived original downloads are separate from this delivery limit.

Twenty Python identity/date/source-label tests passed during preparation, and a separate read-only sample checked 12 newly added records. No test database or catalogue test fixture was created. These are correctness checks, not ten-million-row load-test evidence.

## Recovery and retained data

- Selection: `artist-inventory.json`, `discovery-v2/`, `discovered-v2.json`.
- Source captures and image manifests: `profiles/`, `captures/`, `selected/`, `images/`.
- Local and production transaction and selection receipts: `delivery-local/`, `delivery/`, `applied/`, `personal-selection/`.
- Earlier attachment reconciliation: `previous-target-identity-audit.json`, `earlier-target-delivery/`, `earlier-target-verification.json`.
- Existing-record owner selection audit, receipts and public checks: `existing-selection-coverage/`.
- Exact recovery preimages: `/Users/vadimdulub/Library/Application Support/Artline/backups/wikiart-artist-followup-20260920/`.
- Original downloads: `/Users/vadimdulub/Library/Application Support/Artline/source-images/wikiart-artist-followup-20260920/`.
- Served local derivatives: `apps/web/public/assets/artworks/wikiart/`.

Delivery reused completed `applied/local/` receipts, preserving original creation counts and avoiding repeated local writes. Exact artwork, collection and citation preimages were saved before production mutations. The additional reconciliation and collection helpers are archived under the backup directory's `operation-scripts/`; [their manifest](operation-scripts.json) records checksums. Historical progress logs can retain a resolved hold count; the final verification checks the active receipts and both databases and confirms zero current-pass holds.

The entrypoint is `ops/wikiart-artist-followup.py`; the Python environment used is `/tmp/artline-popular-20260917-venv/bin/python` with `PYTHONDONTWRITEBYTECODE=1`. The normal Cloud SQL proxy endpoint is localhost:55433. No frontend/backend deployment, Terraform apply or commit was performed for this continuation.
