# Source-index production delivery — 10 October 2026

Delivered **1,631 authentic images** and **835 missing descriptive fields** to **1,844 existing production artworks**. All changed records passed database and live API readback. No user review is pending.

The starting research document is [the source index](../source-index-20261009/README.md). Its 20,000 URLs are a mixture of object records, artist pages, catalogues, books and discovery resources. They are not 20,000 distinct artworks. All **7,209 directly linked artworks already existed in production**; verified native objects also resolved to existing records. No duplicate artwork records were created.

## Delivered

| Image source | Added images |
|---|---:|
| Walters Art Museum | 314 |
| Minneapolis Institute of Art | 273 |
| J. Paul Getty Museum | 159 |
| Pushkin State Museum of Fine Arts | 150 |
| Rijksmuseum | 139 |
| National Palace Museum, Taipei | 125 |
| State Russian Museum | 116 |
| National Museum in Kraków | 97 |
| Benaki Museum | 91 |
| Statens Museum for Kunst | 65 |
| Finnish National Gallery | 58 |
| WikiArt | 18 |
| Museum of Byzantine Culture, Thessaloniki | 15 |
| Cleveland Museum of Art | 9 |
| National Museum in Warsaw | 1 |
| National Museum in Kraków | 1 |

Metadata fills: 323 dimensions, 282 accession numbers and 230 medium descriptions across 504 works. Added 1,844 source citations, per-image rights evidence and explicit before/after audit records. Existing titles, dates, creator links, qualified attributions, holdings, display claims, image attachments and historical editorial statuses were preserved. Review records remain accessible through the unified catalogue.

Of the original 7,209 linked works, **1,780 now have a primary image**, compared with 547 at the pinned baseline; **5,429 still lack one**. Another 398 images enrich existing works reached through native museum references beyond those original direct bindings. These counts describe this source-index pass, not the entire Artline catalogue.

## Verification and recovery

- Cloud SQL backup `1791631795709` succeeded. Fresh per-record preimages, locked transaction preimages and postimages are under `~/Library/Application Support/Artline/backups/source-index-delivery-20261010/`.
- 18 offline source-binding and preservation tests passed. All 1,635 prepared files were visually checked on 42 contact sheets; original files also passed strict decode checks. Images are proportional, uncropped JPEG derivatives no larger than 100,000 bytes. Frames, scale bars, monochrome reproductions, album covers and fragment views are labelled where applicable.
- All 1,631 uploaded assets were fetched through `artlines.org` and checked against their SHA-256. All 1,844 changed records passed public artwork checks: painter detail routes validate changed metadata and images; the public artwork directory validates identity and primary images for unlinked creators, with all descriptive fields independently verified in the database. Route counts are in `public-api-verification.json`.
- Signed-out museum API checks returned the expected HTTP 401 under the 10 October member-access policy. Those observations are retained in `public-verification-attempts/`. No access settings, accounts or sessions were changed; intentionally public individual-artwork surfaces were used for public content checks.
- Mutations ran in one bounded transaction with the curated-ingestion advisory lock, row locks and exact preimage comparison. Protected fields and existing attachments were verified before commit and independently after commit. Source evidence and the plan are pinned by SHA-256.
- The real local database was not changed. No application deployment, schema change, status rewrite or commit was performed. Indexed, scoped lookups were used; reconciliation query plans are retained. This batch does not constitute a 10-million-row load test.

## Remaining source gaps

This delivery does **not** claim complete image coverage. Every indexed URL is accounted for in `final-source-ledger.json.gz`; every directly linked or changed work is accounted for in `final-artwork-ledger.json.gz`. Capturing a page does not establish its object identity or grant image reuse.

Source download holds include Chicago and Nationalmuseum access denials, Smithsonian and Athens image-host certificate failures, and two unusable Walters files. The visibly damaged Walters reproduction of *Joseph Accused by Potiphar’s Wife* was excluded; its exact-URL retry was denied and no alternate endpoint was used. Three prepared Minneapolis images retain unresolved date ranges crossing 1970. Two other targets have date-scope notes but no prepared image. Native duplicate conflicts (SMK KMS3477 and Walters 37.2619) remain unresolved, without creating more duplicates.

Some indexed sources still need exact object/image research or a usable reproduction: source-access failures, unknown creation dates, title/accession conflicts, missing or restrictive reuse labels and unprocessed reference material remain explicit in the ledgers. No invented artworks, dates, holdings, images or rights claims were added to close these gaps. User-approved Greek, Russian and WikiArt source decisions remain separate from actual copyright labels; Taiwan’s larger image tier retains CC BY 4.0 credit and attribution.

## Evidence

- `delivery-summary.json`, `production-applied.json`, `production-verification.json`, `public-api-verification.json`
- `delivery-plan-pin.json` and `delivery-plan.json.gz`
- `native-resolution-v2.json.gz` and final `secondary-resolution-008.json.gz` (including the exact Rijksmuseum language-alias reconciliation)
- `visual-review.json`, `contact-sheet-index.json`, `strict-image-decode-check*.json`
- `captures/`, `native/`, `object-pages/`, `secondary-native/`, `prepared-images/`, `uploads/`, `public-verification/`

Source-index SHA-256: `5d87c90644819d3b84fa2c09be85626716ebb79ad5d85647cdb9297a1aef2fed`. Delivery-plan SHA-256: `29133b50725a699ec6ad7011e1a0f7c8bda5b4e859a7e6550bd70ec9e625defb`.
