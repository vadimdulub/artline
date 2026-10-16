# Continued illustrated catalogue expansion — 11 October 2026

The user instructed “ok, go ahead find more and more” after the verified
3,002-work French printmaking delivery. This continuation first reconciles the
188 previously reviewed French reserve prints against current production, then
researches a substantial American printmaking selection from 1800–1970.

This continuation is complete: **2,557 new production artworks and 2,557
verified primary images** — 188 additional French prints and 2,369 American
prints. The American batch covers 578 artists, including 170 newly added artists.
Source leads, reserves and prepared files do not count as new production works.

## French reserve

All 188 reserve objects are individually accessioned Paul Gavarni prints. Their
source records and actual prior visual approvals are checksum verified, and
their creator identity, native IDs, accessions and image similarities are
rechecked against current production before delivery. Evidence is under
`french-reserve/`; execution is `ops/printmaking-continuation-20261011.py`.
Earlier 3,002-work evidence remains immutable.

The fresh audit compared 1,635 existing Gavarni images and found no additional
holds. All 188 records passed backend date-scope and holding-evidence checks;
all 188 public images matched their prepared checksums. Seven anonymous detail
and artist-browsing samples passed. The French selection now contains 3,190
works. See `french-reserve/production-verification.json`,
`french-reserve/public-verification.json` and `french-reserve/delivery-manifest.csv`.

Three source labels require additional physical-date research: Yale objects
80082, 80437 and 81054 state “ca. 1935” for Paul Gavarni (1804–1866). Whether
these denote later impressions or source-date errors remains unresolved.
Production citations record that uncertainty; no 1835 substitution or
posthumous-print claim is made. Supplied dates and review status are preserved.
See `french-reserve/source-date-followup.json`.

## New topic

A bounded discovery comparison found American printmaking the strongest next
illustrated source pool among American, British and Japanese searches at Yale.
Search counts are leads, not accepted objects or coverage. The new pass captures
at most 45 pages of 100 metadata identities, then selects individual objects by
actual creator, literal creation date, physical print identity, documented
holding and exact official IIIF image. The completed batch delivered 2,369 new illustrated
American works, meeting the 2,000–3,000 target. All passed backend date-scope
and source-backed holding checks. All public image checksums and seven
anonymous artwork-detail/artist-browsing samples passed.

The [American delivery ledger](../american-printmaking-20261011/README.md)
tracks this separate batch. These are editorial subjects, not new movement
classifications. No current-display claim follows from a museum holding.

Selected image delivery continues the user's existing approval. Actual rights
labels and credits remain separate from that authorization. No local database
connection, fixture, commit or deployment is used. Backups are kept in
`~/Library/Application Support/Artline/backups/printmaking-continuation-20261011/`.
Cloud SQL backup **1791734142380** completed successfully before this delivery.


The [completion summary](completion-summary.json) combines only these two
new batches. The earlier 3,002 French prints and 2,500 Soviet Realism works
are excluded from the 2,557 new-addition total. Every new record retains review
status and is available through the unified catalogue.
