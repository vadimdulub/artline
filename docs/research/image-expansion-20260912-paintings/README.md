# Additional eligible paintings — 12 September 2026

This follow-up to the [main campaign](../image-expansion-20260912/README.md)
targets existing paintings that were outside the initial selection. It uses
the same museum rights gates, 100,000-byte cap, local and GCS copies, and exact
database attachment checks.

The frozen SQL selection contains **6,609 distinct paintings**:

| Museum | Selected existing paintings |
| --- | ---: |
| National Gallery of Art | 2,666 |
| Metropolitan Museum of Art | 1,337 |
| Art Institute of Chicago | 758 |
| Cleveland Museum of Art | 141 |
| Statens Museum for Kunst | 1,707 |

All 10,000 IDs from the first campaign and all 25 IDs from the Rijksmuseum
supplement were explicitly excluded. The three manifests have no overlapping
artwork IDs. Selection requires `work_type='painting'`, existing museum source
provenance, no current primary image, SQL creation-date eligibility, and
documented selection evidence. The per-source bound was 3,000; none reached
that bound. This is a metadata-first selection, not a promise that every work
will have a reusable museum image.

Selection command:

```sh
/tmp/artline-images-venv/bin/python ops/enrich-artwork-images.py select \
  --run docs/research/image-expansion-20260912-paintings \
  --providers nga,met,chicago,cleveland,smk --per-source 3000 \
  --work-type painting \
  --exclude-run docs/research/image-expansion-20260912 \
  --exclude-run docs/research/image-expansion-20260912-rijks
```

`ops/continue-painting-images.py` coordinates the two campaigns. It starts a
museum's follow-up worker only after every selected ID for that museum in the
earlier campaign has a terminal outcome. An observation timeout is never
treated as completion. Incomplete final JSONL lines are left for the next
read. The coordinator also observes the earlier process's live PID; if that
process ends with unattempted IDs, that museum's follow-up is deferred for
inspection. There remains only one active image worker per museum across the
two campaigns, with an additional request gap at handoff.

The coordinator was started against the confirmed live original importer
PID 43810. Do not launch another coordinator or standard importer against this
run while it is live. After it has actually exited, the ordinary importer can
resume any incomplete work using the saved receipts and outcomes.

This campaign is running/waiting; final image counts and independent audits
will be recorded after application. Research evidence uses `candidates.json`,
`metadata/`, `selected/`, `images/`, `events.jsonl`, and `verification-*.json`,
as in the original campaign. Both earlier backups cover this authorized
enrichment workflow. No painters, artworks, publication states, creation
dates, or on-view claims are added or altered by the image importer.

## Database transport check

