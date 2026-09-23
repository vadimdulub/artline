# Starting-point filter review — 23 September 2026

All 30 starting points were checked against the existing local catalogue in a
PostgreSQL-enforced read-only snapshot. This extends the historical subject and
source review in [the preset review](research/preset-review-20260922/README.md).
No records, publication flags, dates, creator identities or image assets changed.

## Decisions

Every starting point now exposes its geographic or subject scope both on its
starting card and above the resulting timeline. Thirteen periods offer editable
artwork country defaults. These are a useful initial selection, not exhaustive
historical coverage. The country filter identifies itself as **Artwork countries**.
A visible checkbox can apply those countries to books and events as well.

The initial audit showed that applying the proposed defaults to all three lanes
removed reviewed books and events whose recorded geography differs or is sparse.
The final defaults therefore narrow artworks only and preserve the full period's
book and event context. Visitors can remove the defaults to use the full reviewed
period focus, or explicitly apply countries to every lane.

Periods with existing regional, tradition or subject scopes retain them. Global
subjects including empire, decolonization and the digital turn remain global.
Byzantine traditions retain anonymous and unlinked object-level records without
an additional country restriction. The earlier review's core, related and context
record assignments are unchanged. Empty layers reflect available catalogue
coverage; this change does not fill them with unrelated records.

Choosing a card starts its advertised scope. Switching the period dropdown
replaces a previous automatic country selection, while preserving a visitor's
custom geography. Existing URLs with explicit countries keep their original
all-lane semantics unless they opt into `country_scope=artwork`.

## Catalogue results

Counts below are **artworks / books / events**, with highlights enabled and
illustrated artworks only, in preview visibility. “Full” means the reviewed
period scope before additional starting-country defaults, not an unrestricted
worldwide date slice. These are a local snapshot and change with the catalogue.
All starting selections retain each period's book/event totals and reviewed core
records. Responses remain bounded to 60 records per lane.

