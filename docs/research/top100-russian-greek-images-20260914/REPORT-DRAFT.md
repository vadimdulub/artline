# Artwork image coverage and source research

<!-- Final figures and the painter-by-painter table are generated from committed image receipts and verified database snapshots. -->

The catalogue’s image gaps fall into several distinct groups: existing museum objects with open reproductions, works with usable Commons files but incomplete object matching, reproductions whose rights are unresolved, and images that cannot currently be delivered by the source. These groups require different follow-up. A missing image does not establish that a reproduction is unavailable, and a discovered image does not establish that it depicts the catalogue’s exact physical object.

The scope follows the catalogue’s existing popularity selection and adds artists associated with Russian and Greek traditions. The original top-100 ranking has 99 currently active, selected painters: the rank-24 entry is explicitly unselected. That editorial choice is preserved. Regional coverage follows recorded cultural affiliations and includes works in collections outside Russia and Greece; it does not infer nationality from birthplace or present-day borders.

The initial audit found 727 painters in the combined scope and 22,481 eligible artwork records without primary images. Of those gaps, 5,671 were classified as paintings. The remainder includes prints, drawings and other existing artwork types. The creation cutoff applies to the work, not the creator’s lifetime. Four separately researched Byzantine icons extend the image work to anonymous and workshop-labelled objects.

## Source findings

Museum records provide the strongest practical starting point when the catalogue already carries a stable object identifier. Image selection can then use the museum’s exact object number and primary-image relationship, followed by source-specific rights checks. This substantially reduces confusion between similar titles, versions of a composition, copies, later impressions and different physical objects in the same series.

The National Gallery of Art supplied the largest group of available images. Its published-image data links a reproduction to a specific object identifier and distinguishes primary views and open-access availability. Its image policy expressly releases eligible digital images under CC0; the catalogue-data licence alone is not the evidence for image reuse. The recommended credit is retained with the selected reproduction.[^nga-policy]

The Met’s public object API distinguishes public-domain works and supplies a primary image when one is available. A positive public-domain flag, an image URL and an exact accession match support selection. An empty image field remains a source gap, while a restrictive rights statement prevents automatic attachment. Neither case is treated as proof that no alternative image exists.[^met-api]

The Art Institute of Chicago exposes useful object, accession and public-domain metadata. Its image endpoint refused access during the selected download batch, so delivery was paused. The evidence-supported candidates remain in the research inventory, with the access failure recorded separately from image rights. Chicago’s image reuse policy and API documentation distinguish freely reusable images from metadata and images with other rights statuses.[^aic-policy][^aic-api]

The Cleveland check returned no eligible open images in its selected cohort. This is a cohort result rather than a statement about the museum’s collection as a whole. Its open-access programme remains a valid source for objects explicitly marked CC0; the current object-level response determines whether an individual image can enter the attachment queue.[^cleveland]

The Finnish National Gallery’s object data includes an individual licence on each multimedia item. Selected records use the explicit CC0 image asset and preserve the supplied photographer credit. An additional pass through the top-painter gaps located reproductions for Van Gogh, Cézanne, Gauguin, Munch and Signac, beyond the Russian-focused candidates found earlier. The source sometimes serves genuine JPEG bytes with an `application/octet-stream` content type; actual image decoding and checksums distinguish that transport detail from a failed image response.[^fng]

Minneapolis requires a current object check as well as a usable image URL. The selected records retain the museum’s current public-domain classification, image-display eligibility and credit line. Earlier research established the current image-delivery paths; legacy image endpoints are not assumed to work. Walters candidates use the exact museum object and its per-image CC0 statement. Rijksmuseum candidates use the museum’s exact object/aggregation identity and public-domain image rights.[^mia][^walters][^rijks]

## Wikimedia identity and rights

Commons is valuable because file pages can connect a reproduction to an artwork’s title, inventory number, institution, creator and source. Those fields are evaluated together. A search result, a familiar composition or a plausible filename is a discovery lead; it is insufficient when several versions or similarly titled works exist. Wikipedia-hosted local fair-use files are outside this reuse workflow.[^commons-reuse]

For records already identified in Wikidata, the work’s current primary image claim is checked against the catalogue’s creator authority and the independent Commons file page. Strong corroboration includes an explicit artwork identifier or exact inventory number. A dedicated Commons category can also resolve a language mismatch when its name is the exact, specific artwork title and the file belongs to that work category. Generic artist or landscape categories do not provide this confirmation.

