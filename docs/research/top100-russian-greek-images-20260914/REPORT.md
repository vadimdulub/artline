# Artwork image coverage and source research

## Verified additions

**1,055 existing artwork records received images in both the local and production catalogues.** These additions cover 53 named painters and 4 separately tracked Byzantine icons. Every counted addition passed database, image-byte and production HTTP verification.

The additions comprise 115 paintings, 932 prints, seven watercolours and one drawing, using the catalogue’s existing classifications.

| Measure | Result |
|---|---:|
| Distinct artworks assessed for image sources | 3,757 |
| Distinct source-supported candidates | 1,284 |
| Images attached and verified in both catalogues | 1,055 |
| Top-100 painters receiving additions | 39 of 99 active selected painters |
| Images for the active top-100 group | 1,034 |
| Images for Russian-associated painters | 15 |
| Images for Greek-associated painters | 3 |
| Additional Byzantine icon photographs | 4 |
| Delivered JPEG bytes | 94,988,949 |
| Largest delivered JPEG | 99,993 bytes |
| Source-supported candidates not attached | 229 |

The geographic and popularity groups overlap; their image counts must not be added together. Counts describe artwork records and distinct museum impressions, rather than a deduplicated count of compositions. All 1,055 works retain their existing review status.

| Image source | Verified additions |
|---|---:|
| National Gallery of Art | 823 |
| The Met | 110 |
| Minneapolis Institute of Art | 51 |
| Walters Art Museum | 20 |
| Finnish National Gallery | 20 |
| Rijksmuseum | 15 |
| Wikimedia Commons | 15 |
| Smithsonian American Art Museum | 1 |

Files: [per-image sources, licences and checksums](image-manifest.json), [follow-up candidates](follow-up-candidates.json), [per-painter before/after data](artists-after.json), [verification summary](summary.json).


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

## Russian and Greek painter results

| Painter | Recorded priority affiliation | Added images |
|---|---|---:|
| Alexej von Jawlensky | RU | 1 |
| Alexey Bogolyubov | RU | 3 |
| Constantin Westchiloff | RU | 2 |
| El Greco | GR | 1 |
| Grigory Sedov | RU | 1 |
| Hmayak Artsatpanian | RU | 1 |
| Ioannis Altamouras | GR | 1 |
| Konstantin Korovin | RU | 1 |
| Michael Economou | GR | 1 |
| Mikhail Nesterov | RU | 1 |
| Mikhail Shibanov | RU | 1 |
| Nicholas Roerich | RU | 1 |
| Nikolai Dmitriyevich Kuznetsov | RU | 1 |
| Pavel Filonov | RU | 1 |
| Vincent G. Stiepevich | RU | 1 |

## Reproduction quality and editorial state

All accepted images are authentic source reproductions. Proportional resizing and JPEG compression retain the selected source frame; signatures, paper margins, frames and the full documented composition are not deliberately cropped away. Original prints are commonly monochrome and are evaluated as prints. A poor monochrome archive photograph of a coloured painting is treated separately and can remain a replacement candidate.

The delivered JPEG limit is 100,000 bytes per image. Each accepted derivative is decoded, dimension-checked and visually reviewed in a contact sheet before attachment. Very faint or unsuitable reproductions are held with an individual reason. Contact sheets support composition and obvious-quality review; they do not establish colourimetric accuracy or replace scholarly authentication of the underlying artwork.

The image update changes the primary-media relationship, associated media and rights evidence, and the artwork’s revision/update fields. It does not publish an artwork, amend its creator, supply an unknown date, or convert museum-source provenance into a newly accepted holding assertion. Existing review records remain in their existing editorial state. Distinct catalogue records and museum print impressions are preserved rather than merged by visual similarity.

## Evidence and verification

The application record separates a source candidate from an attached image. A selected metadata record can remain unprepared because of delivery restrictions, fail visual review, or become unnecessary if another catalogue process supplies an image first. The final count is based on committed per-artwork image receipts, not the number of search results, downloaded files or candidate URLs.

Recovery includes a verified local database dump, a successful Cloud SQL backup and exact before-images for the affected records in both catalogues. Attachments check the frozen artwork and creator state again before writing. The source reproduction, licence, credit, metadata evidence and image checksums are recorded with each media asset.

