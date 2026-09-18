# Artline overnight research and catalogue review

Research began on 13 September 2026 at 18:59 UTC. The delivered catalogue snapshot is dated 14 September 2026. **Twenty research rounds for each of ten countries were imported and verified in both databases.** Additional Greek research, primary-museum checks, country verification and duplicate reconciliation followed. Portugal's next 20 scopes were researched and prepared, but remain unimported. Exact creator scopes, discoveries and initial verification receipts are listed in the [round ledger](research_round_ledger.csv).

Google Cloud required interactive reauthentication at approximately 02:00 UTC. Production changes completed before that point remain verified. Later work continued locally, with source evidence, recovery snapshots and guarded production plans preserved. The two databases therefore have explicitly documented differences; this report does not claim complete synchronization.

## Delivered records and pictures

| Result | Local | Production |
|---|---:|---:|
| Gross inserted artwork rows | 2,718 | 2,717 |
| Gross inserted creator profiles | 610 | 610 |
| Verified selected image assets, including retained duplicate-record assets | 1,535 | 1,506 |
| Session images used on active artworks | 1,525 | 1,496 observed through public API |
| Confirmed artwork duplicates consolidated | 438 | 238 |
| Confirmed painter duplicates consolidated | 60 | 56 |

These are this session's receipt-based figures, excluding a separate concurrent import of 271 artworks, 41 creators and 38 images. Inserted rows are not automatically new physical discoveries: **212 active added rows replace earlier/other catalogue identities, and 11 additions were subsequently archived as duplicates**. Another 2,495 active additions had no earlier identity found by this audit; further research can still discover overlaps. See [the row-level identity review](new_row_identity_review.csv).

All 2,707 active added works have creator links and selection evidence. Of these, 2,216 are currently classified as eligible under the creation-date cutoff and 491 still need date review. All 610 added profiles have cultural-affiliation records; two are correctly represented as anonymous masters. **Every added record remains unpublished and In review.** No current-display claim was invented. [Local audit](LOCAL_AUDIT_SUMMARY.json)

The initial ten-country campaigns produced the following gross additions. The image column is the initial round-verification count; later rights holds and supplementary image work are accounted for in the final totals above.

| Country | Rounds verified in both DBs | Added artwork rows | Added creator rows | Initial images |
|---|---:|---:|---:|---:|
| Netherlands | 20 | 446 | 159 | 248 |
| Greece | 20 | 43 | 11 | 34 |
| Russia | 20 | 495 | 36 | 336 |
| France | 20 | 159 | 44 | 76 |
| Italy | 20 | 180 | 39 | 76 |
| Spain | 20 | 296 | 94 | 214 |
| Germany | 20 | 176 | 69 | 109 |
| Austria | 20 | 42 | 25 | 18 |
| Belgium | 20 | 429 | 121 | 120 |
| Finland | 20 | 257 | 11 | 219 |

Additional work included 20 Greek historical scopes, 20 Greek primary-catalogue scopes, 20 Dutch Met image scopes, and 20 country-gap review scopes. These supplemental activities are separate from the main country table. Greek work added 14 historical records, 178 primary-catalogue records and two Tzanes works. Forty additional Dutch museum images were delivered. The newly identified Antwerp triptych panel accounts for the one later local-only artwork row. Empty follow-up files were not counted as independent substantive investigations. [Country ledger](research_round_ledger.csv), [delivery ledger](local_and_production_delivery.csv)

## Country was treated as evidence, not a location shortcut

The final database contains country-review citations for **7,719 distinct artist identities** from this session's sources. This measures documented review coverage, not publication approval. The remaining country-gap queue contains 3,589 active profiles without cultural affiliation; 3,419 lack any country relationship. The supplied [country evidence](country_source_evidence.csv) retains source wording and disagreements alongside exact museum/authority identifiers.

Museum location, birthplace, ancestry, imperial citizenship and cultural affiliation were kept distinct. Multiple documented affiliations were retained. Ukrainian and Lithuanian corrections, German-ancestry distinctions and additional cross-country contexts were reviewed without converting every Russian Empire or Soviet reference into Russian affiliation.

