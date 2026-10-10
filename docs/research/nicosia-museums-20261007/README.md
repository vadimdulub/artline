# Nicosia museum and artwork expansion — 7 October 2026

**Uploaded to production and independently verified.** Authentication was restored. The museum transaction committed at 12:20 UTC; the main artwork transaction committed at 13:15 UTC, followed by one additional Cyprus Museum object at 13:16 UTC. Read-only verification used separate database connections after each artwork commit.

The user authorized production additions. This pass covers both sides of Nicosia and its immediate metropolitan municipalities, not every rural museum in Nicosia district. New institutions and artworks remain in review. Production storage does not imply public publication or current display.

## Committed result

| Item | Count |
|---|---:|
| New institutions | 51 |
| Existing institutions documented | 4 |
| New artworks | 616 |
| Existing artworks linked to their documented museum | 5 |
| New links to verified existing painter records | 45 |
| Artwork source citations | 624 |
| Institutions receiving selected artwork records/links | 12 |
| Museums now at least 100 records | 4 |
| Museums still below 100 records, including zero | 51 |
| Museums still without artwork records | 42 |
| New artworks with unknown numeric creation dates | 104 |
| New publications, display claims, image changes or local DB writes | 0 |

**The minimum-100 target is not complete for all museums.** The counts include review records with unknown numeric creation dates. In particular, Leventis Gallery has 103 records but only eight currently classify as date-eligible. Some specialist institutions have no selected art objects within the catalogue scope. The saved gaps identify missing object sources and unresolved identities; no quota-based records were invented.

| Institution with records | Production artworks | Date-eligible through 1970 |
|---|---:|---:|
| A. G. Leventis Gallery | 103 | 8 |
| Archbishop Kyprianos Ecclesiastical Museum | 7 | 7 |
| Bank of Cyprus Cultural Foundation | 7 | 7 |
| Byzantine Museum and Art Galleries, Archbishop Makarios III Foundation | 225 | 222 |
| Centre of Visual Arts and Research (CVAR) | 230 | 225 |
| Cyprus Folk Art Museum | 2 | 2 |
| Cyprus Museum | 100 | 99 |
| Dervish Pasha Mansion — Ethnographic Museum | 1 | 1 |
| Lapidary Museum, Nicosia | 1 | 1 |
| Leventis Municipal Museum of Nicosia | 31 | 31 |
| Museum of the George and Nefeli Giabra Pierides Collection | 3 | 3 |
| Museum of the History of Cypriot Coinage | 3 | 3 |
| State Gallery of Contemporary Cypriot Art | 6 | 6 |

All 55 institutions, including zero-count museums, are listed in `production-museum-coverage.csv`. These counts are the verified snapshot after this pass; other authorized jobs may subsequently add records.

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

Additional live-production reconciliation and editorial decisions:

- Five existing artworks were matched to primary object records and linked without changing their titles, dates, creator links, images or publication states: CVAR's *Derviş Mansion* and *Rooftops at Nicosia*, and Leventis Gallery's *Tremetiousia*, *Those Left Behind* and *Bathers in Kyrenia*.
- Boudin's Leventis AGLG 276 is a separate canvas from the smaller wood/cardboard paintings with related titles already in the database. Debucourt's AGLG 450 is a separate print impression from two existing NGA impressions. Physical-object evidence and compared IDs are recorded in `editorial-identity-resolutions.json`.
- Incomplete creator label “Marc” was not assigned to Franz Marc. Parenthesized given names are preserved: “[Bordone (Benedetto)]” was not assigned to Paris Bordone. Original labels remain in citations and, where unresolved, on the object record. Exact full-name/alias links also check known life dates and creation chronology.
- One original parser hold was resolved after visually checking catalogue pages 180–181: decorated shell H19-1935, catalogue 133. Its source period, “Hellenistic/Roman period”, remains literal; numeric creation bounds remain null and the object stays in review. The description and illustration establish carved decoration rather than an unmodified natural specimen. This follow-up brings Cyprus Museum to 100 records, with 99 date-eligible. The other 67 held source records remain unresolved.
- Makarios native object evidence uses its actual HTTP URLs. The database requires HTTPS for location assertion reference URLs, so those assertions use the independently captured HTTPS institutional directory as an identity anchor; the actual HTTP object URL, hash and object facts remain separately cited and explicitly named in the holding evidence. No HTTPS fetch of the native object URL is claimed.

## Delivery safeguards and verification

The successful Cloud SQL backup `1791368721734` was rechecked and its actual response saved in `production-backup.json`. It is an existing full-instance recovery backup, not a newly created backup. Current transaction preimages and after-images are under `~/Library/Application Support/Artline/backups/nicosia-museums-20261007/`, including the follow-up subdirectory.

Each delivery checked the production database identity, pinned source hashes and reviewed plan, took the existing curated-ingestion advisory lock, and locked/rechecked institution and artwork versions. Native IDs, aliases, museum inventories, exact/translated titles, creators, dates, dimensions and physical versions were reconciled before insertion. Original creators, metadata, images and publication states on existing records were preserved. Shared catalogue/PDF URLs required an object identifier; the URL alone was never treated as a unique object.

The 15 offline checks in `ops/test-nicosia-artwork-candidates-20261007.py` passed. They cover source hashes, date parsing, unknown fields, accession versus creation dates, original versus copy dates, source duplicates, conflicting inventories, institution coverage, parenthesized creator names, incomplete labels and impossible creator chronology. The follow-up additionally asserts the visually checked caption, inventory, null dates and source hash. Post-commit database verification checked all 621 affected artwork records, 624 artwork citations, accepted holdings, selection evidence, review/date/image/publication invariants and all 55 institution counts.

Query plans were recorded. Enrichment was scoped to candidate IDs, related institutions and verified creators; the one-time global title identity lookup was inspected. These checks do not constitute a 10-million-row load test.

An earlier read-only planning connection ended unexpectedly while closing its transaction, after saving snapshots; it made no artwork writes. That plan was archived, the read-only transaction lifetime was shortened, and a fresh plan passed production version checks before the successful write. No approval or source identity guard was bypassed.

## Files

- `delivery-summary.json`: exact committed totals and remaining gaps.
- `institutions-applied.json`, `artworks-applied.json`: committed receipts, IDs and pinned plan hashes.
- `production-verification.json`: independent verification of the main batch.
- `nicosia-cyprus-museum-followup-20261007/`: separate source, plan, committed receipt and verification for catalogue 133; its verification contains the final museum counts.
- `production-museum-coverage.csv`: final production counts, date eligibility and gaps for all 55 institutions.
- `artwork-plan.json.gz`, `editorial-identity-resolutions.json`: production identity decisions and preimages.
- `prepared-summary.json`, `museum-coverage.csv`, `README-prepared-before-auth.md`: historical preparation state, superseded for delivery status.
- `artwork-candidates.json.gz` and `.csv`: original 620 selected candidates; the one follow-up is separate.
- `research-gaps.json.gz`: original institutional and source gaps; its catalogue-133 hold is resolved only by the documented follow-up.
- `captures/`, `pages/`, `artwork-pages/`, `artwork-indexes/`: immutable source responses, hashes and extraction records.

## Broader authorized museum expansion

The existing 1–100 museum expansion worker was resumed after Nicosia verification, using its dedicated production proxy and unchanged 13 pinned scripts. Its frozen cohort is separate from these newly added institutions. `broader-worker-resumed.json` records the launch; live progress remains in `../all-museums-minimum-100-20261006/expansion-1-100-20261007/worker/status.json`. A running worker is not a claim that every museum has reached the target.
