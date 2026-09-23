# Local Artline data

## Russian icon image research — 21 September 2026

The [Russian icon image delivery](research/russian-icon-images-20260921/README.md)
attached 217 selected museum reproductions to existing local review records.
Recovery baselines and exact artwork/relationship preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/russian-icon-images-20260921/`.
Source originals are under the matching
`source-images/russian-icon-images-20260921/originals/` directory. Derivatives
are at most 100,000 bytes and live in
`apps/web/public/assets/artworks/imported/russian-icon-images-20260921/`.
Research captures, selection, visual decisions and verification receipts remain
in `docs/research/russian-icon-images-20260921/`. After the user's explicit upload
instruction, the [production delivery](research/russian-icon-images-20260921/production/README.md)
copied these 217 review artwork records and their evidence to production and
uploaded the matching GCS derivatives. Its exact export, production preflight,
locked recovery snapshot and post-import snapshot are in the backup directory's
`production/` subdirectory. Other image candidates remain local research records.

## General locations

The real database is PostgreSQL `artline` on localhost. Read-only audits query it directly. Never point fixture/destructive integration tests at this database; never create a test database as part of the collection workflow.

Authentic artwork files remain in `apps/web/public/assets/artworks/`, with database media associations and source/rights evidence. Research captures, pinned selections and application receipts are real provenance, not disposable test data.

Larger source-image evidence, when retained separately from the <=100,000-byte
application derivative, belongs under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/`.
The first such archive is `athens-icon-20260912/`: one original photograph and
its capture receipt, both hash-verified after relocation. It is not a test image
or an extra served web asset.

## Backups moved out of Documents

On11 September2026, the22 individually inspected top-level `Documents/artline-…backup…` directories were relocated, not deleted, to:

`/Users/vadimdulub/Library/Application Support/Artline/backups/`

Each original folder name and dump filename is retained. Historical reports retain their original paths for audit: replace the leading `/Users/vadimdulub/Documents/` with the backup root above to find the same dump. The relocation journal contains original/new paths and before/after SHA256 verification:

`output/data-collection-20260911-2016/backup-relocation.jsonl`

Future backups go under this dedicated folder, never scattered at the top of Documents. Keep the pre-mutation safety requirement; these are recovery snapshots, not extra live databases. This relocation does not reclaim disk space, and no backup was deleted.

## First GCP migration backup (12 September 2026)

The PostgreSQL archive used to populate project `artline-508319` is retained at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/gcp-migration-20260912/artline.dump`

SHA256: `1100961ded54f74b8ddda765fc7bdb49b2f098e5c9eabbb8ca0bc475e9a45837`.

The local catalogue and 644 original application images remain in their existing
locations. Cloud Storage contains copies in `gs://artline-508319-images/assets/`.
This initial migration does not establish ongoing replication. See
`docs/deployment-20260912.md` for deployment and migration validation.

## Armenian/Georgian research and Women artists filter (13 September 2026)

Recovery dump, selected original reproductions and the verified completion archive:

`/Users/vadimdulub/Library/Application Support/Artline/backups/armenian-georgian-women-20260913/`

The pre-mutation local dump is `local-before.dump`; the successful Cloud SQL
backup is `1789326954000`. Research, application receipts, image credits and
verification are in `docs/research/armenian-georgian-women-20260913/`.
The completed pass added 271 review artworks, 41 artist profiles and 38 images
to both databases. No existing records, backups or artwork assets were removed.

## Overnight country research (13–14 September 2026)

Recovery dumps and per-change preimages:

`/Users/vadimdulub/Library/Application Support/Artline/backups/overnight-countries-20260913/`

The initial `local-before.dump` and final `local-after-20260914.dump` are retained.
Final dump SHA-256: `7d45f811ebee2d69fc322758916e19c52eeb6e77abdcc9d63503d303ee2e8d24`.
Its archive directory was verified without restoring it or creating a test database.
The successful pre-import Cloud SQL backup is `1789326339640`.