Public-domain and Creative Commons labels are recorded per file. Credits preserve the photograph’s author where the photograph has its own licence, rather than substituting the depicted painter’s name. The attribution also identifies the artwork, source licence and resizing/compression. Generic life-based public-domain tags with a concrete conflict against the documented creator’s death require further rights review.[^commons-licensing][^commons-credit]

A source’s creation date for the photograph is not the artwork’s creation date. Similarly, a museum photograph taken in a particular year does not establish that the work remains on display. The catalogue’s existing creation dates, attribution wording and holding/display assertions remain unchanged by image attachment.

The Wikimedia image server rate-limited the selected downloads. After a cooldown longer than the server’s requested retry interval, a slower same-origin pass obtained additional images but encountered a further rate limit. Further image requests were then paused. No alternate host or access-bypass route was used. Existing downloaded icon photographs could still be reused after their checksums and current Commons file identities were confirmed.

## Russian painters and regional priorities

The Russian work combined museum sources with accession-led Commons searches. The museum approach is particularly useful for artists whose works are held abroad: the image identity follows the museum object, while the artist’s cultural affiliation remains separate. Examples include Korovin and Bogolyubov in the Finnish source, Jawlensky at Minneapolis, and Stiepevich in Washington.

The new Russian accession pass selected 800 further existing museum records after excluding the earlier accession-search cohorts. It found four exact identities with source-supported image rights: a Nesterov portrait, a Filonov work, and two portraits by Vladimir Makovsky. Exact matching required the museum inventory and title, the museum’s creator authority, and independent Commons accession/museum/creator evidence. Files found by a coincidental inventory-number fragment were not accepted.

Nesterov and Filonov images were downloaded and visually reviewed. The Makovsky candidates remain source-delivery follow-ups. Other successful Russian-associated additions include works by Westchiloff, Sedov, Artsatpanian, Shibanov, Roerich and Kuznetsov. Cultural affiliation is reported from the catalogue; it does not turn an unresolved attribution into a named authorship claim.

## Greek painters and Byzantine icons

The Greek search exposed a useful weakness in simple inventory matching. Several Commons records cite historical museum image URLs with percent-encoded Greek inventory numbers. Decoding the URL for comparison can recover exact object evidence while retaining the original URL as provenance. This supported *Martigues (South France)* by Michael Economou and other exact inventory matches.

The current museum page for *Martigues* identifies inventory Κ.457 and dimensions 38 × 55 cm. The Commons source cites the historical Κ.457 image path and describes the same museum object. The museum’s dating range and creator spelling are preserved; the Commons date and transliteration do not overwrite the catalogue. Ioannis Altamouras’s *Boat on the Shore* is another successful exact-inventory addition.[^martigues-museum][^martigues-commons]

The remaining El Greco records were researched using complete inventory identifiers to distinguish versions. Eight source-supported matches were found, including separate Annunciation versions and works associated with London, the Louvre, the Thyssen collection and Toledo. Only images actually downloaded, visually accepted and attached are counted as additions. *Christ Blessing (The Saviour of the World)* passed those stages; the other candidates remain in the delivery follow-up inventory.

Four Byzantine and Christian Museum objects use photographs by George E. Koronaios with CC BY-SA 4.0 attribution: *The Hospitality of Abraham*, *The Apostles Peter and Paul*, *The Raising of Lazarus* and *Saint Marina*. Their existing anonymous, workshop or stylistic-attribution labels remain intact. The Saint Marina identification retains the earlier comparison between the museum object and independently documented photographs; no new creator or precise creation year is supplied.

Several Greek title matches remain unsuitable for automatic attachment. A Commons Altamouras seascape is explicitly inventory Π.1818, whereas the three remaining similarly titled catalogue works carry different inventory numbers. These are different object identities. Maleas’s *Aswan* and Gyzis’s *Wishbone* require closer comparison of the source image and museum record because the available descriptions differ in date or dimensions. Doxaras’s *Assumption of Mary* remains on hold for its unresolved dating question.

## Reproduction quality and editorial state

All accepted images are authentic source reproductions. Proportional resizing and JPEG compression retain the selected source frame; signatures, paper margins, frames and the full documented composition are not deliberately cropped away. Original prints are commonly monochrome and are evaluated as prints. A poor monochrome archive photograph of a coloured painting is treated separately and can remain a replacement candidate.

