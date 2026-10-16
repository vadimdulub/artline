# Exhibition catalogue linking — 13 October 2026

Requested: at least 1,000 iterations, ten exhibitions per iteration, adding
and linking supported artworks created before 1980 and their creators. The
user explicitly authorized Google Cloud SQL and Secret Manager for this batch
and subsequently requested direct publication without a manual review queue.
The user subsequently approved Cloud Build and Cloud Run for the narrow artwork
viewer release described below. Unrelated Google services remain prohibited.
The real local catalogue is read-only.

## Frozen inventory and delivery plan

The production inventory contains 10,406 active exhibitions, 29,185 documentary
entries and 23,280 artist-participant references. All exhibitions are assessed
once in chronological order: 1,040 full ten-exhibition iterations and one final
six-exhibition iteration. Repeated preparation and retries do not count as new
iterations or new exhibitions.

Completed and independently verified in production on 13 October 2026:

- **4,199 new published artworks** and **1,043 new published creators**.
- **7,800 artwork-entry links** resolved.
- **8,250 existing artist references** resolved and **8,509 additional artist
  connections** added from exact object authorship.
- **4,199 accepted museum holdings** and **2,402 artwork–creator links**.
- **1,040 full ten-exhibition iterations**, plus six final exhibitions.

The artworks comprise 3,828 Cleveland and 371 Fitzwilliam objects: 2,386 prints,
1,256 drawings and 557 paintings. They include 186 works dated 1971–1979.
Unknown creation dates remain explicit for 275 works; 1,809 retain source-level
creator labels without a forced canonical creator match. No images were added.

The independent read-only snapshot audit checked every planned ID and field,
publication timestamps, source evidence, author links and holdings. It confirmed
that all 10,474 pre-existing artwork rows in the comparison set, exhibition
metadata, original entry labels and participation fields were preserved.
See [`delivery.json`](delivery.json) for verified totals and unresolved reasons.
The real local database received no writes.

This is catalogue reconciliation, not a claim that all historical checklists
have been transcribed. 8,658 inventoried exhibitions have no captured entries.
There are also 1,776 unresolved artwork-entry references and 12,816 unresolved
artist references, with source/identity/date reasons recorded. These are research
gaps, not a manual approval queue for the user.
Each iteration records checklist gaps explicitly and leaves checklist completeness
unchanged. No artworks are invented for an empty checklist.

## Evidence and matching

- Cleveland: selected native object IDs, exact accessions, official medium,
  creation intervals, original date wording, legal status, creator descriptions
  and current ownership evidence. Public API metadata pages are retained with
  retrieval receipts and SHA-256 checksums; no image files are downloaded.
- Fitzwilliam: previously captured native object records, accessions, original
  exhibition references, maker IDs and acquisition evidence. A documented
  pre-1980 acquisition establishes prior existence without inventing a creation
  year. Qualified and unknown dates remain explicitly unknown where necessary.
- Art Platform Japan: 1,355 official native artist profiles, linked using
  explicit source IDs/authority IDs or unique source names with matching life
  dates. Original Japanese labels and aliases remain intact. Profiles that
  collide with existing identities are not duplicated or silently merged.

Native object and institution/accession matches precede creation. A title alone
does not establish the same object. A plate date is not a physical impression
date; explicit printing years are retained separately from the original full
date label and source numeric fields. New works with unsupported date bounds,
whole bound portfolios, version conflicts or excluded media are not forced in.
Creator qualifiers such as “after,” “imitator of,” and “attributed to” remain
source labels and are not converted into unqualified primary authorship.

All new accepted records have `published` status and publication timestamps.
Existing unrelated statuses are not rewritten. Historical event dates, original
entry labels, catalogue numbers, occurrence scope and participation distinctions
are preserved. A holding is not a current-display assertion.

## Storage, procedures and verification

Evidence and iteration receipts:
`~/Library/Application Support/Artline/source-metadata/exhibition-catalogue-links-20261013/`.
The authoritative frozen plan is `plan-v3.json.gz`; earlier plans are unexecuted
preparation artifacts. Backups and row preimages are under
`~/Library/Application Support/Artline/backups/exhibition-catalogue-links-20261013/`.

Procedures:

- `ops/exhibition_catalogue_collect_20261013.py`: bounded official source capture.
- `ops/exhibition_catalogue_links_20261013.py`: offline planning and resumable
  production transactions, each scoped to ten exhibitions.
- `ops/exhibition_catalogue_verify_20261013.py`: independent read-only field and
  identity verification across the full frozen cohort.
- `ops/test_exhibition_catalogue_links_20261013.py`: identity ambiguity, authority
  conflict, name-order, duplicate prevention and qualified-year tests.

Each transaction uses ingestion locks, checks current identities against its
preimages, preserves existing source evidence, and verifies resulting entry and
participant links. Receipts are saved only after commit. Scoped production query
plans were inspected against the actual catalogue; sampled entry, participant
and native-identifier lookups executed in approximately 5–8 ms. This is not a
ten-million-row load test. Six focused identity tests pass.

Catalogue verification uses production SQL. The direct artwork viewer previously
reused the timeline date predicate, rejecting supported exhibition objects with
1971–1979 or unknown dates. The API fix scopes inspection to the requested
UUID and retains active-record, creator and source-backed selection/holding
checks, without applying timeline bounds. Timeline discovery is unchanged.
Read-only tests against real production records cover both date cases and a
missing object; atlas and HTTP API tests pass. The user explicitly approved this
API deployment. Its build replays the currently serving source and changes only
`ArtworkVisible`; unrelated local edits are excluded. Candidate and live API verification passed for older, 1971–1979 and unknown-date
objects, plus a missing UUID. Revision `artline-api-exhibition-detail-1013-v1`
serves 100% of API traffic; runtime configuration is preserved. See
[`deployment.json`](deployment.json). No image delivery or translation is involved.

The first isolated release build exposed a stale Books test expecting `limit=151`
to be rejected, despite the deployed Books handler accepting up to 300. That
expectation also fails against the unchanged baseline. The replacement build
runs atlas and HTTP API tests with this one unrelated legacy test excluded;
the current workspace's updated suite passes without exclusions. The failure
and baseline reproduction are retained with the release receipts.

Sources: [Cleveland Open Access API](https://openaccess-api.clevelandart.org/),
[Art Platform Japan](https://artplatform.go.jp/artists),
[Fitzwilliam collection](https://data.fitzmuseum.cam.ac.uk/).
