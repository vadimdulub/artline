# US and European museum catalogue expansion

Date: 2026-09-09. Audience: Artline owner. Baseline to verify: 715 artworks, 56 institutions.

The planning tool is unavailable in this workspace; this file is the working plan.

## Scope and success criteria

Build a source-backed museum discovery inventory for the United States and Europe, audit country and source coverage, and import substantially more eligible museum painting metadata into local PostgreSQL. A discovery registry is not a verified census. Distinguish institutions, venues, current holders, online catalogue records, total objects and paintings. Preserve metadata and image rights independently. No images, publication, deployment or commits. Artwork creation cutoff remains 1970; ambiguous dates and creator identities are staged for review rather than guessed. Preserve all existing editorial work.

Primary evidence: national museum directories, museum-owned bulk datasets/APIs and documentation, object records and terms. Wikidata may supply explicitly labelled CC0 discovery candidates, not authoritative holdings or completeness claims. Include country coverage gaps and document geographic boundary choices.

## Work phases

1. Complete — discovery and baseline. Verified 715 artworks/56 institutions, structurally audited 111 supplied sources; independent US/European directory and Louvre research completed, with explicit coverage gaps.
2. Complete — follow-up and implementation. Captured pinned NGA metadata (145,707 objects; 4,455 painting records), verified 1,510 eligible records linked to 356 existing authorities, implemented checksum-safe staging and catalogue import. Collected Muséofile and country-scoped Wikidata candidates; remaining bounded retries recorded separately. Full Go test suite with isolated PostgreSQL fixtures passes.
3. Complete — apply and verify. Added 1,508 artworks, 3,021 citations, and 10,324 separate research source rows. Catalogue is 2,223 artworks/56 institutions. New and older imports replay without changes; tests, vet, live bounded API and scoped query plans pass. Backup and before/after receipts retained. Museum discovery covers 57/58 attempted partitions, with Italy unavailable, and is explicitly not a census.
4. Complete for this pass — synthesis and deliverable. Final source-linked seven-page PDF contains 32 hyperlinks; every page rendered and visually inspected, link/content/count checks passed. One proof-layout correction removed two nearly empty continuation pages. Full museum/source registry remains in PostgreSQL and an auditable JSON snapshot. The report explicitly distinguishes this delivered pass from the unfinished all-museum/all-catalogue ambition.

## Evidence gaps

| Claim family | Evidence needed | Confidence now | Next action |
|---|---|---|---|
| US art museum inventory | IMLS retired 2018 named directory, current NMS privacy; 940 Wikidata candidates | High on definitions, incomplete current coverage | Obtain reusable current named frame and reconcile branches |
| European inventory | 1,216 Muséofile rows; 12 national source routes; country graph snapshots | Official France complete downloaded snapshot, not national/all-Europe census | Italy missing; other national-directory reconciliation pending |
| Louvre volume | >500k total entries and >10k painting-department records; Etalab text terms | High broad count/terms, exact live department count uncertain | Obtain official paintings CSV after access issue resolves |
| Bulk artwork import | Pinned NGA CC0 export; 4,455 painting records staged, 1,508 added | Verified local data, tests and receipts | Reconcile 1,699 remaining local artist-authority records |
| Existing application safety | Backup, rollback, tests, index plans, API and no-op replays | Verified for tested scope, not 10m-row load | Larger capacity and refresh tests remain |

## Follow-up findings

NGA empty date labels may have artist life years in searchable numeric dates: require meaningful literal creation dates and compare both representations. `artist` and `painter` roles can both identify the sole current maker of a classified painting; preserve qualifiers and stage uncertain identities. Separable panels are not duplicates; virtual covers and inseparable children are deferred. National directory definitions vary, and no global candidate count is a complete active art-museum census. Metadata reuse does not authorize reproduction downloads.

Stop catalogue requests on persistent access denial. Do not substitute general website discovery for verified object metadata. Deliver any incomplete geographic/source coverage explicitly rather than claiming all museums or all artworks were collected.
