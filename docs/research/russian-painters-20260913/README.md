# Russian painters research and catalogue import — 13 September 2026

The owner requested Russian painters, their artworks and reproductions, aiming
for about 10,000 artworks, and explicitly authorized both local and production
database application. The final selection contains **7,264 artworks**: 7,251
linked to 519 painters and 13 retained under 10 named creator labels while their
profiles await reconciliation. Each database receives 470 new painter profiles;
49 painters match existing profiles. All records remain in review.

**Completed in both local and production:** 7,264 new artworks, 470 new painter
profiles, 42 attached reproductions and 231 image-candidate citations. Image
verification passed database rights/identity checks, local-file and GCS hashes,
and authenticated local/production API and image delivery. The 42 JPEGs total
3,724,279 bytes; the largest is 99,410 bytes.

| Selected artwork type | Actual artwork records |
|---|---:|
| Painting | 3,237 |
| Drawing, including the museum's drawing/watercolour section | 2,747 |
| Print | 1,280 |
| Total | 7,264 |

There are 6,606 records with an eligible creation interval and 658 whose date
wording needs review. All new artworks and artist profiles remain in review.
Unparsed dates retain their literal source wording and have null numeric bounds.
No masterpiece designation, current-display assertion, publication or invented
biography accompanies this import. Medium, dimensions and accession remain
unknown where they have not been checked against an individual object notice.

## Evidence and selection

