# Cyprus island expansion — 7 October 2026

Production verified at 2026-10-07T18:23:15Z.

Added **111 institution records**, **1,147 artwork records**, **3 links to existing artworks**, and **62 links to existing painter identities**. Added 64 places and filled Kykkos Museum's missing geography. All new institutions and artworks remain in review. Existing metadata, images and publication states were preserved. No new images, publication changes, display assertions, local catalogue writes, commits or deployments.

The tracked Cyprus scope is now **169 institutions and 1,869 artworks**. This is a researched registry, not a certification that every museum on the island has been found. **Only 2 institutions meet the requested minimum of 500; 167 remain below it, including 147 with no artwork records. The requested per-museum target is not complete.** Some documented collections contain fewer than 500 total objects; others lack sufficient verified object-level evidence or predominantly contain works outside the creation cutoff.

## Collections enriched in this pass

| Museum | Before | Production artworks | Dated eligible |
| --- | ---: | ---: | ---: |
| Centre of Visual Arts and Research (CVAR) | 230 | 941 | 880 |
| Byzantine Museum and Art Galleries, Archbishop Makarios III Foundation | 225 | 533 | 524 |
| Cyprus Museum | 100 | 102 | 99 |
| Museum of Kykkos Monastery | 0 | 47 | 46 |
| Archaeological Museum of the Lemesos (Limassol) District | 0 | 27 | 26 |
| Museum of Christian Art — Christoforou Collection | 0 | 20 | 11 |
| Archaeological Museum of the Larnaka (Larnaca) District | 0 | 14 | 14 |
| Archaeological Museum of the Pafos (Paphos) District | 0 | 10 | 8 |
| Local Archaeological Museum of Palaipafos (Kouklia) | 0 | 4 | 4 |
| Local Archaeological Museum of Marion-Arsinoe, Polis Chrysochous | 0 | 4 | 4 |
| Pierides Museum – Bank of Cyprus Cultural Foundation | 0 | 2 | 2 |
| Local Archaeological Kourion Museum, Episkopi | 0 | 1 | 1 |

“Dated eligible” is the backend creation-scope classification; it does not mean published. Unknown dates remain unknown. Seven source dates stated as circa 1970 correctly remain in editorial review. Artist life dates, print-design dates, acquisition dates and excavation dates were not substituted for object creation dates.

## Evidence and verification

The national Visit Cyprus directory, Department of Antiquities, municipal/regional directories, northern departmental and tourism sources, and museum-owned websites supplied institutional evidence. Additional rural collections and separate branches were reconciled before insertion. Actual source URLs, native identifiers, literal metadata, source body hashes and retrieval timestamps are preserved in research captures and production citations.

The main artwork batch used selected CVAR and Makarios object pages. The regional batch used the Department of Antiquities' official *Ancient Cyprus: Cultures in Dialogue* (2012) catalogue, Kykkos Monastery's hosted museum guide, and the officially linked Aradippou Christian Art Museum virtual tour. Historical catalogue holdings are explicitly distinguished from current display. Detail images and duplicate native objects were not counted as extra artworks. Seventeen native identity candidates remain held; source exclusions are recorded separately.

Each production transaction used an acknowledged full-instance backup, transaction-specific preimages, source hash checks, object/version checks, duplicate checks, the curated-ingestion lock and an atomic transaction. Independent read-only checks verified all delivered artwork holdings, source citations, review/publication states and retained metadata. The final country-scoped count and plan are saved. No application query or 10-million-row load-performance claim is made.

Two attempts rolled back entirely on schema validation before successful retries: blank creator labels now map to NULL; absent date-display text maps to “Unknown” while numeric years remain NULL. Literal source fields remain in citations. A later audited correction explicitly identifies the Pomos evidence as local reporting and lowers its historical-identity confidence to 0.88.

Backups and preimages are under `/Users/vadimdulub/Library/Application Support/Artline/backups/cyprus-island-expansion-20261007/`.

## Outstanding source work

