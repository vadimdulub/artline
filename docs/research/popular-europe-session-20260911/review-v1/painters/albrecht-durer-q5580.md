# Albrecht Dürer — source review

Artist ID `1e6dc7e2-7c1d-4ec6-b3a6-25c05bfe4a93`; authority `Q5580`. Local snapshot: 1080 artwork links, 9 images.

- [x] Inventory and existing source queue inspected by the backend.
- [ ] Cross-museum research complete.
- [ ] Every image gap resolved.

## National Gallery, London

Structured source: [official API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api), [metadata and separate image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). One bounded current-name/explicit-alias query; not a complete oeuvre search. The 102 selected objects passed pinned importer, preservation, idempotency and API checks. Other entries below are automated source-specific screening decisions, not individual curatorial approval.

- [Saint Jerome](https://www.nationalgallery.org.uk/data/0CP7-0001-0000-0000): ADDED, verified review record `c9668f4b-d955-478d-bb35-7f92fd6a95a6`; no image in this batch.
- [The Virgin and Child ('The Madonna with the Iris')](https://www.nationalgallery.org.uk/data/0EG1-0001-0000-0000): multiple or missing creators.
- [The Painter's Father](https://www.nationalgallery.org.uk/data/0FLG-0001-0000-0000): multiple or missing creators.

## Selected image outcomes

- Artwork `6c74c0ca-8dc6-43a3-a282-8f2add014354`: attached, 84862 bytes; `/assets/artworks/imported/pinakothek-alte-study-d9ccb6b062567b6043d9b28e89c544ec80e0d03bb3c1fe52d888aa4218b11e62.jpg`. Exact accession, creator, date, collection branch and per-object CC BY-SA 4.0 verified. Source snapshot and rights evidence retained in `output/popular-europe-session/pinakothek-selection.json`; disk hashes and API delivery independently checked. No masterpiece or display change.

## Next

## 11 September supplement: eight additional paintings and images

- [Glimsche Beweinung, inv. 704](https://www.sammlung.pinakothek.de/de/artwork/Y0GRY2XLRX): circa 1500; Alte Pinakothek; added with authentic image, 96,498 bytes.
- [Maria als Schmerzensmutter, inv. 709](https://www.sammlung.pinakothek.de/de/artwork/Pdxz0KvGw5): source `1495/98`, retained as 1495–1498; Alte Pinakothek; image 72,239 bytes.
- [Muttergottes mit der Nelke, inv. 4772](https://www.sammlung.pinakothek.de/de/artwork/QrLWeqA4NO): 1516; Alte Pinakothek; image 99,476 bytes.
- [Bildnis eines jungen Mannes, inv. 694](https://www.sammlung.pinakothek.de/de/artwork/o5xrQgP47X): 1500; Alte Pinakothek; image 91,681 bytes.
- [Lucretia, inv. 705](https://www.sammlung.pinakothek.de/de/artwork/k2xnBjAxPd): 1518; Alte Pinakothek; image 85,948 bytes.
- [Herkules, inv. 5379](https://www.sammlung.pinakothek.de/de/artwork/02LAWJX4yk): 1500; documented permanent loan to Germanisches Nationalmuseum; image 89,881 bytes. GNM's own inventory Gm166 remains an alias-reconciliation follow-up, not a second artwork.
- [Michael Wolgemut, inv. 700](https://www.sammlung.pinakothek.de/de/artwork/M0xyZ1VLpl): 1516; documented permanent loan to Germanisches Nationalmuseum; image 94,135 bytes. GNM inventory Gm885 remains an alias follow-up.
- [Jakob Fugger, inv. 717](https://www.sammlung.pinakothek.de/de/artwork/8MLv2rZLz3): circa 1520; Staatsgalerie in der Katharinenkirche Augsburg; image 95,673 bytes. The branch is reported closed; no on-view assertion.

All eight additions passed pinned global deduplication, backup, preservation and API checks. Images use the exact primary museum reproduction, each individually marked CC BY-SA 4.0; no masterpiece designation inferred. Receipts: `output/popular-europe-session/durer-apply/`, `durer-images-apply.json`, `durer-images-after.json`, `durer-images-api.json`.

Still unresolved: multipart Paumgartner, Four Apostles, Jabach and Oswolt Krel units, disjunctive Holzschuher dating, and qualified works among 44 artist-index records. Neither index review nor these eight additions complete the painter's research.

## Remaining next work

Review existing European museum source links and unresolved exact dates/attributions; test documented alternate names only where the current query has a known gap. Search at least one different museum before regarding this source pass as representative. Do not retry inherited blocked image hosts or infer current display, ownership, or masterpiece status.
