# Nicosia museum and artwork expansion — 7 October 2026

**Prepared, not uploaded.** Production Google Cloud authentication expired during the read-only audit. The subsequent connection check failed with `Reauthentication failed. cannot prompt during non-interactive execution.` No Nicosia museum or artwork writes have been made to production or the local catalogue in this pass.

The user authorized adding Nicosia museums and their artworks to production. The scope covers both sides of Nicosia and its immediate metropolitan municipalities. It does not automatically include every rural museum in Nicosia district. Institutions remain in review; holding evidence never establishes current display.

## Prepared batch

| Item | Count |
|---|---:|
| Identified institutions | 55 |
| Missing from the preserved production institution snapshot | 51 |
| Existing institutions reconciled | 4 |
| Artwork candidates after source-duplicate reconciliation | 620 |
| Candidates with creation dates through 1970 | 514 |
| Named-creator candidates with unknown/unclassified dates, for review | 106 |
| Institutions with artwork candidates | 12 |
| Confirmed duplicate object pages merged | 3 |
| Other source records held | 68 |
| New production writes/publications/display claims | 0 |

These are source candidates, **not 620 guaranteed new database objects**. Live production identity reconciliation must decide which are existing records to link, new records, or unresolved duplicates. The 106 unknown-date objects must remain in review and do not count toward eligible pre-1971 totals. More object research remains for the other 43 institutions; no minimum of 100 per museum has been achieved or claimed.

| Institution | Prepared objects |
|---|---:|
| Makarios Byzantine Museum and Art Galleries | 225 |
| CVAR | 145 |
| Cyprus Museum | 99 |
| A. G. Leventis Gallery | 98 |
| Leventis Municipal Museum | 31 |
| Archbishop Kyprianos Ecclesiastical Museum | 7 |
| Bank of Cyprus Cultural Foundation | 5 |
| Museum of the George and Nefeli Giabra Pierides Collection | 3 |
| Museum of the History of Cypriot Coinage | 3 |
| Cyprus Folk Art Museum | 2 |
| Lapidary Museum | 1 |
| Dervish Pasha Mansion | 1 |

## Evidence and review decisions

