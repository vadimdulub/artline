# Bartolomeo Cesi deep review and Top 100 expansion — 10 October 2026

Completed in production. The user requested a deep Cesi review and more works, followed by supported artwork, picture and connection enrichment for the existing Top 100 painters. New artworks and teaching claims remain in review; all active artwork records are available through the unified catalogue. No publication status was changed.

## Delivered and verified

| Scope | New artworks | New images | New museum holdings | New creator links | Existing works enriched | New teaching links |
|---|---:|---:|---:|---:|---:|---:|
| Cesi | 12 | 3 | 12 | 13 | 2 | 1 |
| Top 100 | 1419 | 1423 | 725 | 1419 | 275 | 4 |

The Top 100 cohort is the production `artist_discovery_selection.is_popular` list captured before research, rather than a new subjective ranking. All 100 were audited; 97 received artwork or holding additions. See the [100-painter before/after ledger](top100-painter-ledger.csv). Verrocchio and Artemisia Gentileschi had no supported additions among the checked objects. Bob Ross had no confirmed source index; the native WikiArt catalogue URL returned 404.

Across Cesi and the Top 100, the production cohort now contains 41,279 distinct active works, 26,401 with primary images and 32,221 linked to holding institutions. These are catalogue totals, not claims of complete artist coverage.

## Cesi findings

Cesi now has 18 linked active works and 8 illustrated works. The additions include paintings and drawings, with source uncertainty retained.

