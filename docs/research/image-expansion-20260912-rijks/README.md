# Rijksmuseum image supplement — 12 September 2026

This supplement to the [main image campaign](../image-expansion-20260912/README.md)
selects 25 existing, eligible, museum-supported works without images. They
already have exact Rijksmuseum identifiers, including 24 current persistent
IDs and one legacy accession number. No new artworks or painters are created.

The [current search API](https://data.rijksmuseum.nl/docs/search) resolves the
legacy accession number; the response's exact object number is checked again.
The [EDM representation](https://data.rijksmuseum.nl/tutorials/oai-pmh/) provides
the exact object identity, primary image, and Public Domain Mark. Metadata CC0
is not used as image permission. Conflicting image-level rights are rejected.
The [official IIIF service](https://data.rijksmuseum.nl/tutorials/iiif/) supplies
a bounded image, then the shared importer enforces the 100,000-byte cap.

Museum reuse policy: [Information and Data Policy](https://data.rijksmuseum.nl/policy/information-and-data-policy).

The two-image canary passed local-file decoding/checksums, GCS checksums, and
media/rights/artwork-link audits in both databases. It added 198,482 bytes in
total; the larger image was 99,952 bytes. One reproduction was visually
inspected. `verification-canary.json` preserves the read-only report.

All **25 images** were uploaded and attached in both databases, with no skips
or failures. Its receipts and events use the same layout as the main campaign.
The final audit is preserved as `verification-final.json`. Resume, if needed,
with:

```sh
/tmp/artline-images-venv/bin/python ops/enrich-artwork-images.py apply \
  --run docs/research/image-expansion-20260912-rijks --providers rijks
```

Use the shared verifier with this run directory and a new report filename.
Both campaigns use the same pre-import backups, compression, GCS destination,
rights-evidence schema, and safe existing-image preservation.

Final verification: **2,242,651 bytes** across 25 images, largest **99,952 bytes**;
all files decode, all GCS sizes/checksums match, and both databases contain all
25 media records, rights records, and expected artwork links. No errors.