Verification compares all preserved artwork fields and creator links against their before-images, confirms media/rights relationships, checks local image bytes and dimensions, verifies the uploaded object, and requests the delivered production image. These checks establish image attachment and delivery. They do not claim publication of review records or a fresh on-view status for any museum object.

## Follow-up priorities

Of the 229 source-supported candidates not attached, 223 await source access and six remain on visual-quality or editorial hold. Chicago accounts for 201 access-paused candidates and Wikimedia for 22.

The most direct remaining opportunities are already identified, rights-supported images whose source delivery is paused. The follow-up inventory retains the exact object and file URLs, rights evidence and failure reason. A later pass should recheck source availability under the provider’s access guidance before requesting those images again.

The next editorial opportunities are exact-object reconciliations, particularly Greek variants with differing dates or dimensions and Commons files whose titles are translated differently from the museum catalogue. Rights-restricted modern works require an explicitly usable reproduction or permission; the pre-1971 artwork cutoff does not itself establish image reuse rights. Unsupported biographies, dates, museum holdings and attribution upgrades are outside image enrichment.

## Top-100 painter coverage

The table reports this session’s additions separately from the final catalogue gap count. Other catalogue work can change overall coverage concurrently. The full 727-painter inventory is retained in `artists-after.json`. Rank 24 is explicitly unselected and is not silently reinstated.