| Added work | Documented institution | Creation date | Attribution | Evidence |
|---|---|---|---|---|
| Holy Family with Saint John the Baptist Adored by an Unidentified Figure | J. Paul Getty Museum | about 1590s | Cesi | [Source](https://www.getty.edu/art/collection/object/107VNY) |
| Madonna and Child with SS. Benedict, John the Baptist and Francis | Los Angeles County Museum of Art | circa 1595–1598 | Cesi | [Source](https://collections.lacma.org/object/20912) |
| Etude d'un homme drapé assis, les mains appuyées sur un bâton | Musée de Grenoble | XVIIe siècle | Cesi | [Source](https://www.museedegrenoble.fr/oeuvre/2572/1922-etude-d-un-homme-drape-assis-les-mains-appuyees-sur-un-baton.htm) |
| Studie van een jongeman | Rijksmuseum | 1607–1615 | Cesi | [Source](https://www.rijksmuseum.nl/nl/collectie/object/Studie-van-een-jongeman--4a080e0e117760ebde60000614a3028a) |
| Jeune homme assis, tenant un livre | Musée du Louvre | Unknown | Cesi | [Source](https://collections.louvre.fr/en/ark:/53355/cl020004994) |
| Portrait d'un religieux | musée des Augustins — Toulouse | Unknown | Attributed to Cesi | [Source](https://collections.augustins.toulouse.fr/fr/notice/2004-1-118-portrait-d-un-religieux-c38ba34f-1209-42be-ad95-c004c147ef68) |
| Studio per la figura di San Paolo, delle mani e di un piede | Musei di Strada Nuova | Unknown | Cesi | [Source](https://catalogo.museidigenova.it/oggetti/48256-studio-per-la-figura-di-san-paolo-delle-mani-e-di-un-piede) |
| Compianto su Cristo morto (recto) / Una testa e un volto virili di profilo (verso) | Musei di Strada Nuova | Unknown | Attributed to Cesi | [Source](https://catalogo.museidigenova.it/oggetti/47771-compianto-su-cristo-morto-recto-una-testa-e-un-volto-virili-di-profilo-verso) |
| Madonna col Bambino e i santi Giacinto, Agostino e Filippo Benizzi | Pinacoteca Nazionale di Bologna — Bologna (BO) | Unknown | Cesi | [Source](https://pinacotecabologna.cultura.gov.it/eventi-mostre/bartolomeo-cesi-1556-1629-pittura-del-silenzio-nelleta-dei-carracci) |
| Incarnazione della Vergine in sant’Anna come Immacolata Concezione | Pinacoteca Nazionale di Bologna — Bologna (BO) | Unknown | Cesi | [Source](https://pinacotecabologna.cultura.gov.it/eventi-mostre/bartolomeo-cesi-1556-1629-pittura-del-silenzio-nelleta-dei-carracci) |
| San Pietro | Pinacoteca Nazionale di Bologna — Bologna (BO) | Unknown | Cesi | [Source](https://pinacotecabologna.cultura.gov.it/eventi-mostre/bartolomeo-cesi-1556-1629-pittura-del-silenzio-nelleta-dei-carracci) |
| San Paolo | Pinacoteca Nazionale di Bologna — Bologna (BO) | Unknown | Cesi | [Source](https://pinacotecabologna.cultura.gov.it/eventi-mostre/bartolomeo-cesi-1556-1629-pittura-del-silenzio-nelleta-dei-carracci) |

Three authentic images were attached: Getty Holy Family (98.GB.1), Grenoble's seated draped man and the recto of Rijksmuseum RP-T-1967-68(R). Each was individually checked against the native museum record. Recto and verso are one physical sheet, not two new artworks.

The existing Corsini portrait was linked as **attributed to Cesi**, preserving its supplied creator label. Official ICCD evidence supplies approximately 1580–1607, oil on canvas and inventory 278; the source capture from 5 October was verified and cited without claiming a new retrieval. The existing Met pregnant-woman drawing was corrected from the imported 1556–1629 range to the current museum's 1576–1629 range. Previous values remain in the audit trail. Existing images, holding assertions and statuses were preserved.

A concise biography and a Nosadella → Cesi teaching claim were added from the [Getty biography](https://www.getty.edu/art/collection/person/103KWN). Nosadella remains a source label because the corresponding artist authority was not securely reconciled.

The Louvre Saint Anthony lead was excluded because the catalogue commentary rejects the Cesi attribution and favors Calvaert; another kneeling nude belongs to Macchietti. British Museum, Morgan and Prado sources that denied access were held without bypassing their restrictions. Unknown creation dates stay unknown. The Bologna 2025–26 exhibition establishes documented collection connections, not current display after that exhibition ended. Outstanding Cesi image and authority gaps remain in `cesi-candidates.json`, `cesi-unlinked-candidates.json` and the captured source evidence.

## Top 100 selection and image checks

Full metadata indexes were reviewed for 99 of the 100 painters, totaling 29,696 source entries. Gauguin's malformed stored profile lead was resolved against the correct native profile in a separate supplemental evidence set. Historical intermediate captures are retained; `discovery-v2/` plus `discovery-supplements/` are the authoritative discovery sets.

This is a bounded curated pass, not exhaustive ingestion. Per painter, research considered up to 40 existing image gaps, 15 existing connection gaps and 45 fresh object pages, selecting up to 30 new highlights. Existing source URLs/IDs and exact artist identity take precedence. A title-based existing-image match additionally requires a distinctive unique title, matching creation bounds and compatible holding evidence. Repeated titles, translations, versions, copies, physical print editions and uncertain attributions remain deferred.

The image workflow uses the existing conservative creation cutoff of 1955; the overall catalogue cutoff remains 1970. Later eligible catalogue works, unknown dates and ambiguous ranges require a separate reviewed metadata selection. New WikiArt works were selected as personal owner highlights, including source-famous works and under-illustrated periods. That selection is stored separately from museum masterpiece designations and museum holdings.

Every delivered image was visually inspected, proportionally resized without cropping to at most 100,000 bytes, uploaded with an immutable object precondition and fetched through the public site for an exact byte-hash check. Actual WikiArt rights labels, including restricted or unknown labels, remain intact; the user's source approval is recorded separately and is not described as a licence grant. Museum images retain their actual source and rights evidence. No existing primary image was replaced.

All 24,975 existing cohort primary images were hashed for comparison. The perceptual check flagged 99 selected reproductions for duplicate/version review; similarity is a warning rather than proof of identity. There were 301 delivery holds plus 18 earlier ambiguous source rows. These sets overlap other visual/duplicate review counts and must not be added together as distinct artworks. Visual review also withheld book pages with uncertain edition identity, wrong pictures, composite objects and uncertain authorship. See [remaining object research](remaining-object-research.csv), `visual-review/`, `duplicate-image-review.json` and `identity-ambiguity-holds.json`.

Institution labels were reviewed against existing records: 204 mappings were accepted and six were held, including erroneous broad aliases for Rimini and Fragonard d'Alfort and labels naming multiple collections. Literal source labels are retained. New assertions mean documented holdings, with an editorial confidence assessment of 94% for reviewed WikiArt matches, not calibrated probability and not current display.

## Artist connections

The relationship audit recorded 1,037 explicit source assertions: 281 already matched stored claims, 732 lacked an unambiguous exact artist authority, and the remaining assertions reduced to 23 candidate pairs. Four independently corroborated teacher relationships were added in review:

- Henri Matisse → Matthew Smith: Museum of Modern Art catalogue, printed page 115 (PDF page 120), visually inspected: Smith enrolled at Matisse’s Paris school in 1910. [Source](https://assets.moma.org/documents/moma_catalogue_2887_300190205.pdf).
- Jacques-Louis David → Pieter van Hanselaere: Museum of Fine Arts Ghent collection text, via Vlaamse Kunstcollectie, says Van Hanselaere studied with David in Paris after his Ghent training. Pierre/Pieter variants refer to the same artist in this object record. [Source](https://vlaamsekunstcollectie.be/en/collection/1820-b).
- Ilya Repin → Oleksandr Murashko: The Ukrainian Ministry of Culture museum portal identifies Murashko as a pupil of Ilya Repin and as a student at the St Petersburg Academy. [Source](https://museum.mincult.gov.ua/authors/murashko-oleksandr-oleksandrovich).
- Giovanni Battista Tiepolo → Giovanni Domenico Tiepolo: Städel Museum biography documents training in his father Giambattista Tiepolo’s workshop beginning around 1740. [Source](https://sammlung.staedelmuseum.de/en/person/tiepolo-giovanni-domenico).

The other 19 resolved candidate pairs remain deferred or rejected as stated. In particular, the source directions Rembrandt → Mantegna and Pissarro → Vermeer contradict chronology. Source labels alone were not used to merge artist identities. Detailed evidence and gaps are retained in `top100-connection-audit-final.json.gz` and `top100-reviewed-connections.json`.

## Verification and recovery

- Successful Cloud SQL backup **1791655436996** precedes both deliveries.
- Immutable plans, locked preimages and transaction postimages are archived under `/Users/vadimdulub/Library/Application Support/Artline/backups/cesi-top100-20261010`.
- Cesi plan SHA-256: `00654a87bb617c4e95c70f482d69b5bed490ea8c82d26ecf599bb01ed339884f`.
- Top 100 plan SHA-256: `55edfac8b9b0a72d9178945495fb182db3905734c1a0794ce27dba4e2490a807`.
- Eight offline guard tests passed. No real local test fixtures or test database were used.
- Database verification checked every delivered artwork, image checksum, rights-evidence row and new Top 100 teaching claim. Existing status, creator, image and holding preservation checks passed.
- Public detail APIs were verified for every Cesi addition and one affected object per Top 100 painter; every delivered image separately passed a public byte-hash check. Bounded one-item gallery requests verified counts for all 100 painters plus Cesi against production SQL.
- The real local catalogue was queried read-only. Its before/after counts match: 310,209 artworks and 103,254 illustrated artworks after the pass.
- No commits, application deployment, bulk status rewrite or current-display assertions were made. All new artworks remain review records.

Queries were scoped to artist IDs, selected object IDs and relevant institutions, with an actual production query plan retained in the baseline. This pass makes no new claim of verified ten-million-row performance; representative large-scale load testing remains separate backend work.

## Reproducible evidence

The campaign scripts are `ops/cesi-top100-20261010.py`, `ops/cesi-reviewed-records-20261010.py`, `ops/cesi-delivery-20261010.py`, `ops/review-top100-connections-20261010.py`, `ops/pin-top100-reviewed-connections-20261010.py`, `ops/record-cesi-top100-visual-review-20261010.py` and `ops/report-cesi-top100-20261010.py`. Source receipts pin URL, retrieval time, response status and SHA-256. Originals and contact sheets are archived outside Documents under `/Users/vadimdulub/Library/Application Support/Artline/source-images/cesi-top100-20261010`. Delivery receipts and verification results are in `cesi/` and `top100/`.
