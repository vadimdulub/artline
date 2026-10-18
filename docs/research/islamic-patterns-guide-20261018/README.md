# Islamic geometric patterns guide

English is canonical at `/guides/islamic-patterns`. Nine user-supplied translations use the existing Artline language codes. The guide lives in Guides and its Interactive filter; all editions are public.

The supplied 13,754,660-byte standalone HTML is replaced by native article pages, scoped styles and shared geometry code. No embedded raster images or external image hotlinks remain. Six Met Open Access reproductions have three proportional WebP sizes each. Ordinary photographs use responsive lazy loading. Manuscript-page detail images and enlargements load on demand. Full source frames, object references, accession numbers, credits and rights are preserved in `assets.json`, the six official Met API records here, and Storage receipts. The four architectural/decorative objects are guide photographs rather than main-catalogue paintings.

Two exact manuscript paintings were missing from the production catalogue. Their native IDs, accessions, dates and holding assertions now identify them independently. Only Shaikh Zada's **Artist** role is linked for Met 446606; Nizami's Author role and the calligraphers are separate. His 1510–1550 activity dates are not birth/death dates. The painter of 452672 is unidentified. Its explicit `ca. 1525–35` label is retained alongside the broader structured API date discrepancy in the citation. Both works and the new painter remain in review. The real local catalogue was not modified.

Eight original SVG designs retain editable palettes, drawing styles, scale, line weight, rotation, individual piece colours, keyboard navigation, undo/reset and PNG/SVG export. Four construction lessons distinguish a motif's rotational symmetry from that of its repeating lattice; the fivefold and tenfold medallions have finite boundaries.

`input-receipt.json` pins the three supplied inputs. Article prose and translations came from those inputs; no translation service was used. `node ops/verify-islamic-patterns-images.cjs <original.html>` recreates and verifies local debug images with the installed Sharp/libvips versions. Images stay in Cloud Storage, outside Git. Run `python3 ops/build-guide-search-index.py --check` whenever editions change; deploy the matching API search projection and web editions together.

Validation and live release results are recorded in `docs/islamic-patterns-release-20261018.json` after deployment.