| Starting point | Visible scope | Artwork country defaults | Full | Starting |
| --- | --- | --- | --- | --- |
| Writing and the first cities | Mesopotamia, Egypt, the Indus region, China & Mesoamerica | Existing period focus | 0 / 2 / 6 | 0 / 2 / 6 |
| The classical world | The Mediterranean & its Persian neighbours | Existing period focus | 0 / 8 / 8 | 0 / 8 / 8 |
| Buddhism and its early journeys | South, Central & East Asian journeys | Existing period focus | 0 / 2 / 3 | 0 / 2 / 3 |
| The Silk Roads | Eurasia & the Indian Ocean | Existing period focus | 512 / 6 / 10 | 512 / 6 / 10 |
| Byzantium | The eastern Mediterranean & Byzantine traditions | Existing period focus | 557 / 2 / 7 | 557 / 2 / 7 |
| Islamic worlds and learning | Abbasid centres, North Africa, Iberia & Central Asia | Existing period focus | 0 / 2 / 6 | 0 / 2 / 6 |
| Tang and Song China | China & its recorded dynasties | Existing period focus | 6 / 2 / 3 | 6 / 2 / 3 |
| West African trade and learning | The western Sahel & trans-Saharan connections | Existing period focus | 0 / 0 / 1 | 0 / 0 / 1 |
| The Mongol world | Mongol Eurasia, from China to Iran & the western steppe | Existing period focus | 40 / 4 / 2 | 40 / 4 / 2 |
| The Renaissance | Italy & Northern Europe | Italy, France, Germany, Netherlands, Belgium | 1,697 / 7 / 8 | 1,477 / 7 / 8 |
| Printing and the Reformation | Printing, reform & religious settlement across Europe | Germany, Switzerland, United Kingdom, France, Netherlands | 1,976 / 4 / 7 | 800 / 4 / 7 |
| 1492 and the Atlantic encounter | Indigenous Americas, Europe, the Caribbean & West Africa | Existing period focus | 449 / 1 / 6 | 449 / 1 / 6 |
| The Mughal world | South Asia & Persian connections | Existing period focus | 9 / 0 / 3 | 9 / 0 / 3 |
| Edo Japan | Japan, including recorded historical states | Japan, Empire Of Japan, Tokugawa Shogunate, Ryukyu Kingdom | 46 / 0 / 2 | 46 / 0 / 2 |
| The Scientific Revolution | European science, art & philosophical writing | Italy, United Kingdom, France, Germany, Netherlands, Poland | 1,782 / 6 / 3 | 1,518 / 6 / 3 |
| The Enlightenment | European & Atlantic debate | France, United Kingdom, Germany, United States | 3,002 / 11 / 5 | 2,512 / 11 / 5 |
| The French Revolution | France, related writing & revolutionary context | Existing period focus | 170 / 2 / 4 | 170 / 2 / 4 |
| The Industrial Revolution | Britain, continental Europe & North America | United Kingdom, France, Germany, United States | 9,689 / 35 / 4 | 8,637 / 35 / 4 |
| Romanticism | Europe & the Americas | Germany, United Kingdom, France, Spain, Russia | 5,978 / 26 / 8 | 5,654 / 26 / 8 |
| Empire and resistance | Worldwide · colonised societies & imperial powers | Existing period focus | 14,181 / 68 / 11 | 14,181 / 68 / 11 |
| Modern life and modernism | International art, literature & urban life | France, Germany, Russia, United States, Japan, Mexico | 9,627 / 46 / 6 | 1,994 / 46 / 6 |
| The First World War | A global war, its prelude & aftermath | France, Germany, United Kingdom, Russian Empire, Ottoman Empire, Austria-Hungary | 2,711 / 21 / 6 | 1,170 / 21 / 6 |
| The Russian Revolution | Russia, the Russian Empire & the Soviet Union | Russia, Russian Empire, Soviet Union | 307 / 2 / 5 | 307 / 2 / 5 |
| Between the world wars | Worldwide · cultural life between the wars | France, Germany, United Kingdom, Soviet Union, United States, Japan | 3,333 / 30 / 14 | 1,506 / 30 / 14 |
| The Second World War | A global war, its prelude & reconstruction | France, Germany, United Kingdom, Soviet Union, China, Japan | 2,122 / 19 / 6 | 507 / 19 / 6 |
| Decolonization | Asia, Africa & worldwide struggles for independence | Existing period focus | 2,408 / 40 / 9 | 2,408 / 40 / 9 |
| The Cold War | Worldwide · rivalry, conflict & non-aligned societies | United States, Soviet Union, China, Cuba, Vietnam, India | 1,075 / 31 / 11 | 222 / 31 / 11 |
| The US civil rights movement | United States · civil rights & selected human-rights context | Existing period focus | 290 / 6 / 4 | 290 / 6 / 4 |
| The Space Age | The US–Soviet space race & selected flown missions | Existing period focus | 238 / 9 / 16 | 238 / 9 / 16 |
| The digital turn | Worldwide · computing, networks & Internet milestones | Existing period focus | 687 / 24 / 5 | 687 / 24 / 5 |

## Verification and limits

`TestStartingPointsReadOnly` checks all 30 periods for bounded results, date
intersection, image presence, retained book/event totals and reviewed core
records. `TestCountryScopeValidationAndCursor` rejects invalid scopes and cursors
from a different geography scope. The browser audit opens every starting point
and checks its description, URL geography and three content lanes.

`TestPainterPaintingsReadOnly` checks the shared artwork endpoint with native
painter filters, creation cutoff, image metadata and disjoint cursor pages.
The Monet plan uses `artwork_artists_artist_work_idx` and artwork primary-key
lookups; the snapshot has 213 illustrated works without the highlight restriction.
Disposable query plans and audit output stay under `/tmp/artline-starting-review`.
These checks use the real local catalogue without writes, fixtures or a test
database. They do not establish 10-million-artwork capacity; representative
large-catalogue concurrency and cold-cache load tests remain outstanding.
