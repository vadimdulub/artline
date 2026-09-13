# Museum-source resolution of the expanded CSV

The six-column CSV omitted object identities and source evidence. This follow-up
matches its retained candidates against official museum metadata, stores the
evidence separately from the immutable CSV, and adds eligible named artworks to
the catalogue in **review** status.

Local and production execution are complete. Evidence, dispositions and active
catalogue mappings match; see `database-comparison.json`.

The user subsequently authorized retaining entries without additional details as
actual review artworks. That additive phase is documented in
[the incomplete-artwork receipt](../expanded-review-artworks-20260912/README.md).

| Source | Unique source matches | Catalogue-linked entries in both DBs |
|---|---:|---:|
| Joconde / French Ministry of Culture | 30,817 | 4,306 |
| Statens Museum for Kunst | 4,898 | 3,651 |
| Tate | 3,799 | 2,199 |
| Total | 39,514 | 10,156 |

The linked entries identify 10,153 physical catalogue objects: **9,420 new
artworks**, with 733 previously catalogued objects reused. They introduce
**2,357 named painters**. Every new active artwork has a linked artist, an
official source citation, eligible creation dates, and review status.

Another 29,358 matched entries retain explicit review reasons, including missing
creator authorities/biographies, ambiguous existing identities, uncertain dates,
physical-part/group records and holding/deposit questions. The remaining 65,420
staged entries have no unique exact match in these three datasets. Counts are
research entries, not a claim that every supplied row represents a distinct object.

## Sources and evidence

