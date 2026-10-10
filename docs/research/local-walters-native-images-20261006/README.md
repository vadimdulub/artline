# Selected Walters native images — 6 October 2026

Thirty existing local artwork records without pictures were reviewed against current Walters accession pages. **Twenty-three CC0 pictures were downloaded, visually reviewed and attached locally.** Seven records remained without an approved picture at this checkpoint; three were subsequently resolved in the [individual reconciliation](../local-walters-reconciled-images-20261006/README.md). No catalogue records, creator profiles or holding claims were added, and no artwork was published.

The selected source is each photograph's own CC0 download on its exact accession page, for example [Martin Rykaert, River Landscape with Mining, 37.1730](https://art.thewalters.org/object/37.1730/). Matching checks cover inventory number, title, creator, attribution role and creation date. The displayed photograph and the licensed download must share the same resource. Different creator names and roles require individual review. Native question-mark qualifications are retained explicitly in image credits and evidence; the later [qualification audit](../local-walters-creator-qualification-20261006/README.md) documents seven corrections across the native passes. Native object pages, hashes and fetch receipts are preserved under `metadata/`; the full evidence is also attached to the local media rights record. Museum acquisition credits are retained without creating new accepted holdings or display records.

Thirteen approved pictures are archival monochrome reproductions. This limitation is recorded in their source evidence and database attribution. All 23 application images retain the complete source frame, including miniature mounts and fan-shaped compositions. No cropping, colour reconstruction or image generation was performed.

The anonymous Russian [Three-Panel Icon with the Deesis, 37.568](https://art.thewalters.org/object/37.568/) was explicitly included with its existing object-level creator label and century date. Its photograph shows only the Virgin panel. Visual review rejected it as a primary image for the complete three-panel group. Its private source and derivative are preserved, its public derivative is absent, and its database record is unchanged. The validator also prevents attaching that single-panel photograph through this operation.

The other six holds concern attribution/role wording (37.2454 and 38.16), a primary photograph whose filename does not match the exact inventory (35.310 and 35.311), or a photograph not identified as a front view (37.226 and 38.274). These are unresolved matches, not findings that suitable images do not exist.

Application JPEGs are in `apps/web/public/assets/artworks/imported/local-walters-native-images-20261006/`. Originals and both inspected contact sheets are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-walters-native-images-20261006/`. Locked preimages are under the corresponding `backups/local-walters-native-images-20261006/` directory. Every approved JPEG is below 100,000 bytes. Historical prepared metadata before the visual review is retained in `history/`.

Post-write checks passed for all 23 file hashes, source archives, primary-image links, artwork/media associations, exact stored rights evidence, source identifiers, CC0 licences and credits. All artwork metadata, creator links, external identifiers and review statuses were preserved; all seven held records remain byte-for-byte equivalent to their original catalogue snapshots. Four negative controls reject missing photograph licences, changed inventory numbers, qualified attribution and attaching the single icon panel as the whole group. They used private temporary HTML files and no database fixtures.

HTTP delivery is unverified for this operation: the existing Next.js server timed out during the latest earlier check and was not restarted. Files and database links have been verified independently.

- [Attached pictures and source pages](attached-images.csv)
- [Visual decisions](visual-review.json)
- [File and database verification](verification.json)
- [Exact rights evidence and unchanged holds](source-rights-verification.json)
- [Validator controls](validator-controls.json)
- [Counts and limitations](report.json)
- [Combined recovery checkpoint](../local-image-recovery-20261006/README.md)