The queued pass uses [Psycopg pipeline mode](https://www.psycopg.org/psycopg3/docs/advanced/pipeline.html)
inside each existing explicit transaction. The exact-identity lookup is
synchronized before deciding whether to enqueue media, rights evidence, and
the artwork link. Pipeline errors propagate before transaction completion,
so the existing atomic attachment and rollback behavior is retained.

`pipeline-readonly-benchmark.json` records a six-SELECT protocol check with
Psycopg 3.3.5 against both databases. Median cloud exchange time fell from
1,934.53 ms to 1,071.12 ms (1.81×); local times were effectively unchanged.
A deliberately failing read-only SELECT confirmed rollback and subsequent
connection recovery on both targets. This measures round-trip overhead, not
end-to-end download speed or write throughput. No catalogue fixtures or
records were inserted by the benchmark.

The initial waiting coordinator was intentionally interrupted before it had
started any museum worker, then restarted to load this transport change.
The original 10,000-work importer continued throughout with its original
transport behavior. The eight offline museum-rights/compression tests passed
again after the change; subsequent real attachment results will be audited
from this campaign's receipts and databases.

## First live results

Chicago's initial 2,000 records reached terminal outcomes and its 758-painting
follow-up started automatically. `verification-canary.json` independently
checked the first **59 images**, totaling **5,333,023 bytes**, maximum **99,504
bytes**. All local files decoded and matched GCS; all database metadata, rights,
source provenance, and exact artwork links matched the receipts on both
targets. All 59 fresh creation-date ranges remained within the cutoff. No
errors were found. This also verifies real media/rights/link writes using the
optimized transaction transport. Other museum follow-ups remain queued behind
their own earlier workers.

## Connection-reset recovery

After a long execution pause, the Cloud SQL proxy reported TCP resets and the
existing client sessions became unusable. The original importer and waiting
coordinator reached terminal process states after their bounded error limits;
they were not restarted on the basis of an observation timeout. Fresh
read-only connections to both databases passed.

`AttachmentDB` now reconnects after connection-class errors and repeats the
same idempotent attachment, up to three attempts. Stable receipt/media IDs,
create-only uploads, and the primary-image guard handle an uncertain commit
without duplicating or replacing images. Constraint and row-lock errors retain
their existing handling; the two-second row-lock timeout is not retried.
Ten offline tests pass, including lost-session recovery with the same receipt
and preservation of the row-lock timeout behavior.

Both campaigns resumed under one process, with one sequential chain per museum:

```sh
caffeinate -i /tmp/artline-images-venv/bin/python ops/continue-painting-images.py \
  --after docs/research/image-expansion-20260912 \
  --run docs/research/image-expansion-20260912-paintings --resume-chain
```

This mode requires all previous import processes to have actually exited.
For each museum it finishes pending first-campaign work before continuing the
painting supplement. It skips completed images and current-version rights
skips, reuses saved derivatives, and retains historical events. `caffeinate`
holds an idle-sleep assertion only for the life of this job. All **40 interrupted
database attachments** (32 main-campaign and 8 supplement) were recovered;
the latest-event audit shows no remaining connection-error items. The 17
blocked Chicago source URLs and four missing Met API records remain separate
from successful images.

## Recovery audit

`verification-recovery.json` independently checked **281 Chicago paintings**,
totaling **24,931,353 bytes**, maximum **99,970 bytes**. All local files, GCS
checksums, database metadata, rights evidence, and exact artwork links passed
on both targets. All 281 fresh creation dates remained eligible. The audit
found no errors. This is a checkpoint while the remaining selection runs.

## Chicago painting pass completed

All 758 selected Chicago paintings now have a terminal outcome: **371 images
added** and **387 rights/availability skips**. `verification-chicago-complete.json`
checked all 371 images, totaling **32,946,647 bytes**, maximum **99,970 bytes**,
with no errors in local files, GCS, either database, or fresh creation dates.

`chicago-rights-skip-audit.json` confirms all 758 exact museum objects were
present in the saved API responses. Of the 387 skips, 385 were not marked
public domain (214 also had a copyright notice); the other two had no image
ID. Ten of the 385 non-public-domain records also lacked an image ID. No
otherwise eligible image was skipped because of a missing batch response.
The earlier main campaign's 17 blocked Chicago image URLs remain recorded
as source failures after bounded retries.

`verification-nga-met-handoff.json` checked **576 supplement images** after
NGA and Met automatically continued into their painting batches: Chicago 371,
NGA 142, and Met 63. The images total **50,957,854 bytes**, maximum **99,998
bytes**. All local/GCS checks, database metadata, rights evidence, and exact
artwork links passed on both targets; 434 fresh museum date ranges were
checked with no cutoff conflicts. Together with the latest main-campaign
and Rijksmuseum audits, **8,698 images** are independently verified.
Processing continues beyond this checkpoint.

`verification-10000-checkpoint.json` checked **1,309 painting-supplement
images**, totaling **110,135,563 bytes**, maximum **99,998 bytes**, with no
errors. Provider counts were Chicago 371, NGA 573, Met 356 and Cleveland 9.
All local/GCS and both-database metadata, rights and exact-link checks passed;
736 fresh museum date ranges remained eligible. Cleveland completed its
initial IDs and started its 141-painting supplement automatically. One
additional Met API ID, 437501, returned HTTP 404 and remains a source failure
at this checkpoint.

## DNS interruption and local preparation — 13 September

The main coordinator exited at 21:45:15 UTC on 12 September after NGA finished.
Met and SMK had already paused following DNS-resolution errors at 21:29 UTC.
The live process and its waiting Sisley coordinator were confirmed terminal
before further work. NGA and Cleveland now have no unattempted selected IDs.
At the pause, 1,680 selections remained unattempted: Met 143 and SMK 1,537.

Fresh DNS checks passed on 13 September, but gcloud reported that the active
account requires reauthentication. The user was asked to reauthenticate that
same account. `verification-local-paused.json` passed for **2,804 uploaded
supplement images**, totaling **241,031,515 bytes**, maximum **99,998 bytes**.
It verifies local files and catalogue links only; a fresh cloud audit remains
pending. The Romney source error was recovered in the separate
[Commons painting supplement](../image-expansion-20260912-commons-paintings/README.md).

While waiting for cloud authentication, a local-only preparation process was
started for the remaining Met and SMK selections:

```sh
caffeinate -i /tmp/artline-images-venv/bin/python ops/enrich-artwork-images.py apply \
  --run docs/research/image-expansion-20260912-paintings \
  --providers met,smk --prepare-only
```

This mode saves verified rights snapshots and <=100,000-byte derivatives,
recording **prepared** rather than complete outcomes. It does not create a
GCS client, retrieve a cloud secret, upload objects or write either database.
An offline test verifies that storage and database attachment are not called;
all 14 offline tests pass. Once this process ends and authentication is
restored, ordinary application reuses its receipts and files. Prepared images
must not be counted as uploaded or attached. Do not run a competing source
worker while this preparation process remains live.

`verification-prepared-canary.json` checked the first **81 newly prepared SMK
files**, totaling **7,541,341 bytes**, maximum **99,521 bytes**. All local hashes,
sizes and decodes passed; a read-only query confirmed zero media rows for
these prepared IDs. This is evidence of preparation only, not cloud upload
or database attachment. Met’s remaining 154 attempts ended with 151 explicit
rights/availability skips and the three known API 404 records; there are no
unattempted Met IDs. SMK local preparation continues.

## Authentication restored; prepared uploads resumed

The authorized gcloud account’s authentication was verified on 13 September.
`ops/upload-prepared-artwork-images.py` consumes only fully written prepared
events and existing immutable receipts. Its worker cannot fetch museum
metadata or images, even if a receipt is missing. The single source worker
continues on its own future IDs; the consumer attaches earlier prepared IDs.
Fifteen offline tests pass, including the no-source-request consumer guard.

The consumer was started with the confirmed live preparation PID 66640:

```sh
caffeinate -i /tmp/artline-images-venv/bin/python ops/upload-prepared-artwork-images.py \
  --run docs/research/image-expansion-20260912-paintings --producer-pid 66640
```

Do not start another consumer while it is live. Source and upload outcomes
share an append-only log; each small JSONL event is flushed before the
consumer can select that prepared ID. Completed upload events are never
overwritten by the producer, which has already moved past those IDs. The
consumer ends only after the actual producer exits and no prepared events
remain. Any failed cached attachments remain separately auditable.

`verification-resumed-upload.json` independently verified **3,061 completed
supplement images**, totaling **264,798,395 bytes**, maximum **99,998 bytes**,
in local storage, GCS and both databases with no errors. This includes
**257 newly uploaded prepared SMK files** and validates the producer/consumer
flow against actual rights and artwork links. At the snapshot, 113 further
files were prepared but were correctly excluded from uploaded-image counts.
Together with the initial campaign and completed recovery supplements,
**12,040 images** are independently verified. SMK processing continues.

## Completed

Both preparation and upload processes reached terminal states. All 6,609
painting selections were attempted: **3,467 images added**, 3,139 explicit
rights/availability skips and three source API failures. Romney’s source
failure was recovered separately; the two Eilshemius records remain
unavailable. There are no remaining prepared files or unattempted IDs.

`verification-final.json` passed for all 3,467 supplement images, totaling
**302,852,694 bytes**, maximum **99,998 bytes**, in local storage, GCS and both
databases. The subsequent all-campaign audit independently rechecked every
completed link, eligibility predicate and image copy. See the final
[combined results](../image-expansion-20260912/RESULTS.md).
