# At least 300,000 illustrated artworks — completed

The user explicitly requests at least 300,000 illustrated artworks and asks to
find pictures. Production primary-image enrichment is authorized; the real local
catalogue remains read-only. The verified starting total was **180,596 illustrated
active artworks**, requiring **119,404 additional illustrated artworks** to reach the target.

The image count follows the production renderer's `artworks.primary_media_id`
relation to a usable image asset. The first diagnostic additionally required an
`artwork_media` junction row and reported 94,905; that was not the application's
definition for legacy images. `coverage-method-correction.json` records the
corrected count and public checks. New attachments require both relations.
Known date exclusions and explicit Rijks verso views do not count toward the
goal. Alternate images and replacement files do not advance coverage.

Native-image discovery found 356,618 eligible Rijksmuseum gaps and 28,862 NGA
gaps. A bounded selection contains 125,000 Rijks and 25,000 NGA candidates to
allow for technical, version and duplicate holds; these are not delivered counts.
The target is complete. Independent final verification on **11 October 2026**
confirmed **300,192 illustrated artworks** among
**1,016,008 active catalogue artworks**. This campaign added
**116,594 net illustrated artworks**:

| Image source | Net new illustrated artworks |
| --- | ---: |
| Rijksmuseum | 87,581 |
| National Gallery of Art | 24,998 |
| WikiArt | 4,015 |
| **Campaign total** | **116,594** |

The production total increased by 119,596 from the verified baseline.
A separate authorized catalogue job contributed 3,002 of that increase;
those additions are not attributed to this campaign. The campaign net subtracts
two defective images withdrawn after supplemental review.

[`final-verification.json`](final-verification.json) independently rechecks all
116,594 current campaign attachments, exact media IDs/checksums,
100,000-byte limit, JPEG format, artwork-media relations, source-rights evidence,
search documents and original source identity/date fields. All delivered public
files had byte-hash checks before attachment. Final verification additionally
fetched a fresh image and public artwork API response from each of the
75 nonempty verified batches. Per-batch verification also compares
metadata, creator links, holdings and status against transaction preimages.
The real local catalogue's four baseline table counts remain unchanged.

All scoped preparation, audit and delivery workers have stopped; see
[`workers-stopped.json`](workers-stopped.json). Three prepared batches (Rijks
044–046) remain unreleased, with their research evidence retained. There are no
unverified started attachment transactions. The first final-audit client stalled
in transport after 2,000 rows; only that read-only client was restarted, and the
fresh audit completed all checks. The shared database proxy and other jobs were
left running. See `final-audit-retry-0001.json`.

Prepared files and candidate selections are never reported as delivered images.
No source image dump was downloaded.

Every candidate has a pinned previously verified museum object/inventory ID,
an eligible literal creation date through 1955, and an explicitly designated
native primary image. Source image URLs reused across multiple catalogue objects
are held. Every file receives decoding, dimensions, full-frame proportion,
100,000-byte derivative, source/derivative checksum and duplicate checks.

Visual review covers every quality/version flag, each newly encountered creator,
first/middle/last images per object type and a deterministic 4% batch sample.
Sampling is labelled honestly: unsampled files are not described as individually
visually inspected. A sampling failure stops the batch for expanded review.
No upload or database attachment is allowed before the recorded review decision.
WikiArt review was expanded to every selected image after an early batch exposed
whole-altarpiece/constituent overlaps and a montage of separate religious scenes.
Those ambiguous component/montage cases remain held, with official museum
relationship evidence recorded in the batch. The first NGA batch also holds a
whole-altarpiece image incorrectly designated as the primary picture of a single
panel in its native image mapping.

Counts refer to distinct native inventory objects, including separately
accessioned physical print impressions. They do not claim unique artistic
compositions. Repeated NGA portfolio motifs were checked against the official
medium, accession, nonvirtual status and native image IDs; these are screenprints
on paper/paperboard, although the museum classifies them within its drawing
collection. Original classifications and qualified attributions are preserved.
WikiArt reviews also distinguish painted versions from aliases: the two Bingham
County Election compositions have separate museum inventories and visible
differences, while an identical Bronnikov portrait under two titles is attached
only once. Three opposite banknote faces remain held pending design/object
reconciliation, and an incomplete photograph of Laurens's Les Ondines is held.
The collaborative Four Seasons is supported as one complete museum object.
These decisions and conflicting source dates are recorded in the corresponding
batch evidence without rewriting catalogue metadata.

