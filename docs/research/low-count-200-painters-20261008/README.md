# Random low-count painter expansion

Completed and verified 2026-10-08T21:32:20Z.

- **8,926 new production artwork records** for **200 randomly selected painters**.
- Every selected painter had **0–10 active artworks** at selection time and received **20–100 additional artworks**.
- All 8,926 additions were checked in PostgreSQL and found through the live unified catalogue API (282 pages, at most 50 records per page).
- New records retain review status as audit metadata and are available through the unified catalogue. Existing records were preserved inside each import transaction.
- **2,895 creation dates remain explicitly unknown.** Unknown dates are retained for editorial review; no artist lifespan was substituted for an artwork date. Explicit post-1970 dates, date conflicts and unresolved versions were excluded.
- This delivery adds catalogue metadata. **No new images were uploaded or attached.** Source image URLs remain preserved as identity evidence; no source rights label was converted into a different claim.

[Painter counts](painters.csv), [new artwork records](new-artworks.csv), [production verification](production-verification.json), [live API verification](api-verification.json), and [authorization](authorization.json).

## Sampling and evidence

The frozen seed is `de7c4bc589eac9ef74df0ac5d08b83cd`. The sample was drawn uniformly without replacement from 212 verified candidates: active individual production artists with 0–10 artworks, an unambiguous WikiArt identity, and enough additional source-supported objects to meet the requested minimum after duplicate, version and date checks. It is a source-supported sample, **not** a uniform sample of all 20,300 low-count catalogue artists. No country or popularity weighting was used, and no selected painter was substituted after freezing the cohort.

The audit found 824 exact WikiArt matches among 20,300 low-count artists; 388 had sufficiently large source lists for research. The frame excludes cultural traditions, collective creator profiles, exclusively architectural/photographic/sculptural profiles, a father–son alias conflation for Vicente Masip, and unresolved lifespan conflicts. See [sampling frame](sampling-frame.json), [cohort](cohort.json), [source feasibility](source-feasibility.json), and [preflight](preflight.json).

The WikiArt additions are grounded in explicit named-creator entries with stable content IDs and reconciled object links/titles in the artist's visible list. Source bodies, SHA-256 receipts, original retrieval times, translated-title checks and catalogue deduplication evidence are retained. Direct object pages were checked for every selected undated work and a sample of dated works, plus already captured pages. Missing types, media, dimensions, dates and holdings remain unknown. The selection is a user-requested personal study collection, distinct from museum designations. No holdings or current-display claims were inferred.

Two translated titles revealed existing works for Grigoriy Myasoyedov, leaving 19 WikiArt additions. The twentieth is a separately inventoried [Museum of the Academy of Arts drawing sheet](https://collection.artsacademymuseum.org/entity/OBJECT/49112), accession `НИМ РАХ КП-610/4139. Р-2197`. It contains a mountain-road sketch and three caricatures and is counted as one object. Its explicit nineteenth-century date, graphite/paper medium, dimensions and source provenance are preserved. The museum source remains separately labelled. A WikiArt entry labelled as a Zemstvo study remains held because it may be a detail of an existing composition; visual/source review did not establish a separate object.

WikiArt is used under the [user-approved source policy](../../ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026). Any source rights labels are preserved separately from that approval.

## Recovery and limits

Successful Cloud SQL backup: `1791493265929`. Recovery snapshots and logs: `/Users/vadimdulub/Library/Application Support/Artline/backups/low-count-200-painters-20261008/`. Per-painter transactions have immutable plan pins, source citations and a database audit marker; interrupted receipt writing can be recovered without creating duplicate records. Source code: `ops/low-count-200-painters-20261008.py`; pure source/plan tests: `ops/test_low_count_200_painters_20261008.py`.

The local catalogue was never connected to or changed. No commit or deployment was performed. Other workflows changed 0 pre-existing records between the preflight and final verification; exact before/after differences are retained separately in `concurrent-original-record-changes.json.gz`, and this importer writes only its new artwork IDs. These are selected additions, not exhaustive catalogues raisonnés. Saved query plans and bounded live API checks do not establish performance at ten million artworks; representative scale/load testing remains separate work.
