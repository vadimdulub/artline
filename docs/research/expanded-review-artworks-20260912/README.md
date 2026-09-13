# Incomplete named artworks retained in the database

A [second research round](../expanded-round2-20260913/README.md) subsequently
linked another 7,785 artworks and enriched 5,640 with official museum metadata
in both databases. The historical import receipts below remain unchanged.

Follow-up on 13 September: [creator reconciliation](../expanded-creator-reconciliation-20260913/README.md)
has linked 3,137 of these artworks to 721 existing painters in both local and
production, with matching database verification and passing live checks. The original import results
and verification receipts below describe the completed state before that follow-up.

On 12 September 2026 the user explicitly requested actual artwork records even
when additional research finds no details. This supersedes the staging-only
outcome for incomplete named entries. It does not validate missing metadata,
publish records, or remove the anonymous/unknown creator exclusion.

**Completed in local and production.** All 105 committed batch receipts match.
The final database comparison found no differences in imported artwork content,
source links, dispositions, date/type counts or publication guards, and no
integrity violations. All retained entries are accounted for. Receipts:
`execution-comparison.json`, `database-comparison.json`, `local-verification.json`
and `production-verification.json`.

This phase follows [official museum-source resolution](../expanded-resolution-20260912/README.md).
Of 104,934 retained distinct CSV entries, 10,156 already link to catalogue objects.
The remaining 94,778 entries include ten explicit attribution holds. The import
creates **94,726 review artworks**, links **42 entries to existing objects**, and
retains the ten holds without adding artworks. Repeated CSV rows remain preserved
in the original staging record-number arrays.

The new works have object-level named-creator labels, not invented artist
authorities or biographies. Source-only entries have an explicit `unknown` type.
Official museum facts are used where available, with the unresolved reason
preserved. Original CSV museum/country labels are clearly marked unverified;
there are no new accepted holding assertions, current display claims, images,
nationalities or masterpiece selections in this phase.

| New artwork metadata | Records |
|---|---:|
| Painting supported by matched source | 28,897 |
| Drawing supported by matched source | 1 |
| Artwork type unknown | 65,828 |
| Parsed creation dates within the cutoff, still unvalidated | 69,614 |
| Creation dates needing review | 25,112 |

An unknown or ambiguous date remains unknown in numeric date fields. The
original wording remains in the CSV and, where appropriate, an explicitly
unverified date label. Supplied closed dates are parsed without inventing years.
Known post-1970 creations are excluded; crossing/unknown dates can be stored in
review. Date eligibility alone is not publication or museum evidence.

An additional wording audit found only one retained supplied date mentioning a
year after 1970: `1822, restored 2011`. It remains in review with the original
wording; the restoration year is not substituted for a creation date. See
`date-wording-review.json`.

## Storage and publication

Migration 0017 adds `unknown` to artwork types, the `research_candidate` flag,
an indexed review queue and `research_artwork_links` with a foreign key to the
immutable source record. A database constraint prevents publication while the
candidate flag or unknown type remains. Future reconciliation must validate
identity, dates/content scope, type and evidence before clearing that flag.

These are actual `artworks` rows. Without a reconciled artist or accepted museum
membership, they do not appear in public painter timelines or museum holdings.
They can be reviewed through the database and their indexed source links. This
phase does not create a new editorial UI or automatically validate them.

Stable official object IDs, exact source URLs, existing citations and previous
research links are checked before insertion. No object is merged by generic
title or painter name. Source-only records use a CSV fingerprint identity, which
identifies a supplied candidate rather than proving a distinct physical object.
Unrecognized cross-source duplicates may require later editorial reconciliation.

## Reproduction and evidence

`apps/server/cmd/retain-research` defaults to a read-only plan:

```
retain-research -dir NEW_DIRECTORY
retain-research -dir REVIEWED_DIRECTORY -apply
```

