# Pietro Perugino — source review

Artist ID `e4cb6720-d3e3-4a5a-96ee-d9fa62e7c3c8`; authority `Q5827`. Local snapshot: 10 artwork links, 2 images.

- [x] Inventory and existing source queue inspected by the backend.
- [ ] Cross-museum research complete.
- [ ] Every image gap resolved.

## National Gallery, London

Structured source: [official API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api), [metadata and separate image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). One bounded current-name/explicit-alias query; not a complete oeuvre search. The 102 selected objects passed pinned importer, preservation, idempotency and API checks. Other entries below are automated source-specific screening decisions, not individual curatorial approval.

- [Christ Crowned with Thorns](https://www.nationalgallery.org.uk/data/0ET3-0001-0000-0000): multiple or missing creators.
- [The Virgin and Child in a Mandorla with Cherubim](https://www.nationalgallery.org.uk/data/0F5I-0001-0000-0000): multiple or missing creators.
- [The Archangel Raphael with Tobias](https://www.nationalgallery.org.uk/data/0F7Q-0001-0000-0000): ADDED, verified review record `d78ea5e4-ec0c-465d-87b9-1dee097a76cc`; no image in this batch.
- [The Archangel Michael](https://www.nationalgallery.org.uk/data/0F89-0001-0000-0000): ADDED, verified review record `b8ae663f-e043-47a2-8a9f-ce49f3418ba2`; no image in this batch.
- [The Virgin and Child with Saint John](https://www.nationalgallery.org.uk/data/0FAC-0001-0000-0000): qualified or non-exact source creator.
- [The Virgin and Child with an Angel](https://www.nationalgallery.org.uk/data/0FBI-0001-0000-0000): ADDED, verified review record `b5a83a97-d95d-44d8-bc27-fbc6fd79c098`; no image in this batch.
- [The Baptism of Christ](https://www.nationalgallery.org.uk/data/0FHX-0001-0000-0000): multiple or missing creators.
- [The Virgin and Child with Saints Jerome and Francis](https://www.nationalgallery.org.uk/data/0FR8-0001-0000-0000): creation date notation or cutoff review.
- [The Virgin and Child with Saints](https://www.nationalgallery.org.uk/data/0G5N-0001-0000-0000): multiple or missing creators.
- [Three Panels from an Altarpiece, Certosa](https://www.nationalgallery.org.uk/data/0HXC-0001-0000-0000): not accessioned main-collection picture.

## Selected image outcomes

No image added for this painter in the current European five-image batch. Existing images were preserved; missing permission is not a completed image review.

## Next

### Caen follow-up, 11 September 2026

- [x] Added and verified [Le Mariage de la Vierge, inv. 171](https://pop.culture.gouv.fr/notice/joconde/06570007477). Exact [museum notice](https://mba.caen.fr/oeuvre/le-mariage-de-la-vierge) supports 1504; original national-dataset notation `1503,1504` retained in source evidence. Review-only, no image or masterpiece assertion. Receipt: `output/popular-europe-session/caen-apply/chunk-001.json`.
- [ ] [Saint Jérôme dans le désert, inv. 79](https://mba.caen.fr/oeuvre/saint-jerome-dans-le-desert): museum 1498–1502 versus national catalogue 1496–1502. Deferred rather than silently choosing a boundary.
- [ ] Caen images: reuse remains unresolved for the intended use; no image downloaded. Other Perugino museums remain open.

Review existing European museum source links and unresolved exact dates/attributions; test documented alternate names only where the current query has a known gap. Search at least one different museum before regarding this source pass as representative. Do not retry inherited blocked image hosts or infer current display, ownership, or masterpiece status.
