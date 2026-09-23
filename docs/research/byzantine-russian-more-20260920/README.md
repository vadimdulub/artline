# More Byzantine and Russian icons and frescoes — 20 September 2026

Added **727 new artworks to the real local catalogue: 616 icons and 111 fresco
records**, with **23 visually reviewed CC0 images**. All additions remain
`review`, unpublished, marked as research candidates and included in the
personal owner collection. The expansion follows the user's request for more
Byzantine, post-Byzantine and Russian material, including Greek icons.

Together with the [first pass](../byzantine-russian-icons-frescoes-20260920/README.md),
these two passes added **1,531 works: 1,393 icons and 138 fresco records**, with
**31 attached images**. These are exact campaign receipt totals, not global
catalogue deltas or a complete inventory of these traditions.

## Added records

| Official source | Icons | Frescoes | Total | Attached images |
| --- | ---: | ---: | ---: | ---: |
| Andrei Rublev Museum | 389 | 111 | 500 | 0 |
| Icon Museum and Study Center | 179 | 0 | 179 | 0 |
| Victoria and Albert Museum | 25 | 0 | 25 | 0 |
| Metropolitan Museum of Art | 18 | 0 | 18 | 18 |
| Cleveland Museum of Art | 5 | 0 | 5 | 5 |
| **Total** | **616** | **111** | **727** | **23** |

Of the icons, 593 are paintings. The other 23 retain `object_form=icon`, their
literal museum medium and classification, and `work_type=unknown` pending
broad-type review. These include carved, enamelled and mosaic icons and
catalogued fragments. Source attributions and unknown creators remain
object-level labels; no anonymous painter authorities were invented.

The 111 fresco records describe actual museum-catalogued wall paintings or
fragments. Modern copies and tracings were excluded. Rublev and the Icon Museum
were added as review institutions with official website identities; unsupported
place or country identifiers were not fabricated.

There are **707 source-backed holding assertions and zero display assertions**.
Twenty Icon Museum entries explicitly describe loans. They retain their source
connection but have no holding assertion or current holding institution.
Personal collection selection is separate from museum masterpiece designation.

## Sources, identities and dates

The bounded metadata review captured 536 unique Rublev cards from its
[icon catalogue](https://www.rublev-museum.ru/collection/icons/) and
[fresco catalogue](https://www.rublev-museum.ru/collection/frescoes-monumental-painting/),
186 Icon Museum object pages reached through its
[Russian](https://www.iconmuseum.org/country/russia/) and
[Greek](https://www.iconmuseum.org/country/greece/) indexes, and 44 object details
from the [V&A icon search](https://api.vam.ac.uk/v2/objects/search?q_object_type=icon&page_size=100).
The selected Met and Cleveland records reuse the first pass's same-day official
API captures, preserving their original paths and hashes. Exact URLs, source
fields, dates, accessions and capture receipts are in the pinned selection.

Rublev exposes several objects on each listing page. Stable museum card IDs
and exact accessions distinguish objects sharing a source URL. Four pairs of
cards represent the same physical object: КП3871, КП-549, КП942 and КП1935.
Each pair became one artwork, with both source cards preserved and cited.
Double-sided icons were not counted twice.

**652 works have creation bounds eligible for the dated timeline; 75 require
date review.** The latter comprise 57 unknown structured dates, two open-ended
dates and 16 conservative century/range envelopes crossing 1970. Original date
wording remains available. Icon, metal-cover, frame and restoration dates are
not combined into invented artwork dates; unresolved layered or tentative
dating remains in review. Undated and unresolved records remain in the database
and applicable museum review views, outside the dated timeline.

**58 metadata candidates were held:** 21 Rublev icons need medium review,
three wall-painting entries lack an established original fresco medium, six
are copies or tracings, two lack exact accessions, six Icon Museum objects need
medium/form review, 19 V&A records need title/origin/medium review, and one
Icon Museum mummy portrait predates Byzantine art. Captures remain preserved;
these held candidates were not imported.

## Images

Only the 23 selected Met and Cleveland CC0 reproductions were downloaded.
All passed visual inspection and were attached. Catalogued fragments remain
identified as fragments. The double-sided pendant uses its Christ face, and
the Cleveland pendant photograph includes its later frame. The Hypapante image
shows both catalogued fragments. See the [visual review](image-visual-review.json)
and [attachment receipt](images-attached.json).

Application JPEGs were proportionally resized without cropping and range from
60,374 to 99,579 bytes. Source URLs, credits, rights declarations, original and
derivative hashes, dimensions and transformations are retained in the image
receipts. **704 new records remain without images**; this pass did not establish
reproduction permission for the other three museums' photographs.

Application assets are in
`apps/web/public/assets/artworks/imported/byzantine-russian-more-20260920/`.
The 23 source originals are separately archived under
`~/Library/Application Support/Artline/source-images/byzantine-russian-more-20260920/originals/`.

## Verification and recovery

The [final read-only verification](verification.json) passed for all 727 exact
receipt IDs, review state, creation/classification fields, selection evidence,
source citations, four alternate card identities, holdings and image records.
It passed **91 bounded API checks and 23 HTTP image checksum checks**. New museum
lists were checked across two keyset pages, with holding counts of 500 for
Rublev and 159 for the Icon Museum; both have zero asserted on-view works.
All 12 offline parser and identity regression tests passed.

The bounded 20-ID lookup used `artworks_pkey`, with its execution plan preserved
in the verification report. This is local functional evidence, not a
10-million-artwork benchmark. Representative large-scale ingestion and query
load tests remain separate backend work. No test database or catalogue test
fixtures were created.

Image delivery was checked through a fresh temporary instance of the existing
Next build, serving the real public-assets directory, and that instance was
stopped afterward. Existing production-mode previews need a restart to discover
new public files. The existing research-preview API setting was preserved;
review visibility does not publish database records. No production database,
cloud storage, deployment or publication state was changed by this pass.

The first 100 records committed before an alternate external-ID uniqueness
constraint stopped the next batch, which rolled back. Alternate card identities
were then represented by citations, matching the schema. The final selection
also excluded the pre-Byzantine mummy portrait before its insertion. The resumed
import added the remaining 627 records. The [delivery manifest](delivery-manifest.json)
aggregates all eight successful batch receipts, so the resumed selection receipt
alone is not the campaign total. Final reconciliation found no missing records,
new duplicates or identity conflicts. The 727 IDs are disjoint from the 936-ID
read-only baseline.

Final selection SHA-256:
`f6509d0964197125118966d63114ba5a5115ee8467357e1db97b5227527e4d6f`.
See the [selection pointer](latest-selection.json), [pinned selection](selections/f6509d0964197125118966d63114ba5a5115ee8467357e1db97b5227527e4d6f.json)
and [final preflight](preflights/f6509d0964197125118966d63114ba5a5115ee8467357e1db97b5227527e4d6f.json).

The validated pre-import PostgreSQL dump is:

`~/Library/Application Support/Artline/backups/byzantine-russian-more-20260920/local-before.dump`

It is **620,943,496 bytes**, with 339 archive-list entries and SHA-256
`8d21db50cfb51db6a0b27a62633f6bfae253b69a44f6782657b516a49e52912c`.
The [backup receipt](backup.json) references an earlier research selection;
the full database dump predates every mutation in this campaign. Exact batch
and image preimages are in `batch-preimages/` and `image-preimages/` beside it.

The reusable workflow is [byzantine-russian-more.py](../../../ops/byzantine-russian-more.py),
using the shared [expansion module](../../../ops/byzantine-russian-expansion.py).
Research evidence, failed attempts and earlier selections remain preserved.
