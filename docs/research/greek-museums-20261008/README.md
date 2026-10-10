# Greek museums — production delivery, 8 October 2026

Delivered **621 new review artworks**, **500 new primary images**, and **1 supported holding link to an existing artwork**. Greek browsing now contains **80 collections, 1,264 artworks and 725 illustrated works**. The pass created 73 institutions with real catalogue items. [Browse Greece](https://artlines.org/museums?country=GR) · [Delivery report](report.html) · [Per-artwork results](delivery.csv) · [Museum totals](museums.csv).

## Coverage and remaining work

The request was “let's cover all greek museums and upload pictures and artworks.” This is a nationwide research and selected-delivery pass, **not complete coverage of every Greek museum**. All 214 entries in the [Ministry directory](https://archaeologicalmuseums.culture.gov.gr/en) were checked. 41 have an exact catalogue institution represented in this delivery; 173 still require individual-object research. The 80 collections also include fine-art, folk-art, religious and institutional collections outside this directory. The directory is not a census of all Greek institutions.

The [complete Ministry ledger](ministry-coverage.csv) records every listed identity, source, region, status and native-site lead. HTTP 200 alone was insufficient: 3 entries returned soft 404 pages (Benaki, Cycladic Art and Historical Museum of Crete); native and museum-supplied catalogues were used where available. A directory description or gallery-room photograph was never imported as an invented object. Empty institutions remain excluded from browsing.

All 163 [SearchCulture collection-directory entries](digital-collections.csv) were indexed; 39 museum/gallery candidates were screened with bounded first-page and oldest-page metadata selections. The Ministry public National Archive catalogue was searched by 45 store-location labels, reconciled to 44 museum/collection identities. Additional native research covered Acropolis, Goulandris, Cycladic Art, Delphi, Olympia and Crete. The [ICOM directory leads](icom-directory-leads.csv) preserve another discovery route. These are overlapping research lists, not additive museum counts. No exhaustive image harvesting was performed.

## Selection and source decisions

- Metadata is supported by exact object identifiers, accession numbers or uniquely named native museum highlights. Works dated after 1970 were not imported; uncertain dates remain explicit review values. Anonymous creators, qualified workshops and fragmentary antiquities are retained without invented biographies or years. Physical print edition dates take precedence over the date of the depicted subject or artist biography.
- All new artwork records remain `review`, unpublished and research candidates. Holding assertions are accepted on documented object-level evidence; no current-display assertions were added. Editorial confidence is a judgment, not a statistically calibrated probability.
- The 62 Goulandris image updates preserve all existing catalogue metadata. All prior primary images were preserved. El Greco’s existing *Mount Sinai* was reused and linked to the Historical Museum of Crete using the native collection and [WikiArt’s explicit holding](https://www.wikiart.org/en/el-greco/mount-sinai-1570); no duplicate was created.
- The early *Baptism of Christ* remains a version-reconciliation lead. The existing WikiArt reproduction is an arched panel; the museum’s text and older caption disagree on 1567/1569. The detailed native resource returned HTTP 500 and its Commons-origin image returned HTTP 403. No guessed merge or new duplicate was delivered.
- Three Ministry records called bronze bracelets in English were corrected to **gold earrings** using their Greek titles, gold material and object descriptions. Original conflicting text remains in source captures and audit history.
- Thirteen Varnavas objects were assigned to the **Interactive Agricultural and Folklore Museum of Varnavas**, which their object-level location identifies, instead of the broad European Bread Museum repository label. Previous holding assertions were superseded and preserved. Three suspicious 1905 calendar strings were cleared to explicit unknown creation dates; their images were withheld. No replacement year was inferred.
- Near-identical Paros icon compositions were checked against distinct inventory numbers, panel construction and signatures. Different physical versions remain separate records.

## Image delivery

All 500 newly attached images were visually reviewed, uploaded with create-only storage writes, and retrieved through the public site with exact SHA-256 verification. The main batch has 489 images; the native follow-up has 11. Three cropped PLI thumbnails were replaced with complete files from their public file viewers. Delphi’s Charioteer uses the complete surviving statue photograph after excluding a bust, hand detail and reconstruction diagram. The cropped Apollo cylix image remains withheld.

Derivatives preserve the complete selected source frame and original source marks, with proportional resizing and a maximum of 100,000 bytes. Actual rights labels, credits, page/file URLs and source evidence remain separate from user source approval. Restricted labels were not converted into public-domain claims. Originals are archived outside Documents.

There are 183 [new artwork records without an image](image-gaps.csv), principally because creation dates are unknown or later than the existing 1955 museum-image cutoff. Records remain available for research and museum browsing. Known download failures are preserved in evidence, including the transient Ministry download recovered in the follow-up.

## Verification and recovery

[Verification JSON](verification.json) records 684 complete artwork-row checks, 79 museum artwork API samples and all 500 public image checksums. Bounded country API pages returned every expected museum with a positive visible-work count. Source identities, selection evidence, accepted holdings, rights evidence, audit coverage and review/publication safeguards passed. Local baseline counts were unchanged: True. The local database was queried read-only, with no fixtures or test databases.

The authoritative metadata plans are `delivery-plan-v4.json.gz`, `supplement-delivery-plan.json.gz`, `native-delivery-plan-v2.json.gz` and `quality-correction-plan.json.gz`. Image plans are `greek-image-plan.json.gz` and `native-image-plan.json.gz`; visual reviews bind specific contact-index and image checksums. Earlier plan versions are retained for provenance and must not be reapplied. Applied receipts and transaction after-states distinguish actual delivery from candidates and holds.

Cloud SQL backup **1791471559641** completed before writes. Before/after snapshots are under `/Users/vadimdulub/Library/Application Support/Artline/backups/greek-museums-20261008/`; original images, contact sheets and procedures are under the matching `source-images/greek-museums-20261008/` directory. Accepted application derivatives use `apps/web/public/assets/artworks/imported/greek-museums-20261008/` and matching paths in the production image bucket. No application deployment or commit was performed.
