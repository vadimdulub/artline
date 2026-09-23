# Met painter-by-painter continuation — 20 September 2026

## Result

**30 additional artworks and 30 CC0 images delivered for 12 painters.** Both databases, cloud-storage hashes, rights evidence, live images and artwork API responses passed verification at 12:44 UTC, with zero errors.

The largest image is **98,170 bytes**; total delivery size is **2,069,873 bytes**. All images are full-frame, proportional JPEG derivatives. Seventeen drawings and thirteen prints were added as **review / research candidate** records, without publication timestamps. Museum holdings are evidenced; no current-display claims were added.

| Painter | Country | New images |
| --- | --- | ---: |
| Edgar Degas | France | 3 |
| Eugène Devéria | France | 1 |
| Gustave Doré | France | 2 |
| Hippolyte Flandrin | France | 7 |
| Jules Dupré | France | 1 |
| Paul Delaroche | France | 1 |
| Philibert-Louis Debucourt | France | 1 |
| Édouard Detaille | France | 2 |
| Stefano Della Bella | Italy | 9 |
| John Martin | United Kingdom | 1 |
| Paul Sandby | United Kingdom | 1 |
| Ferdinand Olivier | Germany | 1 |

Country totals: France 18, Italy 9, UK 2, Germany 1. Together with the preceding delivery, **80 Met images have been added across the two batches**. This is a bounded continuation, not exhaustive collection downloading or a claim that all painters have been fully researched.

## Individual review and importer correction

The continuation checked both catalogues, excluded previously selected source objects, and obtained current metadata for **46 further objects across 13 painters**. Review identified a source-vocabulary gap: the importer recognized Artist/Painter/Maker but not explicit Draftsman, Etcher or Artist and publisher credits.

The verifier now recognizes Draftsman/Draughtsman for drawings and Etcher/Artist and publisher for prints. It still requires exactly one supported maker with the same creator authority as the existing painter. Publisher-only, sitter, original-designer-only, multiple-maker and qualified-attribution cases remain held. Artwork dates, classification, object/accession identity, museum ownership and current CC0 image eligibility remain independent checks. Exact known creator life years must also agree with the museum in each target catalogue; unknown years remain unknown.

With that correction, **164 checksum-verified current API captures covering 49 painters** were rechecked from both selected lists. This includes previously researched works, not 164 new discoveries. Outcomes:

- **30 newly delivered** objects.
- **49 already delivered** objects passed the expanded checks.
- **4 title/version collisions** held without creating duplicates.
- **81 source/creator cases** held for further review.

The two earlier HTTP-404 objects had no current API body to recheck; their prior hold evidence remains preserved. Captured responses were less than 24 hours old, had matching checksums and source URLs, and were reused without unnecessary repeat requests. Earlier review outcomes were not overwritten.

## Creator-date discrepancies retained for review

| Painter | Catalogue life dates | Met life dates |
| --- | --- | --- |
| Anthonie Palamedesz. | 1602–1673 | 1601–1673 |
| Giovanni Benedetto Castiglione | 1607–1665 | 1609–1664 |
| Giovanni David | 1743–1790 | 1749–1790 |
| Thomas Rowlandson | 1756–1827 | 1757–1827 |

These discrepancies affect 50 reviewed source records, including 46 Rowlandson objects. Neither authority was silently preferred, and no biographies were changed. Palamedesz. object **338789**, delivered in the preceding batch, now has this additional metadata discrepancy logged; its existing review record and image were preserved. This does not revoke its museum image licence or settle the disputed birth year.

## Evidence

- [Painter-by-painter, artwork-by-artwork ledger](role-reviewed/painter-by-painter-review.json): creator identities and roles, source titles, dates, rights flags, outcomes and hold reasons.
- [Captured-source recheck provenance](role-reviewed/role-recheck-provenance.json).
- [Final selection and duplicate holds](delivery-round2/plan.json).
- [Checksum-pinned visual review](delivery-round2/reviewed-images.json); contact sheets [1](delivery-round2/contact-sheet-1.jpg), [2](delivery-round2/contact-sheet-2.jpg), [3](delivery-round2/contact-sheet-3.jpg).
- [Image/storage/rights verification](delivery-round2/image-verification.json).
- [Catalogue, artist-preservation and public-URL verification](delivery-round2/catalogue-public-verification.json).
- [Met Open Access policy](https://www.metmuseum.org/hubs/open-access) and [official API documentation](https://metmuseum.github.io/).

Only primary images were selected. The Degas recto/verso record and Olivier portfolio retain their complete source titles; this delivery does not claim to include every side or plate. Pale pencil/chalk studies retain their original source appearance, without artificial enhancement or cropping.

Recovery evidence is under `/Users/vadimdulub/Library/Application Support/Artline/backups/met-top-europe-20260920/delivery-round2/`. Existing painter profiles and country relationships were verified unchanged. No existing image or artwork was deleted or replaced, and no publication, commit, deployment, schema change or test-database operation was performed. Thirty-three offline tests passed across the Met source-gating, museum-image campaign and compression suites.
