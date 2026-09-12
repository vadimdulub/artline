# Camille Pissarro — source review

Artist ID `e25feb90-9e7b-4a81-92e2-37b85fa09dbe`; authority `Q134741`. Local snapshot: 204 artwork links, 21 images.

- [x] Inventory and existing source queue inspected by the backend.
- [ ] Cross-museum research complete.
- [ ] Every image gap resolved.

## National Gallery, London

Structured source: [official API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api), [metadata and separate image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). One bounded current-name/explicit-alias query; not a complete oeuvre search. The 102 selected objects passed pinned importer, preservation, idempotency and API checks. Other entries below are automated source-specific screening decisions, not individual curatorial approval.

- [The Pork Butcher](https://www.nationalgallery.org.uk/data/0CN6-0001-0000-0000): not accessioned main-collection picture.
- [A Wool-Carder](https://www.nationalgallery.org.uk/data/0CXD-0001-0000-0000): not accessioned main-collection picture.
- [The Little Country Maid](https://www.nationalgallery.org.uk/data/0CY3-0001-0000-0000): not accessioned main-collection picture.
- [Portrait of Félix Pissarro](https://www.nationalgallery.org.uk/data/0D2C-0001-0000-0000): not accessioned main-collection picture.
- [The Boulevard Montmartre at Night](https://www.nationalgallery.org.uk/data/0DCD-0001-0000-0000): existing exact object; preserved, source review retained.
- [The Côte des Bœufs at L'Hermitage](https://www.nationalgallery.org.uk/data/0E8F-0001-0000-0000): existing exact object; preserved, source review retained.
- [Fox Hill, Upper Norwood](https://www.nationalgallery.org.uk/data/0EGX-0001-0000-0000): existing exact object; preserved, source review retained.
- [The Louvre under Snow](https://www.nationalgallery.org.uk/data/0EHQ-0001-0000-0000): existing exact object; preserved, source review retained.
- [The Avenue, Sydenham](https://www.nationalgallery.org.uk/data/0EM2-0001-0000-0000): existing exact object; preserved, source review retained.
- [Portrait of Cezanne](https://www.nationalgallery.org.uk/data/0FAE-0001-0000-0000): not accessioned main-collection picture.
- [View from Louveciennes](https://www.nationalgallery.org.uk/data/0GGD-0001-0000-0000): shared custody review.
- [Late Afternoon in our Meadow](https://www.nationalgallery.org.uk/data/0Q74-0008-0000-0000): existing exact object; preserved, source review retained.

## Selected image outcomes

- Artwork `9583fbdd-277d-4ad3-af6d-f23ebc0d5f31`: attached, 91190 bytes; `/assets/artworks/imported/pinakothek-neue-study-2ef45892748104d1e55dee09603c59fa274a5a6e008d497ce1bc4dd017be4bf8.jpg`. Exact accession, creator, date, collection branch and per-object CC BY-SA 4.0 verified. Source snapshot and rights evidence retained in `output/popular-europe-session/pinakothek-selection.json`; disk hashes and API delivery independently checked. No masterpiece or display change.

## Next

Review existing European museum source links and unresolved exact dates/attributions; test documented alternate names only where the current query has a known gap. Search at least one different museum before regarding this source pass as representative. Do not retry inherited blocked image hosts or infer current display, ownership, or masterpiece status.