The delivered JPEG limit is 100,000 bytes per image. Each accepted derivative is decoded, dimension-checked and visually reviewed in a contact sheet before attachment. Very faint or unsuitable reproductions are held with an individual reason. Contact sheets support composition and obvious-quality review; they do not establish colourimetric accuracy or replace scholarly authentication of the underlying artwork.

The image update changes the primary-media relationship, associated media and rights evidence, and the artwork’s revision/update fields. It does not publish an artwork, amend its creator, supply an unknown date, or convert museum-source provenance into a newly accepted holding assertion. Existing review records remain in their existing editorial state. Distinct catalogue records and museum print impressions are preserved rather than merged by visual similarity.

## Evidence and verification

The application record separates a source candidate from an attached image. A selected metadata record can remain unprepared because of delivery restrictions, fail visual review, or become unnecessary if another catalogue process supplies an image first. The final count is based on committed per-artwork image receipts, not the number of search results, downloaded files or candidate URLs.

Recovery includes a verified local database dump, a successful Cloud SQL backup and exact before-images for the affected records in both catalogues. Attachments check the frozen artwork and creator state again before writing. The source reproduction, licence, credit, metadata evidence and image checksums are recorded with each media asset.

Verification compares all preserved artwork fields and creator links against their before-images, confirms media/rights relationships, checks local image bytes and dimensions, verifies the uploaded object, and requests the delivered production image. These checks establish image attachment and delivery. They do not claim publication of review records or a fresh on-view status for any museum object.

## Follow-up priorities

The most direct remaining opportunities are already identified, rights-supported images whose source delivery is paused. The follow-up inventory retains the exact object and file URLs, rights evidence and failure reason. A later pass should recheck source availability under the provider’s access guidance before requesting those images again.

The next editorial opportunities are exact-object reconciliations, particularly Greek variants with differing dates or dimensions and Commons files whose titles are translated differently from the museum catalogue. Rights-restricted modern works require an explicitly usable reproduction or permission; the pre-1971 artwork cutoff does not itself establish image reuse rights. Unsupported biographies, dates, museum holdings and attribution upgrades are outside image enrichment.

[^nga-policy]: [National Gallery of Art — Terms and Notices, image-specific Open Access Policy](https://www.nga.gov/terms-and-notices); [official object/image data](https://github.com/NationalGalleryOfArt/opendata).
[^met-api]: [The Metropolitan Museum of Art — Collection API](https://metmuseum.github.io/); [Open Access](https://www.metmuseum.org/about-the-met/policies-and-documents/open-access).
[^aic-policy]: [Art Institute of Chicago — Open Access Images](https://www.artic.edu/open-access/open-access-images).
[^aic-api]: [Art Institute of Chicago — API documentation](https://api.artic.edu/docs/).
[^cleveland]: [Cleveland Museum of Art — Open Access](https://www.clevelandart.org/open-access).
[^fng]: [Finnish National Gallery — collection portal and object data](https://kokoelma.kansallisgalleria.fi/). Exact object and multimedia records are linked in the image manifest.
[^mia]: [Minneapolis Institute of Art — official collection metadata](https://github.com/artsmia/collection). Current object/image evidence is retained per candidate.
[^walters]: [Walters Art Museum — official collection](https://art.thewalters.org/). Each attached image retains the exact object page and its image-level CC0 evidence.
[^rijks]: [Rijksmuseum — collection data](https://data.rijksmuseum.nl/). Each selected record retains the exact EDM object and image aggregation.
[^commons-reuse]: [Wikimedia Commons — Reusing content outside Wikimedia](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia).
[^commons-licensing]: [Wikimedia Commons — Licensing](https://commons.wikimedia.org/wiki/Commons:Licensing).
[^commons-credit]: [Wikimedia Commons — Credit line](https://commons.wikimedia.org/wiki/Commons:Credit_line/en); [Creative Commons — Attribution practices](https://wiki.creativecommons.org/wiki/Best_practices_for_attribution).
[^martigues-museum]: [National Gallery of Greece — Martigues (South France)](https://www.nationalgallery.gr/en/artwork/martigues-south-france/).
[^martigues-commons]: [Wikimedia Commons — Martigues, painting by Michalis Oikonomou](https://commons.wikimedia.org/wiki/File:Martigues,_painting_by_Michalis_Oikonomou,_1913.jpg).