| Rank | Painter | Eligible image gaps before | Images added here | Eligible gaps after |
|---:|---|---:|---:|---:|
| 1 | Leonardo da Vinci | 2 | 0 | 2 |
| 2 | Michelangelo | 2 | 0 | 2 |
| 3 | Vincent van Gogh | 38 | 8 | 30 |
| 4 | Pablo Picasso | 3,415 | 0 | 3,415 |
| 5 | Raphael | 20 | 0 | 20 |
| 6 | Rembrandt van Rijn | 58 | 2 | 56 |
| 7 | Salvador Dalí | 44 | 0 | 44 |
| 8 | Albrecht Dürer | 73 | 2 | 71 |
| 9 | Frida Kahlo | 3 | 0 | 3 |
| 10 | Claude Monet | 298 | 4 | 294 |
| 11 | Peter Paul Rubens | 67 | 1 | 66 |
| 12 | Caravaggio | 15 | 0 | 15 |
| 13 | Francisco Goya | 26 | 1 | 25 |
| 14 | Johannes Vermeer | 10 | 0 | 10 |
| 15 | Sandro Botticelli | 12 | 0 | 12 |
| 16 | Edvard Munch | 116 | 2 | 114 |
| 17 | Diego Velázquez | 9 | 0 | 9 |
| 18 | Henri Matisse | 789 | 4 | 785 |
| 19 | Pierre-Auguste Renoir | 105 | 26 | 79 |
| 20 | Jean-Auguste-Dominique Ingres | 3,263 | 0 | 3,263 |
| 21 | Paul Cézanne | 83 | 12 | 71 |
| 22 | Paul Gauguin | 234 | 47 | 187 |
| 23 | Giotto di Bondone | 1 | 0 | 1 |
| 25 | Titian | 13 | 0 | 13 |
| 26 | Gustav Klimt | 5 | 0 | 5 |
| 27 | El Greco | 15 | 1 | 14 |
| 28 | Wassily Kandinsky | 100 | 0 | 100 |
| 29 | Piet Mondrian | 30 | 3 | 27 |
| 30 | Édouard Manet | 82 | 38 | 44 |
| 31 | Eugène Delacroix | 266 | 6 | 260 |
| 32 | Hieronymus Bosch | 15 | 0 | 15 |
| 33 | Pieter Bruegel the Elder | 1 | 0 | 1 |
| 34 | Amedeo Modigliani | 32 | 1 | 31 |
| 35 | Joan Miró | 118 | 0 | 118 |
| 36 | Marc Chagall | 688 | 0 | 688 |
| 37 | Jan van Eyck | 6 | 0 | 6 |
| 38 | Edgar Degas | 78 | 33 | 45 |
| 39 | Masaccio | 1 | 0 | 1 |
| 40 | Jacques-Louis David | 54 | 0 | 54 |
| 41 | Tintoretto | 7 | 0 | 7 |
| 42 | Gustave Courbet | 139 | 8 | 131 |
| 43 | Alphonse Mucha | 16 | 0 | 16 |
| 44 | Paolo Veronese | 16 | 0 | 16 |
| 45 | Nicolas Poussin | 71 | 0 | 71 |
| 46 | Giuseppe Arcimboldo | 1 | 0 | 1 |
| 47 | Henri de Toulouse-Lautrec | 580 | 218 | 362 |
| 48 | Caspar David Friedrich | 3 | 0 | 3 |
| 49 | Anthony van Dyck | 47 | 4 | 43 |
| 50 | Andrea del Verrocchio | 0 | 0 | 0 |
| 51 | Fra Angelico | 1 | 0 | 1 |
| 52 | Paul Klee | 180 | 16 | 164 |
| 53 | René Magritte | 34 | 0 | 34 |
| 54 | Artemisia Gentileschi | 1 | 0 | 1 |
| 55 | Georges Braque | 204 | 0 | 204 |
| 56 | Camille Pissarro | 103 | 43 | 60 |
| 57 | Jean-Antoine Watteau | 20 | 1 | 19 |
| 58 | Giorgione | 2 | 0 | 2 |
| 59 | Giovanni Bellini | 5 | 0 | 5 |
| 60 | Egon Schiele | 15 | 10 | 5 |
| 61 | Domenico Ghirlandaio | 2 | 0 | 2 |
| 62 | Diego Rivera | 55 | 0 | 55 |
| 63 | Kazimir Malevich | 56 | 0 | 56 |
| 64 | Jean-François Millet | 118 | 8 | 110 |
| 65 | Piero della Francesca | 3 | 0 | 3 |
| 66 | J. M. W. Turner | 181 | 1 | 180 |
| 67 | Andrea Mantegna | 11 | 0 | 11 |
| 68 | Lucas Cranach the Elder | 8 | 0 | 8 |
| 69 | Théodore Géricault | 74 | 2 | 72 |
| 70 | Francisco de Zurbarán | 13 | 1 | 12 |
| 71 | Ilya Repin | 116 | 0 | 116 |
| 72 | Frans Hals | 13 | 0 | 13 |
| 73 | Bartolomé Esteban Murillo | 10 | 0 | 10 |
| 74 | Henri Rousseau | 13 | 0 | 13 |
| 75 | Pietro Perugino | 5 | 0 | 5 |
| 76 | Rogier van der Weyden | 1 | 0 | 1 |
| 77 | Alfred Sisley | 82 | 7 | 75 |
| 78 | Gustave Doré | 338 | 2 | 336 |
| 79 | Bob Ross | 0 | 0 | 0 |
| 80 | Jackson Pollock | 112 | 0 | 112 |
| 81 | James Abbott McNeill Whistler | 841 | 228 | 613 |
| 82 | Jean-Baptiste-Camille Corot | 231 | 77 | 154 |
| 83 | Georges Seurat | 26 | 0 | 26 |
| 84 | Berthe Morisot | 93 | 2 | 91 |
| 85 | Canaletto | 19 | 0 | 19 |
| 86 | Bronzino | 5 | 0 | 5 |
| 87 | Max Ernst | 59 | 0 | 59 |
| 88 | Giovanni Battista Tiepolo | 38 | 4 | 34 |
| 89 | François Boucher | 114 | 5 | 109 |
| 90 | Duccio | 0 | 0 | 0 |
| 91 | Jean-Honoré Fragonard | 69 | 1 | 68 |
| 92 | Cimabue | 1 | 0 | 1 |
| 93 | Élisabeth Vigée Le Brun | 39 | 1 | 38 |
| 94 | Oskar Kokoschka | 59 | 0 | 59 |
| 95 | Honoré Daumier | 1,237 | 190 | 1,047 |
| 96 | Paolo Uccello | 2 | 0 | 2 |
| 97 | Vittore Carpaccio | 0 | 0 | 0 |
| 98 | Paul Signac | 106 | 14 | 92 |
| 99 | Sofonisba Anguissola | 4 | 0 | 4 |
| 100 | Claude Lorrain | 57 | 0 | 57 |

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