- [Joconde export](https://ministere-culture.s3.sbg.io.cloud.ovh.net/POP/joconde.csv),
  captured 9 September 2026. Each match retains its POP notice URL and museum code.
  Notice creation/acquisition dates are never substituted for artwork dates.
- [SMK API](https://api.smk.dk/api/v1/docs/), Danish painting metadata captured
  12 September 2026. Eight pages contain 7,378 painting records; selection is
  restricted to the supplied candidates. Source creator IDs and object numbers
  are retained. Notes identifying lifetime-based artwork dates defer promotion.
- [Tate's official collection dataset](https://github.com/tategallery/collection),
  commit `a51d8afc988ed083557e2950f4d0b644e7719f4a`.
  This is a historical October 2014 dataset. It establishes a documented museum
  connection, not a current physical venue, display status, or current biography.
  No missing death year is interpreted as a claim that someone is alive.

Source files and checksum receipts remain in `content/imports/`, including the
Joconde capture under `joconde-20260910/` and new captures under
`expanded-resolution-20260912/`. The final matched inventory is
[matches-v3/manifest.json](matches-v3/manifest.json), with 80 checksummed chunks.
Earlier matching attempts are retained as research history; they are not inputs
for replay. The original staged CSV fingerprint remains
`210a729ead48d12b0f228eb9e1fe0c5a6708750b196be38ddfbbb270aa1355c8`.

The selected facts, unresolved ledger and source checksum receipts also have a
private copy at
`gs://artline-508319-images/research/expanded-resolution-20260912/source-evidence-v3.tar.gz`.
[Archive receipt](evidence-archive.json) records its checksum. Full original
museum captures remain locally preserved; the archive is the selected evidence,
not a copy of every complete museum dataset. No image bytes were downloaded,
attached, or declared rights-cleared. The CSV `hasPicture` field remains a claim.

## Import rules and corrections

`ops/resolve-expanded-research.py` performs exact normalized matching within the
supplied candidates, verifies source checksums and rejects ambiguous source-object
matches. It does not access a database or download images.

`apps/server/cmd/resolve-research` validates all selected chunks before opening a
database. Database changes require `-apply`; catalogue promotion additionally
requires `-promote`. Each 500-entry chunk runs in a serializable transaction under
the ingestion advisory lock. Individual identity conflicts roll back their work
savepoint and retain a review reason. Unexpected database errors stop the batch.

Migrations 0013/0014 add `research_resolutions` and indexed identity lookups.
Migration 0015 indexes the staged source-record identity used by reconciliation.
The previous plan read 17,317 research-table pages for 500 selected IDs; the
indexed local plan read 490 pages through bounded record lookups. Before/after
plans are preserved in `staging-lookup-before.json` / `staging-lookup-after.json`.
The same migration was applied during the production job without replacing it.
The importer also analyzes its actual temporary batch and uses correlated
indexed lookups to prevent a merge plan from scanning earlier fingerprints.
Replaying the real 500-entry penultimate batch inserted zero records and confirmed
500 index lookups returning one row each; see `local-bounded-query-plans.jsonl`.
Every resolved row must match the original staged fingerprint **and all six CSV
cells**. Replays check the stored fact checksum. Promotion reconciles existing
object IDs, canonical URLs and meaningful inventory numbers; shared placeholders
such as `SN` / “sans numéro” are never object identities. Name-only creator matches
do not merge people, and shortened-name/biography collisions require review.
Joconde notice IDs are not fabricated into artist authority IDs.

Unknown dates and ranges crossing 1970 remain in review. Documented creator
lifespans are preserved; otherwise the timeline explicitly describes the range
of documented works, not a lifespan. No nationality, popularity, masterpiece
designation, ownership or current display is inferred. Tate is represented as
an aggregate institution without an invented venue.

The local identity audit found three Danish school/unnamed-master labels after
the initial import. Their three newly created painter/work pairs were archived
with audit history retained, and their resolutions returned to review. The guard
was added before production import, so these pairs are never created there.
Named people such as Johannes Hofmeister and Anshelm Schultzberg remain eligible.
The exact guarded correction SQL and backup receipts are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/source-resolution-20260912/`.
No pre-existing catalogue record was removed to apply the exclusion policy.

## Execution and verification

The full local backup is `local.dump` in the backup directory above. Production
managed backup `1789233121520` completed successfully before catalogue writes.

Local receipts: [initial chunk](local-first-chunk.jsonl),
[first ten chunks / replay](local-import.jsonl),
[remaining chunks](local-import-part2.jsonl), and
[final verification](local-verification.json).

Production runs the same importer in a temporary Cloud Run Job beside Cloud SQL:

- Project: `artline-508319`; region: `europe-west1`.
- Job: `artline-source-resolution-20260912`.
- Execution: `artline-source-resolution-20260912-8pz7d`.
- Build: `c762b6c7-5e55-4f8f-9916-48b6d79b5afa`.
- Image: `europe-west1-docker.pkg.dev/artline-508319/artline/research@sha256:69a12498eb652096dd470219c9a12f0e4f675980b7bcb1a6c385065d041dcc72`.
- Runtime account: `artline-runtime@artline-508319.iam.gserviceaccount.com`.
- Cloud SQL: `artline-508319:europe-west1:artline-postgres`;
  `DATABASE_URL` is supplied by the existing Secret Manager secret.

The first execution committed chunks 1–25 (12,500 resolution entries), then was
stopped to use the bounded lookup implementation. The database import ledger
confirmed an uninterrupted prefix before resuming at chunk 26; no committed
batch was discarded. Resume receipt: `production-resume.json`.

- Resumed execution: `artline-source-resolution-20260912-hfnh9`.
- Build: `31e40106-e992-433a-aef4-1f768c322232`.
- Image: `europe-west1-docker.pkg.dev/artline-508319/artline/research@sha256:310fd5a35b2bf49af56aa766ea042a8f10175744510e9315a03417edfd625f78`.

After ingestion, `ops/format-resolved-research-details.sql` formats SMK dimension
objects as readable source measurements and removes duplicated city suffixes
from Joconde holding labels. It only changes newly created review artworks whose
fields still match this import's original values. Original facts/citations remain
intact and database audit triggers preserve the updates. The local pass formatted
7,222 artworks; replay is a no-op. The importer applies the same display formatting
to future eligible records.

`ops/Dockerfile.research-resolution` documents the isolated build. Its context
contains server sources and a `research/` directory with the selected inventory;
credentials and `.env` files are excluded. Unrelated in-progress UI/server changes
were excluded from this build. The public web/API revisions are not redeployed.

[Read-only verification SQL](verification.sql) compares checksums of all source
facts, dispositions and catalogue mappings without depending on generated UUIDs.
Unit tests cover cutoff boundaries, source-date conflicts, lifetime fallbacks,
creator alias collisions, inventory placeholders and Danish anonymous attributions.
Existing ingestion tests also pass with `ARTLINE_TEST_DATABASE_URL` unset. No test
database or catalogue fixtures were created.

The actual 39,514-row resolution table uses its identity index for a single-object
lookup; see [query plan](identity-query-plan.txt). This batch does not establish
performance at the 20,000-painter / 10-million-artwork planning scale. That load
test remains separate backend work.

## Supplemental creator review

The final SMK source audit also inspected separate `creator_qualifier` and
`notes` fields. Twenty matched records carry these notes; eight require an
explicit attribution hold, including a copy after Furini recorded only in a note.
Migration 0016 adds supplemental `review_evidence` without changing the original
matched-fact checksum. `ops/review-smk-resolved-creators.py` verifies the pinned
source pages and produces the guarded correction SQL.

Two newly imported review artworks were archived; one new painter whose only
work was held was also archived. Existing catalogue objects were preserved.
The eight affected resolutions have `conflict` status, and importer replay
respects that hold. The other twelve creator notes supplement the evidence
without changing the source attribution. Regenerated inventories now retain
these separate fields so the importer can detect the caveats before promotion.
Use the original v3 inventory with its supplemental review receipt for replay;
regenerating changed facts requires explicit reconciliation, not silent replacement.

The local database retains three additional archived painter/work pairs from
the earlier Danish-label correction. Production excluded those before insertion.
Compare active catalogue mappings and evidence checksums; total physical row
counts intentionally include that local audit history.

The resumed production job completed all remaining chunks. Its temporary Cloud
Run Job was deleted after verification to prevent replay of an obsolete worker.
A final local inventory-number correction recovered one source-backed object
with the shared placeholder `SN`; evidence and guarded receipts are preserved in
`inventory-number-correction/` and `local-inventory-number-correction.jsonl`.
