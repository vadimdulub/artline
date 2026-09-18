# Danish painters research — 13 September 2026

The owner requested a further national-painter research/import session, aiming at
10,000 artworks and images. The established local-and-production workflow applies.
The pinned selection contains **10,000 new SMK artworks by 303 source-named
Danish-associated painters**. All 10,000 artworks and 46 new painter profiles
are committed in **both local and production**. Every new record remains in review.

| Artwork type | New records |
|---|---:|
| Painting | 141 |
| Drawing | 8,236 |
| Print | 1,623 |
| Total | 10,000 |

9,199 works have source-supported creation intervals ending by 1970. Another 801
retain unknown numeric dates and the museum’s original date wording in review.
Artist lifespan/activity and museum accession dates are not artwork creation dates.
All new artworks and painter profiles remain **review**, without publication,
masterpiece designations or current-display claims.

## Research scope and evidence

The [official SMK API](https://www.smk.dk/en/article/smk-api/) supplies museum
catalogue facts, exact person IDs and per-object image rights. Its
[field documentation](https://api.smk.dk/api/v1/art/field_info) and API schema are
preserved with SHA256 receipts. Generated enrichment, machine-written description
and visual-recognition fields are not imported as catalogue facts.

The nationality-scoped capture covers 4,579 paintings (the complete current
Danish-associated painting result), a bounded 15,000 drawings, and 5,000 prints.
It does not download the entire collection. The painting records identify 621
named creators with actual painter-practice evidence; 467 already have exact SMK
person identities in both catalogues. Additional person-authority requests are
limited to the other 154 source IDs. Empty authority responses remain unknown.

Only single named primary creators whose source nationality explicitly includes
Danish enter the selection. Multiple cultural associations remain visible: 300
selected authorities say Danish, one repeats Danish in the source, one says
French/Danish, and one German/Danish. Museum location alone does not establish a
Danish painter. Prints after other artists, ambiguous/qualified creator records,
unsupported object types and explicit post-1970 works are deferred.

The source has repeated accession numbers assigned to different internal object
IDs. Such groups are deferred together. Existing local **or** production objects
are excluded by SMK identities, canonical source URLs, citations and museum
accession numbers. Selection rotates across painters, preferring paintings and
dated/image-backed works within each painter; import chunks are then grouped by
painter for efficient authority lookups. The 10,000 cap excludes 2,035 otherwise
usable candidates in this capture.

`captures/`, `persons/`, `painter-registry.json`, `selected-authors.json`,
`selection-decisions.json` and source snapshot receipts preserve the research.
Most eligible SMK paintings were already present; the additions are therefore
predominantly drawings and prints by painters, not 10,000 oil paintings.

## Database application

`batch/manifest.json` pins 40 atomic chunks of 250 real research objects:

`71ce94f8d7dba2048ce139de6934f3385c9c5ce8df262cd828d2d5c3b6aa2b66`

The Go importer validates source identity, named Danish association, painter
practice, attribution, literal life dates, creation bounds and artwork types
before connecting. PostgreSQL performs indexed duplicate checks and bounded set
writes. Transactions are serializable, explicitly targeted and protected by an
advisory lock. Each chunk has a checksum-based idempotency key. A temporary table
holds only that chunk’s real source records inside its transaction; no fixture
data or test database is created.

Full rollback previews passed on both databases. All 40 chunks replay in each
database with zero new records. The final complete metadata comparison passes: source
identities, values, creator links/labels and review states agree in both databases. Both applications created
10,000 artworks and 46 painter profiles each. Of those new profiles, 39 have
source-supported closed lifespans and seven use documented work activity bounds.
9,994 artworks link to 299 profiles; six
retain four creator labels pending reconciliation: Bertha Wegmann (3), Eleonora
Tscherning (1), Hans Voigt Steffensen (1), and Søren Hansen (1). A conflicting
existing name or missing reliable timeline does not justify a duplicate profile
or invented lifespan. Wegmann’s source birth year is 1846, while the existing
Wikidata-derived profile records 1847; neither date is overwritten. Their exact
SMK creator IDs remain in audit/citation data. `creator-conflicts.json` records
this unresolved comparison.

Museum holding assertions refer to official collection records. On-view fields
in source JSON remain raw evidence; no display assertion is imported. Raw source
JSON, checksums, normalized decisions and import job/record receipts are stored
in each database. Existing artist biography, lifespan and editorial status remain
intact; sourced Danish cultural associations are added separately.

`backups.json` records the checked local PostgreSQL archive and successful Cloud
SQL backup **1789312715225**. Both precede this import. The local archive directory
was verified with `pg_restore --list`; a restore was not performed. Backups are in
`~/Library/Application Support/Artline/backups/danish-painters-20260913/`.
No commit, schema migration, application deployment or Terraform apply is part
of this session.

## Images

The selected metadata supplies **1,460 dated, explicitly public-domain image
candidates across 92 painters**. Image copying is a separate bounded selection
of **500** source reproductions across 91 painters, rotating across painters and preferring
paintings. Source public_domain=true, the exact Public Domain Mark URL, object
identity, source metadata and request URL are pinned before transfer.

Images are proportionally resized from the museum’s available reproduction,
without generated content, and compressed to JPEG files of at most 100,000 bytes.
Rights metadata, source and derivative checksums, size, dimensions, transformation
and retrieval time are retained. Local files and checksum-verified GCS copies are
attached independently by exact source identity in both databases. **All 500 images
are attached in both databases**, totalling 45,482,875 bytes; the largest is
99,994 bytes. All 1,460 image-candidate citations are present in both databases.
No downloader or importer remains active. Existing media
is preserved. Provider restrictions stop transfers and retain resumable evidence.

`images/events.jsonl`, prepared image receipts, `image-candidate-database-receipt.json`
and `final-image-verification.json` record actual results. A researched candidate
is not counted as an attached/downloaded image.

## Verification and limits

Go source-guard tests and static analysis pass without catalogue test fixtures.
`final-metadata-verification.json` compares each source identity, title, literal
and numeric date, work type, medium, dimensions, creator link/label, raw source
checksum, holding and review state between the two databases and the pinned input.
`final-query-plans.json` preserves read-only exact-object plans from the actual
catalogue. These bounded checks do not establish 10-million-row performance;
representative large-load and concurrency tests remain outstanding.

Final media verification **passed** all 500 selected file hashes, JPEG decoding,
byte limits, GCS copies, database rights/identity evidence, authenticated local
and production artwork/image delivery, and bounded museum result pages.

A completed evidence/code/selected-image archive is retained beside the database
backup as `completed-session-evidence-and-images.tar.gz`; its external checksum
receipt is `session-archive-receipt.json`. Local and production global totals can
differ due to other catalogue sessions; this report counts only this import.

This reaches the requested artwork count in a substantial SMK pass. It is not an
inventory of every Danish painter or every work held by museums worldwide.
Further institutions, creator reconciliations, deferred source objects and the
remaining rights-cleared image candidates remain available for later research.
