# India: minimum 300 new museum artworks

The user instructed on 11 October 2026: “ok, go ahead with India, add at least
300 artworks.” This reactivated India immediately, retaining the earlier
**broad coverage first, then deepen** preference. The separate Southern Cone
continuation remains recorded in its own research directory.

## Verified production result

**350 new, distinct artwork records across 10 Indian museums**, plus source
enrichment for **9 existing artworks**. Existing records do not count toward the
300 minimum. Eight new museum institutions and ten verified country/city links
were added. All new works retain review status and are available in the unified
catalogue. No publication or current-display assertions were made.

| Museum | New artworks | Existing enriched |
| --- | ---: | ---: |
| Allahabad Museum, Prayagraj | 64 | 0 |
| Indian Museum, Kolkata | 64 | 0 |
| National Museum, New Delhi | 43 | 0 |
| Archaeological Museum, Old Goa | 32 | 0 |
| Archaeological Museum, Nagarjunakonda | 32 | 0 |
| Salar Jung Museum, Hyderabad | 31 | 0 |
| National Gallery of Modern Art, New Delhi | 30 | 0 |
| National Gallery of Modern Art, Bengaluru | 21 | 0 |
| Victoria Memorial, Kolkata | 21 | 9 |
| National Gallery of Modern Art, Mumbai | 12 | 0 |
| **Total** | **350** | **9** |

The new works comprise 212 paintings, 132 sculptures and 6 drawings. There are
235 records with source-supported creation bounds through 1970 and 115 with
unknown or unresolved creation dates, including ranges crossing the cutoff.
The latter retain null numeric years and explicit review treatment; they are
not asserted to be conclusively eligible by date. No creator lifespan, subject
date, acquisition date or invented year supplies an artwork creation date.
Eleven new artworks link to uniquely identified existing artists; other native
creator labels and qualifications remain explicit at object level.

The transaction added 350 accepted museum-holding assertions, 359 object source
citations and 359 native external identifiers. Holdings are archival collection
evidence, not current-display claims. Existing artwork metadata, images, creator
links and holdings were verified unchanged.

## Sources, selection and reconciliation

The primary source is the Government of India's
[Museums of India repository](https://museumsofindia.gov.in/repository/).
The captured [national directory](https://museumsofindia.gov.in/repository/museumDirectory)
contains 1,192 entries across all museum types. Eleven collection profiles and
432 selected native object pages were captured, using bounded category pages.
Native accession numbers and source record identifiers establish physical
object identity; no placeholder artworks were created for museum visibility.

`national-directory-delivery-ledger.csv` records every directory entry, the
eleven researched collection profiles, delivered artwork IDs and remaining
gaps. Directory entries are leads, not a claim of full national artwork coverage.
The portal's Goa painting-category count returned no objects in the selected
API pages; the delivered Goa selection therefore uses verified sculpture records.

Nine Victoria Memorial records were securely reused by exact native object URLs
already present in existing citation evidence, including legacy HTTP/double-slash
forms. NGMA branch accessions were checked across the selected records; none
collided. Bengaluru and Mumbai are separately identified branches of the same
national institution, supported by native profiles and directory addresses.
The existing Victoria Memorial canonical record was reused rather than creating
another institution under its alternate name.

Seventy-three captured candidates were held: post-1970 works (including five
with dates in titles but no Period field), unresolved photographic print dates,
potential manuscript/fragment component duplication, missing native titles,
one repeated accession, and three unresolved existing-object/version cases.
The latter include Amrita Sher-Gil's Self Portrait (3), Ravi Varma's Lady in
Moonlight, and Bharat Mata, which already has two existing source identities.
These were not counted as new artworks or merged without sufficient evidence.

The portal's Sunayani Devi record gives 1875–1962 in its Period field. The
[official NGMA biography field](https://museumsofindia.gov.in/repository/record/ngma_blr-acc-no-00355-466)
identifies these as her lifespan, so the delivered artwork has an unknown
creation date and preserves the original wording in evidence.

No new images were attached in this metadata batch. Authentic image enrichment
remains open under the existing source and image-use policies. No portal image
archive was downloaded and no synthetic artwork image was supplied.

## Verification and recovery

- `IN-wave1/plan.json.gz` and `plan-pin.json`: immutable reviewed selection,
  source-body hashes, scoped production preimages and identity decisions.
- `IN-wave1/applied.json`: committed production receipt; 350 new records and
  9 existing records separately counted.
- `production-verification.json`: ID-by-ID checks of the 359 records, native
  identifiers, citations, accepted holdings, date bounds and ten Indian cities.
- `public-directory-verification.json`: live HTTP 200 search responses for
  Partha-sarathi and Three Pujarins, including undated/review records.
- `public-dated-detail-verification.json`: live HTTP 200 detail response for
  Amrita Sher-Gil's Adam and Eve, with its source citation and NGMA holding.
- `public-api-verification.json`: initial calls to the chronology-specific atlas
  detail endpoint returned 404 for undated works, consistent with its dated
  scope. The ordinary catalogue searches above returned both records.
- `ops/test_india_300_dates.py`: sixteen cutoff, BCE, century, qualifier,
  unknown-date and conflicting-year cases passed without database fixtures.

Production Cloud SQL backup **1791710900885** completed successfully before
ingestion. Row-level preimages and post-transaction snapshots are under
`/Users/vadimdulub/Library/Application Support/Artline/backups/india-300-artworks-20261011/`.
Writes used the shared curated-ingestion advisory lock, object locks and drift
checks in atomic transactions.

The real local database was accessed read-only and remains at **310,209 artworks,
1,599 institutions and 23,479 artists**, matching the initial baseline. No local
fixtures, deployment or commit were required for this production data delivery.

The one-time global title audit used a parallel sequential scan; it is not a
scalable online-query design or a ten-million-row performance proof. Delivery,
enrichment and verification remained scoped to institution, creator and object
IDs. Full-scale load testing remains separate engineering work.

The requested minimum is complete. Nationwide India museum coverage, deeper
object selections and image enrichment remain incomplete and are tracked in
the directory ledger.
