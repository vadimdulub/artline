# Walters native image follow-up — 6 October 2026

Thirty additional existing local artworks without pictures were checked against their current Walters accession pages, excluding the thirty records in the first native pass. **Twenty-two CC0 pictures were downloaded, visually reviewed and attached locally.** Eight records remained held at this checkpoint; five were subsequently resolved in the [individual reconciliation](../local-walters-reconciled-images-20261006/README.md). All catalogue metadata and review statuses were preserved; no new artwork, creator, holding or current-display records were created.

This operation uses the [same native identity and photograph-specific CC0 checks](../local-walters-native-images-20261006/README.md) as the first pass. The approved additions span 1789–1829 and include portrait miniatures, landscapes and other painted scenes. Ten are archival monochrome photographs, explicitly identified as such in their image attributions and evidence. All 22 preserve the complete source frame and are below 100,000 bytes.

One source discrepancy is retained explicitly: the [38.109 object page](https://art.thewalters.org/object/38.109/) calls the work *Portrait of the Marquise de La Fayette*, while its descriptive body identifies the uniformed sitter as La Fayette and uses “marquis.” The photograph matches the exact inventory and native description. It was attached with the original catalogue title unchanged, and the discrepancy is recorded in the rights evidence for editorial review. The uncertain sitter wording in *Alexander Hamilton (1757–1804) (?)* was likewise preserved.

The eight unresolved records are:

- 37.2778, 38.305 and 37.761: primary photograph not identified as a front view.
- 38.388: native creator differs from the stored creator; no reassignment was made.
- 35.313: primary image filename does not match the exact inventory.
- 38.2: native attribution is qualified or uses a different role.
- 38.376 and 38.377: no primary image on the captured current object pages.

Application files are in `apps/web/public/assets/artworks/imported/local-walters-followup-images-20261006/`. Original reproductions and the two inspected contact sheets are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-walters-followup-images-20261006/`; locked preimages use the corresponding `backups/local-walters-followup-images-20261006/` directory. Source HTML and fetch receipts remain in `metadata/`.

Verification passed for files, archive hashes, database associations, licence URLs, credits, exact stored source evidence and source identifiers. The combined recovery check also verifies unchanged creator links and external identifiers. All eight held artwork snapshots remain unchanged. HTTP delivery remains unverified because the existing local Next.js server timed out in the latest earlier check; this operation did not restart it or repeat that request.

- [Attached pictures and source pages](attached-images.csv)
- [Visual decisions](visual-review.json)
- [File and database verification](verification.json)
- [Exact rights evidence and unchanged holds](source-rights-verification.json)
- [Counts and limitations](report.json)
- [Combined recovery checkpoint](../local-image-recovery-20261006/README.md)
