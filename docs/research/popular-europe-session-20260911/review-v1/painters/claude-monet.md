# Claude Monet — source review

Artist ID `e96261e8-e784-4830-b29e-8380f34cc6af`; authority `Q296`. Local snapshot: 298 artwork links, 31 images.

- [x] Inventory and existing source queue inspected by the backend.
- [ ] Cross-museum research complete.
- [ ] Every image gap resolved.

## National Gallery, London

Structured source: [official API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api), [metadata and separate image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). One bounded current-name/explicit-alias query; not a complete oeuvre search. The 102 selected objects passed pinned importer, preservation, idempotency and API checks. Other entries below are automated source-specific screening decisions, not individual curatorial approval.

- [Still Life](https://www.nationalgallery.org.uk/data/0BWO-0001-0000-0000): not accessioned main-collection picture.
- [Grainstack (Sunset: winter)](https://www.nationalgallery.org.uk/data/0BZQ-0001-0000-0000): not accessioned main-collection picture.
- [Water-lilies](https://www.nationalgallery.org.uk/data/0C1J-0001-0000-0000): not accessioned main-collection picture.
- [The Museum at Le Havre](https://www.nationalgallery.org.uk/data/0CKK-0001-0000-0000): existing exact object; preserved, source review retained.
- [Irises](https://www.nationalgallery.org.uk/data/0CL3-0001-0000-0000): existing exact object; preserved, source review retained.
- [The Water-Lily Pond](https://www.nationalgallery.org.uk/data/0CLG-0001-0000-0000): existing exact object; preserved, source review retained.
- [Water-Lilies](https://www.nationalgallery.org.uk/data/0CRV-0001-0000-0000): creation date notation or cutoff review.
- [Flood Waters](https://www.nationalgallery.org.uk/data/0CUV-0001-0000-0000): existing exact object; preserved, source review retained.
- [La Pointe de la Hève, Sainte-Adresse](https://www.nationalgallery.org.uk/data/0CVJ-0001-0000-0000): existing exact object; preserved, source review retained.
- [Lavacourt under Snow](https://www.nationalgallery.org.uk/data/0CXU-0001-0000-0000): shared custody review.
- [The Gare St-Lazare](https://www.nationalgallery.org.uk/data/0CYY-0001-0000-0000): existing exact object; preserved, source review retained.
- [The Thames below Westminster](https://www.nationalgallery.org.uk/data/0D11-0001-0000-0000): existing exact object; preserved, source review retained.
- [Bathers at La Grenouillère](https://www.nationalgallery.org.uk/data/0D13-0001-0000-0000): existing exact object; preserved, source review retained.
- [The Beach at Trouville](https://www.nationalgallery.org.uk/data/0D1P-0001-0000-0000): existing exact object; preserved, source review retained.
- [The Petit Bras of the Seine at Argenteuil](https://www.nationalgallery.org.uk/data/0D5A-0001-0000-0000): existing exact object; preserved, source review retained.
- [Woman Seated on a Bench](https://www.nationalgallery.org.uk/data/0D82-0001-0000-0000): not accessioned main-collection picture.
- [Snow Scene at Argenteuil](https://www.nationalgallery.org.uk/data/0J1X-0001-0000-0000): existing exact object; preserved, source review retained.
- [Water-Lilies, Setting Sun](https://www.nationalgallery.org.uk/data/0J57-0001-0000-0000): existing exact object; preserved, source review retained.
- [Waterlilies](https://www.nationalgallery.org.uk/data/0Q6N-000B-0000-0000): not accessioned main-collection picture.

## Selected image outcomes

No image added for this painter in the current European five-image batch. Existing images were preserved; missing permission is not a completed image review.

## Next

## Athens supplement and user-visible image follow-up

- [Rouen Cathedral in the Morning (Pink Dominant)](https://goulandris.gr/en/artwork/monet-claude-rouen-cathedral-pink-dominant): added at Goulandris Athens, 1894, oil on canvas, 100.3 × 65.5 cm. Original title and translation retained; no published accession invented. Provenance mentions earlier owners and museums; only the explicit current Athens collection notice supplies the holding link. Other local Rouen paintings were compared by title, museum, accession and dating; they are different versions.
- No image downloaded from Goulandris: permission unresolved. Import and API receipts: `output/popular-europe-session/goulandris-apply/chunk-001.json`, `goulandris-after.json`, `goulandris-api.json`.
- **User report, 11 September: Monet pictures are not visible. Unresolved.** After the active enrichment task, reproduce the actual timeline/right-panel, catalogue and museum views. Check first-page/pagination ordering, image filters, API media fields, visibility rules and local asset delivery. Stored image counts are not proof that the UI displays them. See `docs/POPULAR_RESEARCH_CONTINUATION_PROMPT.md`.

## Remaining next work

Review existing European museum source links and unresolved exact dates/attributions; test documented alternate names only where the current query has a known gap. Search at least one different museum before regarding this source pass as representative. Do not retry inherited blocked image hosts or infer current display, ownership, or masterpiece status.