Institution identities were compared against a read-only snapshot of 1,746 production institution records. Sources include the [Nicosia Municipality directory](https://www.nicosia.org.cy/en-GB/discover/museums/), [Nicosia Tourism Board city directory](https://visitnicosia.com.cy/meet-nicosia-meet-culture/museums-art-institutions/), the northern Department of Antiquities directory, museum websites, the University of Cyprus directory, and primary institutional reports. The final two additions are Alparslan Türkeş House Museum and the Museum of Turkish Cypriot Islamic Arts.

The State Gallery's SPEL and Majestic venues remain one existing institution. The Makarios Byzantine Museum and Art Galleries are one institutional complex. The two Bank of Cyprus museums are distinct from the existing parent foundation. Rural district museums, the Mitsero Kouroussis Museum, Saçaklı Ev, and the unresolved Paraskevaides museum lead are documented separately in the gaps file. This is a reconciled list of identified institutions, not a claim that every possible institution has been discovered.

The [Makarios native catalogue](http://www.makariosfoundation.org.cy/bmcen.html), [CVAR paintings catalogue](https://cvar.severis.org/en/explore/collections-archives/paintings/), [Leventis Gallery catalogue](https://leventisgallery.org/artworks/), [Leventis Municipal collections](https://leventismuseum.org.cy/permanent-collections/), and smaller museum/municipal object descriptions provide item-level evidence. The official Department of Antiquities *Ancient Cyprus: Cultures in Dialogue* (Nicosia 2012) identifies Cyprus Museum objects by lender and inventory, separately from the temporary Brussels exhibition. Its original PDF and hashes are retained; column extraction and visual checks preserve the object/date/inventory layout.

- Native inventory numbers, creator qualifications, provenance, and source date labels remain literal evidence. Website authors, acquisition dates, depicted events, reigns and publication timestamps are not silently substituted for creation dates.
- CVAR calendar dates such as `1965-03` mean March 1965; `1924-5` is an abbreviated year range. The source-specific parser distinguishes them.
- AGLG 276, 454 and 315 each had duplicate native pages. One object retains both source identities and metadata. AGLG 557 was assigned to two differently titled miniatures; both are held.
- Unknown Leventis creation-year fields remain unknown. Named-creator museum records are retained for review under the explicit incomplete-data preference; they are not declared eligible or published.
- Anonymous Byzantine icons and ancient art objects are supported as such. No creator identity is invented, and source schools/attributions remain object-level labels until reconciled.
- Hambis collection pages cover both Nicosia and Platanisteia. Unverified branch assignments remain held. The former Zampelas website serves unrelated gambling content and was rejected as museum/artwork evidence.
- University directory and school-visit evidence establish museum identity but do not freshly verify opening. HTTP denials are recorded. The Makarios public HTTP URL is preserved because its HTTPS certificate failed; the evidence is not mislabelled as HTTPS.
- No artwork image assets were downloaded or changed. The documentary PDF contains its published catalogue illustrations. No image rights or matching decision is implied.

## Files and validation

- `prepared-summary.json`: exact prepared counts and blocking condition.
- `institution-plan.json.gz`: 55 institutions, existing preimages and identity evidence. The earlier 53-institution plan is preserved as superseded.
- `museum-coverage.csv`: all institutions, object counts, sources and individual gaps.
- `artwork-candidates.json.gz` and `artwork-candidates.csv`: the 620 selected object candidates, including unknown-date review flags.
- `research-gaps.json.gz`: unresolved institutions, scope exclusions and withheld artwork records.
- `captures/`, `pages/`, `artwork-pages/`, `artwork-indexes/`: immutable source responses, SHA-256 receipts and extraction records.
- `production-baseline.json.gz` and `all-institution-identities.json.gz`: production read-only snapshots taken before authentication expired.

Backups and prepared preimages are under `~/Library/Application Support/Artline/backups/nicosia-museums-20261007/`. No local catalogue fixtures were created. Disposable PDF renderings and extraction files are under `/tmp`.

The 12 offline checks in `ops/test-nicosia-artwork-candidates-20261007.py` passed. They cover real source hashes, date handling, unknown-field preservation, the Horned God inventory/date, the Roman date of the Aphrodite copy rather than its Hellenistic original, duplicate reconciliation, and institution coverage. They do not replace live database constraints or production verification.

## Resume production delivery

1. The user must restore the existing account with `gcloud auth login vadim@alingva.com`. This is authentication renewal, not another request for ingestion approval.
2. Confirm access to `artline-508319:europe-west1:artline-postgres`, database `artline`, using the existing production-only connection helper. Do not expose database credentials in logs or reports.
3. Confirm a successful full-instance recovery backup and save its actual API response as `production-backup.json`, with the backup under the `production` key. The institution apply phase checks instance/project/status. The last previously confirmed backup, before this pass, was `1791368721734`; do not describe it as newly verified.
4. Refresh institution identity/version checks. `ops/nicosia-museums-20261007.py institution_apply` preserves existing institutions, checks names/slugs and locked preimages, and inserts new institutions in review with citations. If the prepared versions have changed, preserve the old plan and regenerate it against production.
5. **Artwork production planning/delivery remains to be completed.** Reconcile native identifiers and aliases, inventory within institution, creators, titles/translations, dates, dimensions and physical versions. Shared collection-page/PDF URLs are not unique object identities: use `scheme` plus `source_id` and museum inventory. Do not pass these shared URLs to a generic URL-only duplicate matcher. Preserve `alternate_sources` for the three reconciled duplicates. Check anonymous generic icon subjects as distinct physical objects using their native catalogue evidence, without assuming identical subject titles identify the same object.
6. Apply supported links at the authorized editorial-confidence threshold, with fresh locked object/version checks, preimages and audit history. Create missing objects in review. Preserve existing dates, images, qualified labels and publication states; unknown-date candidates must retain null creation bounds and review status. Use accepted holding assertions only where the source supports them, never display assertions.
7. Read production back using a separate read-only connection. Verify inserted rows, citations, holdings, images/publication invariants and per-museum counts. Update this report with committed and held totals; no prepared count substitutes for a committed receipt.

The earlier all-museum 1–100 expansion worker also stopped with `needs_attention` after two delivered waves, while planning wave `expand-1-100-wikidata-003`. Its pinned shared scripts were not edited. After authentication is restored, inspect its saved status and resume the existing guarded worker without a duplicate active process.
