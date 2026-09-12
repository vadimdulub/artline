# Nationalmuseum: popular-artist records and image gaps

## Findings

Ten exact museum notices were examined for Monet, Renoir and Rembrandt. One existing Monet record now has an evidence-backed creation year of **1882**. No new artworks or images were added. Six additional object leads remain outside this import pending date review; these include paintings, a drawing and a print, not six interchangeable paintings.

Nationalmuseum's [image guide](https://www.nationalmuseum.se/en/explore-art-and-design/images) directs users to its catalogue, media portal and museum-provided Commons images. Its [media-portal announcement](https://www.nationalmuseum.se/om-nationalmuseum/nyheter/nationalmuseum-tillg%C3%A4ngligg%C3%B6r-bildskatt-genom-ny-mediaportal), published 1 July 2025, says assets carry their own licences. The notices confirm that photographs of the **same artwork** can have different licences. Neither public-domain artwork age nor the first visible image is sufficient to clear every reproduction.

Three direct image links returned HTTP 403 in one retrieval batch. Further image requests were paused. This is an access limitation, not a finding that the images lack permission. No images were obtained from alternate hosts or mirrors. [Recorded access results](../../../output/popular-nationalmuseum-followup/image-access.json).

## Existing records reviewed

| Artist | Exact museum record | Date finding | Local outcome |
|---|---|---|---|
| Claude Monet | [View over the Sea, NM 2122 / object 19182](https://collection.nationalmuseum.se/en/collection/item/19182/) | Signature says 1882; separate museum description explicitly says the painting was made at Pourville in 1882. | Creation interval changed from unknown to 1882–1882, exact. Signature display and existing editorial description preserved. New source citation and audit history stored. No image added. |
| Pierre-Auguste Renoir | [La Grenouillère, NM 2425 / object 19486](https://collection.nationalmuseum.se/en/collection/item/19486/) | Museum labels the work made in 1869. | Existing identity and date confirmed for this source check. Image access blocked. |
| Rembrandt van Rijn | [Self-Portrait, NM 5324 / object 22374](https://collection.nationalmuseum.se/en/collection/item/22374/) | Signature and museum narrative support 1630. | Existing record retained. Image access blocked. |
| Rembrandt van Rijn | [The Kitchen Maid, NM 584 / object 17587](https://collection.nationalmuseum.se/en/collection/item/17587/) | Museum labels the work made in 1651. | Existing record retained, including its unquoted local title. Image access blocked. |

The Monet evidence is present in the bilingual descriptive field `ObjDescriptionTxt_sv` inside the English page's embedded catalogue data. It is not simply a translated guess from the signature, an acquisition date, or a date inferred from the artist's lifespan. The complete source response is preserved with a checksum; only a concise factual evidence note was added to the database, not the museum's full authored description.

The old description's signature-only caution remains as editorial history. The new field-level citation explains why creation dating is now resolved. Further editing could reconcile that prose, but it was not silently replaced in this targeted update.

## Additional museum leads, not imported

| Artist | Artwork and museum accession | Source facts | Remaining requirement |
|---|---|---|---|
| Claude Monet | [View from Voorzan, NM 2513 / object 19574](https://collection.nationalmuseum.se/en/collection/item/19574/) | Oil on canvas; 34 × 73 cm. The notice links Wikidata Q18574592. | Museum creation-date fields are blank. Donation in 1926 is not a creation date. Retain as a lead until a catalogue or other reliable object-specific source resolves dating. |
| Pierre-Auguste Renoir | [Mother Antony's Tavern, NM 2544 / object 19605](https://collection.nationalmuseum.se/en/collection/item/19605/) | Oil on canvas; 194 × 131 cm; museum date field says signed 1866. | Independent creation-date confirmation before import. A signature is not automatically a creation date. |
| Pierre-Auguste Renoir | [Bathing Women, NM 2103 / object 19163](https://collection.nationalmuseum.se/en/collection/item/19163/) | Oil on canvas; 40.5 × 51 cm. | Creation-date fields blank. Purchase in 1918 must not become its creation year. |
| Pierre-Auguste Renoir | [Conversation, NM 2079 / object 19139](https://collection.nationalmuseum.se/en/collection/item/19139/) | Oil on canvas; 45 × 38 cm. | Creation-date fields blank; no year inferred from acquisition. |
| Pierre-Auguste Renoir | [Enfant jouant à la balle, NMG 351/1956 / object 90551](https://collection.nationalmuseum.se/en/collection/item/90551/) | Lithograph on paper, catalogued as an original print. | Creation dating and edition/impression identity; accession suffix 1956 is not a creation date. Not a painting. |
| Pierre-Auguste Renoir | [Landskap i Provence, NMH 68/1949 / object 32867](https://collection.nationalmuseum.se/en/collection/item/32867/) | Watercolour on paper, catalogued among free-hand drawings; 30.9 × 43.7 cm. | Creation dating; accession suffix 1949 is not a creation date. Preserve drawing/medium distinction. |

Monet's [museum artist page](https://collection.nationalmuseum.se/en/artists/artist/7713/) lists two related objects; both notices were checked. Renoir's [artist page](https://collection.nationalmuseum.se/en/artists/artist/7617/) reports eight related objects, but only six object links were visible in the retrieved page. Those six notices were checked; the other two remain a discovery gap. This is not an exhaustive museum or oeuvre review. Rembrandt's wider museum holdings were not enumerated in this pass.

## Images, licensing and display

For Renoir object 19486, media 174191 is labelled Public Domain, whereas media 746031 carries CC BY-SA 4.0. The default image therefore cannot inherit another photograph's Public Domain label. The captured metadata retains each media identifier, URL, photographer credit and licence independently.

The catalogue reported the two Rembrandts on display and the Monet/Renoir objects not on display when retrieved on 11 September 2026. No display assertion was added or changed in the app. These are dated source observations, not evergreen promises. An exhibition page showing a Monet held elsewhere would likewise not establish permanent Nationalmuseum ownership.

No museum-highlight or owner-favourite flags changed. A museum's qualitative description of a work does not cause this image/date maintenance pass to edit curation lists.

## Verification and current inventory

- [Current popular-artists checklist](inventory-v5/PAINTERS.md): 100 artists, 22,232 distinct works and 383 pictures. Monet remains at 298 works and 30 pictures; one existing work now has a usable timeline year.
- Whole catalogue totals remain 5,328 artists, 106,195 artworks and 581 pictures. Zero new images or artwork records in this pass.
- [Date preview](../../../output/popular-nationalmuseum-followup/date-preview.json), [applied change](../../../output/popular-nationalmuseum-followup/date-apply.json), [no-op replay](../../../output/popular-nationalmuseum-followup/date-replay.json), [preservation, citation, audit and API checks](../../../output/popular-nationalmuseum-followup/verification.json).
- All 106,194 other artwork records were unchanged. Artists, attributions, holdings, media and curation lists were preserved. The record remains in review; public unauthenticated access remains unavailable.
- Source capture: [object 19182 HTML](../../../content/imports/popular-nationalmuseum-20260911/19182.html), SHA-256 `901099fe2967569ff0878c6884a5c63f457ca39116aae4fc067a07afa09f1207`. The other nine captures and all URL/time/checksum sidecars are in the same directory.
- Pre-write PostgreSQL backup: `/Users/vadimdulub/Documents/artline-nationalmuseum-backup-20260911.Win8KS/before-nationalmuseum.dump`, SHA-256 `05c27f52e1b35c4f6d8b7e0b8477efd0c7115fe409eec050b559e8c72dcc3e7c`.

No commits, publishing, deployment or Terraform changes. No painter or research round is marked complete.

## Sources and next research

Primary sources are the ten exact museum notices and two artist pages linked above, plus Nationalmuseum's image guide and dated media-portal announcement. The notices were captured on 11 September 2026. Artist-page renderings can lag the live catalogue; the reported eight/six Renoir difference is left explicit.

Next work should resolve the six date/edition leads through museum catalogues, finish Renoir's two unexposed related-object links, and investigate other European institutions independently. Image access to this source remains paused. Do not substitute similar Monet or Renoir paintings from other museums for these exact objects.
