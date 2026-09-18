# Review of the returned ChatGPT research

The original four supplied files are preserved. This review queried local and production read-only, checked the returned CSVs against the starting assignment, retrieved selected official records, and inspected available candidate previews. It did not import records, upload images, or publish anything.

## Supplied results and integrity

- All 100 artwork rows and 88 painter rows have the expected headers, unique IDs, complete assignment coverage and unchanged existing-context fields.
- All 188 existing entities still match their separate local and production UUIDs. The 100 artworks still have no primary image in either database.
- ChatGPT reports 9 image results, 71 metadata-only results, 11 needing review and 9 blocked. Its image task therefore remains incomplete for 91 rows before the additional review holds below.
- Only eight painters were researched: four country proposals and four unresolved historical/identity cases. Eighty painter rows were not revisited.
- Five supporting files named in the research report are absent. The reconstructed remaining-task CSVs are derived from the supplied rows; they do not recreate the missing original search logs or prove those searches occurred.

## Independently checked findings

Four country additions agree with primary data: Claude Lorrain → FR; Giorgione, Perugino and Paolo Uccello → IT. NGA explicitly gives French/Italian labels for the first three, preserving Venetian/Umbrian historical display wording. The Met explicitly identifies Uccello as Italian with matching Wikidata identity. Keep Flemish and Netherlandish claims in review rather than silently mapping them to modern countries. [NGA official data](https://github.com/NationalGalleryOfArt/opendata), [Met object record](https://www.metmuseum.org/art/collection/search/438028).

All five new physical-object proposals match their official museum object IDs, titles, attributions and accessions. Live duplicate checks found no matching museum identifier, Wikidata crosswalk or same-institution accession. Numeric accession/ID collisions occurred in other museums and were correctly kept separate. Similar Rubens Holy Family records describe other museum objects. These checks are strong identifier checks, not proof that no unidentified or differently attributed duplicate can exist.

The four NGA works retain their source's qualified date wording and review status. For the Met Crucifixion, the source says “probably mid-1450s” and its API gives 1453–1457; the submitted 1450–1459 decade bounds are broader. Exact source bounds are supplied separately for date review. [NGA object data](https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data/objects.csv), [Met API](https://collectionapi.metmuseum.org/public/collection/v1/objects/438028).

An additional image for the new Met Uccello triptych was located and visually inspected. It shows all three painted panels with the engaged frame. The exact object page labels the image public domain, the API marks it public domain and supplies its direct URL, and the museum Open Access policy provides CC0. The reviewed candidate CSV includes this image and credit. [Object and image](https://www.metmuseum.org/art/collection/search/438028), [CC0 policy](https://www.metmuseum.org/hubs/open-access).

## Image findings requiring follow-up

The nine submitted image candidates have retrievable Commons metadata and match the stated source objects. Eight candidate previews were independently inspected. The Goya image returned HTTP 429 on renewed retrieval; its visual check remains incomplete, and it is only 640×886 pixels.

- Dürer: the visible Commons licence says PDM-owner while structured file data lists CC BY-SA 4.0/copyrighted. The museum's own record says Public Domain. Resolve the exact file discrepancy or use a separately verified museum-direct image. Its corrected unknown-sitter title and watercolour medium are supported. [Commons](https://commons.wikimedia.org/wiki/File:Portrait_of_a_Young_Woman_with_Her_Hair_Down_(SM_937).png), [Städel](https://sammlung.staedelmuseum.de/en/work/portrait-of-a-young-woman-with-her-hair-down).
- Van Gogh: Commons PDM and National Gallery image-download restrictions require reconciliation for this museum-sourced reproduction. The file's identity is the London NG3861 version. [Commons](https://commons.wikimedia.org/wiki/File:Vincent_van_Gogh_-_Wheat_Field_with_Cypresses_(National_Gallery_version).jpg), [museum terms](https://www.nationalgallery.org.uk/terms-of-use).
- Six Uffizi candidates: the file-level PDM/CC0 statements and visual matches check out, but the institution publishes a separate image-use authorization process. Its applicability to Artline publication was not determined here. This is an unresolved institutional-use issue, not a finding that the Commons licences are false or that every use is prohibited. [Publication policy](https://www.uffizi.it/en/professional-services/publications), [commercial-use policy](https://www.uffizi.it/en/professional-services/photo-rights-reproductions).
- Fra Angelico's photograph covers the main panel with its gold ornament, excluding the reunited predella. Preserve that distinction in the image caption and catalogue title; it does not show the complete reunited ensemble. [Museum object](https://www.uffizi.it/en/artworks/angelico-glorification).

These observations are recorded individually in `image_review.csv`. File-level licensing, successful image retrieval, visual identity and publication readiness are separate checks. None of the returned `verified_image` labels was blindly converted into a production attachment.

## Files and remaining scope

`country_updates_verified.csv` contains the four sourced country proposals; `new_artworks_reviewed.csv` contains all five new objects and the added Met image. Both preserve review and are unapplied proposals. `live_identity_validation.csv`, `structural_checks.json` and `live_catalogue_checks.json` record the identity/database checks. `selected_official_records.json` contains only the selected public institutional records needed for those checks.

`remaining_artwork_tasks_reconstructed.csv` contains the 91 rows without a reported approved image. The nine original image proposals also need the follow-up recorded in `image_review.csv`; images found are not images uploaded. `remaining_painter_tasks_reconstructed.csv` contains four unresolved researched painters and 80 unvisited profiles.

The 71 existing-work metadata-only proposals were checked structurally and against live identities, but their proposed facts were not all independently reread field by field. Do not treat this review as blanket approval to overwrite current titles, dates, attributions or museum records. Several otherwise verified-outcome rows also lack metadata-terms URLs; counts and scope are recorded in `review_summary.json`.
