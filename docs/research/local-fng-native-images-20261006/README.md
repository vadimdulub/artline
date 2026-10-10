# Finnish National Gallery image recovery — 6 October 2026

**17 CC0 reproductions are saved locally and attached to 17 existing artworks.** All were visually inspected as complete source frames. The files, archived originals, database links, complete image evidence and credits passed verification. Catalogue titles, creation dates, artist records and identifiers, holding assertions and review status remain unchanged.

The museum's [documented anonymous metadata export](https://kokoelma.kansallisgalleria.fi/api/swagger/) supplied current object records and photograph-specific CC0 grants. A read-only intersection with 1,883 eligible missing-image records produced 17 preferred-photograph leads. Only these 17 artworks count as individual reviews; no catalogue records or fixtures were created. The current 89,091-object metadata export was archived privately with its response receipt and SHA-256. Image downloads were limited to the selected photographs.

The initial discovery used the older holding-writing validator and held fifteen leads. The new image-only path retains native ownership verbatim and compares existing holding assertions without changing them. Photograph permission and legal ownership are separate facts. The original validator still requires state ownership by default, and a negative control confirms that it continues to reject a loan in that workflow.

Two records needed individual reconciliation:

- *A Dutch Townscape*, Aert van der Neer, object 392848, inventory A I 673: current museum records use person IDs 62412 and 62968 for the same named artist with matching life years and birth/death places. The comparison with object 388924 is preserved in `metadata/aert-creator-authority-review.json` and the image evidence. Existing artist records and identifiers were preserved.
- *Interior, Summer*, Elin Danielson-Gambogi, object 6127043, inventory A-2026-55: the current native date range 1903–1913 lies within the catalogue's 1900–1919 range. Both ranges and the review qualification are retained in image evidence and attribution; catalogue dates were preserved. The native owner spelling `Suomen valtip` is retained verbatim.

Sallinen's *Kaarina*, object 430074, uses a source-provided archival monochrome reproduction. Its attribution explicitly states that original painting colours are not represented. The specific photograph ID, source checksum and visual review are pinned. The source image was inspected separately at full size. Gallen-Kallela's *Spring* remains labelled as a study for the Jusélius Mausoleum frescoes.

Application JPEGs, each at most 99,716 bytes, are under `apps/web/public/assets/artworks/imported/local-fng-native-images-20261006/`. Originals, the current metadata export and the approved contact sheet are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-fng-native-images-20261006/`. Locked preimages are under the corresponding `Artline/backups/local-fng-native-images-20261006/` directory. Earlier prepared evidence is retained in `history/` for the credit cleanup and monochrome qualification.

Verification passed for all 17 source matches and ten negative controls, including incorrect photograph URLs, missing CC0 permission, altered owner evidence, unreviewed date changes, incorrect artist identity and missing monochrome qualifications. No test database or catalogue fixtures were used. The combined verification also checked creator links and artwork identifiers. HTTP delivery remains unverified for this batch following earlier local server timeouts; file and database verification passed. Production was not changed.

- [Attached artworks, source pages and file sizes](attached-images.csv)
- [Visual decisions and pinned file checksums](visual-review.json)
- [Source rights, unchanged artists and holding assertions](source-rights-verification.json)
- [Local attachment receipt](apply-receipt.json)
- [File and database verification](verification.json)
- [Operation counts](report.json)
- [Source validator controls](validator-controls.json) and [monochrome controls](monochrome-validator-controls.json)
- [Combined recovery report](../local-image-recovery-20261006/README.md)
