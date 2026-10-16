# Switzerland, then India — nationwide museum coverage

**India reactivated, 11 October 2026:** the user's subsequent instruction,
“go ahead with India, add at least 300 artworks,” has been completed in the
[India production pass](../india-300-artworks-20261011/README.md): 350 new
artworks across ten Indian museums, plus nine existing records enriched.
The sequence notes below preserve the earlier decisions and Swiss receipts.

**Sequence update, 11 October 2026:** the user subsequently requested Switzerland,
then Argentina, Uruguay and Paraguay. The [continuation record](../switzerland-southern-cone-museums-20261011/README.md)
tracks that priority. This directory remains the source of the earlier Swiss
evidence and delivery receipts; the India continuation is deferred.

The user confirmed the revised sequence again in this conversation and retained
the **broad coverage first, then deepen** strategy. See
`sequence-confirmation.json`.

Requested 11 October 2026. Switzerland's first three production batches are
verified; nationwide artwork coverage remains incomplete.
The national directory and institution reconciliation precede selected,
source-backed artwork and authentic image delivery. A directory entry is not a
verified artwork, and a collection record is not evidence of current display.

## Switzerland baseline

The [Swiss museum association directory](https://www.museums.ch/de/museumsbesuch/museen/museen-1852.html)
supplied 1,328 unique directory entries, including 310 with an art-museum category.
The first displayed category labels 213 entries as art museums; the larger 310
figure includes institutions with art as an additional category. These are
directory figures, not a claim that all entries hold eligible artworks, that
every venue is a distinct collection, or that neighbouring-country entries have
already been excluded. Country and duplicate institution identities require
individual reconciliation.

The initial production read found eight active institutions explicitly linked
to Switzerland, with 946 artworks assigned to seven as their primary holding
institution. Additional Swiss identities lack geography or duplicate labels;
accepted holding assertions and canonical institutions still need reconciliation.
No India institutions had an explicit country link in this initial query;
several named Indian institutions already exist without geography. This is not
a claim that India has no catalogue artworks.

## Verified Swiss production delivery

| Batch | New artworks | Existing works enriched | Museums | New institutions |
| --- | ---: | ---: | ---: | ---: |
| CH-wave1 | 39 | 1 | 10 | 5 |
| CH-wave2 | 31 | 3 | 9 | 8 |
| CH-wave3 | 20 | 1 | 9 | 8 |
| Unique campaign total | **90** | **5** | **27** | **21** |

Rietberg appears in two batches, so the museum total is deduplicated. These
deliveries added 94 accepted holding assertions and 95 source citations, with
27 verified Swiss city assignments. All 90 new artworks remain in review.
Existing metadata, images and publication states were preserved. No current
display assertions were added.

The third batch adds Jenisch, Thun, Toms Pauli, Interlaken, Deusser, Abegg,
Castello San Materno and Rehmann. It keeps workshop and model/execution labels
explicit. Thun's Klee lithograph is a separate inventoried physical impression;
the existing Abegg Triptych was reused, with the museum's qualified workshop
attribution preserved in its new source evidence.

One authentic Rietberg image was uploaded, attached and verified through the
public image URL. The [museum's municipal open-data release](https://data.stadt-zuerich.ch/dataset/mrz_drenowatz_sammlung)
explicitly distinguishes its public-domain image files from the dataset's
CC BY-SA metadata licence. Inventory RCH 1021 retains the photographer and museum
credit. Only three selected ZIP members were retrieved using HTTP byte ranges;
the complete 230 MB image archive was not downloaded. Two selected horizontal
scroll images proved to be sections and remain unattached. The accepted image
preserves the complete supplied painting field, is proportionally resized, and
is below 100,000 bytes.

Four object candidates remain held for version reconciliation: Langmatt's
Bonnard boulevard painting, Neuchâtel's Hodler landscape, and the Braque and
Gauguin candidates at La Chaux-de-Fonds. No duplicate artworks were added for
these leads. Thun municipal public art and Rehmann's 1951/2001 versions were
excluded from this museum selection.

`CH-production-verification.json` verifies all 95 selected artwork identities,
their accepted holdings, review-state safeguards and 27 Swiss institutions.
`CH-breadth-summary.json` records the campaign totals. The real local catalogue
remains unchanged: 310,209 artworks, 1,599 institutions and 23,479 artists, checked
against the initial read-only baseline.

## Scope and safeguards

- Initially Switzerland first, India second; the confirmed continuation is now
  Argentina, Uruguay and Paraguay. The user confirmed **broad coverage first,
  then deepen**: prioritize verified selections for unrepresented institutions
  before aiming for large per-museum totals.
- Artworks created through 1970; unknown dates and ranges crossing the cutoff
  retain explicit review treatment. No subject, accession or artist-life date
  is substituted for creation.
- Reconcile native identifiers, accession numbers, creator qualifications,
  object versions and existing records before production additions.
- Keep new works in review. Preserve existing pictures and historical statuses.
- Apply the existing source/image policies, retain actual rights and credits,
  and visually verify selected complete-frame image derivatives.
- Empty institutions do not receive invented works and remain outside museum
  browsing. Non-art directory categories remain research leads for eligible
  visual or decorative objects, rather than automatic artwork imports.
- The real local database is read-only. Source evidence stays in this research
  directory; backups and original images belong under Artline's Library data
  locations. No deployment or commit is part of this museum request.

## Evidence and continuation

`production-baseline.json.gz` captures institution identities and primary-holding
counts; `local-readonly-baseline.json` records the local baseline.
`CH/directory.json.gz` binds every index entry to the captured source hash.
`CH/directory-details/` preserves all 1,328 checked directory identities,
descriptions and native-site leads. The native-site pass records 1,051 successful
homepage captures, 166 source gaps and 111 websites requiring manual selection.
The bounded collection discovery pass captured 200 distinct collection-page
outcomes; retrieval alone does not verify a particular artwork.

`CH/directory-delivery-ledger.csv` records every directory entry, its native-site
outcome, collection-source leads, delivered artwork IDs, held candidates and
remaining gaps. This is the current delivery ledger;
`CH/directory-coverage.csv` preserves the earlier baseline reconciliation.
Neighbouring-country entries, multi-venue institutions and museums without
eligible object evidence still need individual review. Directory coverage is
not complete artwork coverage.

`CH-wave1/`, `CH-wave2/` and `CH-wave3/` hold immutable source selections, scoped
duplicate checks, pinned plans, atomic production receipts and geography
verification. The successful Cloud SQL backup is recorded in
`cloud-sql-backup.json`; row-level recovery snapshots and image originals remain
under Artline's Library data directories.

Argentina's initial official national-museum directory and the blocked open-data
homepage outcome are preserved in `AR/directory-discovery/`. No India production
ingestion was performed. Further country work is tracked in the
[confirmed continuation](../switzerland-southern-cone-museums-20261011/README.md).
