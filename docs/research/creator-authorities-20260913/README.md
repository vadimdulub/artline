# Creator authority research — 13 September 2026

Completed in **both local and production**: **1,686 additional artwork links**, including **44 new review painters** and links to 10 existing painters. Together with the [explicit lifespan pass](../creator-lifespans-20260913/README.md), this reconciles **6,429 of the 75,965 unresolved artworks**. **69,536 artworks remain unlinked in each database**, representing 27,276 distinct object-level creator labels. This is not a claim that all 75,965 identities have been resolved.

Research includes existing and new museums and collections without restricting reconciliation to the earlier 342-institution list. This creator-only operation adds no museum, holding, on-view, artwork or image records. Existing records and uncertain attributions remain supported in review.

## Evidence and matching

Researched the 100 largest eligible unresolved closed-biography groups (2,794 artworks) against Wikidata, preserving API responses, full entity claims, retrieval timestamps, hashes and every decision. Discovery tries museum surname-first names and reordered names. Acceptance still requires a documented complete name variant, both source lifespan years, a human authority and one unique identity. Museum facts or the literal supplied creator lifespan independently corroborate the Wikidata identity.

New people require no collision with existing names, aliases, Wikidata IDs or source museum person IDs, including NGA, MoMA and Tate identifiers. Property mappings were checked against Wikidata property definitions. Conflicting authority IDs, date discrepancies and namesakes remain held. Alfred Stevens and an ambiguous `Moreau` alias were specifically held; one work falls outside its creator's lifetime. The initial unapplied plan is preserved in `planning-draft-001`; the final plan also checks original museum creator IDs.

Sources for the 1,686 applied links: Joconde 913; explicit supplied biographies corroborated with Wikidata 717; Tate 40; SMK 16. Museum physical-object/holding review notes remain unresolved; a supported creator identity does not validate those other fields. All original research facts, source holds, CSV cells and entry checksums are preserved.

