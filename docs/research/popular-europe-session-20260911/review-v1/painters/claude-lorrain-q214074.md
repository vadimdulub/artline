# Claude Lorrain — source review

Artist ID `22910ad1-23c3-42b1-94d0-c0ba32681f3b`; authority `Q214074`. Local snapshot: 82 artwork links, 2 images.

- [x] Inventory and existing source queue inspected by the backend.
- [ ] Cross-museum research complete.
- [ ] Every image gap resolved.

## National Gallery, London

Structured source: [official API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api), [metadata and separate image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). One bounded current-name/explicit-alias query; not a complete oeuvre search. The 102 selected objects passed pinned importer, preservation, idempotency and API checks. Other entries below are automated source-specific screening decisions, not individual curatorial approval.

The bounded query returned no candidate objects. This is not evidence of zero museum holdings; source spellings, query coverage and other museums remain open.

## Selected image outcomes

No image added for this painter in the current European five-image batch. Existing images were preserved; missing permission is not a completed image review.

## Next

## 11 September supplement: documented Claude alias

The [museum biography](https://www.nationalgallery.org.uk/artists/claude) documents the name `Claude`. One additional targeted source query, not a repeat of the full cohort, selected 11 exact direct-attribution paintings. Imported IDs and individual official source URLs are recorded in `output/popular-europe-session/ng-aliases-apply/chunk-001.json`; all 11 details passed API checks and the database preservation audit. Works include *The Enchanted Castle*, *The Mill*, and both the Saint Ursula and Queen of Sheba embarkation paintings. Date range across these selections: 1632–1672.

New records remain in review with no image, masterpiece or current-display inference. Metadata permission does not clear National Gallery images. Other Claude-name results included different creators; exact-authority gates excluded them. Research across other museums and all image gaps remains open.

## Remaining next work

Review existing European museum source links and unresolved exact dates/attributions; test documented alternate names only where the current query has a known gap. Search at least one different museum before regarding this source pass as representative. Do not retry inherited blocked image hosts or infer current display, ownership, or masterpiece status.
