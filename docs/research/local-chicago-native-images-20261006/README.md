# Chicago native image recovery — 6 October 2026

Thirty-six images are saved locally and linked to existing database artworks: 29 drawings and seven prints. Forty exact native-ID records were individually reviewed, one from each of forty existing creators. Four remain unattached. The broader [metadata discovery](../local-chicago-native-audit-20261006/README.md) found 4,056 leads; these are not treated as approved images or individually reviewed artworks.

Current native object records independently corroborate the exact inventory, title, date wording and bounds, artwork type and unique unqualified primary creator. Existing artist names/aliases, known life years and Wikidata authorities are retained as matching evidence. All source and catalogue dates remain unchanged.

The current `/images` responses leave `credit_line` null and return an absolute IIIF URL. The existing shared validator was left unchanged. A separate current-page check requires the exact photograph's native gallery download button to carry **CC0 Public Domain Designation**, the matching image ID, inventory and dimensions, and the museum's image-licensing link. The native image resource must identify this object alone, and the page's primary-image metadata must agree. Captured [image-licensing policy evidence](source-policy-review.json) corroborates the label-specific grant. A metadata CC0 statement alone does not approve a photograph.

Thirty-nine records passed these source checks. Millet's *Study: Nude Woman Seen from the Back*, Morisot's *Jeanne Pontillon* and Rembrandt's *The First Oriental Head* returned HTTP 403 for the selected image URL and remain unattached. Murillo's *Saint Joseph and the Sleeping Christ Child* remains held because the current native creator record says 1618 while the existing artist birth year is 1617; neither was rewritten.

Both contact sheets were inspected. Full-source inspections confirmed faint marks and paper supports in the Renoir, Daumier and Géricault drawings and the pastel colours and subject of the Whistler study. Complete source frames, margins, mounts, paper damage and the Claude Lorrain photographic tonal strip were retained. No cropping, recolouring or generated content was applied. Application JPEGs are at most 99,916 bytes.

Three double-sided sheets have explicit recto labels, accessible text and attribution: Monet's caricature of a man beside a desk, Whistler's Mrs. Louis Huth study and Toulouse-Lautrec's *Mme Lili Grenier*. Their reverse subjects are expressly not shown. The original two-sided catalogue titles remain intact.

All 36 source-image hashes, application files, database primary references and artwork/media associations passed verification. Complete stored image-rights evidence, creator records/aliases/identifiers and holding assertions also passed. Eleven source-validation negative controls and three view-qualification controls passed using in-memory copies only. All four held artwork records are unchanged. No catalogue records, fixtures, holding claims or production updates were created, and review states remain intact. A fresh HTTP-delivery check was not completed following earlier local server timeouts.

Application JPEGs: `apps/web/public/assets/artworks/imported/local-chicago-native-images-20261006/`. Selected original reproductions and contact sheets: `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-chicago-native-images-20261006/`. Locked database preimages: `/Users/vadimdulub/Library/Application Support/Artline/backups/local-chicago-native-images-20261006/`. Public source metadata, native pages, redirects and capture receipts remain in `metadata/`.

- [Attached pictures and source pages](attached-images.csv)
- [Visual decisions](visual-review.json)
- [Explicit recto qualifications](view-scope-review.json)
- [Held source findings](held-source-review.json)
- [Native source controls](source-verifier-controls.json)
- [Image-view controls](view-verifier-controls.json)
- [Complete source/database verification](source-rights-verification.json)
- [Operation counts](report.json)
