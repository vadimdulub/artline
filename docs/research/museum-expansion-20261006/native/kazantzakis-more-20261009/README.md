# Nikos Kazantzakis Museum — reviewed continuation, pending production access

**105 artworks are fully reviewed but not yet added.** The last verified production count remains **118 catalogue works / 112 date-eligible works**. Applying this selection after fresh checks would bring those counts to **223 / 217**, above the preferred 200-work target. No production write or cloud backup was attempted in this continuation.

- [105 proposed artworks](proposed-production-artworks-001.csv)
- [All 110 source decisions](all-source-decisions-001.csv)
- [Pending-delivery state](pending-delivery-001.json)
- [Checks and remaining requirements](checks-001.json)

The selection comprises 104 drawings and one mixed-technique scenery detail whose physical type remains unknown, dated by dedicated object fields to 1940–1941. All retain review status and the literal unknown creator label. The separate EKT enrichment naming Giorgos Anemoyannis remains unresolved. Two corrupted title fields are corrected from clean title text on the same object page, with original strings and HTML preserved.

All 110 selected thumbnails were inspected, including 12 enlarged comparisons. Four records are explicit reproductions: **35035, 35036, 35037 and 35032**. Their production dates do not establish the copies’ creation dates. Copies 35036 and 35037 report their originals at ELIA; the visually distinct studies 35057 and 35056 are separately documented museum objects. Record **35062** remains held because its Emma 17 description conflicts with a jester-like thumbnail. Separate costume versions are distinguished by contours, pose, support and annotation. Reverse sketches, attached fabric samples, cut-paper proscenia and diptych panels remain one physical artwork. Source NC/ND labels are preserved; thumbnails are internal identity references, with no production image attachment.

The completed read-only identity check examined 128 existing artwork records and 149 citations, including all 118 museum works and 10 translated-title comparators. It found no exact source identities. The later full-row comparator snapshot could not run because Google Cloud token refresh requires reauthentication. No existing metadata, dates, images, statuses or holdings were changed. The real local database remains read-only.

Twenty offline regression tests passed. This supports the selection and preservation logic; it does not prove production delivery or performance at ten million rows. The production phase remains 920 new artworks and one existing-work link across seven museums. This pending selection is not included in those totals.

After `gcloud auth login` restores access, run `ops/museum-expansion-kazantzakis-more-comparators-20261009.py`, then `ops/museum-expansion-kazantzakis-more-apply-20261009.py prepare`. Preparation must recheck the live museum baseline, all 128 comparators and 921 prior campaign records. If state changed, create a reconciled new version; do not overwrite pinned evidence. A successful Cloud SQL backup and pinned execution plan must precede atomic application. Verify the committed rows and a zero-write replay before issuing a delivery receipt or updating museum counts.

Do not rerun the original review main function: it produced institution and visual artifacts before stopping at the missing comparator snapshot. `museum-expansion-kazantzakis-more-review-complete-20261009.py` finished the immutable editorial artifact from those results without claiming a production snapshot. No execution plan exists yet.

The selected index manifest retains one further candidate from page 6; additional archive pages were not fetched. Once this selection is applied, the museum will have passed 200 and attention can move to other institutions. [Official-source research for Kilkis](../kilkis-20261010/README.md) has begun while production authentication is unavailable. The full every-museum goal remains active.
