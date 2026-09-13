# Selected museum image expansion — 12 September 2026

User-authorized enrichment of existing artwork records, with a local image copy
and a matching object in `gs://artline-508319-images/assets/`. Each derivative is
at most **100,000 bytes**. This campaign does not add painters or artworks and
does not publish review records.

## Selection and sources

The frozen `candidates.json` contains 10,000 existing works: up to 2,000 each
from the National Gallery of Art, Metropolitan Museum of Art, Art Institute of
Chicago, Cleveland Museum of Art, and Statens Museum for Kunst. Selection uses
the catalogue's PostgreSQL creation-date eligibility and documented-selection
functions. It requires an exact museum object identifier, source provenance,
and an empty primary image. Russian/Greek-linked creators, popular painters,
and paintings/frescoes/manuscript illuminations receive priority. Anonymous
attributions are not excluded by this image campaign.

Metadata is checked before each image is requested. Open metadata alone does
not qualify an image for reuse. The following per-object gates are required:

| Museum | Image evidence | Official documentation |
| --- | --- | --- |
| NGA | `openaccess=1`, primary view, exact object and IIIF image identity | [Dataset](https://github.com/NationalGalleryOfArt/opendata), [image policy](https://www.nga.gov/artworks/free-images-and-open-access) |
| Met | `isPublicDomain=true`, no conflicting rights text, primary image | [Collection API](https://metmuseum.github.io/) |
| Chicago | `is_public_domain=true`, no copyright notice, image ID | [API](https://api.artic.edu/docs/), [image policy](https://www.artic.edu/open-access/open-access-images) |
| Cleveland | `share_license_status=CC0`, no copyright notice, web image | [Open Access API](https://openaccess-api.clevelandart.org/) |
| SMK | `public_domain=true`, image present, explicit Public Domain Mark | [SMK API](https://www.smk.dk/en/article/smk-api/), [PDM](https://creativecommons.org/publicdomain/mark/1.0/) |

The NGA image metadata CSV is pinned to the fetched Git commit, with its hash
and source URL retained. It is used only to match the selected existing IDs;
the museum's entire image collection is not downloaded. Other API responses
are retained with source URLs, retrieval dates, hashes, and available HTTP
validators. SMK supports both its IIIF images and current primary JPEG URLs.

## Import and recovery

`ops/enrich-artwork-images.py` separates read-only selection from application.
One worker runs per museum, with at least 1.05 seconds between source requests,
bounded retries, response byte limits, an HTTPS host allowlist, and a stop after
eight consecutive item failures. Chicago metadata is batched by exact IDs;
its image downloads remain sequential.

Selected image rights snapshots are written before download. Derivatives use
proportional resizing and JPEG compression; they retain the full frame and
contain no generated material. Originals are processed in memory. Receipts
record source and derivative hashes/sizes, dimensions, JPEG quality, original
image URL, rights, attribution, and transformation.

Uploads use create-only generation preconditions and compare the returned GCS
MD5 and size against local bytes. Database attachment rechecks the exact museum
identifier, eligibility, selection evidence, and empty primary-media slot.
Existing images are preserved. Local and cloud transactions are separate:
receipts permit safe recovery after partial success. Short row-lock timeouts
avoid blocking the concurrent catalogue import. Only artwork media pointers,
revision/audit fields, media records, and image-rights evidence are written.

The cloud database uses the existing Cloud SQL proxy at `127.0.0.1:55433`.
Credentials come from the authorized gcloud account and Secret Manager and
are never written into the campaign evidence. The production asset route
serves the same `/assets/...` paths from GCS.

Resume the frozen campaign (do not run two copies simultaneously):

```sh
/tmp/artline-images-venv/bin/python ops/enrich-artwork-images.py apply \
  --run docs/research/image-expansion-20260912
```

Completed records and explicit rights skips for the current adapter version
are not redownloaded. Failed records reuse their saved rights/derivative
receipts. A source-adapter version change permits re-evaluating previous skips.
Use the latest event for each artwork when counting results; historical
canaries and recovered failures remain in the append-only log.

`ops/recover-enriched-image-links.py --run <campaign-directory>` can repair
historical failed attachments when a derivative receipt and matching GCS
object already exist. It verifies local and remote bytes before attachment,
does not contact a museum or upload files, and preserves existing images.
Use it only after the main importer has passed the failed items, or after
the main importer stops. Two earlier lock-timeout failures (SMK `KMSsp734`
and Chicago `12007`) were recovered this way and are attached in both
databases; their recovery events preserve the original failures in the log.

## Evidence and verification

- `candidates.json`: fixed, metadata-first scope.
- `metadata/`: museum responses and HTTP/hash receipts.
- `selected/`: per-object image selection and rights snapshots.
- `images/`: local derivative and provenance receipts.
- `events.jsonl`: append-only upload and attachment outcomes.
- `verification-*.json`: read-only local/GCS/database audits.

The early verification checked **690 images**, totaling **60,783,505 bytes**.
All 690 decoded correctly, matched GCS checksums, and had media, rights evidence,
and artwork links in both databases. No oversized files or verification errors
were found. A production asset URL returned HTTP 200 and the expected 68,043
bytes. A visual canary inspection covered nine images across the providers.
Seven offline tests cover explicit rights gates, object identity, source-host
restriction, image decoding, aspect ratio, and the byte cap.

The next checkpoint, `verification-2000.json`, checked **2,075 images** totaling
**187,636,295 bytes**, with a maximum of **99,990 bytes**. All local/GCS hashes,
media records, rights evidence, and expected artwork links matched in both
databases. No errors were found. Fresh museum creation dates were also checked
for 1,604 images; none contradicted the 1970 cutoff. NGA's image CSV does not
contain artwork creation dates, so those continue to use the catalogue's
existing date evidence and SQL eligibility check.

`verification-3000.json` audited **2,994 main-campaign images**, totaling
**273,075,749 bytes**, with a maximum of **99,998 bytes**. All expected links,
rights records, decoded local images, and GCS checksums passed. It also checked
2,344 fresh museum creation-date ranges without finding a cutoff conflict.
Together with the completed 25-image Rijksmuseum audit, this checkpoint
independently verifies **3,019 new images**. The main import continues.

`verification-4000.json` independently checked **4,120 main-campaign images**,
**378,949,587 bytes**, maximum **99,998 bytes**. All 4,120 images have matching
GCS copies and media/rights/artwork links in both databases, with no audit
errors. It checked 3,240 fresh creation-date ranges without a cutoff conflict.
Including Rijksmuseum, **4,145 new images** are independently audited at this
checkpoint. Both the initial batch and queued painting follow-up remain active.

`verification-5000.json` checked **5,056 main-campaign images**, totaling
**465,892,047 bytes**. The largest is exactly **100,000 bytes**, within the
requested cap. All 5,056 decoded files, GCS copies, rights records, and expected
links passed in both databases. No cutoff conflicts were found among 3,976
fresh museum date ranges checked. Together with Rijksmuseum, **5,081 new
images** are independently verified at this checkpoint.

`verification-7000.json` passed for **7,124 main-campaign images**, totaling
**649,223,951 bytes**, with complete file, GCS, metadata, rights, and exact
artwork-identity checks in both databases. The largest remains 100,000 bytes;
5,592 fresh museum date ranges showed no cutoff conflict. Chicago's initial
2,000 records are fully attempted: **1,873 images added**, 110 without explicit
open images, and 17 source-response failures pending bounded retry.
The queued Chicago painting pass has started. Its first 59 images also passed
the detailed audit; including Rijksmuseum, **7,208 new images** are independently
verified across the three campaigns at this checkpoint.

`chicago-source-response-check.json` records inspection of one failed IIIF
request: both its metadata and image URLs returned HTTP 403, with a browser
challenge page. This was not an oversized-image response. The failed item
remains separate from completed images for a later bounded retry.

`image-quality-screen-5000.json` examined 5,318 derivative receipts across the
main and Rijksmuseum campaigns. No image had a dimension below 100 pixels.
Four repeated-hash groups (nine records) all belong to Cleveland's *The Great
Triumphal Car of Emperor Maximilian*, accession family `1945.26`. The API
supplies shared views for adjoining sheets and the parent record. A repeated
view was visually checked: it is a genuine two-sheet woodcut reproduction,
not a placeholder. Existing museum object records remain distinct.

`verification-detailed-5500.json` checked **5,656 main-campaign images** totaling
**520,146,520 bytes**. In addition to file/GCS/link counts, it compared each
database's actual path, SHA-256, size, dimensions, license, artist credit,
source image URL, source record ID, source-response hash, verification fields,
and attribution against the immutable receipt. All 5,656 passed in both
databases. Later audits also verify the exact museum identifier and source
provenance of each linked artwork, including the original local artwork UUID.

`verification-6000.json` passed for **6,093 main-campaign images**, totaling
**558,564,471 bytes**, maximum **100,000 bytes**. All metadata comparisons and
exact linked museum identifiers, source provenance, and local artwork UUIDs
matched in both databases. No errors or cutoff conflicts were found; 4,795
fresh museum date ranges were checked. Including Rijksmuseum, **6,118 new
images** are independently verified at this checkpoint.

A separate [Rijksmuseum supplement](../image-expansion-20260912-rijks/README.md)
adds images for 25 existing works using exact IDs and per-image EDM rights.
The shared adapter now has eight offline tests, including this additional
museum's identity and image-rights gates.

A [painting follow-up](../image-expansion-20260912-paintings/README.md) selects
6,609 additional eligible paintings outside both earlier manifests. Its
coordinator waits for each museum's initial selected IDs to finish before
starting that museum's next worker, maintaining one active worker per museum.

An additional application check used Monet's *Apples and Grapes* (Chicago
object 16549, local artwork `ef5709bf-c291-4670-a3a9-ae87a3475635`): both local
and production artwork endpoints returned the same new media URL and CC0
attribution. Both asset endpoints returned HTTP 200 and identical 92,376-byte
JPEGs, SHA-256 `5908661d08aff77df060865e7b3703cfb90c430db93adf314e4691bc147c68ff`.

Run a fresh read-only audit, using a new report filename:

```sh
/tmp/artline-images-venv/bin/python ops/verify-enriched-images.py \
  --run docs/research/image-expansion-20260912 \
  --report docs/research/image-expansion-20260912/verification-final.json
```

The main batch is still running; final counts belong in its final verification
report. Rights-unavailable objects are left without a new image. Unknown or
ineligible creation dates remain outside this campaign. No museum holding is
converted into a currently-on-view claim.

## Backups

The pre-import local PostgreSQL dump is at:

`/Users/vadimdulub/Library/Application Support/Artline/backups/image-expansion-20260912/local-media-and-artworks.dump`

A Cloud SQL backup was also completed before application. Its successful
backup ID is `1789238996143`, operation ID
`9158e0bf-c3ed-4804-91f5-59cd00000024`, description
`Before verified artwork image expansion 2026-09-12`.

Research evidence and real artwork assets are retained. Disposable visual
checks and the Python environment live under `/tmp`. This workflow has not
been load-tested at ten million artwork records; selection is bounded and
attachment uses exact museum IDs and individual artwork rows.

`attachment-readonly-plans.json` captures actual local `EXPLAIN ANALYZE` plans
for the attachment lookup's read-only SELECT, one successfully matched work per
main provider. Each returned exactly one row in 1.0–10.4 ms on this catalogue.
The audit omits `FOR UPDATE` so it does not lock catalogue rows; it does not
measure write contention, cloud round trips, or ten-million-row performance.

## Recovery audit

`verification-recovery.json` independently checked **7,601 images**, totaling
**689,328,410 bytes**, with a maximum of **100,000 bytes**. Local file checks,
GCS checksums, database metadata, rights evidence, and exact museum/artwork
links passed on both database targets with no errors. Fresh museum creation
dates were checked for 5,904 images; none conflicted with the cutoff. Together
with the supplement recovery audit and the completed Rijksmuseum audit,
**7,907 images** are independently verified at this checkpoint. Processing
continues beyond this snapshot.

`verification-8000.json` passed for **8,097 main-campaign images**, totaling
**732,685,931 bytes**, maximum **100,000 bytes**. All file/GCS checks, metadata,
rights, and exact artwork links passed in both databases. The 6,230 fresh
museum date ranges checked remained eligible. This includes all **1,867**
successful initial NGA images; the other **133** selected NGA works had no
explicit reusable image in the published image index. NGA has continued to
the disjoint painting supplement. Together with the completed Chicago
supplement and Rijksmuseum audits, **8,493 images** are independently verified
at this checkpoint. The overall import remains active.

`verification-10000-checkpoint.json` checked **8,773 main-campaign images**,
totaling **793,555,489 bytes**, maximum **100,000 bytes**, with no errors. Both
databases matched file receipts, rights, source metadata, and exact artwork
links. All 6,906 fresh museum date ranges checked remained eligible.
Together with the painting checkpoint, Rijksmuseum and Commons recoveries,
**10,110 distinct images** are independently verified.

The [Commons recovery](../image-expansion-20260912-commons/README.md) resolved
three original Met HTTP 404 image gaps using exact museum-donated CC0 files.
Their old errors remain in this campaign’s historical log; the recovered
images are counted once in the supplement.

## Initial selection completed; local audit on 13 September

All 10,000 selected IDs reached terminal outcomes: **8,949 images added**,
1,030 explicit rights/availability skips and 21 source failures. Three of
those source failures were subsequently recovered in the Commons supplement;
Sisley’s exact current-ID recovery is prepared separately.
`verification-local-complete.json` rechecked all 8,949 local files and links,
totaling **809,963,824 bytes**, maximum **100,000 bytes**, with no errors. It
checked 7,082 fresh museum date ranges. This report is explicitly local-only:
Google Cloud requires account reauthentication before the final cloud audit.

## Final full audit of the initial selection

After authentication was restored, `verification-final.json` passed for all
**8,949 initial-campaign images** (809,963,824 bytes; maximum 100,000 bytes)
in local storage, GCS and both databases. All metadata, rights and exact
artwork links matched; 7,082 fresh museum date ranges were eligible. The four
retired Met image gaps were recovered in the Commons and exact-accession
Sisley supplements. Seventeen blocked Chicago image URLs remain unresolved
after bounded retries. A single next-day recheck still returned HTTP 403.
A Commons Dürer alternative was rejected: its accession 2009.133 differs
from the selected impression’s 1952.1204. No different impression was used.

## Completed combined workflow

The final [results](RESULTS.md) consolidate all six campaign folders and
account for deliberate recovery overlaps. The all-campaign closing audit
passed for **12,446 distinct images** and all selected IDs have outcomes.
No preparation or upload worker remains active.