Selected originals are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/overnight-countries-20260913/`;
served derivatives remain in `apps/web/public/assets/artworks/`.

The report, exact receipt membership, CSV package and pending production differences
are documented in [the research index](research/overnight-countries-20260913/README.md).
Later local updates await Cloud reauthentication; this is not a fully synchronized
post-run production backup. Historical facts, archived duplicates and assets were preserved.

### Resumed production delivery — 14 September 2026

The post-delivery local recovery dump is `local-after-resumed-20260914.dump` under the overnight backup directory above (399,013,814 bytes; SHA-256 `e578e736fdd08a69689aa931deb0a41424ef1016dc15df2859bc99e0820adf59`). Its archive directory was validated without a restore. Post-delivery Cloud SQL backup `1789364642427` completed successfully. Both receipts are linked from [the current research index](research/overnight-countries-20260913/README.md); earlier backups and handoffs remain preserved.

## Cypriot painters (14 September 2026)

The pre-import local recovery dump, selected originals and completed research archive are retained under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/cypriot-painters-20260914/`

Cloud SQL backup `1789369991390` completed successfully before import. The bounded pass added 7 painter profiles (6 Cypriot, plus one explicitly active in Cyprus), 36 review artworks and 3 verified images to both databases. See the [research report and verification receipts](research/cypriot-painters-20260914/README.md). No existing catalogue records or artwork assets were deleted.

## Cypriot expansion (14 September 2026)

The next selected pass added 13 artist profiles, 31 review artworks and 19 licensed images to local and production. Recovery dump, selected originals and completed research archive are under:

`/Users/vadimdulub/Library/Application Support/Artline/backups/cypriot-expansion-20260914/`

Cloud SQL backup `1789372089497` completed before delivery. Combined Cyprus coverage is 20 artists, 67 artworks and 22 images. See the [expansion report and verification receipts](research/cypriot-expansion-20260914/README.md), including the preserved date disagreement and superseded image selection.


### Cypriot further expansion — 14 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/cypriot-more-20260914/`.
- Contains validated local pre-import dump, selected image originals (including two rejected Venice views), cloud backup request and completed research archive.
- Cloud SQL pre-import backup: `1789376146123` (successful).
- Evidence and receipts: `docs/research/cypriot-more-20260914/`.
- Delivered to local and production: 7 new artists, 26 artworks, 11 licensed images. Existing Minas and Goul identities reused; all new records remain in review.


### Cypriot and Greek artist portraits — 14 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/cyprus-greece-portraits-20260914/`.
- Validated local pre-import dump, target-specific artist preimages, selected source originals and completed evidence archive.
- Cloud SQL pre-import backup: `1789379855575` (successful).
- Research, coverage inventory, gallery and verification: `docs/research/cyprus-greece-portraits-20260914/`.
- 22 artist portraits stored locally in `apps/web/public/assets/artists/imported/cyprus-greece/` and in GCS `artline-508319-images` under matching asset keys; attached in both databases. Private bucket access preserved; public images delivered through Artline.

### Spanish painters deep expansion — 17 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/spain-deep-20260916/`.
- Contains a validated pre-import local dump, exact preimages for the 74 existing artworks enriched in each target, and the successful pre-import Cloud SQL backup receipt.
- Research, selection, rights review, transaction receipts, post-delivery audit and verification: `docs/research/spain-deep-20260916/`.
- Delivered identically to local and production: 69 new artist profiles, 906 new review artwork records, evidence enrichment for 74 existing artworks, and 79 licensed images. All 79 served image files were checksum-verified; no records were published and no current-display claims were added.

### Spanish paintings image follow-up — 17 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/spain-images-followup-20260917/`; selected source originals are under the corresponding `source-images` directory.
- Cloud SQL pre-attachment backup `1789632648328` completed successfully. The local full dump and exact target preimages were validated before delivery.
- Evidence, visual review, transaction receipts, API smoke checks and public-file verification: `docs/research/spain-images-followup-20260917/`.
- Attached 27 additional licensed images to the same records in local and production. Twelve prepared alternatives were held because an existing primary image was present; no existing media or catalogue metadata was replaced.

