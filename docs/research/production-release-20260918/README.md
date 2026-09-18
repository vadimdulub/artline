# Production catalogue and image audit — 18 September 2026

The user requested production data/image parity, deployment of the latest code,
clear commits and a Git push. When concurrent UI work appeared, the user asked
to wait and include it after completion. That work subsequently recorded 60
passing browser scenarios; it was reviewed and committed as `0cfcc28` for the
follow-up web release. A subsequent All-axis edit was included as `3c8300f`
after 45 unit tests and 36 additional read-only browser scenarios passed. The
earlier tested baseline had already gone live when the wait instruction arrived.

## Recovery and scope

Cloud SQL backup `1789759341285` completed successfully before any production
data change. Audits used read-only local and production connections. There were
no local catalogue writes, fixture inserts, test databases, deletions, automatic
publication, new on-view claims or Terraform apply. Production-only records and
target-specific provenance were preserved.

Raw receipts below are retained beside this report and intentionally ignored by
Git, consistent with the repository's research-evidence policy. Do not delete
them as build output. Temporary test screenshots and isolated build trees live
under `/tmp/`, not Documents.

## Verified and delivered

- `before/*`: streamed inventories of every public-schema table in both
  databases, including counts and content fingerprints. Different UUIDs are not
  missing content; identity-normalized comparison is recorded in
  `content-before/*`.
- Shared artist and artwork metadata matched after identity normalization.
  Three local-only archived artists and three archived SMK artworks were not
  revived. Two additional non-archived artwork gaps were repaired below.
- All 546 sources, 355 connector configurations, 545 redirects, 23 checksummed
  research snapshots and 14,774 research-artwork enrichments matched after
  identity normalization. `content-summary.json` records the completed tables.
- `atlas-delivery.json`: additive migrations 0020, 0021, 0022 and 0024; 10,000
  book records, 4,092 creators, 9,988 creator links, 510 discovery terms, 10,000
  discovery projections and 10,000 event records copied and verified. Every
  copied book/event remains in review. The Books view exposes 8,685 date-eligible
  books, not every stored book. `atlas_drafts` remains empty.
- The source and destination Books/Events fields matched except ingestion
  clocks and locale-generated `search_text`. Local `lower()` and production
  `lower()` handle some Unicode capitals differently. The search projection is
  generated on each database, not copied or used to excuse source-data changes.
- `woodville-plan.json` and `woodville-delivery.json`: two existing, sourced
  review works, `wikimedia-artwork-q28026294` and
  `wikimedia-artwork-q28038359`, delivered with two media records, two media
  rights records, two media links, two existing holding assertions, two external
  identifiers and four citations. The object-level creator label remains
  “Richard Caton Woodville Jr.” No person biography, creator link, creation date
  or holding was invented. Royal Collection source evidence was preserved.
- `citation-review.json`, `citations-plan.json`, `citations-delivery.json`: 35
  missing original citations delivered and verified: 30 institution image-policy
  notes, three artist geography references and two artwork-identity references.
  These insertions did not alter entity facts, rights decisions or status.
- Citation differences caused by target-specific UUIDs, correction-plan hashes,
  timestamps, or valid alternative first-seen object references were retained.
  Twelve production SMK image credits use fuller institution wording; they were
  not overwritten with shorter local wording. Eight production-only
  source/institution relationships were preserved.
- Sampled differing image-rights evidence contains production-only
  `target_ids.cloud` and `institution_ids.cloud` delivery mappings. These are
  retained in `rights-difference-samples.json`; the sample is not a claim that
  every historical evidence payload is identical after removing those fields.

## Images

`storage-before.json` inventoried 80,222 storage objects and all 80,771 unique
database storage paths across both targets. Existing local bytes were checked
against database SHA-256/size where recorded, and against Cloud Storage MD5/size.
Legacy records without a database SHA-256 still received local-to-cloud byte
checksum comparison.

All 80,158 active local artwork/portrait paths matched cloud storage. Production
initially referenced 80,156 of these; the two Woodville record insertions attached
the other two images, whose bytes were already present and checksum-verified.
No new bulk image download or upload was necessary.

The independent [regional image round](../popular-painting-images-20260918-round9-regional/README.md)
finished during this release and attached six additional images to both
catalogues. `post-delivery.json` detected every new path, freshly checked its
local SHA-256, production database checksum/size and GCS MD5/size, and confirmed
**80,164 active image paths** in the final production state. That receipt also
re-read and exactly verified all rows inserted by this release. Final production
counts: 264,953 artworks, 13,450 artists, 859 institutions, 80,776 media records,
10,000 books, 10,000 events and 24 migration entries. This does not mean every
artwork has an image; it verifies the active images that are already catalogued.

The inventory also found 590 historical, inactive paths missing from both local
files and cloud storage. These include withdrawn Commons images, Italian rights
holds and an unused historical Wikipedia asset whose disposition still requires
review. They were not restored merely to make inventories identical. A separate
local-only Met image record had been explicitly withdrawn for depicting the
wrong artwork; its remaining local file was not uploaded or linked.

`public-images.json` verifies 20 actual public image responses by SHA-256 and
size, including recent Danish/Swiss selections and both Woodville works. This is
a delivery sample in addition to the full storage inventory, not a claim that
every HTTP image URL was downloaded again. Book covers are a separate,
versioned, on-demand remote manifest; a real Odyssey cover and source credit
were tested in the browser. The entire remote cover manifest was not downloaded.
After the final UI deployment, `public-images-final.json` rechecked the original
20 images plus all six newly delivered regional images: 26 public HTTP responses
passed SHA-256 and size verification.

## Verification and limits

Go package tests, read-only local Books/Events/Atlas integration tests, 547
existing Python operation tests and six release-audit tests passed. The final UI
passed 45 unit tests, ESLint and TypeScript. The first UI workflow recorded 60
passing read-only browser scenarios; the scale follow-up passed 36 scenarios.
Release-candidate checks are documented in the deployment report.

Unbounded provenance scans initially timed out and coincided with API deadline
failures on the small `db-f1-micro` production database. A later audit connection
also closed unexpectedly. The audit was changed to bounded, indexed keyset
pages, retaining completed immutable per-table receipts on resume. Resumed
receipts therefore have different observation times, not one global atomic
snapshot. Delivered rows have separate exact verification receipts. No database
capacity upgrade was performed. Sustained concurrent-load and 10-million-row
performance tests remain outstanding.

The remaining expensive historical research joins were stopped before the
final release tests. `research-identities.json` instead resolves snapshot UUIDs
by original source SHA-256 and compares every stored primary identity: all
115,258 research records, 39,514 resolutions and 94,778 artwork links are present
on both targets, with no missing or extra identities. This is an identity and
source-snapshot check, not a claim that historical execution payloads, embedded
target IDs and correction receipts are byte-identical. The per-table normalized
content audit remains partial for these three historical tables. Audit logs,
import execution receipts and editor accounts were not mirrored.

See [the deployment report](../../deployment-20260918.md) for immutable image
identities, traffic state and rollback commands.
