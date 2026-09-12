# Popular-painter research continuation

## Latest measured checkpoint — 20:04 UTC

This run has added **9 artworks and 11 authentic images**: SMK 3 images; Nivaagaard 6 works/6 images; Athens 1 work; Poldi Pezzoli 2 works/2 images. All applied batches passed preservation and API checks. No highlights, publication or editorial changes. Research remains in progress; neither all-100 coverage nor the requested active-work window is complete.

Athens Entombment Π.9979: corrected selection `athens-entombment-v2` applied one work; preservation and object/access checks passed. Image deferred: museum permission unresolved and the exact Commons file lacks a US public-domain tag. Do not substitute the different Christie's Entombment.

Poldi Pezzoli: Piero Saint Nicholas0445 and Bellini Imago Pietatis1587 added, followed by independently licensed Commons reproductions, **82,429 and91,369 bytes**. Both visually inspected, full compositions retained;7 API checks,2 full JPEG decodes and served hashes passed. Commons stale dating and incorrect dimension-unit labels were not imported over museum facts. See painter checklists and `poldi-*` receipts.

Backups in `/Users/vadimdulub/Documents/artline-popular-resume-20260911-backup.xM3Mcm/`, all archive lists verified:

- `before-athens-entombment.dump`: `540cb6c5e3d1a32c7650456b24d2778620679e45487b94458a0760eb89a784e9`.
- `before-poldi.dump`: `09c956672c897447a952363d229a1102ac8680f4022b6c90f1be71d6f807ec4d`.
- `before-poldi-images.dump`: `b9624365697d83be63b74d3fddd162559fcf62ca306204ec3ddaed61249245d1`.

Paris Musées manually reviewed leads: Cézanne PPP2099, Morisot PPP488, Courbet PPP3130. The API requires an account and acceptance of terms; automated extraction outside compliant access is restricted. No Paris imports/images were made. Continue another permitted source, not a block bypass.

Run start: **2026-09-11 18:52:48 UTC**. Requested active-work window: four to five hours; earliest wall-clock target **22:52:48 UTC**, extended for any significant idle/approval waits. Record useful-work spans and interruptions as work proceeds; elapsed time alone is not an active-work claim.

Baseline rechecked: **106,330 artworks, 621 media assets, 5,328 artists and 100 popular painters**. The earlier session's 135 artwork/13 image additions are already included; never count them again in this run.

Read `AGENTS.md`, priority instructions, the popular-cycle methodology, all-100 source index and the prior session's progress, findings and exact continuation checkpoint. Existing untracked work is preserved. No commit, push, publication, deployment or Terraform.

## Activity spans

- 18:52:48 UTC onward: active instruction/checkpoint review, baseline verification, targeted painter inventories and official European catalogue/rights research. No approval waits so far.

## Current queue

1. Austrian holdings and permitted images for Schiele/Klimt and other popular painters at Belvedere; per-object licence review before image requests. Press-photo permission is not a general reuse grant.
2. Regional/other European notices for low-coverage popular painters; carry forward the explicit Greek and Russian source conflicts.
3. Continue across the popular cohort and checkpoint each verified bounded batch. Do not mark painters complete from query or download success.
4. After the research cycle, carry out the user-requested real UI image-visibility audit beginning with Monet; see `docs/POPULAR_RESEARCH_CONTINUATION_PROMPT.md`.

## Verified first batch

At 19:12 UTC, three Matisse SMK images were attached: KMSr171 (97,283 bytes), KMSr73 (96,650), KMSr75 (93,691). All were visually inspected; full-image decoding, served hashes, 11 API checks and whole-database preservation checks passed. No new artworks, highlights, publication or editorial changes. Current media total: 624; baseline 621.

Receipts: `output/popular-resume-20260911-1852/smk-matisse-{selection,preview,apply,before,after,api}.json`. Exact sources and backup recorded in [FINDINGS.md](FINDINGS.md).

Fresh [all-100 inventory](inventory-v1/PAINTERS.md) exported after this batch: 22,367 popular-painter artwork links and 426 linked images. Automated verification counters are not individual source-review completion.

19:05–19:07 UTC was a user-requested service-error diagnostic interruption, not painter research. No reported Bad Request reproduced; exact failed URL still needed.

19:18–19:23 UTC: paused for the user's repeated service-error report, excluded from painter research. Resumed at19:23:44UTC.

## Nivaagaard metadata batch

Six individually verified works added across six popular painters: Sofonisba Anguissola, Giovanni Bellini, Artemisia Gentileschi, Lucas Cranach the Elder, Claude Lorrain and Rembrandt van Rijn. New institution: The Nivaagaard Collection, Nivå, Denmark. **Run additions now6 artworks +3 images**; DB106,336 artworks /624 media before Nivaagaard image work.

Pinned selection: `nivaagaard-v1/manifest.json`, exact SHA256 `a13344de933b611bcebc727c991c98eb756799bce9b6c46528d98d53ac0e1595`.

Backup: `/Users/vadimdulub/Documents/artline-popular-resume-20260911-backup.xM3Mcm/before-nivaagaard.dump`, SHA256 `77e1a1847fde4c664d96c3ddc2a5822e167c58d353beb0ac0ab4da66221ee1bb`; pg_restore archive list verified. Dry run: six creations,13 citations,zero highlights. Apply matched. Whole-DB preservation and six object-detail/two access-control checks passed. Receipts: `output/popular-resume-20260911-1852/nivaagaard-{preview,apply,before,after,api}` (directories for preview/apply; JSON for checks).

Bellini's generic title collided with NGA accession1939.1.182, object323. Official notices document separate holdings/accessions and distinct provenances: Nivaagaard bestowed1908; NGA Kress gift1939 with separate provenance. Reviewed as distinct, never merged on title alone. Sofonisba birth-year discrepancy1532/1535 preserved without artist edits. Rembrandt's later-added hand/prayer book by another artist noted. No ownership/current-display/masterpiece claims added.

Next: exact public-domain reproductions for these six records, then another European museum/painter batch. Successful import does not complete any painter's research.

## Nivaagaard images verified

Six authentic images attached: Sofonisba69,635 bytes; Bellini82,303; Rembrandt59,578; Artemisia89,336; Cranach91,170; Claude59,161. All full compositions visually inspected. Whole-DB preservation passed;20 API checks,6 complete JPEG decodes and6 served hashes passed. **Run totals:6 new artworks,9 new images; database106,336 artworks /630 media.** No highlights/publication/editorial changes.

Image backup SHA256 `3303805e65b99422b84d473dc552c0b66f31d53fd3ef5ec8bc6ed4e6656b7025`, file `before-nivaagaard-images.dump` in the existing backup directory. Image selection SHA256 `b250a74eb8cfed24f5ce9b013f7ea07926e24846ae753c76c2b375ac5d223386`. New Go exact-object/rights/image parser and negative mutation tests passed. Per-painter checklists saved in this directory; all mark wider research and real UI audit as unfinished.

User added an all-artwork image-research request and safe retry request. Updated `docs/POPULAR_RESEARCH_CONTINUATION_PROMPT.md` with full-inventory resumable queues, exact identity/rights checks and HTTP400 diagnosis rather than endless unchanged retries. Specific Bad Request remains unidentified; no claim of a fix.

Next source review: Athens El Greco Entombment; Italian Poldi Pezzoli/Carrara object notices. Poldi Botticelli's two paintings and Piero's Uffizi diptych are already present in the database; do not duplicate them. Nivaagaard's Danish painters are outside the current popular100, so they remain later full-inventory leads rather than silently changing popularity.
