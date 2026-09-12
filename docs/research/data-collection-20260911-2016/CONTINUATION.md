# Exact collection-first continuation

## Latest priority — image-first, 12 September 2026

Owner requested authentic images after the manual CSV export. Completed a new
12-image SMK batch (Købke, Michael Ancher, Hammershøi). Live totals now **106350
artworks / 656 pictures**. See `docs/research/image-focus-20260912/README.md` for
per-item checklists, backup, immutable selection, verification and precise queue.
All twelve <=100000-byte files are attached and locally served/hash-verified;
existing editorial metadata/media preserved. Do not replay them as new downloads.
Next rotate to the pending Michael/Marina Athens icon images, which are captured
metadata leads only. The metadata-first import candidates remain unimported.
The owner's CSV is deliberately preserved as its earlier 644-picture snapshot.

## Metadata-first research checkpoint — 12 September 2026, 10:52 UTC

The latest request shifted to source-backed CSV research with images secondary.
See `docs/research/metadata-first-20260912/README.md` for two completed staging
exports: 20 artwork records / 10 unique painter names / six institutions.
These are NOT DB additions: two existing records, 18 further candidates pending
full reconciliation and import conversion. Live DB remains 106350 artworks,
5328 artists and 644 media; no mutations, downloads, commits or publication.
Six unresolved deferred candidates remain after the Theocharakis metadata lead
was resolved in the follow-up. Approximate date mapping and rights remain open.

The prior Michael/Marina image work stopped after Commons API metadata captures
in `content/imports/data-collection-20260912/athens-followup/`; no images attached
from those captures. Preserve them and their Go capture mode. Do not confuse
source capture, staging export or successful name matching with an import.
Resume the metadata report's exact queue before the older image-first queue.

## Latest checkpoint — 12 September 2026, after final audits

Live totals **106350 artworks / 644 attached images**. Latest follow-up completed
four Karlsruhe paintings/images plus one image on an existing Athens icon.
Collection-first cumulative additions: 11 artworks / 12 images. Do not replay
the Karlsruhe-next metadata/image applications or Athens icon image application.
No active-time claim includes the overnight gap.

Use final `library-audit-v3` and `receipt-audit-v3`, not older snapshots. All 644
image files fully decode/hash-match, no unlinked artwork raster files. Eligible
gaps: 105705 all types, including 14751 paintings. Legacy 161 oversized files and
15 missing structured rights records are preserved and separately deferred.

206 metadata receipts, 107745 exact source/row assertions, 106189 distinct works,
zero failures. Eleven of 161 outside-format works traced to real migrations;
see LEGACY_RECONCILIATION.md. Remaining 150 still need other-format reconciliation.

Next queue, in order:

1. Use the v3 missing-image JSONL and prior checklists; do not repeat blocked or
   rights-deferred searches. Rotate away from Karlsruhe to another permitted
   European/regional museum, maintaining Greek/Russian/icon coverage.
2. Athens icon BXM 01354 front is DONE. Reverse is a separately licensed lead,
   not a second artwork. Read athens-icons.md before work: Commons BXM 01544
   collision with Damaskinos must never be used to attach the wrong picture.
   Hospitality's matching museum-derived photo is rights-deferred; Nativity
   BXM 01099 has no verified candidate from the exact-accession search yet.
3. Karlsruhe Cranach accession 2749 is still a source lead;
   Boucher 479/480, Pissarro 2488 and Rubens 2759 are now DONE for this batch.
4. Reconcile the remaining 150 legacy/other-format receipts without deleting or
   duplicating records; actual source searches remain separate from inventory.
5. After collection, audit Monet's real right-panel visibility: still 300 records
   and 32 images. Do not publish review data or weaken access control as a fix.

Exact new receipts are `karlsruhe-next-*` and `athens-icon-*` under this session's
output directory. Applied metadata selection: `karlsruhe-next-v2`; image selection
pins are in PROGRESS.md / athens-icons.md. All new served images <=100000 bytes.
The larger original Athens photo and receipt were preserved under
`/Users/vadimdulub/Library/Application Support/Artline/source-images/athens-icon-20260912/`,
not under Documents. Do not rerun its source-photo capture; it was already reviewed.