### Japanese painters deep expansion — 17 September 2026

- Recovery directory: `/Users/vadimdulub/Library/Application Support/Artline/backups/japan-deep-20260917/`.
- The validated local pre-import dump is `local-before.dump` (SHA-256 `87e0631a01dea092a5cfee744ea7b357639ab6a9ebf421d3f83b2c8465fc2663`). Cloud SQL backup `1789640581717` completed successfully before delivery.
- Research, bounded discovery, authority evidence, visual review, per-record receipts, API smoke checks and public checksum verification: `docs/research/japan-deep-20260917/`.
- Delivered identically to local and production: 19 new named artist profiles, 27 new review paintings, 27 CC0 images, and source enrichment for eight existing Met objects. No records were published and no current-display claims were added.

## Marc Chagall painting additions (19 September 2026)

The verified pre-import archive and exact selected preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/chagall-paintings-20260919/`.
The local catalogue gained 10 sourced review paintings, bringing Chagall’s
painting count to 87. No images, publication or production delivery were included.
See [the selection and verification report](research/chagall-paintings-20260919/README.md).

## WikiArt collection and image-size delivery (19–20 September 2026)

Exact target preimages, migration recovery states and personal collection membership backups are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/wikiart-selected-images-20260919/`
and `.../backups/wikiart-artist-coverage-20260920/`.
Downloaded originals are under the corresponding `.../source-images/` campaign directories.
The follow-on backup directory's `existing-image-size-cap/` subdirectory preserves all 161 original oversized catalogue images and their database preimages.

Reports and delivery receipts: [initial selected images](research/wikiart-selected-images-20260919/README.md) and [artist-first expansion](research/wikiart-artist-coverage-20260920/README.md).
Served derivatives are at most 100,000 bytes; the separate original archives are not subject to that delivery limit.

The [next artist follow-up](research/wikiart-artist-followup-20260920/README.md) added 2,144 image attachments and 2,119 artwork records in both local and production catalogues after Google Cloud authentication was renewed. It also reconciled 23 earlier production image attachments and added owner-collection membership for 133 existing local and 129 existing production artworks. Its exact preimages and originals use the corresponding `wikiart-artist-followup-20260920` directories under `backups/` and `source-images/`, including `earlier-target-reconciliation/`, `existing-selection-coverage/` and archived `operation-scripts/`. Public-file, database and collection API verification passed; all three WikiArt passes now total 7,219 production image attachments.

## Frida Kahlo and women artists — 20 September 2026

Exact recovery preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/women-wikiart-20260920/`;
source originals use the corresponding `source-images/women-wikiart-20260920/`
directory. Research evidence and the complete 682-artist CSV are in
[the women-artists report](research/women-wikiart-20260920/README.md).

Delivered to both databases: 1,555 image attachments, including 1,534 new review
artworks and 21 existing-record image gaps, across 189 artists. Added 147 sourced
women-filter memberships and 275 artist review citations. Frida now has ten
illustrated works. All 1,556 uploaded files passed public checksum verification;
one duplicate reproduction remains unattached and its extra source identifier
is linked to the existing artwork. Artist metadata, review states, original
assets and prior provenance remain preserved.

## Armenian painter expansion — 20 September 2026

The [verified catalogue report](research/armenian-painters-20260920/README.md)
records 505 new active artist profiles, 1,027 new artwork records and 134 new
image attachments in both local and production databases. The collection now
contains 559 active Armenian-linked profiles and 1,485 linked artwork records.
All 137 uploaded image files are at most 100,000 bytes, including three public
alternate views that did not create additional artwork records.

Exact preimages, source-identity corrections, collection recovery states and
final operation scripts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/armenian-painters-20260920/`.
WikiArt originals use the matching `source-images/armenian-painters-20260920/`
directory; Commons originals are in the backup directory's
`museum-images/selected-originals/` subdirectory. Captures, per-record receipts,
full painter/artwork lists and successful final verification remain in the
research directory. New records retain review status and unknown fields.

