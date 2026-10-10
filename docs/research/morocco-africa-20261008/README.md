# Morocco and Africa museum expansion — 8 October 2026

The initial pass was applied to the real **local** `artline` catalogue in response to “find all museums in marocco add more artworks for them then try to cover museums in affrica”. That initial pass did not write to production. The subsequent user-authorized production publication is recorded below.

**108 institutions and 97 artworks added; one existing artwork received a verified holding.** The pass covers 109 institutions across 12 African countries, including the existing South African National Gallery. All new institutions and artworks remain in review. Museum existence, collection ownership, building/venue identity and current display are separate claims.

| Country | Institutions covered | New institutions | New artworks | Existing artworks linked |
|---|---:|---:|---:|---:|
| Morocco | 45 | 45 | 63 | 0 |
| Nigeria | 43 | 43 | 10 | 0 |
| South Africa | 2 | 1 | 7 | 1 |
| Egypt | 2 | 2 | 12 | 0 |
| Kenya | 1 | 1 | 5 | 0 |
| Tanzania | 7 | 7 | 0 | 0 |
| Algeria | 4 | 4 | 0 | 0 |
| Benin | 1 | 1 | 0 | 0 |
| Namibia | 1 | 1 | 0 | 0 |
| Rwanda | 1 | 1 | 0 | 0 |
| Tunisia | 1 | 1 | 0 | 0 |
| Zimbabwe | 1 | 1 | 0 | 0 |
| **Total** | **109** | **108** | **97** | **1** |

## Production publication — 8 October 2026

After the initial local pass, the user explicitly instructed “no no, skip review phase deploy them to prod”. Production already contained the complete source-pinned batch, including two records reconciled to existing WikiArt objects. The publication transaction reused those identities: **98 artworks, 109 institutions and two venues are now published**. No duplicate artworks were inserted by this publication operation.

- Full compare-and-swap checks pinned all scoped production rows and their artwork/creator links, media, citations, external identifiers and location assertions before any write. The shared ingestion advisory lock and row locks prevented concurrent changes during publication.
- Two already-reconciled Mahmoud Said works retained their established WikiArt dates: *The Artist’s Mother* (1921) and *My Friend in the Mixed Courts* (1923). Their previously unknown work types were set to painting using explicit official oil-on-canvas captions. Other artwork metadata was unchanged.
- Visual comparison confirmed the mother portrait’s identity. The official catalogue gives 88 × 70 cm, while the existing WikiArt record gives 73 × 52 cm. The existing value and both source records were preserved; no frame-size explanation was invented. The friend portrait’s distinctive title/creator and 81 × 65 cm dimensions agree.
- **83 artworks retain eligible creation-scope classification; 15 retain unknown dates and the backend’s review classification for chronology.** The user authorized their publication without inventing dates. Publication status and chronology classification remain separate.
- Production’s existing anonymous website configuration exposes the broader catalogue. That access configuration was preserved. Strict `preview=0` API results still follow existing creator-publication and creation-scope policies; unrelated artist profiles were not published in this batch.
- All source evidence, attribution qualifications, images, rights labels, holdings and display assertions were verified unchanged. Publication does not imply current display. No artworks or institutions were deleted.

The durable transaction receipt is [production-publication-receipt.json](production-publication-receipt.json). `publication-preflight.json.gz` records the full preimages and identity mapping. Private pre/post backups are under the existing Artline backup directory. The bounded publication script is `ops/morocco-africa-publish-20261008.py`; it refuses replay after the successful receipt exists.

## Morocco coverage and remaining gaps

The 45 Moroccan institutions comprise **44 museums and one foundation collection**, with two additional Villa des Arts venue records (Casablanca and Rabat). All **22 museums in the captured official FNM directory** are included. Private, university, bank and other museum sources extend that directory; its 22 entries are not treated as all museums in Morocco.

