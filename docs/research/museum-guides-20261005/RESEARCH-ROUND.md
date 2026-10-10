# Museum research and picture links — 5–6 October 2026

[Open the museum index](README.md)

The files cover **1,219 holding institutions**: 1,190 museums, 18 historic sites and 11 foundations. They list **257,270 existing artworks with accepted museum or institutional holding links**, with a separate file for each institution and pages of at most 500 artworks for large collections. These are catalogue holdings; they do not confirm present display or physical presence.

## New museum research

This round saved and verified **2,022 new accepted holding links in both the local and production databases**, plus **90 additional holding candidates in review** in each database. It created no artworks, changed no creator or creation-date fields, published no records, and attached no images.

| Research | Accepted links in each database | Additional review records in each database | Evidence |
| --- | ---: | ---: | --- |
| Tate | 1,509 | 90 | Current public catalogue responses for 1,600 selected accessions; exact historical accession crosswalk, titles, creators, collection and accession status checked. One accession returned no current object. |
| French deposit recipients | 205 | 0 | Exact conservation place and receiving museum, reconciled against the official museum register and deposit-field specification. Includes 68 Musée de l’Armée records. Legal ownership is preserved separately. |
| Museo Nacional de Colombia | 308 | 0 | Unique title/creator/date matches with explicit current museum and inventory fields. The museum's technical-metadata research flag and Artline editorial review remain intact. |

The French interpretation follows the [Ministry of Culture’s Joconde field specification](https://www.culture.gouv.fr/de/content/download/271211/pdf_file/specifications_export_%20Joconde_20231218.pdf?inLanguage=fre-FR&version=35), especially the distinction between conservation place, deposit recipient and legal owner. Colombia’s [catalogue policy](https://colecciones.museonacional.gov.co/) explains that its current collection-management records can contain historical technical metadata still under investigation. This does not authorize changing an artwork’s attribution, dates or publication status.

The final read-only checks on 6 October found **41,110 local artworks and 41,109 production artworks without an accepted museum link**. The one-record difference predates this round; all 2,112 research claims from this round match across the databases. Unresolved matches were not assigned a museum merely to reduce these numbers.

## Picture links

| Link type | Artworks |
| --- | ---: |
| Existing Artline picture | 84,797 |
| Direct image identified by a museum catalogue | 27,485 |
| Commons depiction candidate requiring identity review | 589 |
| Catalogue page explicitly reporting an image, without a verified direct image URL | 30,596 |
| Catalogue reports no image | 8,165 |
| Further image research needed | 105,638 |

The export therefore adds **58,670 external image-source associations** alongside the existing Artline picture links. These are links and research evidence, not new image attachments. No image binaries were downloaded by this round. A museum's image-clearance flag or an available image URL is not treated as an Artline reuse licence; source credits and recorded rights are preserved.

Five pre-existing asset references were excluded from the picture links after their local files were found missing and their production URLs returned 404. Three other assets missing locally returned valid image responses in production and remain linked. The database asset records were left intact. See the [individual header checks](missing-local-assets-live-check.json).

Highlights include:

- [Louvre](museums/musee-du-louvre.md): 3,286 artworks; 33 existing pictures, 555 direct museum image links and 2,544 catalogue image pages.
- [Prado](museums/museo-del-prado.md): 548 artworks; 183 existing pictures and 265 Commons image candidates.
- [Tate](museums/tate.md): 3,717 artworks; 270 existing pictures and 1,459 direct museum image links.
- [Russian Museum](museums/state-russian-museum.md): 8,055 artworks; 941 existing pictures and 5,276 direct museum image links.

Source dates matter. Tate responses and Commons file metadata were fetched on 5–6 October. The image pass also reused checksum-verified official metadata captured earlier: Louvre, Joconde and NGA captures from 4–5 October, and Russian Museum collection-listing captures from September. Some Prado holding evidence comes from the March 2026 catalogue dataset documented in the previous research round. A retrieval date is not a new physical-location observation or the publication date of an underlying catalogue.

The export includes all accepted holdings in the snapshot, including previously researched records. It does not claim that all 257,270 holdings were newly investigated in this round. External URLs were not all live-tested; the validation report records the exact checks performed.

## Database delivery

**Local and production delivery are complete and verified.** Production received all **2,022 accepted holding links, 90 review assertions and 2,112 supporting citations**. Tate's fresh production preflight held no records. The guarded writer verified each batch against its saved preimages and preserved existing artwork fields, creator relationships, publication status and images.

The [production delivery receipt](production-delivery.json) records completion. A subsequent [read-only comparison](production-final-verification.json) checked all 2,112 assertions and citations in each database, confirmed identical researched artwork identities, museum associations, review states, source object IDs, source URLs and response hashes, and found no new display claims. Matching normalized claim hashes are recorded for both databases.

| Batch | Local result | Production result |
| --- | --- | --- |
| French and Colombian batch | [513 accepted links verified](../artwork-locations-20261004/delivery/museum-guides-deposits-colombia-01/verification.json) | 513 accepted links verified in the same receipt |
| Tate batch | [1,509 accepted and 90 review records verified](../artwork-locations-20261004/delivery/museum-guides-tate-01/verification.json) | [1,509 accepted and 90 review records verified](../artwork-locations-20261004/delivery/museum-guides-tate-production-01/verification.json) |

Recovery preimages and plan pins are preserved under `/Users/vadimdulub/Library/Application Support/Artline/backups/artwork-locations-20261004/`. Database delivery evidence is under `../artwork-locations-20261004/delivery/`.

Two additional accepted artworks and 11 changes to existing primary-image links appeared during the snapshot interval from separate operations. They were preserved and included in the catalogue export, but are **not counted as this round’s museum or image deliveries**. See [the comparison](concurrent-catalogue-changes.json).

The museum guides retain their documented export snapshot. Later catalogue image changes from separate operations are reflected in the final database counts, not retroactively counted as image links delivered by this round. The original report state is preserved under `revisions/before-production-delivery/`.

## Verification and evidence

- [Guide manifest and file hashes](guide-manifest.json)
- [Validation results](verification.json)
- [Eleven identity, custody and broken-link decision checks](decision-test-results.json)
- [Representative external image URL header checks](external-image-sample-head-checks.json)
- [Consistent final database snapshot](snapshots/final/manifest.json)
- [Representative query plans](snapshots/final/query-plans.json)
- [Final local coverage counts](local-final-counts.json)
- [Artwork-to-image source associations](artwork-image-source-associations.json.gz)
- [Museum image-source index](image-sources-extended.json.gz)
- [Commons candidate evidence](commons-image-candidates.json.gz)

The export uses read-only, repeatable-read queries, scoped to an institution and bounded to 500 artworks per page. It uses indexed artwork, creator and media lookups. The representative plans use the real catalogue; they are not a claim of tested performance at ten million artworks. No test database or catalogue fixtures were created.

Validation reconciled all 257,270 artwork rows to the snapshot, checked 3,804 internal document links, and verified 9,531 distinct source-response hashes covering 778,687,744 uncompressed bytes. Seven sampled existing Artline image URLs and eight sampled external image URLs returned HTTP 200. The checks used HTTP headers without downloading image bodies; they do not establish that every external URL will remain available.
