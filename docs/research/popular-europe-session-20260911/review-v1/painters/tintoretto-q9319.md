# Tintoretto — source review

Artist ID `0200b9bd-c767-4173-904d-2ac416328cca`; authority `Q9319`. Local snapshot: 11 artwork links, 3 images.

- [x] Inventory and existing source queue inspected by the backend.
- [ ] Cross-museum research complete.
- [ ] Every image gap resolved.

## National Gallery, London

Structured source: [official API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api), [metadata and separate image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). One bounded current-name/explicit-alias query; not a complete oeuvre search. The 102 selected objects passed pinned importer, preservation, idempotency and API checks. Other entries below are automated source-specific screening decisions, not individual curatorial approval.

- [Portrait of Vincenzo Morosini](https://www.nationalgallery.org.uk/data/0EQY-0001-0000-0000): ADDED, verified review record `ec93bd21-8967-4c2c-8016-814d9c5bd982`; no image in this batch.
- [Portrait of a Gentleman](https://www.nationalgallery.org.uk/data/0F1Q-0001-0000-0000): multiple or missing creators.
- [Saint George and the Dragon](https://www.nationalgallery.org.uk/data/0F75-0001-0000-0000): ADDED, verified review record `97864c40-061a-4a59-a050-5d2bb116afcb`; no image in this batch.
- [The Origin of the Milky Way](https://www.nationalgallery.org.uk/data/0FHI-0001-0000-0000): ADDED, verified review record `735d953e-89c7-4e1e-8efc-c4f0bbc42fb4`; no image in this batch.
- [Jupiter and Semele](https://www.nationalgallery.org.uk/data/0FRC-0001-0000-0000): multiple or missing creators.
- [Christ washing the Feet of the Disciples](https://www.nationalgallery.org.uk/data/0FS2-0001-0000-0000): ADDED, verified review record `4ae9c806-a245-410b-8700-374697c113a3`; no image in this batch.
- [The Miracle of Saint Mark](https://www.nationalgallery.org.uk/data/0GAO-0001-0000-0000): qualified or non-exact source creator.
- [Portrait of a Woman (perhaps Pellegrina Morosini Capello)](https://www.nationalgallery.org.uk/data/0GER-0001-0000-0000): multiple or missing creators.
- [The Nativity](https://www.nationalgallery.org.uk/data/0GJI-0001-0000-0000): multiple or missing creators.

## Selected image outcomes

No image added for this painter in the current European five-image batch. Existing images were preserved; missing permission is not a completed image review.

## Next

### Caen follow-up, 11 September 2026

- [x] Added and verified [La Descente de Croix, inv. 17](https://pop.culture.gouv.fr/notice/joconde/06570007713). [Museum notice](https://mba.caen.fr/oeuvre/la-descente-de-croix) identifies Jacopo Robusti / Le Tintoret and dates the work 1556–1558. The two names are source aliases, not two collaborators. National dataset and exact date source retained.
- [ ] *La Cène*, 1566, accession `16 ; Musées impériaux 499 MR (Ancien numéro)`: reconcile inventory aliases globally before import.
- [ ] School/after-Tintoretto records must remain qualified; no automatic autograph assignment. Caen images remain deferred.

Review existing European museum source links and unresolved exact dates/attributions; test documented alternate names only where the current query has a known gap. Search at least one different museum before regarding this source pass as representative. Do not retry inherited blocked image hosts or infer current display, ownership, or masterpiece status.