## Byzantine and Russian icons and frescoes — 20 September 2026

The [verified research report](research/byzantine-russian-icons-frescoes-20260920/README.md)
records 804 new local review artworks: 777 icons and 27 fresco records, including
seven ensembles. Eight selected CC0 images are attached; 18 existing records
were preserved. This pass did not change production or publication state.

The validated 589,142,267-byte pre-import dump and exact batch, image and
date-correction preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/byzantine-russian-icons-frescoes-20260920/`.
Nine source originals are under the corresponding
`source-images/byzantine-russian-icons-frescoes-20260920/originals/` directory.
Eight approved application images and one retained, unattached panel view are
in `apps/web/public/assets/artworks/imported/byzantine-russian-20260920/`;
all nine derivatives are at most 100,000 bytes.

The [follow-up expansion](research/byzantine-russian-more-20260920/README.md)
added another 727 local review artworks: 616 icons and 111 fresco records,
with 23 verified CC0 image attachments. Across these two passes, the exact
receipts total 1,531 new works and 31 image attachments. Both passes remain
local and unpublished.

The follow-up's validated 620,943,496-byte pre-import dump and exact batch/image
preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/byzantine-russian-more-20260920/`.
Its 23 source originals use the corresponding
`source-images/byzantine-russian-more-20260920/originals/` directory.
Application JPEGs are in
`apps/web/public/assets/artworks/imported/byzantine-russian-more-20260920/`;
each is at most 99,579 bytes. The research directory retains the full selection,
all eight successful batch receipts, visual review and final verification.


## WikiArt 1000–1500 review — 20 September 2026

The [period review](research/wikiart-1000-1500-20260920/README.md) audited all
501 years and 1,175 dated WikiArt highlights across 100 creator/tradition
profiles. It added 450 review artworks with images to both databases, including
63 works dated wholly before 1300. All 451 delivered or already-attached image
associations passed public-file, database and provenance verification; the
largest derivative is 99,976 bytes. Nineteen prepared candidates remain held.

Exact preimages, five creator-kind corrections, operation scripts and visual
review evidence are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/wikiart-1000-1500-20260920/`.
Source originals use the corresponding
`source-images/wikiart-1000-1500-20260920/` directory. Research receipts include
the complete year-by-year audit, delivered artwork list and concurrent changes
outside this campaign. New records remain in review and belong to the personal
owner collection, without invented museum holdings.

## Top 100 painter expansion — 20 September 2026

The [complete cohort review](research/wikiart-top100-20260920/README.md)
audited all 100 selected painters and 29,628 WikiArt index entries. It added
1,037 review artworks and 1,093 image attachments to both local and production
databases, filling 56 existing image gaps across 97 painters. All uploaded
images passed public checksum verification and are at most 99,953 bytes.
Sixty-three prepared candidates remain held for duplicate or identity review.

Exact target preimages, thirteen existing production-ID reconciliations,
personal collection snapshots, visual review evidence and operation scripts
are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/wikiart-top100-20260920/`.
Source originals use the corresponding
`source-images/wikiart-top100-20260920/` directory. The research directory
contains the full 100-painter audit, delivered artwork list, source captures
and verification receipts. The Top 100 membership and ranking were preserved.

## Cyprus painter images — 20 September 2026

The [Cyprus coverage review](research/cyprus-images-20260920/README.md)
audited all 27 existing Cyprus-linked painters and delivered 57 image
attachments to both local and production databases: 22 existing image gaps
and 35 new review artworks across nine painters. The cohort now contains
128 artworks and 90 images. All 57 public image checksums and artwork API
responses passed verification; the largest derivative is 99,850 bytes.

