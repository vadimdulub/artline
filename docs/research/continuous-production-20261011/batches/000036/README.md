# Batch 36 — Berlin Byzantine mosaic icons

Verified production additions: **2 artworks, 2 primary images, 2 documented
museum holdings, 0 painters, 0 alternate images**. One distinct museum collection
record was created for the Skulpturensammlung und Museum für Byzantinische Kunst,
Staatliche Museen zu Berlin. Its two anonymous mosaic panels remain in review.
The generic Berlin network and Gemäldegalerie institutions were preserved.

| Native object | Inventory | Original source date | Stored conservative bounds |
| --- | --- | --- | --- |
| [Christ the Merciful](https://search.smb.museum/en/object/obj-1408418) | 6430 | Datierung: 1. Viertel 12. Jahrhundert | 1101–1125 |
| [Crucifixion with Mary and John](https://search.smb.museum/en/object/obj-1436813) | 6431 | Ende 13. Jahrhundert | 1201–1300 |

The late-thirteenth-century qualifier remains verbatim; the range covers the
whole century rather than inventing a precise late-century year. Both official
creator arrays are empty. No named artist or culture was inferred. Native mosaic
materials are retained; the broad work-type field remains `unknown` because the
established importer does not map mosaics to a dedicated category.

Five exact objects were researched. Three further icons (1722054, 1788002,
1787214) have explicit long-term-loan statements naming Frankfurt. They remain
research holds for ownership/custody representation. They were not imported and
their images were not requested. This is neither complete institutional nor
directory coverage. The legacy `doc_types` query was ignored by the new portal;
its unrelated search results were discarded.

Both selected native image assets explicitly identify the front (`Vorderseite`)
and carry `Public Domain Mark 1.0`. Native object references, photographer credits,
rights labels and URLs are preserved separately from user authorization. Both
prepared files were individually viewed using `view_image`. They retain the full
supplied compositions and measure 96,424 and 95,674 bytes. Source reproductions
are archived outside Documents under Application Support/Artline/source-images.

Verification checks the persisted metadata-plan checksum and empty transaction
preimages against live citations, native identities, source captures, insertion
audit events and production rows. Image checks cover every decoded file, hashes,
dimensions, exact native front-view identity, null-primary preimages, audit
updates, rights-plan checksums, storage metadata and public delivered bytes.
All 362 pre-existing artworks in the reconciled Berlin institution scope were
unchanged. No local-catalogue connection was made.

Replaying `apply` and `deliver` produced no new rows, citations or audit events.
The shared `artline-curated-ingestion` transaction lock, worker lock, exact
identity rechecks, immutable manifests and established backup paths remain in
use. The Cloud SQL proxy and actual instance connection name were verified before
writes. No supervisor, prompt, schema, LaunchAgent, deployment or commit changed.

Key receipts: `batch-verification-receipt.json`,
`independent-production-verification.json`, `independent-public-verification.json`,
`independent-resume-verification.json`, `actual-visual-review.json`,
`source-queue-update-verification.json`, and `final-checkpoint-verification.json`.
`CHECKPOINT.json` is also copied to the batch's Application Support runtime path.
The source queue changes only `staatliche_museen_berlin`; all other entries and
provider holds are preserved. The milestone report records measured runtime and
programme increments rather than claiming a whole-catalogue census.

Resume verification with the established environment:

```sh
/tmp/artline-cyprus-venv/bin/python ops/continuous-berlin-000036-verify.py
```

The next suggested bounded task is up to 25 exact Te Papa image-gap reviews with
record-specific reusable rights, preserving Berlin's saved loan/custody queue.
The existing external supervisor owns scheduling and continuation.