For example, the Simferopol Art Museum explicitly identifies Nikolai Dmitrievich Kuznetsov, 1850–1929, with both Russian and Ukrainian painting. Ukrainian affiliation was added locally while preserving Russian affiliation; this update is pending production. This is supported by the museum's description, rather than inferred from his birthplace. [Museum biography](https://simhm.ru/collection/picture/1199-ko-dnyu-rozhdeniya-nd-kuznecova.html)

The final spot-check also corroborated Johan Starbus's Dutch classification in Sweden's Nationalmuseum catalogue and Liepmann Fraenckel's German classification in Getty ULAN. Their works' locations in Nordic museums do not themselves establish Swedish or Finnish affiliation. [Nationalmuseum](https://collection.nationalmuseum.se/en/artists/artist/12436/), [Getty ULAN](https://www.getty.edu/vow/ULANFullDisplay?find=&nation=Indian&role=&subjectid=500068514)

Conventional names were reviewed separately from named people. The Master of the Altenberg Altarpiece and Master of Sierentz were corrected locally from person to anonymous master, preserving their works, dates and country evidence. The corresponding production corrections are queued. Priority Russian icons, Greek, Byzantine and post-Byzantine objects remain in scope when the creator is a documented workshop or anonymous-master identity. [Städel](https://stories.staedelmuseum.de/de/altenberger-madonna-erwerbung), [Kunstmuseum Basel](https://kunstmuseumbasel.ch/de/ausstellungen/2025/verso)

Two added works retain only a formerly-attributed link to Isaac Walraven after the Rijksmuseum rejected that attribution. His Dutch affiliation is documented, but the works correctly do not inherit it. The final qualified-creator audit therefore records 2,705 active added works with a current/qualified creator country and two historical-attribution exceptions. [Country/attribution audit](QUALIFIED_CREATOR_COUNTRY_AUDIT.json), [Rijksmuseum SK-A-5036](https://id.rijksmuseum.nl/200653393), [Rijksmuseum SK-A-5035](https://id.rijksmuseum.nl/200653392)

## Primary museum findings and image verification

The Finnish National Gallery's public metadata export was used to check selected objects against current object IDs, inventories, titles and creator records. It exposed 184 older placeholders with the same physical identities as recently added Finnish records. Those duplicates were consolidated locally before adding the authority identifiers, avoiding conflicting ownership of the same museum ID. A further 13 cross-country objects were reconciled after exact creator checks. The primary export contained 89,072 metadata objects; this did not trigger an exhaustive image download. [FNG public metadata](https://kokoelma.kansallisgalleria.fi/api/v1/objects)

Locally, 235 selected Finnish records received primary-source metadata/evidence updates, including nine supported resolutions of previously unknown creation-date ranges. Unqualified, internally consistent museum dates were required; artist life dates and life-shaped museum bounds were not used to invent artwork dates. Twenty-six selected CC0 museum reproductions were inspected and attached locally. These metadata and image updates await production authentication.

The Russian Museum review distinguished 111 same-title pairs using 222 different primary inventories. Missing inventory, material and dimension fields were filled locally from the exact existing source pages. Original creation dates, creators, countries, holding assertions and publication status were preserved. Dimensions were retained in the source's wording. [Pair-by-pair primary sources](same_title_primary_pair_review.csv)

The Antwerp triptych review distinguished the whole work, inventory 1599, from its three component records, 1599a/b/c. The museum's IIIF start canvases identify the church, procession arrival and moor scenes. Two existing panel titles were corrected and one panel added locally; three reviewed public-domain images were attached. Conflicting central-panel dimensions were not imported. Source identifiers and licensing evidence are included in the [image inventory](verified_selected_images.csv).

Image checks covered the actual selected reproductions, source rights, attribution, licence links, file hashes, dimensions and decoded image integrity. Served JPEG derivatives are at most 100,000 bytes. Two earlier Spanish images were subsequently held after source-rights inconsistencies were found; their evidence and files were preserved. Metadata licensing was not treated as image permission. The final inventory distinguishes 29 local-only images from the assets already delivered to Google Storage. [Image audit](ACTIVE_IMAGE_DELIVERY.json), [rights and credits](verified_selected_images.csv)

## Duplicate decisions and unresolved issues

Confirmed duplicate rows were archived with canonical redirects. Original facts, alternate dates, source assertions, artwork relationships, images and rights evidence were retained. The process did not hard-delete artwork assets or unrelated records. The [498 local consolidation decisions](confirmed_duplicate_consolidations.csv) explicitly identify which 294 are already verified in production and which 204 await synchronization.

Among 170 deeply reviewed same-title pairs, 166 remained separate, two recto/verso pairs retained distinct depictions, and two Pavia pairs were confirmed duplicates. The Appiani studies share an acquisition-register number but have different physical inventories and dimensions; they were retained. Incomplete Brera inventory text was not treated as proof of identity. Shared images of a whole work and its components also did not justify collapsing distinct records. [Detailed decisions](same_title_primary_pair_review.csv)

Remaining leads include four Finnish creator/object crosswalks, five creator/inventory matches with missing institution links, eight shared-image groups, one same-institution accession group and 8,457 same-title groups. Some groups overlap, and several already have evidence supporting distinct objects. The [8,475-group queue](unresolved_duplicate_leads.csv) is a research queue, not authorization for automatic deletion. In particular, conflicting Akimov dates, Khrutsky patronymic/country context and the two André Marchand identities need further source reconciliation.

Institution checks found no repeated exact Wikidata IDs or normalized names. Three shared-website groups were retained: an umbrella collection and its gallery, the separate Alte and Neue Pinakothek, and institutions using a shared regional catalogue portal. Shared hosting does not establish institutional identity. [National Galleries venues](https://www.nationalgalleries.org/visit), [Bavarian museums](https://www.pinakothek.de/en)

The catalogue still has 69,441 unlinked review works across 27,252 creator labels. Those figures include older unresolved research, not just this session's additions. The next pass can start with the [largest 500 creator-label groups](unresolved_creators_top_500.csv), verify the person and country, then consult exact museum object IDs before proposing new rows.

## Reproducibility and remaining delivery

The final local audit checked publication state, creator links, country coverage for additions, creation classification, selection evidence, foreign-key validation state and selected image files. Thirty focused offline counterexample tests passed; no real-catalogue fixtures or test databases were created. Public browser checks returned successful pages without JavaScript errors. A bounded public API inventory observed 11,954 painters and 161,944 artwork IDs; this supplies useful links but does not substitute for a transactionally consistent production DB audit.

An indexed, painter-scoped inventory query was inspected on the real catalogue; the recorded execution was approximately 114 ms for the selected representative scope. This is not evidence of performance at ten million artworks. Representative large-volume load testing, query-plan checks and summary/cache invalidation remain backend engineering work before claiming that capacity.

The local recovery dump and per-change preimages are under `/Users/vadimdulub/Library/Application Support/Artline/backups/overnight-countries-20260913/`. The final dump was hash-checked and its archive directory inspected without restoring it into a test database. The successful pre-import Cloud SQL backup is retained separately. [Final local backup receipt](FINAL_LOCAL_BACKUP.json)

Production still needs one artwork row, 29 images, 200 artwork consolidations, four painter consolidations, 235 Finnish metadata updates, 222 Russian metadata updates, two Antwerp title corrections, two anonymous-master corrections and Kuznetsov's added Ukrainian affiliation. These categories overlap and must not be added as a count of distinct objects. Portugal's 74 candidates need fresh identity plans in both databases before import; eight are explicitly held. A read-only local preflight found 66 potential additions without exact existing authority, inventory or source-URL matches; this is not a completed production preflight or a guarantee that all66 will be new. [Resume instructions](RESUME_PRODUCTION.md)

The next research priorities are the country-gap and creator-label queues, the Portuguese held identities, and further Dutch museum gaps followed by an under-covered country such as Sweden, Denmark or the United Kingdom. The supplied [ChatGPT prompt](RESEARCH_PROMPT.md) specifies evidence, country, duplicate, date and image-rights requirements and structured CSV outputs. It keeps every proposal in review and requires validation before further ingestion.