Exact artwork/media preimages, personal collection snapshots, visual review
evidence, operation scripts and completion receipts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/cyprus-images-20260920/`.
Source originals use the corresponding
`source-images/cyprus-images-20260920/` directory. Application derivatives
are in `apps/web/public/assets/artworks/imported/cyprus-images-20260920/`.

One prepared attribution/title candidate remains unattached, with its original
and evidence preserved. The research report lists all 38 remaining image gaps:
26 later works, 11 unresolved dates and one missing exact-object photograph.
New records remain in review; source restrictions and credits were preserved
under the user's explicit Cyprus museum/artist source policy extension.

## Greek painter images — 20–21 September 2026

The [Greek coverage review](research/greek-images-20260920/README.md) audited
all 43 existing Greek-linked painter profiles and delivered 242 image
attachments to local and production: 93 existing image gaps and 149 new
review artworks across 41 profiles. Both catalogues now contain 609 artworks
and 444 images in this cohort. All 242 public image checksums and artwork API
responses passed verification; the largest derivative is 99,965 bytes.

Exact preimages, personal collection snapshots, five reconciled target-ID
mappings, visual review, operation scripts and completion receipts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/greek-images-20260920/`.
Original reproductions use the corresponding
`source-images/greek-images-20260920/` directory. Application derivatives are
in `apps/web/public/assets/artworks/imported/greek-images-20260920/`.

The research directory preserves source captures, per-painter coverage and
all 165 remaining image gaps: 106 unresolved dates, 10 works after the 1955
image cutoff, and 49 dated works needing source access or identity review.
Thirty-eight selected candidates remain held; one staged reproduction remains
unattached after its qualified creator attribution was identified. No existing
records or assets were removed. Actual rights labels and photographer credits
were retained, and 15 sourced icons use the existing object-form field.


## UK painters and selected artworks — 20–21 September 2026

The [UK coverage report](research/uk-painters-20260920/README.md) surveyed
10,514 source painter identities and resolved 327 named painters in WikiArt’s
British directory. This pass added 8,545 painter profiles, 18,882 artwork
records and 9,217 image attachments to both local and live catalogues.
All 9,284 uploaded files are public and at most 100,000 bytes; the largest
is 99,999 bytes. New records retain review status and unknown source fields.
The research directory includes full painter/artwork indexes, public alternate
links and unresolved identity/date decisions.

Artist/artwork preimages, selected Commons originals, six namesake correction
snapshots, receipt chains and archived operation scripts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/uk-painters-20260920/`.
Original WikiArt downloads are under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/uk-painters-20260920/`.
Earlier artist baselines preserve alias text, not full alias-table row IDs.
Corrections preserve older artist records and their artworks; eight newly
created artworks retain their images on the corrected artist identities.

Final verification completed with zero errors across both databases, source
identities, review states, collection membership, image hashes and public APIs.
Forty-seven offline tests passed. No test databases or fixtures, commits,
Terraform changes or deployments were made for this pass.


UK production synchronization follow-up (21 September 2026): all 9,284 batch images were already present and matched their checksums. Added 37 missing personal-collection links in production. Recovery snapshots are under the UK backup root at `production-sync/collection-memberships/`; the production synchronization receipt is retained in the [UK research directory](research/uk-painters-20260920/README.md).

## Book languages and context — 22 September 2026

The [language audit](research/book-languages-20260922/README.md) covers all
10,000 existing books and records 170 confirmed corrections in local and
production, including 98 previously empty values. Exact baseline and transaction
preimages are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/book-languages-20260922/`.

The [book and author context pass](research/book-context-20260922/README.md)
adds attributed Wikipedia introductions to 9,594 books and 3,782 creators.
Before/after checks preserve the language corrections, dates, creator links,
discovery memberships and review states. Full catalogue preimages, private
Cloud Run configuration snapshots, exact isolated release sources and build
receipts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/book-context-20260922/`.
Retained research responses and decisions remain in the two research directories.
Disposable browser screenshots and test outputs remain under `/tmp/`.