Sources include the [FNM directory](https://www.fnm.ma/museums/), [Al Mada foundation](https://www.fondationalmada.ma/en/nos-initiatives/art-et-culture/villa-des-arts), [Villas des Arts object catalogue](https://www.villadesarts.ma/composition-70), [Tangier American Legation](https://www.legation.org/cultural-center), [Farid Belkahia permanent collection](https://www.museefaridbelkahia.com/collection-permanente), official tourism pages and the [Institut français museum-night brochure](https://if-maroc.org/wp-content/uploads/2023/06/Brochure-2eme-edition-de-la-NMEC-2023.pdf). The older brochure establishes historical identities and addresses, not present opening hours or exhibitions.

The 63 Moroccan artwork additions are:

- **55** individually numbered Al Mada collection works, including Cherkaoui, Gharbaoui, Labied, Morère and other named creators. Execution years come from individual object records, not inventory-number patterns. Selection was bounded to reviewed examples; this is not an exhaustive collection import.
- **3** MMVI–FNM works from the rendered *Horizon(s) en mouvement* collection captions: Ben Ali ’Rbati, Haj Abdelkrim Ouazzani and Mohamed Sarghini.
- **3** Legation works: McBey’s *Zohra* and *The Storyteller*, and Ben Ali R’bati’s *Magistrat au prétoire*.
- **2** Farid Belkahia works titled *Couple*, distinguished by dates, supports and dimensions (1952 and 1962).

The two Villas des Arts share a foundation collection. None of those 55 artworks is assigned to a particular branch or claimed to be currently displayed. Tiskiwin/Bert Flint and Mouassine/Music Museum aliases are consolidated. Bank Al-Maghrib’s closure notice is retained. The Women’s Museum record documents historical identity; later closure reports require operational-status follow-up.

**This is not a claim that every Moroccan museum has been verified or supplied with artworks.** The [Morocco discovery register](morocco-discovery-register.csv) retains all 91 nonblank entries from the captured French secondary list: 35 matched institution labels, one foundation venue, and 55 unresolved or qualified leads. These include historical aliases, reported closed/planned venues, galleries, uncertain identities and a Laâyoune territorial-location case. The secondary list’s stale opening/status labels were not imported as current facts. The primary-source catalogue also includes institutions absent from that list.

## Wider Africa pass

Museum directories are grounded in the [Nigerian NCMM register](https://museum.ng/museums/), [Tanzanian national museum network](https://www.nmt.go.tz/historical-centers/all-museum-centers), Algeria’s Ministry of Culture register and individual museum/operator sources. Nigeria’s directory counts museums and other outlets together; this pass selected 42 distinct museum entries, consolidated repeated headings and the Yola/Fombina alias, and added the Yemisi Shyllon museum separately. Postal addresses resolved Kanta/Argungu and other city-label discrepancies.

Artwork sources are institution-supplied Google Arts & Culture records for [Yemisi Shyllon](https://artsandculture.google.com/partner/yemisi-shyllon-museum-of-art), [Iziko](https://artsandculture.google.com/partner/south-african-national-gallery) and [National Museums of Kenya](https://artsandculture.google.com/partner/national-museums-of-kenya), plus the Egyptian Ministry of Culture’s [Mahmoud Said catalogue](https://www.fineart.gov.eg/AllPics/Catalogs/PDF/376/Mahmoud-Said.pdf). Kenyan archive objects are assigned to the national collection, without inventing a branch holding. Egyptian holding credits refer to the lending Mahmoud Said Museum in Alexandria, not the exhibition venue.

The [54-country coverage tracker](africa-coverage.csv) makes incomplete coverage explicit. Twelve countries have catalogue additions; six additional country-source attempts failed or were unavailable, and the remaining countries still need a primary-source pass. The tracker uses the 54 UN-member African countries and is not an exhaustive inventory of African territories or their museums. No complete continent-wide coverage is claimed.

## Identity, dates and source decisions

- **97 new review artworks:** 80 have explicit source dates/ranges wholly at or before 1970. The other **17** (five Kenyan watercolours and 12 Egyptian paintings) retain unknown dates and the backend classifies them as `review`, not automatically eligible. Artist lifespans were not used as artwork dates.
- **41 links to existing artists** were added to new artworks using unique full-name matches or the documented Mahmoud Said/Saiid spelling reconciliation. Original creator labels remain in citations and on the object. No artist biographies or new artist records were invented.
- **One existing painting reused:** Harry Stratford Caldecott’s *The Cricket Match (Malay Quarter)*, 1924 (`05a8efd8-5531-50a9-953b-0e9d1c7c9bb3`). Its original Wikidata citation already specified collection Q1419469; the museum-supplied object record independently confirms the holding. Only the holding and new evidence were added; existing metadata and images were preserved.
- **Egyptian portrait collision rejected:** the existing *Painter Leysans* image and the Ministry catalogue’s *Portrait of Listas* show different people/compositions, despite the same published dimensions. Visual comparison established separate works. The existing 1940 date was not transferred.
- **Print objects remain separate:** McBey’s Legation print was not merged with the NGA or Met impressions. The Legation’s own date is retained; no edition or accession was invented.
- **62 additional source objects held:** post-1970 works, demonstrably inconsistent dates, separate institutional branches, and unresolved print/impression or photograph chronology are recorded in `source-holds.json.gz`. No chronology was silently repaired from a creator’s life dates.
- All accepted holdings have source URLs, captured evidence hashes, retrieval dates, matching reasons and editorial confidence of at least 80%. Confidence is an editorial assessment, not a calibrated probability. No current-display assertions, publication changes or new images were made.

## Evidence and verification

- [Institution register](institution-register.csv): 109 institution decisions, cities, source URLs, confidence and notes.
- [Artwork register](artwork-register.csv): 98 object decisions, original labels, source dates, materials, dimensions, inventory references and identity explanations.
- `application-plan.json.gz`: immutable applied plan; SHA-256 `656b0a8793096827345789e9afea675d54540991f3d806d91bf96c1125bd0cfa`.
- `captures/`, `fnm-museums/`, `villa-objects/`, `gac-objects/` and the source PDFs retain response bodies and retrieval receipts. Source labels and rights fields remain in the evidence; no museum material is relabelled as WikiArt.
- `identity-audit*.json.gz` and `application-baseline.json.gz` preserve the scoped pre-write identity checks. **1,655 existing artwork records**, their original citations, media, artist links and location assertions were verified against the baseline, allowing only the intended Caldecott holding. Existing artist records were unchanged. The existing Iziko institution received its supported Cape Town place without other field changes.
- Full transactional readback verified every new artwork field, holding, citation and external identifier, plus institution locations, venue records and artist links. Backend creation-scope and selection-evidence checks passed for every new artwork.
- Eight offline negative checks rejected after-1970 dates, inconsistent unknown dates, confidence below threshold, missing named creators, unknown institutions, duplicate source identities, changed evidence hashes and non-HTTPS holding URLs. No test database or fixtures were created.
- Import replay verified the existing applied state with **zero additional writes**. No application query or UI changes were made and no 10-million-row performance claim is implied.

Backups are under `/Users/vadimdulub/Library/Application Support/Artline/backups/morocco-africa-20261008/` (`preimages.json.gz` and `reviewed-plan.json.gz`). Disposable PDF renders and the research Python environment are in `/tmp`, not Documents. Existing evidence and artwork assets were preserved.

The preparation/import scripts are `ops/morocco-africa-20261008.py`, `ops/morocco-africa-build-20261008.py` and `ops/morocco-africa-apply-20261008.py`. The importer is explicitly restricted to the local `artline` database, uses the shared curated-ingestion advisory lock, checks pinned source bodies, and applies changes transactionally.

To verify the applied state without writes:

```sh
/tmp/artline-morocco-africa-20261008-venv/bin/python ops/morocco-africa-apply-20261008.py verify
```

## Public website presentation

The user subsequently chose “Keep entries; show known information only”. The [public cleanup deployment](../../deployment-20261008-public-cleanup.json) removes review labels, internal research descriptions, missing-detail placeholders and empty About sections from public presentation while retaining the records and source evidence. The release is live on https://artlines.org, verified on desktop and mobile.
