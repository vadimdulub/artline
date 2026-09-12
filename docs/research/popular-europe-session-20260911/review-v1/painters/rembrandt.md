# Rembrandt van Rijn — source review

Artist ID `a08fbe07-1cb4-4423-b9e5-a17529eb64d9`; authority `Q5598`. Local snapshot: 898 artwork links, 13 images.

- [x] Inventory and existing source queue inspected by the backend.
- [ ] Cross-museum research complete.
- [ ] Every image gap resolved.

## National Gallery, London

Structured source: [official API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api), [metadata and separate image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). One bounded current-name/explicit-alias query; not a complete oeuvre search. The 102 selected objects passed pinned importer, preservation, idempotency and API checks. Other entries below are automated source-specific screening decisions, not individual curatorial approval.

- [An Old Man in an Armchair](https://www.nationalgallery.org.uk/data/0CNK-0001-0000-0000): multiple or missing creators.
- [The Woman taken in Adultery](https://www.nationalgallery.org.uk/data/0CR5-0001-0000-0000): existing exact object; preserved, source review retained.
- [Self Portrait at the Age of 34](https://www.nationalgallery.org.uk/data/0CRJ-0001-0000-0000): existing exact object; preserved, source review retained.
- [The Adoration of the Shepherds](https://www.nationalgallery.org.uk/data/0CSK-0001-0000-0000): multiple or missing creators.
- [Self Portrait at the Age of 63](https://www.nationalgallery.org.uk/data/0CTQ-0001-0000-0000): existing exact object; preserved, source review retained.
- [Belshazzar's Feast](https://www.nationalgallery.org.uk/data/0CVK-0001-0000-0000): creation date notation or cutoff review.
- [A Woman bathing in a Stream (Hendrickje Stoffels?)](https://www.nationalgallery.org.uk/data/0D7O-0001-0000-0000): existing exact object; preserved, source review retained.
- [Anna and the Blind Tobit](https://www.nationalgallery.org.uk/data/0E9N-0001-0000-0000): existing exact object; preserved, source review retained.
- [Portrait of Margaretha de Geer, Wife of Jacob Trip](https://www.nationalgallery.org.uk/data/0EB8-0001-0000-0000): multiple or missing creators.
- [Saskia van Uylenburgh in Arcadian Costume](https://www.nationalgallery.org.uk/data/0EOD-0001-0000-0000): existing exact object; preserved, source review retained.
- [Portrait of Frederick Rihel on Horseback](https://www.nationalgallery.org.uk/data/0EUH-0001-0000-0000): existing exact object; preserved, source review retained.
- [Portrait of Hendrickje Stoffels](https://www.nationalgallery.org.uk/data/0EYF-0001-0000-0000): creation date notation or cutoff review.
- [The Company of Captain Banning Cocq ('The Nightwatch')](https://www.nationalgallery.org.uk/data/0F1E-0001-0000-0000): multiple or missing creators.
- [Portrait of Philips Lucasz.](https://www.nationalgallery.org.uk/data/0F3F-0001-0000-0000): existing exact object; preserved, source review retained.
- [A Seated Man with a Stick](https://www.nationalgallery.org.uk/data/0F7A-0001-0000-0000): multiple or missing creators.
- [The Lamentation over the Dead Christ](https://www.nationalgallery.org.uk/data/0F88-0001-0000-0000): existing exact object; preserved, source review retained.
- [An Elderly Man as Saint Paul](https://www.nationalgallery.org.uk/data/0F9T-0001-0000-0000): creation date notation or cutoff review.
- [A Franciscan Friar](https://www.nationalgallery.org.uk/data/0FAM-0001-0000-0000): existing exact object; preserved, source review retained.
- [A Bearded Man in a Cap](https://www.nationalgallery.org.uk/data/0FB3-0001-0000-0000): existing exact object; preserved, source review retained.
- [Portrait of Jacob Trip](https://www.nationalgallery.org.uk/data/0FJL-0001-0000-0000): existing exact object; preserved, source review retained.
- [Diana bathing surprised by a Satyr](https://www.nationalgallery.org.uk/data/0FL5-0001-0000-0000): multiple or missing creators.
- [Portrait of Margaretha de Geer, Wife of Jacob Trip](https://www.nationalgallery.org.uk/data/0FL7-0001-0000-0000): existing exact object; preserved, source review retained.
- [A Study of an Elderly Man in a Cap](https://www.nationalgallery.org.uk/data/0FMM-0001-0000-0000): qualified or non-exact source creator.
- [A Young Man and a Girl playing Cards](https://www.nationalgallery.org.uk/data/0FNV-0001-0000-0000): multiple or missing creators.
- [Ecce Homo](https://www.nationalgallery.org.uk/data/0FT3-0001-0000-0000): existing exact object; preserved, source review retained.
- [Portrait of Aechje Claesdr.](https://www.nationalgallery.org.uk/data/0FY1-0001-0000-0000): existing exact object; preserved, source review retained.
- [A Man seated reading at a Table in a Lofty Room](https://www.nationalgallery.org.uk/data/0GJD-0001-0000-0000): multiple or missing creators.
- [Portraits of Jacob Trip and his Wife Margaretha de Geer](https://www.nationalgallery.org.uk/data/0HU5-0001-0000-0000): not accessioned main-collection picture.

## Selected image outcomes

- Artwork `d51704f8-613e-47a8-b90b-85b1d7fc23dd`: attached, 96802 bytes; `/assets/artworks/imported/pinakothek-alte-study-0ba19936f8873caae83675e3864f4044126b0399f3f0de19178475c7f4912bd9.jpg`. Exact accession, creator, date, collection branch and per-object CC BY-SA 4.0 verified. Source snapshot and rights evidence retained in `output/popular-europe-session/pinakothek-selection.json`; disk hashes and API delivery independently checked. No masterpiece or display change.

## Next

Review existing European museum source links and unresolved exact dates/attributions; test documented alternate names only where the current query has a known gap. Search at least one different museum before regarding this source pass as representative. Do not retry inherited blocked image hosts or infer current display, ownership, or masterpiece status.