Examples include [Jeanne-Marie Barbey](https://www.wikidata.org/wiki/Q33100373) (280 linked works) and [Edme-Adolphe Fontaine](https://www.wikidata.org/wiki/Q3047674) (101). Captured source evidence is attached to each artwork citation and each new painter's identity/date citation.

## Verification and recovery

Both targets passed read-only preflight, then 17 serializable write batches of at most 100 works. New painters are created atomically with their first supported artwork link. All 1,686 links/citations and 44 new painter identities were verified in each target. Existing painter metadata, artwork titles/types/dates, museum fields and images were unchanged; **426 unknown artwork dates and 717 unknown types remain unknown**. Across both passes, 2,969 unknown dates and 5,460 unknown types were preserved. No artwork or painter was published.

All selected mappings match across local and production. Final counts: local 228,641 artworks / 11,364 painters; production 228,638 artworks / 11,361 painters. The pre-existing three archived-row difference remains. Public artwork details were checked for every one of the 54 painters in this pass, plus new-painter options and timeline filtering. Together with the first pass, 79 public artwork detail checks passed. No browser interaction test is claimed.

Eleven offline identity-policy tests passed, including activity/approximate-date rejection, insufficient name-only evidence, namesakes, museum-ID/name collisions and contradictory source identities. No real-catalogue fixtures or test databases were used. A read-only indexed lookup of 100 actual artwork/creator links completed in 18.222 ms locally; its plan is saved in `local-scoped-lookup-plan.json`. These checks are not a 10-million-row load benchmark.

Final plan SHA-256: `7f2e742000bda515fb3162d4af3aeb1006fb07e7739db13a4835acbbedadcdc0`. Full selected target preimages and checksums are under `/Users/vadimdulub/Library/Application Support/Artline/backups/creator-authorities-20260913/`. They complement the fresh full local and successful managed production backup taken before the first pass. For scoped recovery, use the plan, target preimages and per-batch receipts; retain any later independent edits. `archive-receipt.json` identifies the private Google Storage evidence archive. No deployment or Git commit was made for these passes.

## Remaining backlog

`remaining-triage.json` accounts for every remaining artwork: 43,319 supplied-label records need source identity evidence; 18,812 museum creator records need additional identity evidence; 7,275 have closed biographies needing a unique authority or conflict resolution; 92 have existing conflict/attribution holds; 38 retain qualified/unknown creator labels. These are research queues, not rejection categories. Missing details do not delete or hide the retained public research records. No guessed person links were used to reduce the unresolved count.

## New review painters

| Painter | Documented lifespan | Linked artworks | Authority |
| --- | --- | ---: | --- |
| Alfred Latour | 1888–1964 | 14 | [Wikidata](https://www.wikidata.org/wiki/Q2835247) |
| André Paul Leroux | 1870–1950 | 13 | [Wikidata](https://www.wikidata.org/wiki/Q52155969) |
| Anna-Eva Bergman | 1909–1987 | 14 | [Wikidata](https://www.wikidata.org/wiki/Q447789) |
| Auguste Couder | 1789–1873 | 37 | [Wikidata](https://www.wikidata.org/wiki/Q2067613) |
| Auguste-Alexandre Baudran | 1823–1907 | 17 | [Wikidata](https://www.wikidata.org/wiki/Q53498346) |
| Charles Camoin | 1879–1965 | 22 | [Wikidata](https://www.wikidata.org/wiki/Q968285) |
| Charles Lapicque | 1898–1988 | 37 | [Wikidata](https://www.wikidata.org/wiki/Q1065281) |
| Charles Milcendeau | 1872–1919 | 26 | [Wikidata](https://www.wikidata.org/wiki/Q2959818) |
| Constant Dutilleux | 1807–1865 | 13 | [Wikidata](https://www.wikidata.org/wiki/Q1127678) |
| Edme-Adolphe Fontaine | 1814–1883 | 101 | [Wikidata](https://www.wikidata.org/wiki/Q3047674) |
| Felix Henri Giacomotti | 1828–1909 | 14 | [Wikidata](https://www.wikidata.org/wiki/Q1479490) |
| Fernand Pelez | 1848–1913 | 16 | [Wikidata](https://www.wikidata.org/wiki/Q174477) |
| François Joseph Heim | 1787–1865 | 34 | [Wikidata](https://www.wikidata.org/wiki/Q3083465) |
| François-Auguste Ravier | 1814–1895 | 61 | [Wikidata](https://www.wikidata.org/wiki/Q3083302) |
| Frédéric Anatole Houbron | 1851–1908 | 13 | [Wikidata](https://www.wikidata.org/wiki/Q94698222) |
| Henry Brokmann | 1868–1933 | 38 | [Wikidata](https://www.wikidata.org/wiki/Q28214480) |
| Jean Achard | 1807–1884 | 18 | [Wikidata](https://www.wikidata.org/wiki/Q3170279) |
| Jean Degottex | 1918–1988 | 15 | [Wikidata](https://www.wikidata.org/wiki/Q1685477) |
| Jean Puy | 1876–1960 | 16 | [Wikidata](https://www.wikidata.org/wiki/Q1685780) |
| Jean Victor Schnetz | 1787–1870 | 43 | [Wikidata](https://www.wikidata.org/wiki/Q709379) |
| Jean-Adolphe Chudant | 1860–1929 | 17 | [Wikidata](https://www.wikidata.org/wiki/Q26705744) |
| Jeanne-Marie Barbey | 1876–1960 | 280 | [Wikidata](https://www.wikidata.org/wiki/Q33100373) |
| Johann Salomon Wahl | 1689–1765 | 13 | [Wikidata](https://www.wikidata.org/wiki/Q1309780) |
| John Lewis Brown | 1829–1890 | 23 | [Wikidata](https://www.wikidata.org/wiki/Q3180832) |
| Jules Emmanuel Valadon | 1826–1900 | 15 | [Wikidata](https://www.wikidata.org/wiki/Q37517113) |
| Juliette Roche | 1884–1980 | 20 | [Wikidata](https://www.wikidata.org/wiki/Q19975144) |
| Lou Albert-Lasard | 1885–1969 | 29 | [Wikidata](https://www.wikidata.org/wiki/Q273197) |
| Louis Édouard Fournier | 1857–1917 | 44 | [Wikidata](https://www.wikidata.org/wiki/Q535800) |
| Maurice Boudot-Lamotte | 1878–1958 | 47 | [Wikidata](https://www.wikidata.org/wiki/Q16693728) |
| Paul Descelles | 1851–1915 | 14 | [Wikidata](https://www.wikidata.org/wiki/Q3371050) |
| Paul Maitland | 1863–1909 | 19 | [Wikidata](https://www.wikidata.org/wiki/Q19569687) |
| Paul Schmitt | 1855–1902 | 15 | [Wikidata](https://www.wikidata.org/wiki/Q102238141) |
| Paul-Constant Soyer | 1823–1903 | 15 | [Wikidata](https://www.wikidata.org/wiki/Q18923419) |
| Paul-Jacques-Aimé Baudry | 1828–1886 | 15 | [Wikidata](https://www.wikidata.org/wiki/Q911575) |
| Pierre Waidmann | 1860–1937 | 20 | [Wikidata](https://www.wikidata.org/wiki/Q3387333) |
| Pierre-Antoine Demachy | 1723–1807 | 36 | [Wikidata](https://www.wikidata.org/wiki/Q3382841) |
| Pierre-Edouard Dagoty | 1775–1871 | 14 | [Wikidata](https://www.wikidata.org/wiki/Q3382971) |
| Roger Toulouse | 1918–1994 | 33 | [Wikidata](https://www.wikidata.org/wiki/Q3439501) |
| Thomas Degeorge | 1786–1854 | 21 | [Wikidata](https://www.wikidata.org/wiki/Q15970235) |
| Théodore Ravanat | 1812–1883 | 17 | [Wikidata](https://www.wikidata.org/wiki/Q3526487) |
| Victor Marec | 1862–1920 | 20 | [Wikidata](https://www.wikidata.org/wiki/Q34314096) |
| William Laparra | 1873–1920 | 28 | [Wikidata](https://www.wikidata.org/wiki/Q3514997) |
| Édouard Baille | 1814–1888 | 12 | [Wikidata](https://www.wikidata.org/wiki/Q3579727) |
| Édouard Debat-Ponsan | 1847–1913 | 31 | [Wikidata](https://www.wikidata.org/wiki/Q274285) |
