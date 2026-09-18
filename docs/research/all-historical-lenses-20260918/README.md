# Historical lenses for All

Research and editorial review: 18 September 2026.

Thirty lenses cover major changes across several world regions and knowledge traditions. Their main windows are browsing choices, not universal periodizations. Context windows deliberately include earlier and later work. The filter is chronological: sharing a period does not assert subject relevance or causal influence. Source links identify further reading, not evidence that every returned object belongs to a movement.

The First World War lens offers 1910–1930 context, with a 1914–1918 main window. All now starts empty until the user chooses a period or existing content. Main-period shading makes the context visible. 1492 is labelled an Atlantic encounter, not the discovery of an uninhabited continent. Civil rights is explicitly the US movement. Buddhism, Islamic learning, China, West Africa, Byzantium, Japan and the Mughal world balance the European revolutions and world wars.

| Lens | Main window | Before and after | Research reference |
| --- | --- | --- | --- |
| Writing and the first cities | 3500 BCE–1000 BCE | 4000 BCE–500 BCE | [The Met](https://www.metmuseum.org/essays/the-origins-of-writing) |
| The classical world | 800 BCE–500 | 1000 BCE–600 | [The Met](https://resources.metmuseum.org/resources/metpublications/pdf/The_Year_One_Art_of_the_Ancient_World_East_and_West.pdf) |
| Buddhism and its early journeys | 500 BCE–600 | 600 BCE–800 | [The Met](https://www.metmuseum.org/essays/buddhism-and-buddhist-art) |
| The Silk Roads | 200 BCE–1400 | 500 BCE–1500 | [The Met](https://www.metmuseum.org/exhibitions/listings/2012/byzantium-and-islam/blog/topical-essays/posts/commerce) |
| Byzantium | 330–1453 | 250–1500 | [University of Washington](https://depts.washington.edu/silkroad/exhibit/byzantium/essay.html) |
| Islamic worlds and learning | 750–1258 | 600–1400 | [The Met](https://www.metmuseum.org/exhibitions/listings/2012/byzantium-and-islam) |
| Tang and Song China | 618–1279 | 550–1400 | [The Met](https://www.metmuseum.org/fr/essays/chinese-calligraphy) |
| West African trade and learning | 1200–1600 | 1000–1700 | [The Met](https://www.metmuseum.org/departments/african-art) |
| The Mongol world | 1206–1368 | 1150–1450 | [The Met](https://www.metmuseum.org/exhibitions/listings/2002/genghis-khan) |
| The Renaissance | 1350–1600 | 1300–1650 | [The Met](https://resources.metmuseum.org/resources/metpublications/pdf/The_Art_of_Renaissance_Europe_A_Resource_for_Educators.pdf) |
| Printing and the Reformation | 1450–1648 | 1400–1700 | [The Met](https://www.metmuseum.org/it/essays/the-reformation) |
| 1492 and the Atlantic encounter | 1492–1600 | 1450–1650 | [Library of Congress](https://www.loc.gov/exhibits/1492/index.html) |
| The Mughal world | 1526–1858 | 1500–1900 | [The Met](https://www.metmuseum.org/-/media/files/learn/for%20educators/publications%20for%20educators/islamic%20teacher%20resource/unit5.pdf) |
| Edo Japan | 1603–1868 | 1550–1900 | [The Met](https://www.metmuseum.org/es/essays/art-of-the-edo-period-1615-1868) |
| The Scientific Revolution | 1543–1700 | 1500–1750 | [Science Museum](https://www.sciencemuseum.org.uk/see-and-do/object-gallery) |
| The Enlightenment | 1680–1800 | 1650–1820 | [Library of Congress](https://newsroom.loc.gov/news/-the-declaration-s-promise--opens-in-treasures-gallery-at-library-of-congress/s/96d415b3-edcf-4c80-bbfb-895a71be1b0f) |
| The French Revolution | 1789–1799 | 1760–1815 | [The Met](https://www.metmuseum.org/de/essays/romanticism) |
| The Industrial Revolution | 1760–1840 | 1700–1900 | [Science Museum](https://blog.sciencemuseum.org.uk/a-new-age/) |
| Romanticism | 1780–1850 | 1750–1870 | [The Met](https://www.metmuseum.org/de/essays/romanticism) |
| Empire and resistance | 1800–1914 | 1750–1930 | [United Nations](https://www.un.org/en/global-issues/decolonization) |
| Modern life and modernism | 1870–1914 | 1850–1930 | [The Met](https://www.metmuseum.org/pt/essays/impressionism-art-and-modernity) |
| The First World War | 1914–1918 | 1910–1930 | [Imperial War Museums](https://www.iwm.org.uk/sites/default/files/files/2023-10/first_world_war_large_print_guide.pdf) |
| The Russian Revolution | 1917–1923 | 1905–1930 | [British Library](https://www.bl.uk/collection/explore-the-collection) |
| Between the world wars | 1919–1939 | 1914–1945 | [Imperial War Museums](https://www.iwm.org.uk/file-download/download/public/2667) |
| The Second World War | 1939–1945 | 1933–1955 | [Imperial War Museums](https://wmr.iwm.org.uk/war/second-world-war-1939-1945) |
| Decolonization | 1945–1980 | 1930–2000 | [United Nations](https://www.un.org/en/global-issues/decolonization) |
| The Cold War | 1947–1991 | 1945–2000 | [Office of the Historian](https://history.state.gov/milestones/1945-1952/asia-and-africa) |
| The US civil rights movement | 1954–1968 | 1940–1980 | [Library of Congress](https://www.loc.gov/exhibits/civil-rights-act/index.html) |
| The Space Age | 1957–1972 | 1945–1990 | [NASA](https://www.nasa.gov/history/dawn-of-the-space-age/) |
| The digital turn | 1970–2000 | 1950–2026 | [CERN](https://home.cern/science/computing/the-birth-of-the-web/) |

## Limits and extension

Broad collections pages provide historical context for some lenses, rather than endorsing the precise window boundaries. In particular, the British Library Russian collections, Science Museum history galleries and UN decolonization pages should be read as starting points. All window boundaries remain editorial. Future subject-specific or causal connections need an explicit evidence-backed relation, separate from this time filter.

The source of truth is `apps/server/internal/atlas/presets.json`, embedded by Go and served by `/api/v1/atlas/presets`. A preset needs a unique ID, name, group, description, main and context bounds, and at least one named HTTPS reference. The automated audit verifies 30 unique presets, source URLs, bounds, context containment and gap-free date bins without year zero.
