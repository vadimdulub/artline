# Masaccio — source review

Artist ID `31aa9615-7b3b-4c29-a74c-d1d9363aa77b`; authority `Q5811`. Local snapshot: 2 artwork links, 1 images.

- [x] Inventory and existing source queue inspected by the backend.
- [ ] Cross-museum research complete.
- [ ] Every image gap resolved.

## National Gallery, London

Structured source: [official API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api), [metadata and separate image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). One bounded current-name/explicit-alias query; not a complete oeuvre search. The 102 selected objects passed pinned importer, preservation, idempotency and API checks. Other entries below are automated source-specific screening decisions, not individual curatorial approval.

- [The Virgin and Child](https://www.nationalgallery.org.uk/data/0DHE-0001-0000-0000): ADDED, verified review record `e1dbe038-07d9-4d9c-b94f-31cd8b0c738b`; no image in this batch.
- [Saints Jerome and John the Baptist](https://www.nationalgallery.org.uk/data/0E7O-0001-0000-0000): multiple or missing creators.
- [The Nativity](https://www.nationalgallery.org.uk/data/0G07-0001-0000-0000): multiple or missing creators.
- [Santa Maria Maggiore Altarpiece](https://www.nationalgallery.org.uk/data/0HNE-0001-0000-0000): not accessioned main-collection picture.

## Selected image outcomes

No image added for this painter in the current European five-image batch. Existing images were preserved; missing permission is not a completed image review.

## Next

Review existing European museum source links and unresolved exact dates/attributions; test documented alternate names only where the current query has a known gap. Search at least one different museum before regarding this source pass as representative. Do not retry inherited blocked image hosts or infer current display, ownership, or masterpiece status.