- The [Russian Museum painting catalogue](https://rusmuseumvrm.ru/collections/painting/index.php?lang=ru),
  [drawings catalogue](https://rusmuseumvrm.ru/collections/drawings/index.php?lang=ru)
  and [print catalogue](https://rusmuseumvrm.ru/collections/engraving/index.php?lang=ru)
  yielded 11,297 distinct object URLs. Repeated highlight cards across pages were
  deduplicated by canonical object URL before selection.
- The [museum author index](https://rusmuseumvrm.ru/collections/references/authors/index.php?lang=ru)
  supplies full names and source-author URLs. Wikidata CC0 authority facts supply
  painter occupation, exact native names/aliases, explicit Russian descriptions
  or Russian Federation citizenship, and independently documented life dates.
  Russian museum location or Russian Empire/Soviet citizenship alone is not the
  Russian-painter inclusion criterion. Multiple cultural affiliations remain
  distinguishable; the new RU links are cultural associations, not exclusive
  nationality or birthplace claims.
- A second pass uses exact [Virtual Russian Museum artist IDs](https://www.wikidata.org/wiki/Property:P12716)
  to resolve additional creators. It adds 1,144 objects to the first 6,107-object
  selection. The two sets have no overlapping object URLs. A final 13 records
  retain named creators as object-level labels because the evidence does not
  support a reliable activity interval for a new painter profile. Source wording
  and authority QIDs remain in their review notes; numeric dates remain unknown.
- Museum membership comes from collection-specific museum listings, not broad
  author pages that may include works belonging to other institutions. Five
  previously imported canonical Russian Museum records were excluded from the
  new selection. Qualified or ambiguous creator labels are deferred.
- `captures/`, `authority-captures/`, the source JSON files and per-capture
  receipts preserve URLs, retrieval times, source payloads and checksums.
  `deferred-works.json` and `additional-deferred-works.json` preserve exclusions
  and unresolved research. These are evidence, not extra imported artworks.

## Identity and import safety

`combined-batch/manifest.json` pins 30 atomic, at-most-250-object chunks:

`d49c6ab7836d864a6cf032c7a2d8f5422eb2c848a238342f45024f92dd5ca22a`

The additional `date-review-batch/manifest.json` pins one 13-object chunk:

`581d8927ee46c2db76a780f11cab461da1e1e46d678068280d169a7d709b4fbd`

Go validates every chunk before opening the database, reuses exact artist QIDs,
checks exact object identities and writes review-only records through the
existing museum importer. Unknown metadata remains unknown. Serializable
transactions, bounded retry of serialization failures, explicit target checks,
and chunk idempotency guard application. The complete local replay created zero
new records. No fixture data, test database, commit, Terraform change or
application-service deployment was used.

Reviewed source-identity exceptions preserve the separate Vereshchagin and
Sokolov homonyms. Exact MoMA artist IDs reconcile Olga Rozanova and Ivan Kliun;
the exact Tate identity reconciles Konstantin Yuon. Kliun's existing MoMA-derived
birth year 1878 remains unchanged; Wikidata's 1873 is separately cited as a
conflict requiring editorial review. Artist audit labels from the first local
pass were corrected using exact artist/import-job transaction timestamps;
`correct-local-creator-audit.sql` changed 418 labels and no artwork content.

`backups.json` records the checked local PostgreSQL archive and successful
production Cloud SQL backup 1789303164083. The local archive table of contents
was checked; a restore was not performed. Backup location follows
`docs/LOCAL_DATA_LOCATIONS.md`.

## Image research

The [Russian Museum's terms](https://rusmuseumvrm.ru/terms/index.php?lang=en)
require a written request for its reproductions. No museum photographs were
downloaded under an assumed licence. Instead, a collection-scoped Wikidata image
query identified candidates on Wikimedia Commons. For 252 selected paintings,
the official detailed museum page independently confirms creator, title and
accession. Per-file Commons metadata clears 231 candidates: 229 marked public
domain and two CC BY-SA 3.0 photographs credited to Sailko. Twenty-one candidates
were deferred for licensing/source or file-size reasons.

Only cleared files are requested. Original-file SHA1 is checked against Commons
metadata, then the complete frame is resized proportionally and compressed into
a JPEG of at most 100,000 bytes. Source checksum, file revision, photographer
credit, licence, transformation, derivative checksum and dimensions are retained.
No image is generated or substituted. Database associations use the exact source
object identity independently in each database; GCS uploads are checksum-checked.

Wikimedia returned HTTP 429 with `Retry-After: 600`. Transfers pause and respect
that interval; the slower continuation uses at least 15 seconds between image
requests. Cleared candidates and pending downloads remain distinguishable from
successfully attached images. **42 reproductions are attached in both databases**;
189 cleared candidates remain pending download. No downloader remains active.
`images/events.jsonl` and `final-image-verification.json` record the completed count. Image-candidate citations retain the reviewed
source and rights evidence in both databases without claiming a downloaded file.

## Verification and remaining scope

The original production rollback preview completed all 25 chunks successfully
in execution `artline-russian-import-20260913-8z7kc`; its complete receipts are
preserved. Additional source records passed local rollback validation. The
combined production application completed all 30 chunks successfully in execution
`artline-russian-import-20260913-hj9sz`, using an isolated, unscheduled import job
and the existing runtime account and Cloud SQL secret. The job's default mode
remains rollback preview. `Dockerfile.import` preserves its build recipe.
The final 13-object chunk passed production rollback preview and committed in
`production-date-review-applied-v4/chunk-001.json`. Earlier connection failures
occurred before writes: expired application-default credentials were replaced
with the already-authenticated gcloud account for the local Cloud SQL proxy.

The final 13-record chunk also replays with zero new records in both databases.
An initial positional comparison exposed different local/Cloud SQL text
collations; verification now orders by canonical source identity in Python.
`final-database-differences.json` preserves that superseded diagnostic and does
not describe mismatched source records.

Final read-only evidence: `final-metadata-verification.json`,
`final-query-plans.json` and `final-image-verification.json`. Import receipts
measure this session directly; global catalogue counts also changed from
concurrent collection work and are not attributed to this batch.

Verification compares every source identity, title, date, type, painter QID,
review state and image association across the two databases and against the
pinned input. It also checks holding evidence, absence of display assertions,
new-profile review states, image rights, file hashes and byte limits, GCS copies,
and authenticated artwork/API image delivery. Go guard tests and `go vet` pass.
Read-only point-query plans use the real catalogue; this does not establish
10-million-row ingestion or concurrent application performance. Those load tests
remain outstanding.

This is a substantial Russian Museum pass, not an inventory of every Russian
painter or every museum worldwide. The 10,000-artwork target remains 2,736 short.
Further creator reconciliation, named icon-painter coverage and Russian works
held at other institutions remain research tasks. No missing fact or extra
record is invented to reach the target.