Read the older checkpoint below only as historical context; the latest totals,
completed work and next queue above supersede it.

Read `AGENTS.md`, `docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md`, `docs/LOCAL_DATA_LOCATIONS.md` and this directory's PROGRESS.md. User says collect verified data and pictures first; design/UI work is later. No commit/push/publish/deploy/Terraform. No test databases/fixtures in real catalogue.

## Completed — do not replay

Live baseline after first collection batch:106346artworks/639images. Karlsruhe7metadata+7images all applied/verified. Per-painter checklists in this directory. Receipts `output/data-collection-20260911-2016/karlsruhe-*`. All7 full compositions visually inspected,23 image API checks/7 decodes/served hashes passed.

All639 current media files fully decoded and size/hash/dimension matched; no unlinked raster files. Read-only library audit completed in `library-audit-v2`; don't use partialv1. Missing eligible images105706(alltypes), of which14752paintings. Prioritize paintings and documented icons, not indiscriminate print downloads. Existing161 oversized legacy images and15 missing structured-rights rows are deferred for evidence-preserving review.

Receipt audit v2:205metadata receipts/106185distinctworks,107741 assertions,0failed.161existing works outside recognized receipt format listed explicitly; no inference they are missing or safe to delete. Eleven lack external identifiers and need exact citation/seed/editorial review.

Backup folders moved out of Documents to Library/Application Support/Artline/backups;22directories/36files hashes verified. Historical source names retained. Use new location for future backups.74 PDF proofs and one browser-test state file moved to Trash; real source evidence preserved.

## Next queued useful work

1. Read the161-row unrecognized-receipt follow-up list, especially11 works without identifiers; reconcile original seeds/editorial evidence without deleting or inventing facts.
2. Continue the missing-image queue in `output/data-collection-20260911-2016/library-audit-v2/eligible-missing-image-queue.jsonl`. It streams every eligible gap but does not erase previous rights/blocked decisions. Use painter/museum-scoped batches and exact object evidence. Prioritize European/regional paintings and icons; keep other artworks queued.
3. Fresh official Karlsruhe leads manually read, NOT captured/imported/images downloaded: Boucher Schäfer und Schäferin1760acc479, Zwei Schäferinnen1760acc480, Pissarro Blick auf die Grosse Brücke zu Rouen bei Regenstimmung1896acc2488, Rubens Die Gründung Konstantinopels c1622–1623acc2759. Links in SOURCE_LEADS.md. Extend via a NEW pinned batch/source while preserving original Karlsruhe manifest. Never import Canaletto Nachahmer or Cranach Nachahmer as autograph. Pissarro drawing dated only after1855 remains date-review.
4. Rotate to another permitted museum/painter after this batch. Paris Musées automated access needs its required account/accepted terms; Belvedere restrictions unresolved. Earlier Nationalmuseum/Chicago403s not to be bypassed. Nivaagaard new6/6 and Athens/Poldi batches already done, not repeat targets.
5. The user's Monet UI complaint remains open:300records/32images. Do actual browser skill-driven visibility audit after collection, without publishing review rows or weakening access rules.

## Run commands (read-only audit modes)

From apps/server, with `DATABASE_URL=postgres://localhost/artline?sslmode=disable`:

- `go run ./cmd/review-painters -mode audit-library -root ../.. -out <new-directory>`
- `go run ./cmd/review-painters -mode audit-receipts -root ../.. -out <new-directory>`

These create no databases/schemas and never modify catalogue/files. Do not set ARTLINE_TEST_DATABASE_URL to artline. Source metadata/image imports remain separately pinned, backed up and verified. Units can run with that test env unset.

Bad Request origin still unidentified; no automatic retry fix claimed. One diagnostic GET retry allowed, unchanged400s need request correction,429/403 obey source policies. Never blindly replay a mutation.