- [https://www.visitcyprus.com/discover-cyprus/culture/museums-galleries/the-archibishop-kyprianos-museum/](https://www.visitcyprus.com/discover-cyprus/culture/museums-galleries/the-archibishop-kyprianos-museum/): Official directory states 138 total exhibits. A 500-object target exceeds the documented collection, even before eligibility filtering.
- [https://musan.com.cy/](https://musan.com.cy/): Museum states 93 sculptures created in 2021. Institution added; works are outside the <=1970 creation scope.
- [https://larnakaregion.com/directory/product/museum-christian-art-christoforou-collection](https://larnakaregion.com/directory/product/museum-christian-art-christoforou-collection): Collection described as 300+ works. Twenty individually identified tour records delivered; no evidence establishes 500 eligible works.
- [https://www.kyreniaship.com/objects](https://www.kyreniaship.com/objects): 573 selected craft/art-object leads indexed. Sampled research histories include missing objects, fragments, duplicate aliases, overseas analysis locations and paginated events. No accepted production holding added from these unresolved leads.
- [https://dioptra.cyi.ac.cy/](https://dioptra.cyi.ac.cy/): Certificate error prevented retrieval. No TLS bypass; digitisation totals are not object records or verified holdings.
- [https://hambismuseum.cy/category/artworks/](https://hambismuseum.cy/category/artworks/): Shared collection spans Nicosia and Platanisteia branches. Branch-specific object custody remains unresolved; do not duplicate shared works into both museums.
- [https://leventisgallery.org/wp-json/wp/v2/artworks?per_page=100&page=4](https://leventisgallery.org/wp-json/wp/v2/artworks?per_page=100&page=4): Official API reports no fourth page. Existing native and Cypriot-artist sources do not establish 500 eligible, distinct museum records in this pass.
- [https://www.pomos.org.cy/](https://www.pomos.org.cy/): Municipal website returned certificate-origin error. Museum identity retained in review from local reporting, with explicit historical-identity uncertainty and 0.88 editorial confidence.

All remaining institution counts and numeric gaps are below and in [final-production-coverage.json](final-production-coverage.json). A missing artwork count is not an assertion that the museum has no real collection. It identifies unfilled Artline coverage requiring individual object research.

## All tracked institutions

| Institution | Place | Artworks | Dated eligible | Gap to 500 |
| --- | --- | ---: | ---: | ---: |
| Olive Museum | Agglisides | 0 | 0 | 500 |
| Early (Proto) – Industrial Museum – Agia Varvara village | Agia Varvara (Nicosia district) | 0 | 0 | 500 |
| Akourdalia Folk Art Museum | Akourdalia | 0 | 0 | 500 |
| Oleastro Olive Museum | Anogyra | 0 | 0 | 500 |
| Aradippou Toy Museum | Aradippou | 0 | 0 | 500 |
| Folklore Museum ‘Kostas Kaimakliotis’ – Aradippou | Aradippou | 0 | 0 | 500 |
| Museum of Christian Art — Christoforou Collection | Aradippou | 20 | 11 | 480 |
| Arsos Folk Art Museum | Arsos | 0 | 0 | 500 |
| Ecclesiastical Museum of Athienou — Archbishop Georgios | Athienou | 0 | 0 | 500 |
| Kallinikeio Municipal Museum of Athienou | Athienou | 0 | 0 | 500 |
| The Avgorou Ethnographic Museum | Avgorou | 0 | 0 | 500 |
| MUSAN — Museum of Underwater Sculpture Ayia Napa | Ayia Napa | 0 | 0 | 500 |
| Thalassa Agia Napa Municipal Museum | Ayia Napa | 0 | 0 | 500 |
| Local Museum of Ancient Idalion in Dali region | Dali | 0 | 0 | 500 |
| Deryneia Folkloric Museum / Open Air Museum for Traditional Professions | Deryneia | 0 | 0 | 500 |
| Byzantine Museum of the Holy Bishopric of Tamasos and Oreinis | Episkopeio | 0 | 0 | 500 |
| Local Archaeological Kourion Museum, Episkopi | Episkopi (Limassol district) | 1 | 1 | 499 |
| The Cyprus Wine Museum | Erimi | 0 | 0 | 500 |
| Cyprus Railways Museum | Evrychou | 0 | 0 | 500 |
| Canbulat Museum | Famagusta | 0 | 0 | 500 |
| Namık Kemal Dungeon and Museum | Famagusta | 0 | 0 | 500 |
| Art Nest — Philippos Yiapanis Sculpture Collection | Fasoula | 0 | 0 | 500 |
| Fassoula Agricultural Museum | Fasoula | 0 | 0 | 500 |
| Fikardou Ethnological Museum: The Houses of Katsinioros and Achilleas Dimitri | Fikardou | 0 | 0 | 500 |
| Pilavakeion Folk Art Museum | Foini | 0 | 0 | 500 |
| Fyti Weaving Museum | Fyti | 0 | 0 | 500 |
| Ecclesiastical Museum of Pafos (Paphos) | Geroskipou | 0 | 0 | 500 |
| Local Ethnographic Museum of Geroskipou | Geroskipou | 0 | 0 | 500 |
| Güzelyurt Archaeology and Nature Museum | Güzelyurt (Morphou) | 0 | 0 | 500 |
| Güzelyurt Railway Station Museum | Güzelyurt (Morphou) | 0 | 0 | 500 |
| İskele Archaeology Museum | İskele (Trikomo) | 0 | 0 | 500 |
| İskele Icon Museum | İskele (Trikomo) | 0 | 0 | 500 |
| Eliomilos Olive Oil Museum, Kakopetria | Kakopetria | 0 | 0 | 500 |
| Linos Museum, Kakopetria | Kakopetria | 0 | 0 | 500 |
| Saint John Lampadistis Byzantine Museum | Kalopanagiotis | 0 | 0 | 500 |
| Kampos Forest Heritage Museum | Kampos | 0 | 0 | 500 |
| Kato Drys Bee and Embroidery Museum | Kato Drys | 0 | 0 | 500 |
| Local Rural Museum of Kato Drys | Kato Drys | 0 | 0 | 500 |
| Cyprus Medical Museum | Kato Polemidia | 0 | 0 | 500 |
| Ecclesiastical Museum, Koilani | Koilani | 0 | 0 | 500 |
| Viticulture Museum, Koilani | Koilani | 0 | 0 | 500 |
| Local Archaeological Museum of Palaipafos (Kouklia) | Kouklia | 4 | 4 | 496 |
| Museum of Kykkos Monastery | Kykkos Monastery | 47 | 46 | 453 |
| EOKA Struggle Museum, Kyperounta | Kyperounta | 0 | 0 | 500 |
| Museum of Rural and Traditional Life, Kyperounta | Kyperounta | 0 | 0 | 500 |
| Archangelos Michael Icon Museum | Kyrenia | 0 | 0 | 500 |
| Cyprus House and Carob Store Museum | Kyrenia | 0 | 0 | 500 |
| Kyrenia Castle and Shipwreck Museum | Kyrenia | 0 | 0 | 500 |
| Peace and Freedom Museum | Kyrenia region | 0 | 0 | 500 |
| Laneia Museum | Laneia | 0 | 0 | 500 |
| Agios Lazaros Byzantine Museum | Larnaca | 0 | 0 | 500 |
| Archaeological Museum of the Larnaka (Larnaca) District | Larnaca | 14 | 14 | 486 |
| Jewish Museum Cyprus | Larnaca | 0 | 0 | 500 |
| Larnaka (Larnaca) Medieval Museum | Larnaca | 0 | 0 | 500 |
| Larnaka (Larnaca) Municipal Museum of Natural History | Larnaca | 0 | 0 | 500 |
| Larnaka Municipal Gallery | Larnaca | 0 | 0 | 500 |
| Larnaka Municipal Gallery — Christoforou Collection | Larnaca | 0 | 0 | 500 |
| Medical Museum Kyriazi – Larnaka (Larnaca) | Larnaca | 0 | 0 | 500 |
| Municipal Historical Archives – Museum of Larnaka (Larnaca) | Larnaca | 0 | 0 | 500 |
| Pierides Museum – Bank of Cyprus Cultural Foundation | Larnaca | 2 | 2 | 498 |
| Salt and Pepper Museum, Larnaca | Larnaca | 0 | 0 | 500 |
| Museum of Sea and Culture | Latchi | 0 | 0 | 500 |
| Local Museum of Traditional Embroidery and Silversmith-work, Lefkara | Lefkara | 0 | 0 | 500 |
| Lefke Mining Museum — Vasıf Palas | Lefke | 0 | 0 | 500 |
| Archaeological Museum of the Lemesos (Limassol) District | Limassol | 27 | 26 | 473 |
| Art Gallery “PSI Foundation” | Limassol | 0 | 0 | 500 |
| Carnival Museum of Lemesos | Limassol | 0 | 0 | 500 |
| Cyprus Historic and Classic Motor Museum | Limassol | 0 | 0 | 500 |
| Cyprus Medieval Museum [Limassol (Lemesos) Castle] | Limassol | 0 | 0 | 500 |
| Cyprus Theatre Museum | Limassol | 0 | 0 | 500 |
| Lemesos (Limassol) Municipal Art Gallery | Limassol | 0 | 0 | 500 |
| Municipal Folk Art Museum | Limassol | 0 | 0 | 500 |
| Pattichion Municipal Museum – Historical Archives of Lemesos (Limassol) – Research Centre of Lemesos | Limassol | 0 | 0 | 500 |
| Takis Pattichis Museum of Industrial Pharmacy | Limassol | 0 | 0 | 500 |
| Water Museum | Limassol | 0 | 0 | 500 |
| XeniArtSpace | Limassol | 0 | 0 | 500 |
| Craft of Caning Museum, Livadia | Livadia | 0 | 0 | 500 |
| The Costas Argyrou Museum | Mazotos | 0 | 0 | 500 |
| Nikos Kouroussis Foundation Museum | Mitsero | 0 | 0 | 500 |
| Museum of Platini | Mosfiloti | 0 | 0 | 500 |
| Aglantzia Municipal Museum of Natural History | Nicosia | 0 | 0 | 500 |
| A. G. Leventis Gallery | Nicosia | 103 | 8 | 397 |
| Alparslan Türkeş House Museum | Nicosia | 0 | 0 | 500 |
| APOEL History Museum | Nicosia | 0 | 0 | 500 |
| Archbishop Kyprianos Ecclesiastical Museum | Nicosia | 7 | 7 | 493 |
| Bank of Cyprus Cultural Foundation | Nicosia | 7 | 7 | 493 |
| Bedesten Medieval Tombstones Museum | Nicosia | 0 | 0 | 500 |
| Byzantine Museum and Art Galleries, Archbishop Makarios III Foundation | Nicosia | 533 | 524 | 0 |
| Centre of Visual Arts and Research (CVAR) | Nicosia | 941 | 880 | 0 |
| CyBC Museum of Broadcasting | Nicosia | 0 | 0 | 500 |
| Cyprus Car Museum | Nicosia | 0 | 0 | 500 |
| Cyprus Classic Motorcycle Museum | Nicosia | 0 | 0 | 500 |
| Cyprus Folk Art Museum | Nicosia | 2 | 2 | 498 |
| Cyprus Food and Nutrition Museum | Nicosia | 0 | 0 | 500 |
| Cyprus Herbarium and Natural History Museum | Nicosia | 0 | 0 | 500 |
| Cyprus Jewellers Museum | Nicosia | 0 | 0 | 500 |
| Cyprus Museum | Nicosia | 102 | 99 | 398 |
| Cyprus Museum of Modern Arts | Nicosia | 0 | 0 | 500 |
| Cyprus Museum of Natural History | Nicosia | 0 | 0 | 500 |
| Cyprus Police Museum | Nicosia | 0 | 0 | 500 |
| Cyprus Postal Museum | Nicosia | 0 | 0 | 500 |
| Dervish Pasha Mansion — Ethnographic Museum | Nicosia | 1 | 1 | 499 |
| Dr. Fazıl Küçük Museum | Nicosia | 0 | 0 | 500 |
| Ethnological Museum — House of Hadjigeorgakis Kornesios | Nicosia | 0 | 0 | 500 |
| Fairy Tale Museum | Nicosia | 0 | 0 | 500 |
| Günsel Art Museum | Nicosia | 0 | 0 | 500 |
| Günsel Office Museum | Nicosia | 0 | 0 | 500 |
| Hambis Municipal Printmaking Museum | Nicosia | 0 | 0 | 500 |
| Heroes Museum, Yeri | Nicosia | 0 | 0 | 500 |
| Historical Labour Museum | Nicosia | 0 | 0 | 500 |
| International Natural History Museum of the Tsirides Foundation | Nicosia | 0 | 0 | 500 |
| Lapidary Museum, Nicosia | Nicosia | 1 | 1 | 499 |
| Leventis Municipal Museum of Nicosia | Nicosia | 31 | 31 | 469 |
| Local Archaeological Museum of Ledroi | Nicosia | 0 | 0 | 500 |
| Loukia and Michael Zampelas Art Museum | Nicosia | 0 | 0 | 500 |
| Lusignan House Museum | Nicosia | 0 | 0 | 500 |
| Mevlevi Tekke Museum | Nicosia | 0 | 0 | 500 |
| Museum of Barbarism | Nicosia | 0 | 0 | 500 |
| Museum of the George and Nefeli Giabra Pierides Collection | Nicosia | 3 | 3 | 497 |
| Museum of the Hellenic Force in Cyprus (ELDYK) | Nicosia | 0 | 0 | 500 |
| Museum of the History of Cypriot Coinage | Nicosia | 3 | 3 | 497 |
| Museum of Turkish Cypriot Islamic Arts | Nicosia | 0 | 0 | 500 |
| National Guard Commandos Museum | Nicosia | 0 | 0 | 500 |
| National Struggle Museum, Nicosia | Nicosia | 0 | 0 | 500 |
| Nicosia Municipal Arts Centre (NiMAC) | Nicosia | 0 | 0 | 500 |
| Nicosia Water Board Museum | Nicosia | 0 | 0 | 500 |
| Pancyprian Geographical Museum | Nicosia | 0 | 0 | 500 |
| Pancyprian Gymnasium Museums | Nicosia | 0 | 0 | 500 |
| Point Centre for Contemporary Art | Nicosia | 0 | 0 | 500 |
| Press Museum, Nicosia | Nicosia | 0 | 0 | 500 |
| Shacolas Tower Museum and Observatory | Nicosia | 0 | 0 | 500 |
| State Gallery of Contemporary Cypriot Art | Nicosia | 6 | 6 | 494 |
| Turkish Cypriot History, Culture and National Struggle Museum | Nicosia | 0 | 0 | 500 |
| Von World Pens Hall | Nicosia | 0 | 0 | 500 |
| Walled City Museum, Nicosia | Nicosia | 0 | 0 | 500 |
| 1955–1959 Struggle Museum, Holy Cross Monastery, Omodos | Omodos | 0 | 0 | 500 |
| Art Gallery, Holy Cross Monastery, Omodos | Omodos | 0 | 0 | 500 |
| Byzantine Art Museum, Holy Cross Monastery, Omodos | Omodos | 0 | 0 | 500 |
| Folkloric Art Museum, Holy Cross Monastery, Omodos | Omodos | 0 | 0 | 500 |
| Lace Museum, Holy Cross Monastery, Omodos | Omodos | 0 | 0 | 500 |
| Photography Museum, Holy Cross Monastery, Omodos | Omodos | 0 | 0 | 500 |
| Museum of Byzantine Heritage – Palaichori Village | Palaichori | 0 | 0 | 500 |
| Archaeological Museum of the Pafos (Paphos) District | Paphos | 10 | 8 | 490 |
| Ethnographic Museum – Pafos (Paphos) | Paphos | 0 | 0 | 500 |
| Monastery of Saint Neophytos | Paphos | 0 | 0 | 500 |
| Museum of Ayia Anna, Paralimni | Paralimni | 0 | 0 | 500 |
| Paralimni Folkloric Museum | Paralimni | 0 | 0 | 500 |
| Paralimni Municipal National History Museum | Paralimni | 0 | 0 | 500 |
| Pedoulas Byzantine Museum | Pedoulas | 0 | 0 | 500 |
| Pedoulas Folkloric Museum | Pedoulas | 0 | 0 | 500 |
| Byzantine Museum of Arsinoe | Peristerona (Paphos district) | 0 | 0 | 500 |
| Maa–Palaeokastro Archaeological Site and Museum | Peyia | 0 | 0 | 500 |
| Museum of Folk Art, Tradition and Heritage, Platanistasa | Platanistasa | 0 | 0 | 500 |
| Hambis Printmaking Museum, Platanisteia | Platanisteia | 0 | 0 | 500 |
| Local Archaeological Museum of Marion-Arsinoe, Polis Chrysochous | Polis Chrysochous | 4 | 4 | 496 |
| Natural History Museum of Pomos | Pomos | 0 | 0 | 500 |
| Saint Barnabas Icon and Archaeological Museum | Salamis | 0 | 0 | 500 |
| Salamis Royal Tombs Museum | Salamis | 0 | 0 | 500 |
| Commandaria Museum, Silikou | Silikou | 0 | 0 | 500 |
| Ecclesiastical Museum – Sotira village | Sotira | 0 | 0 | 500 |
| The Museum of Shoemaker Christos Chrysanthou | Spilia | 0 | 0 | 500 |
| The Steni Museum of Village Life | Steni | 0 | 0 | 500 |
| Taşkent Martyrs Museum | Taşkent (Kyrenia district) | 0 | 0 | 500 |
| Minia Cyprus Museum | Tatlısu | 0 | 0 | 500 |
| Ecclesiastical Museum of Saints Constantine and Helen, Tochni | Tochni | 0 | 0 | 500 |
| Medflora Museum Cyprus | Trachoni | 0 | 0 | 500 |
| Elementary Education History Museum, Vasa Koilaniou | Vasa Koilaniou | 0 | 0 | 500 |
| Zivania Museum, Vasa Koilaniou | Vasa Koilaniou | 0 | 0 | 500 |
| Commandaria Museum, Zoopigi | Zoopigi | 0 | 0 | 500 |
