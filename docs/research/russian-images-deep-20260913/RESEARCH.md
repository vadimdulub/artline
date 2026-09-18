# Russian artwork image research — 13 September 2026

**213 additional images were verified in both the local and production catalogues.** They cover 76 existing creator labels/profiles and 3 artwork types. All added reproductions are JPEGs of at most 100,000 bytes; the largest is 99,974 bytes. Artwork review/publication states, dates, creator attributions and holdings remain unchanged.

## Results and coverage

| Measure | Result |
| --- | ---: |
| Selected images | 213 |
| Attached and verified in both databases | 213 |
| Remaining selected images awaiting download | 0 |
| Prepared images awaiting attachment | 0 |
| Fixed Russian research cohort | 7,651 works |
| Images before this pass | 146 |
| Images after this pass | 359 |
| Remaining eligible image gaps in this cohort | 6,618 |

These figures describe this pass and a fixed catalogue cohort. They do not count the images added by the preceding Danish/Russian pass as new additions, and they do not claim complete coverage of Russian painting. The file-by-file result, original source pages, licenses and existing museum identifiers are in [IMAGE-INVENTORY.md](IMAGE-INVENTORY.md). Database and delivered-byte checks are recorded in [final-verification.json](final-verification.json).

## Research scope

The baseline includes 519 existing artist profiles with an explicit Russian cultural-affiliation record, plus Alexej von Jawlensky and six existing icons whose object-level cultural context explicitly identifies Russian icon painting. Russian affiliation can coexist with another national tradition; it is not a claim of exclusive nationality. Holding country and birthplace alone did not determine scope. Jawlensky is explicitly described as Russian by both [NGA](https://www.nga.gov/artists/1418-alexej-von-jawlensky) and [MoMA](https://www.moma.org/artists/2896-alexei-jawlensky); his catalogue country metadata was preserved. See [scope-supplement-evidence.json](scope-supplement-evidence.json).

Only existing, non-archived works with backend-confirmed selection evidence and eligible creation dates were candidates. Unknown dates and ranges crossing 1970 were not assigned substitute years. Anonymous Russian icon records retained their object-level creator labels. The Greek attribution on the separate Theophanes icon did not become a Russian artist authority through its Moscow holding.

## Search depth and identity evidence

The pass resumed 174 previously researched Russian candidates, then searched another 2,400 missing Russian Museum objects in two disjoint groups of 1,200. These searches retrieved 2,056 distinct Commons file records. The exact creator/accession path confirmed 41 additional object identities before rights selection. A separate photograph path selected 3 images using exact official museum-object links. Another 131 existing objects were checked against Met, NGA, Cleveland and Chicago data; 7 supplied explicitly reusable primary images.

Museum URL inventory hints were discovery terms only. The detailed Russian Museum page had to confirm the actual accession, title and creator-authority link. A Commons file then needed the same accession and institution with a creator match, or an exact official object URL in an independent photograph record. Similar titles, initials alone and repeated accession numbers across institutions were insufficient. The initial Kremlin search, for example, returned a Jan van Scorel painting for Ж-760; it was rejected as a different institution and object.

Commons sometimes places the photographer in its exported Artist field. The independent-photograph path therefore uses exact museum object URLs and separate creator verification. Shakko photographs retain “Photo: Wikipedia / Shakko (Sofia Bagdasarova)” and the explicit CC BY-SA 4.0 license. Gallery frames and surrounding material are retained where present; no automatic cropping, generative filling or restoration was performed.

The search was bounded: 20 accession batches returned a continuation marker, which was recorded instead of treated as an exhaustive result. Files without inventory metadata, alternate spellings, inaccessible records and unsearched works can still contain valid images. Metadata discovery was broader than the selected image downloads. Raw API responses, revision identifiers, museum captures and checksums remain with this research.

## Rights and source disagreements

Commons rights were checked per file, including license, copyright flags, restrictions, source credit and dispute markers. A public-domain painting did not automatically clear every museum photograph. Russian Museum website reproductions with unresolved source-permission conflicts were deferred. Independent photographs needed a reusable photographic license and evidence for the underlying artwork; this pass retained the licensed file credit rather than inventing a photographer. See the rights deferral files beside each search result.

Museum image eligibility was checked against explicit object/image flags. [The Met API](https://metmuseum.github.io/) exposes object IDs and public-domain image fields. [NGA](https://www.nga.gov/artworks/free-images-and-open-access) distinguishes its open-access image programme from its catalogue data; the existing revision-pinned image table was filtered to the selected object IDs, primary views and open-access flag. [Cleveland](https://www.clevelandart.org/open-access) identifies eligible images with CC0 metadata. [Chicago API documentation](https://api.artic.edu/docs/) supports exact object retrieval and image-rights fields; none of the checked Chicago gaps supplied an image meeting this pass’s conditions.

The Kremlin icon *Mother of God of Tenderness* was matched through [official object 9679](https://collectiononline.kreml.ru/entity/OBJECT/9679), accession Ж-267, and the [source record cited by Commons](https://www.icon-art.info/masterpiece.php?mst_id=189). The [Commons file](https://commons.wikimedia.org/wiki/File:Umilenie_Uspenskiy_01.jpg) identifies a faithful public-domain reproduction, the same subject, Novgorod tradition and Dormition Cathedral context. The official museum dates it to the middle of the 12th century; the linked bibliography also records other scholarly dating. The official catalogue interval was preserved. Neither a current display claim nor a named maker was inferred. The other five scoped icon gaps remain unresolved.

## Verification and practical limits

Every completed image was decoded and checked for dimensions, SHA-256 and the 100,000-byte ceiling. Stored GCS objects were checked against the local bytes using size and MD5. Both databases were queried through the exact artwork identifier; media association, source checksum, license, credit and unchanged artwork metadata were verified. Representative authenticated preview API responses and served image bytes were checked for every image provider. Visual observations are retained in visual-review.json.

The image client now identifies Artline with a contact URL, follows a single paced Commons download stream and records provider cooldowns without an early retry. These follow [Wikimedia’s published API guidance](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits); they do not guarantee immunity from operational rate limits.

The query-plan evidence concerns indexed object lookups in the actual catalogue. It is not a 10-million-row load test or a claim about global browsing performance. No application deployment or publication was required for these catalogue media attachments.

## Source and evidence inventory

- [Local baseline](local-before.json) and [production baseline](production-before.json): fixed cohort and metadata before mutation.
- [First accession search](accession-search-targets.json), [second accession search](accession-deeper/accession-search-targets.json), and their file/capture directories: bounded discovery and exact object verification.
- [Photograph matches](photographs-verified-aliases/new-commons-identity-matches.json): official object URLs, independent source and image credits.
- [Museum targets](direct-museum-targets.json), [selected museum images](direct-museum-selection.json), [museum deferrals](direct-museum-deferred.json), and [NGA scoped data](nga-scoped-open-images.json).
- [Icon selection and unresolved cases](kremlin-icon-selection.json), official saved museum record and linked scholarly source capture.
- images/selected: immutable identity and rights decisions before downloading; images/images: immutable compressed-file and source-byte receipts; images/events.jsonl: preparation/application outcomes.
- [Database research citations](commons-research-database-receipt.json), [final verification](final-verification.json), [query plans](final-query-plans.json), and [backup receipt](backups.json).

A visual quality correction replaced one photograph added during this pass with a separately licensed, unobstructed view of the same painting. The previous media and decision remain in the evidence archive; the replacement was conditional on the old media belonging to this pass. See [quality-review/database-receipt.json](quality-review/database-receipt.json). A stalled local development server was restarted before delivery checks were repeated; see [local-web-recovery.json](local-web-recovery.json).
