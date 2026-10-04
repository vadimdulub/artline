# All starting points: illustrated expansion, 28 September 2026

All 31 starting points now have a representative cover and at least 100 illustrated works in the local research preview. Existing large galleries remain available through bounded pages; 100–200 is a minimum depth target for thin topics, not a cap on strong collections.

The campaign adds **873 real museum/archive records and 873 selected image files**: **731 Cleveland Museum of Art objects, 29 Metropolitan Museum of Art objects and 113 NASA historical photographs**. It reuses 123 source identities already present in the catalogue, plus individually reviewed existing modern artworks in `modern-curation.json`. Metadata selection preceded downloading; there was no exhaustive image crawl. All 44 contact sheets and all 31 cover images were inspected. Six repetitive or low-clarity NASA test/stereo photographs remain review records with their source files but are excluded from the galleries. Five previously selected Space Age works were removed from that preset because an artist connection alone did not make the pictures relevant. No catalogue records were deleted.

## Editorial approach

Every topic was reviewed for geographic scope, creator selection, object selection, cover relevance, date range and visible explanation. Renaissance retains its European highlight approach; the French Revolution retains France and relevant creators; Silk Roads retains Uzbekistan and the other overland route countries. Earlier roots or later related traditions are explained in the starting-point descriptions and do not replace each object's actual dates. The user explicitly approved this approach on 28 September.

Writing and classical antiquity now include inscriptions, reliefs, vessels and sculpture. Buddhist journeys follow images and manuscripts across Asia. Byzantium includes decorated ritual objects as well as icons. Arabic and Islamic learning combines calligraphy, manuscripts, metalwork and ceramics, with later Mamluk, Timurid, Ottoman and Safavid traditions explicitly described. Tang/Song and Mughal selections add painting, court portraiture, manuscripts and decorated objects. Medieval Mali remains distinct from the later West African court, community and textile traditions used as context.

Civil rights includes Black artistic agency and Harlem Renaissance roots as well as movement-era responses. Three missing US cultural-affiliation links—Edmonia Lewis, Augusta Savage and Meta Vaux Warrick Fuller—were restored from Smithsonian records; these do not assign a country of creation to their works. WWII includes exile, displacement and artistic survival. Cold War includes postwar abstraction and selected mission photography. Digital art distinguishes the documented Klee/Mondrian precedents from wider formal roots in geometry, grids and abstract rhythm. Women's rights includes artistic training, public participation, self-representation and work. Decolonisation includes earlier cultural autonomy and postcolonial nation-building alongside direct resistance subjects.

## Sources and rights

Individual source objects, responses, retrieval times, checksums and selection reasons are retained in `plan.json`, `captures/`, `modern-curation.json` and database citations. New museum reproductions have explicit CC0 designations under the [Cleveland open-access policy](https://www.clevelandart.org/open-access) and [Met image policy](https://www.metmuseum.org/policies/image-resources). NASA photographs use its [educational/informational media permission](https://www.nasa.gov/nasa-brand-center/images-and-media/), recorded as **licensed**, not a worldwide public-domain assertion. The NASA digital archive is typed as an archive; no physical holding or current display is asserted. These photographs are owner selections, not museum masterpiece designations.

Thematically useful primary references include [The Met's Sahel exhibition](https://www.metmuseum.org/exhibitions/sahel-art-empire-sahara), [gold-weight trade history](https://www.metmuseum.org/art/collection/search/317676), [Smithsonian's Augusta Savage](https://americanart.si.edu/education/oh-freedom/augusta-savage), [Edmonia Lewis](https://americanart.si.edu/artist/edmonia-lewis-2914), [Fuller's Ethiopia](https://nmaahc.si.edu/object/nmaahc_2013.242.1), [NGA's Harlem Renaissance](https://www.nga.gov/educational-resources/uncovering-america/harlem-renaissance), [V&A's digital art history](https://www.vam.ac.uk/articles/digital-art), [MoMA's geometric abstraction](https://www.moma.org/collection/terms/geometric-abstraction), [MoMA's Artists in Exile catalogue](https://www.moma.org/documents/moma_catalogue_1884_300299023.pdf), [The Met's modern South Asia](https://www.metmuseum.org/essays/the-rise-of-modernity-in-south-asia) and [NGA's abstract expressionism](https://www.nga.gov/artworks/abstract-expressionism).

Original source files and recovery dumps live under Library/Application Support/Artline, as recorded by the pinned manifests. New records remain in editorial review. Unknown makers, ambiguous countries and approximate date bounds are preserved. No on-view or publication claims were added. All displayed artwork dates are eligible at or before 1970.

## Local verification

Go tests, all 180 frontend unit tests and lint passed. Real catalogue tests run in database-enforced read-only transactions: all 31 counts, cover eligibility, image presence, the 1970 cutoff, scope retention and 150-item page bounds. The women's rights and decolonisation tests also exhaust bounded keyset pages without duplicates. Representative EXPLAIN ANALYZE plans are retained in the production release evidence. These checks use the real catalogue; they do not claim a 10-million-row load benchmark.

| Starting point | Illustrated works | Starting scope |
| --- | ---: | --- |
| Writing and the first cities | 139 | Mesopotamia, Egypt & early urban cultures |
| The classical world | 202 | Greece, Rome & the ancient Mediterranean |
| Buddhism and its early journeys | 279 | Buddhist journeys & regional traditions across Asia |
| The Silk Roads | 331 | Uzbekistan & the overland routes from China to Anatolia |
| Byzantium | 122 | Byzantine traditions & the eastern Mediterranean |
| Islamic worlds and learning | 231 | Arabic learning, Islamic visual culture & later manuscript traditions |
| Tang and Song China | 170 | China · Tang and Song cultural life |
| West African trade and learning | 105 | Medieval Mali & West African traditions across the centuries |
| The Mongol world | 168 | China, Central Asia, Iran & the western steppe |
| The Renaissance | 1664 | Italy, Northern Europe & Spain · highlights |
| Printing and the Reformation | 1956 | Germany, Switzerland & neighbouring Europe |
| 1492 and the Atlantic encounter | 451 | Europe, the Americas & West Africa |
| The Mughal world | 127 | South Asia & Persian court connections |
| Edo Japan | 2766 | Japan · Tokugawa culture & Ryukyuan connections |
| The Scientific Revolution | 1404 | Observation, geometry & experimental science |
| The Enlightenment | 2790 | Europe & the Atlantic · reason, rights and government |
| Women’s rights | 133 | Equal rights, women’s artistic work & self-representation |
| The French Revolution | 253 | France · revolution, witnesses & political debate |
| The Industrial Revolution | 214 | Britain & continental Europe · industry and labour |
| Romanticism | 2192 | Europe & the United States · 10 selected artists |
| Empire and resistance | 10398 | Imperial powers & societies resisting colonial rule |
| Modern life and modernism | 1681 | Europe & the United States · 15 selected artists |
| The First World War | 122 | Europe & the United States · war artists and witnesses |
| The Russian Revolution | 129 | Russia, Ukraine & Belarus · revolutionary avant-garde |
| Between the world wars | 199 | Europe, the Americas & global literary connections |
| The Second World War | 126 | War, exile, resistance & artistic survival |
| Decolonization | 104 | Independence, cultural autonomy & earlier artistic roots |
| The Cold War | 112 | Postwar art, cultural politics & the space race |
| The US civil rights movement | 128 | United States · Black artistic agency & civil-rights responses |
| The Space Age | 107 | Spaceflight photography, exploration & science fiction |
| The digital turn | 122 | Computer art’s documented precedents & wider formal roots |

Production delivery receipts: `../production-starting-points-20260928/`.
