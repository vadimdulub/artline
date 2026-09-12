# El Greco — source review

Artist ID `1e0af779-3de1-4811-adab-6e7dcaaabf29`; authority `Q301`. Local snapshot: 18 artwork links, 5 images.

- [x] Inventory and existing source queue inspected by the backend.
- [ ] Cross-museum research complete.
- [ ] Every image gap resolved.

## National Gallery, London

Structured source: [official API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api), [metadata and separate image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). One bounded current-name/explicit-alias query; not a complete oeuvre search. The 102 selected objects passed pinned importer, preservation, idempotency and API checks. Other entries below are automated source-specific screening decisions, not individual curatorial approval.

- [The Agony in the Garden of Gethsemane](https://www.nationalgallery.org.uk/data/0CLN-0001-0000-0000): qualified or non-exact source creator.
- [The Adoration of the Name of Jesus](https://www.nationalgallery.org.uk/data/0D7X-0001-0000-0000): existing exact object; preserved, source review retained.
- [Christ driving the Traders from the Temple](https://www.nationalgallery.org.uk/data/0DA6-0001-0000-0000): existing exact object; preserved, source review retained.
- [Saint Jerome as Cardinal](https://www.nationalgallery.org.uk/data/0FFZ-0001-0000-0000): multiple or missing creators.
- [Saint Peter](https://www.nationalgallery.org.uk/data/0FY2-0001-0000-0000): qualified or non-exact source creator.

## Selected image outcomes

No image added for this painter in the current European five-image batch. Existing images were preserved; missing permission is not a completed image review.

## Next

## Greek source supplement

- [St Peter, Π.9027](https://www.nationalgallery.gr/en/artwork/st-peter/): added at National Gallery Athens, circa 1600–1607, oil on canvas, 68.5 × 53 cm. Structured precision `circa_range`; exact source wording preserved. The earlier incorrect single-year `circa` label was rejected in a rollback preview, never applied. v3 import, preservation and API checks passed. Image licence unresolved; no download.
- [Goulandris Veil of Saint Veronica](https://goulandris.gr/en/artwork/el-greco-the-holy-face): direct creator and Athens branch confirmed; early-1580s interval representation remains deferred.
- [Athens Entombment](https://www.nationalgallery.gr/en/artwork/the-entombment-of-christ/), Π.9979, circa 1568–1570: queued exact object capture. [Concert of the Angels](https://www.nationalgallery.gr/en/artwork/the-concert-of-the-angels/), Π.152: source says separated section of an Annunciation; relationship review before importing as an object.
- Historical Museum of Crete Baptism has conflicting source dates 1567/1569; do not synthesize a range. See [session findings](../../FINDINGS.md) for both official links and additional Modena/Denmark leads.
- Pinakothek's El Greco-index records are qualified school/workshop cases, not direct autograph additions.

All unresolved images and cross-museum research remain open.

## Remaining next work

Review existing European museum source links and unresolved exact dates/attributions; test documented alternate names only where the current query has a known gap. Search at least one different museum before regarding this source pass as representative. Do not retry inherited blocked image hosts or infer current display, ownership, or masterpiece status.
