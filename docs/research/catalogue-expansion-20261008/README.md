# Selected catalogue additions — 8 October 2026

Published **2,351 new artwork records and 41 new artist profiles** directly to production at [Artlines](https://artlines.org). The user requested 2,000–5,000 additions, permitted new painters, confirmed Africa first followed by worldwide collections, and had already authorized direct production publication and showing known information only.

| Documented collection | New artworks |
| --- | ---: |
| Fondation Al Mada — Collection des Villas des Arts, Morocco | 92 |
| Art Institute of Chicago | 1,361 |
| Cleveland Museum of Art | 898 |
| **Total** | **2,351** |

African and Egyptian art was prioritized in the Chicago and Cleveland selections, followed by Greek, Byzantine, Russian, medieval and Asian art. African art in these US collections is not represented as a holding of an African museum. This is a selected expansion, not exhaustive coverage of Morocco or Africa.

## Sources and selection

- [Villas des Arts](https://www.villadesarts.ma/): individual object pages confirm inventory number, title, creator, execution year, type and supplied material/dimensions. Inventory-year patterns were discovery hints only. Holdings belong to the foundation collection; no Casablanca/Rabat branch or current display is inferred.
- [Art Institute of Chicago API](https://api.artic.edu/docs/): bounded department/region searches, followed by selected-ID object records and official creator authorities. Metadata is CC0; no descriptive prose or images were imported from this source. Dates referring to an original model, discovery or an artist's working period were excluded. The search endpoint returned an explicit result-window validation error at page 11; search paging stopped. Selected-ID details were obtained through the separately documented endpoint.
- [Cleveland Museum of Art Open Access API](https://openaccess-api.clevelandart.org/): accessioned object-level records, bounded by selected departments. Parts/ensemble components, unknown types, missing dates and unresolved later editions were excluded. Supplied CC0 object descriptions were retained as plain text.

Every published work has explicit source creation bounds ending no later than 1970, a supported object type, stable inventory identity, a source citation and an accepted holding assertion. Holdings do not establish current display. The backend classifies all 2,351 as `eligible` with selection evidence. No images were downloaded or attached in this batch; public pages retain the existing known-information-only behavior.

Source creator labels, cultural identities, qualified attributions and date approximations remain intact. Anonymous/cultural works do not receive invented named artists. New person authorities require official museum identity and explicit lifespan corroboration in the object labels. Possible existing transliterations, conflicting lifespans and activity dates were deferred while retaining the artworks and source creator labels. One Sabbagh record displays the source's name line without its disputed birth year; the full original label and conflicting source references remain in its evidence. A Tillander authority/object first-name conflict remains unlinked. Existing artist biographies, publication states, images and catalogue records were not edited.

## Evidence and safeguards

- [Published artwork register](artwork-register.csv): IDs, catalogue facts, sources and direct live links for every addition.
- `captures/`: immutable gzip source responses and retrieval/checksum receipts. Source bodies are verified against their recorded SHA-256 hashes.
- `candidate-plan.json.gz`: preliminary 2,353-work candidate set after 44 ambiguous date-qualified objects were excluded.
- `publication-duplicate-audit.json.gz`: production native IDs, source URLs, scoped accession/title checks and globally matched Wikidata identifiers.
- `publication-plan.json.gz`: intermediate plan after one repeated Moroccan inventory and one existing Cleveland identity were excluded.
- `publication-plan-final.json.gz`: final 2,351-work, 41-artist publication manifest; SHA-256 `b3e340443f769f6a2ddffbf2383834244f088b519ce05e195e444187af3fd15a`.
- [Production receipt](production-publication-receipt.json) and `production-readback.json.gz`: committed counts and independent post-commit database verification.
- [Live verification](live-verification.json): **22 passed checks** across eight public artwork APIs, three bounded collection pages, eight rendered museum drawers and three new artist profiles; no browser page errors. An initial Cleveland drawer load timed out after 30 seconds. A fresh diagnostic visit and the complete rerun both passed; `live-verification-first-attempt.json` preserves that observation.
- [Artist artwork-loading checks](artist-works-live-verification.json): three additional checks confirm the new profiles' artwork galleries finish loading and expose their recorded works (**25 live checks in total**).

The production transaction uses the shared curated-ingestion advisory lock, rechecks duplicate identities, locks and compares existing parents/linked artist records, and inserts new records only. Native IDs and available Cleveland-supplied Wikidata IDs are retained. Full field/citation/holding/link readback passes before commit; an independent production readback also passes. All 11 offline validation tests pass, including rejection of changed source captures, post-1970/unknown dates, duplicate identities, invented inventories/titles, unsupported display claims and promotion of qualified creators to primary attribution. No real-database test fixtures were created.

Private baseline, final plan and postimages are under `/Users/vadimdulub/Library/Application Support/Artline/backups/catalogue-expansion-20261008/`. The local catalogue was not modified. No application release, Terraform change or commit was needed: existing database cache invalidation exposes the new records on the deployed site. These bounded ingestion checks do not claim to establish 10-million-row query performance.

Implementation: `ops/catalogue-expansion-20261008.py`, `ops/catalogue-expansion-publish-20261008.py`, `ops/test_catalogue_expansion_20261008.py`, and `ops/verify-catalogue-expansion-20261008.cjs`.