The checked manifest has 105 chunks of at most 1,000 entries. Every target batch
must match the source snapshot checksum, all six original CSV cells, and the
official matched-fact checksum/state. An entry checksum prevents changing an
already-applied plan silently. Source evidence and prior resolutions are never
rewritten. Each batch is atomic under the existing ingestion advisory lock.
COPY and set-based inserts avoid per-artwork database requests. Database audit
triggers preserve new artwork history. Replay of the first real local batch
created zero rows; no fixtures or test databases were used.

Production committed an uninterrupted prefix of 36 batches before the worker
was stopped to improve execution on the shared-core instance. The resumed worker
uses accurate statistics for every temporary join table and transaction-local
`jit=off`; the pinned plan and validation rules are unchanged. The database
ledger confirmed all 36 complete batches before resuming at 37. Recent batches
dropped initially from roughly a minute to about 4–5 seconds, but later batch
durations varied under database load. The remaining 69 batches completed in
2,966 seconds on `db-f1-micro`; the adjustment did not eliminate the instance's
I/O and CPU limits. The optimized worker also
replayed actual local batch 100 without creating anything. Receipts:
`production-optimized-resume.json`, `production-optimized-import.jsonl`, and
`local-optimized-replay.jsonl`.

The original input SHA256 is
`210a729ead48d12b0f228eb9e1fe0c5a6708750b196be38ddfbbb270aa1355c8`.
The full plan, manifest and checksum receipt remain in this directory. A private
archive is stored at
`gs://artline-508319-images/research/expanded-review-artworks-20260912/review-artwork-plan.tar.gz`.
The original CSV and official source captures are preserved in the prior receipts.

Backups were completed before writes:

- Local archive: `/Users/vadimdulub/Library/Application Support/Artline/backups/review-artworks-20260912/local.dump`;
  SHA256 `f0ed63cfcbc45e9bb4a3ed4558047a640b17ce43a114267485059860c4c0b52f`.
- Production Cloud SQL managed backup: `1789239422769`, status `SUCCESSFUL`.

Production target is `artline` on `artline-508319:europe-west1:artline-postgres`.
The same checksum-pinned plan is applied through the authenticated Cloud SQL
proxy; database credentials are not written to the plan or receipts. Existing
public API/web revisions remain in service. Unrelated in-progress UI changes
are not included in this database operation.

[Read-only verification](verification.sql) compares counts, evidence mappings
and complete new-artwork content without depending on generated UUIDs. The local
database retains three extra archived artwork/artist pairs from an earlier
attribution correction; this historical difference is intentional. The actual
batch is not evidence of performance at ten million artworks; that load test
remains outstanding.

The read-only plan for a real 100-work review page uses
`artwork_research_review_page_idx` (22.5 ms locally). A separate 100-entry
identity check uses exact ID/URL/source-link indexes (47.1 ms locally), with no
per-entry full-artwork scan. Plans are preserved in `local-review-queue-plan.json`
and `local-identity-lookups-plan.json`.

A separate concurrent image-enrichment task may attach verified images to older
catalogue works. This import does not modify those fields. Final comparison of
the prior source phase checks metadata, identities, dispositions and non-image
integrity separately from that concurrent image work; the new incomplete
candidates still have no image or location claims.

Final live checks returned HTTP 200 for the timeline, catalogue artist search
and a five-item painter artwork page. The timeline reports 7,684 painters in its
current range; the Lansyer artwork endpoint returns a bounded five-item page
from 449 works. During bulk writes that artwork endpoint hit its eight-second
request deadline once; after import it returned successfully in 1.32 seconds.
See `live-during-import.json` and `live-verification.json`.

Across the source-resolution and incomplete-record phases, there are **104,146
new active review artworks** and **2,357 new active named painters**. Incomplete
creators remain object-level labels. Production contains 210,498 physical artwork
rows and 7,686 physical artist rows, including archived history; local contains
three additional archived pairs from the earlier correction. This import does
not publish new records or automatically add unresolved works to painter pages.
