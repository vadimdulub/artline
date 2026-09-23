# WikiArt artist-first collection expansion — 20 September 2026

Later completion: the [next artist follow-up](../wikiart-artist-followup-20260920/README.md) delivered another 2,144 images, reconciled 23 earlier production identity holds across the first two passes, and completed missing personal collection memberships. The counts below describe this pass at its original completion; the cumulative production attachment count is now 7,219.

Completed discovery of all 3,555 artist/source-group pages in WikiArt’s A–Z directory, after auditing 13,384 nonarchived local artist records. Prepared and uploaded 4,436 selected images covering 2,119 artist/source groups. This is an artist-first highlight pass, selecting up to three additional featured works per matched artist and usually one per newly discovered artist; it is not an exhaustive download of every WikiArt image.

| Result | Local catalogue | Production catalogue |
| --- | ---: | ---: |
| Images attached in this pass | 4,435 | 4,408 |
| New artwork records | 4,039 | 4,039 |
| New named artist profiles | 888 | 888 |
| New personal collection selections | 4,039 | 4,039 |

The earlier [674-image pass](../wikiart-selected-images-20260919/README.md) is disjoint. Combined, the two passes downloaded and uploaded **5,110 images**, attached **5,109 locally** and **5,052 in production**. All 5,110 uploaded asset URLs are public through Artline, including the source candidates whose catalogue attachment was held for identity reasons.

The follow-on JPEGs total 282,359,158 bytes; the largest is 99,991 bytes. The decimal limit is **100,000 bytes**, with proportional resizing, no crop and no generated content. Original source downloads remain separate from application derivatives.

## Content and public visibility

The user's instruction selects artworks more than 70 years old. Numeric creation dates must end by 1955, including BCE dates; artist lifespan does not determine artwork eligibility. Explicit approximate dates and ranges remain approximate/ranged. Unknown or conflicting dates are not invented. Modern reconstructions are not assigned an ancient original's date automatically.

All new artwork records remain `review`, with `research_candidate=true`, unknown work type, and no invented museum holding, current-display assertion or biography. The import includes 27 works with object-level creator/cultural labels, including Orthodox icons, Byzantine mosaics, Ancient Greek painting/sculpture and pottery, Egyptian works and Fayum portraits. Nine works have explicit BCE creation dates. Named creators lacking sufficient identity information remain object-level labels where appropriate.

Migration `0025_personal_artwork_collection.sql` permits one owner collection without an institution while requiring institutions for museum collections. All 4,039 new artworks belong to `Personal artwork collection` (`42c83e94-d1f2-539a-accb-b4e9ded61f06`), as owner choices drawn from WikiArt featured works. This allows the existing public atlas selection flow to show them without fabricating museum associations or publishing the underlying review records. Migration and membership preimages/receipts are preserved under `schema-delivery/` and `personal-selection/`.

The deployed Go readers return attached image paths independently of rights status, verification timestamp and missing alt text. Original source links and rights labels remain available. In this pass WikiArt labelled 3,467 images public domain, 963 copyright protected (`restricted`) and six unspecified (`unknown`). This records the source labels and the user's explicit display preference; artwork age was not converted into a licence or independent permission claim. Restricted/unknown images did not receive fabricated verification timestamps.

The live backend remains `artline-api-images-0920`, deployed in the earlier pass. No frontend deployment, Terraform apply or commit was performed.

## Identity reconciliation

Existing primary images and catalogue metadata were preserved except for the documented correction below. New source IDs, exact source metadata, image checksums and target preimages are retained. Duplicate artist spellings and coincident titles are resolved before attachment.

