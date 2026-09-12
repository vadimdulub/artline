# Vincent van Gogh — source review

Artist ID `5167a832-6547-4282-8e63-fa5ab8d5fa5e`; authority `Q5582`. Local snapshot: 84 artwork links, 11 images.

- [x] Inventory and existing source queue inspected by the backend.
- [ ] Cross-museum research complete.
- [ ] Every image gap resolved.

## National Gallery, London

Structured source: [official API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api), [metadata and separate image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). One bounded current-name/explicit-alias query; not a complete oeuvre search. The 102 selected objects passed pinned importer, preservation, idempotency and API checks. Other entries below are automated source-specific screening decisions, not individual curatorial approval.

- [Farms near Auvers](https://www.nationalgallery.org.uk/data/0CPH-0001-0000-0000): not accessioned main-collection picture.
- [Van Gogh's Chair](https://www.nationalgallery.org.uk/data/0DDQ-0001-0000-0000): existing exact object; preserved, source review retained.
- [Long Grass with Butterflies](https://www.nationalgallery.org.uk/data/0E59-0001-0000-0000): existing exact object; preserved, source review retained.
- [Sunflowers](https://www.nationalgallery.org.uk/data/0GE6-0001-0000-0000): existing exact object; preserved, source review retained.
- [A Wheatfield, with Cypresses](https://www.nationalgallery.org.uk/data/0GGV-0001-0000-0000): existing exact object; preserved, source review retained.
- [Two Crabs](https://www.nationalgallery.org.uk/data/0I1Q-0001-0000-0000): not accessioned main-collection picture.
- [Head of a Peasant Woman](https://www.nationalgallery.org.uk/data/0MKD-0001-0000-0000): existing exact object; preserved, source review retained.
- [Landscape with Ploughman](https://www.nationalgallery.org.uk/data/0MZD-0009-0000-0000): not accessioned main-collection picture.

## Selected image outcomes

- Artwork `acff2810-093d-4ce1-89f1-dc9f71411377`: attached, 90597 bytes; `/assets/artworks/imported/pinakothek-neue-study-fe9c2ce374ec35a6ec2889216749989c0d6a52d6327d6d5a8e42c6861e45352c.jpg`. Exact accession, creator, date, collection branch and per-object CC BY-SA 4.0 verified. Source snapshot and rights evidence retained in `output/popular-europe-session/pinakothek-selection.json`; disk hashes and API delivery independently checked. No masterpiece or display change.

## Next

Review existing European museum source links and unresolved exact dates/attributions; test documented alternate names only where the current query has a known gap. Search at least one different museum before regarding this source pass as representative. Do not retry inherited blocked image hosts or infer current display, ownership, or masterpiece status.