Museum image requests use bounded worker pools and a shared per-host request
slot. The initial batches used at most four requests per second; after more than
16,000 successful museum-image preparations without a denial/rate response, the
two validated IIIF surfaces use an operational ceiling of eight per second.
This is not presented as a provider-published quota. Other image hosts retain
four per second, and selected originals stay bounded by the review backlog.
After 42,000 Rijks preparations without a denial, the preparation pool increased
from eight to sixteen workers to overlap response latency and image decoding;
the shared eight-requests-per-second ceiling is unchanged. Batch 020 sustained
approximately 5.3 requests per second with the earlier pool (median response
headers 0.67 seconds, 95th percentile 1.75 seconds). Eight offline checks still pass.
After 44,000 successful Rijks preparations without a rate denial, its next
batches use a shared ceiling of sixteen requests per second and thirty-two
workers. The official IIIF page was checked again and does not state a numerical
quota; this remains an operational ceiling. Response latency remained stable
in the sixteen-worker batch (median 0.63 seconds, 95th percentile 1.70 seconds).
NGA retains eight requests per second. The individual 404 is held, and all
denial, failure-rate, review-backlog and target-stop guards remain active.
See `rijks-throughput-checkpoint-0001.json`.
The thirty-two-thread preparation trial still saturated roughly one CPU core
and delivered about 6.9 images per second. Subsequent batches use sixteen
worker processes so image processing can overlap across cores. The source
request ceiling is unchanged, and source-denial receipts now use a process
file lock as well as the thread lock. A spawn-pool smoke check loaded four
existing receipts without network or database writes; all eight offline checks
pass after the change.
Previously denied surfaces remain held;
an actual 401, 403 or 429 stops that image source. Full-resolution image dumps,
guessed URLs, generated pictures and provider-access workarounds are excluded.

Uploads are create-only with immutable filenames. Each public file's bytes are
verified before the image is attached in a bounded production transaction. The
shared ingestion advisory lock, exact current artwork/native-ID preconditions,
transaction preimages and independent verification preserve existing metadata,
creator links, holdings and review states. Source rights labels and credits are
retained separately from user approvals.
New transactions contain at most 500 attachments. Their ordered object IDs and
visual-review checksum are pinned before writing; existing interrupted 100-row
batches retain their original recovery boundaries. A checksum collision appearing
after the technical audit stops the affected transaction for reconciliation.
Eight offline boundary/recovery and image-defect tests pass without database fixtures.

A supplemental scan of 39,093 prepared receipts found four native Rijks images
with opaque black blocks covering their lower sections. Two earlier attachments
were withdrawn under the ingestion lock, with full preimages and audit events;
the other two were held before attachment. Standard alternate full-frame sizes
retained the defect and were also held. The historical delivery receipts remain
immutable; current coverage and campaign net gains subtract the two withdrawals.
See `black-band-audit-0001.json` and `black-band-withdrawal-0001.json`.
Every subsequent museum audit checks for this defect and forces flagged images
into visual review. Genuine black photographic backgrounds around complete
medals are distinguishable from blocks obscuring the object.

NGA reverse-titled medals in batch 009 were reconciled against native parent/child
records and inventory-scoped production queries: only the physical parent is in
the catalogue; opposite-face child records are absent. The nine images therefore
each illustrate one object. Separately signed IAD drawings of the same baptismal
font were retained as different physical sheets. TIFFANY seasonal panels were
checked against individual Morse Museum inventories and documented historical
separation; these are surviving panels, not newly counted photographic crops.

The baseline, authorization, discovery, batch selections, image receipts,
technical audits, visual decisions, upload receipts, applied transactions and
verification results are recorded here. Source originals, candidate caches and
backups live under the corresponding Artline Application Support directories.
No commits, deployment or real-local-database writes are part of this operation.

Source references: [Rijksmuseum's image service](https://data.rijksmuseum.nl/docs/iiif/image),
[NGA official data](https://github.com/NationalGalleryOfArt/opendata), and individual
WikiArt catalogue pages when an exact artwork/version match is supported.
