# Expanded artwork creator reconciliation — 13 September 2026

Follow-up: the [second research round](../expanded-round2-20260913/README.md)
completed another 7,785 artwork links and 5,640 metadata enrichments in both
databases. This report preserves the preceding phase.

**Complete and verified in local and production.**
The existing artwork import is complete in both databases. This additional phase
links incomplete review artworks to painter identities already established by
the previous official museum-source import.

The checked plan links **3,137 artworks to 721 existing painters**:

| Museum source | Artwork links |
|---|---:|
| Joconde | 2,193 |
| Tate | 498 |
| SMK | 446 |

An exact SMK/Tate person identifier must refer to one already reconciled painter.
Joconde has no person identifier in this capture, so its literal full creator
name and both documented birth/death years must agree with a previous accepted
identity from the same source. Conflicting biographies, qualified attributions,
archived/non-person creators and ambiguous identities are held. No painter is
created or merged by name alone. The source evidence comes from the preserved
[official museum captures](../expanded-resolution-20260912/README.md), not a new
claim about current museum display.

Of 29,306 unlinked source-matched candidate records audited, 26,169 remain held
or lack an established matching identity. Supplied-only artworks are unchanged.
The original anonymous/unknown creator exclusions remain in place.

Each accepted match adds one primary `artwork_artists` attribution and a
`reconciled_museum_creator` citation identifying the source, earlier authority
anchor and plan checksum. The resolved object's `unlinked_creator_label` is
cleared; the original wording remains in immutable research evidence. Every
artwork stays `review` with `research_candidate=true`. Nothing is published.
The 1,282 unknown dates and 198 unknown artwork types in this subset remain
unknown. Museum holdings, physical-object questions, biography fields and
current-display claims are not changed by creator reconciliation.

Linked review artworks can appear in the site's existing personal research
preview painter chronology. Live API checks returned the newly linked objects
for Gaston Ernest Marche, George Garrard and Anton Eduard Kieldrup (HTTP 200,
bounded two-work results; `live-verification.json`). This is distinct from
publication or selection as a painter's representative masterpiece. No frontend
deployment is needed for these database links.

## Evidence and verification

`manifest.json` pins `plan.json` with SHA256:
`58937e1ae15cb5cc214c5cce308021b6dac20339b4ba12d3aeb6ab8ddc4b84e9`.
The original read-only creator anchors and candidate snapshots are preserved
alongside the plan. These JSON evidence files are intentionally ignored by Git.

`local-apply.jsonl` and `production-apply.jsonl` record all 13 batches (250 records maximum).
Every batch receipt matches (`execution-comparison.json`). The importer
checks target slugs, source/anchor checksums, supplemental attribution evidence,
artist biographies, dates/type, original entry checksum and existing attribution
links in each serializable transaction. It uses the existing ingestion advisory
lock. Changed evidence stops the batch rather than accepting stale decisions.

The local and production before/verification receipts confirm all 3,137 correct links
and citations, no remaining unresolved labels in the selected subset, no
publication/cutoff violations and unchanged artwork/painter metadata digests.
Digests exclude generated IDs, audit timestamps/revisions and independently
managed image pointers. Creator labels are checked separately as the intended
change. A replay of the first real 250-record batch added no links and changed
no labels (`local-replay.json`). No test fixtures or test databases were used.

Five offline policy tests cover incomplete identities, namesakes, museum ID
scope, unknown dates, separate qualification/copy fields, existing holds and
impossible painting dates. A read-only plan on 100 actual reconciled works
returned 100 rows in 6.209 ms locally (`local-attribution-query-plan.json`). This
is not evidence of performance at ten million artworks; that load test remains
outstanding.

Before local writes, a full backup was completed and its archive listing checked:

`/Users/vadimdulub/Library/Application Support/Artline/backups/creator-reconciliation-20260913/local.dump`

332,073,259 bytes; SHA256
`379ea2cba177522e37a695c4d8add13fd9426de833cb73d1f00aef03cbe7ae6c`.
The adjacent `local-receipt.json` preserves the receipt.

## Production execution

Google authentication was renewed. Cloud SQL backup **1789294412900** completed
successfully before any reconciliation writes, from 10:13:32 to 10:15:24 UTC on
13 September 2026. The receipt is preserved alongside the local backup and in
`backup-receipts.json`. Target: `artline-postgres`, project `artline-508319`.

The pinned plan, source snapshots and initial script are archived privately at
`gs://artline-508319-images/research/expanded-creator-reconciliation-20260913/creator-plan-v1.tar.gz`.
The 9,801,870-byte archive has SHA256
`48971cec44520f4106e5e3378f53f4e1ad8424a630c306b1f2f6590422dcaba2`;
the cloud object's MD5 was independently checked against the local archive.

The first production audit exceeded its statement timeout. The read-only audit
was changed to use batches of 250 identity keys, avoiding expansion of the full
source-fact JSON in a single query. It reproduced the original local digests.
The writer and pinned plan stayed unchanged. This script version is separately
archived as `reconcile-artwork-creators-v2.py` in the same private prefix;
`audit-adjustment.json` preserves its checksum and the reason for the adjustment.
The historical staging-correction script `ops/reconcile-expanded-creators.py`
is preserved; this phase uses the separate `ops/reconcile-artwork-creators.py`.

Production's pre-update audit matched the saved local baseline. All 3,137 links,
citations and intended label changes were then applied. The final database
comparison found no differences and no publication/cutoff violations
(`database-comparison.json`). All three live painter-work checks passed. No
public application deployment was required.

The script uses normal PG environment variables and never writes credentials
to its plans or receipts:

```
PGDATABASE=artline python3 ops/reconcile-artwork-creators.py before --dir PLAN_DIRECTORY --label production
PGDATABASE=artline python3 ops/reconcile-artwork-creators.py apply --dir PLAN_DIRECTORY --label production
PGDATABASE=artline python3 ops/reconcile-artwork-creators.py verify --dir PLAN_DIRECTORY --label production
```

For production, set the authenticated proxy connection and database credentials
in the process environment as in the existing import workflow. Do not run these
example commands against local defaults with a production label. Apply is
idempotent, so completed batches may safely be replayed after checking receipts.
Keep the shared Cloud SQL proxy running for concurrent image work.