- Twelve initially held artist variants were reconciled using explicit profile names. A further duplicate WikiArt profile for Leonid Šejka was linked to the existing authority. The two source profiles disagree on birth month; no unsupported month was copied into the catalogue. See `artist-identity-resolutions.json` and `artist-identity-resolutions-final.json`.
- Jan Joest was not equated with Juan de Flandes from matching lifespan alone; his artwork retains a named object-level creator label.
- Sixteen same-title cases were visually distinguished as different objects, versions, album designs or explicitly labelled panels/details. See `title-identity-resolutions/`. Source detail titles are preserved.
- Ivan Bilibin’s *Crimea. Batiliman* was corrected to the composition matching Russian Museum accession RS-1902, after distinguishing it from a different shoreline work with the same source title/year. Both original evidence sets and recovery states remain in `identity-correction-history/` and Library backups.
- A Crespi *Dice Players* source variant was retained without making a second artwork record. Twenty-seven existing local artwork identities were absent from production, so their images remain attached locally and publicly uploaded without inventing or overwriting production identities. Earlier-pass production identity holds are recorded in its report.
- Other ambiguous multi-object matches were excluded before downloading, with candidates preserved in `ambiguous-source-identities/` and `full-profile-ambiguities/`. No choice was made from a generic title alone.

## Existing image size correction

The whole-catalogue audit found 161 existing media assets larger than 100,000 bytes. Full-frame JPEG derivatives reduced their combined size from **67,812,280 to 14,650,349 bytes**. Both databases now reference the compressed derivatives using the same media IDs. All originals, artwork references, portrait references and rights evidence are preserved.

[Size verification](existing-image-size-cap/verification.json) confirms all 161 public files against SHA-256 and preservation of the corresponding database records. A final read-only whole-database audit in [the completion summary](completed-delivery-summary.json) found **zero oversized images and zero unknown byte sizes** among 85,994 local and 85,851 production registered image assets; maximum 100,000 bytes. This does not claim that archived, unserved original files are below the delivery limit.

The compression tool's database guard was corrected to use PostgreSQL JSON consistently for both preimages and current rows: Python timestamp string formatting had falsely reported unchanged timestamps as edits. The guard still compares all media fields before updating.

## Verification

[Final verification](verification-4436-1789859062.json) passed with zero errors: all 4,436 local files, all 4,436 public-file SHA-256 checks and 67 public artwork API checks. The verifier checks all prepared local bytes, all uploaded public bytes, attachment metadata, original artwork state, new artist metadata, review state and personal collection membership. Public API checks cover restricted images, new artists and every object-level creator example.

- Twenty Python identity, date, BCE, source-label and immutable-evidence tests passed.
- The full Go suite passed. Final opt-in read-only repository checks passed for 12 actual restricted/unverified media records and 12 new personal collection artworks; no test database or real-catalogue fixtures were created.
- Artist/museum lookups retain backend scoping and bounded responses. Existing scoped museum query-plan checks passed. Representative ten-million-row load tests remain outstanding; current-catalogue checks are not evidence of that capacity.

## Recovery and retained data

- Source directory, profiles and raw captures: `directory/`, `profiles/`, `captures/`.
- Selection, images, target plans and receipts: `discovery-v2/`, `selected/`, `images/`, `delivery-plans/`, `applied/`, `delivery/`.
- Prior selections and corrected receipt versions: `selection-history/`, `title-resolution-history/`, `final-identity-review-history/`, `identity-correction-history/` and finish-marker history folders.
- Exact preimages and migration/membership recovery: `/Users/vadimdulub/Library/Application Support/Artline/backups/wikiart-artist-coverage-20260920/`.
- Downloaded source originals: `/Users/vadimdulub/Library/Application Support/Artline/source-images/wikiart-artist-coverage-20260920/`.
- Original oversized catalogue files and preimages: the backup directory's `existing-image-size-cap/` subdirectory.
- Served images: `apps/web/public/assets/artworks/wikiart/` and `assets/artworks/size-limit-20260920/`, with matching objects in `gs://artline-508319-images`.

Scripts: `ops/wikiart-artist-coverage.py`, `ops/wikiart-selected-images.py`, `ops/enforce-catalogue-image-size.py`; tests in `ops/test_wikiart_*.py` and the two opt-in Go read-only tests. All campaign preparation, delivery, personal selection and verification workers finished successfully.
