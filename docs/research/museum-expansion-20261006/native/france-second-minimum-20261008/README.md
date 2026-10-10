# Second five-museum minimum pass — 8 October 2026

Added **132 real local artwork records**, all in review: 78 drawings, 27 paintings, 22 prints, three ceramic works and two terracotta sculptures. All five museums now have at least 100 eligible linked records. This does not establish the distinctness or completeness of every older catalogue record.

| Museum | Added | Linked before → after | Eligible before → after |
| --- | ---: | ---: | ---: |
| musée des beaux-arts Antoine Lécuyer — Saint-Quentin | 31 | 82 → 113 | 81 → 112 |
| musée du vieux Toulouse — Toulouse | 32 | 87 → 119 | 82 → 114 |
| musée de l'hôtel-Dieu — Mantes-la-Jolie | 33 | 85 → 118 | 83 → 116 |
| musée eucharistique du Hiéron — Paray-le-Monial | 15 | 91 → 106 | 87 → 102 |
| château musée de Nemours — Nemours | 21 | 98 → 119 | 89 → 110 |

The preserved Joconde snapshot supplied 1,236 new source-identity leads in these museums. Only 176 selected metadata records were fetched, all from the current official catalogue API with HTTP 200 and hashed raw responses. Individual physical-object decisions approved 132 and held 44. Another 1,060 unique leads remain unselected or held by the initial screening; the supplemental Toulouse selection supersedes its earlier parser exclusions and is not double-counted. No images were downloaded or attached.

Toulouse's official museum operator explicitly identifies the association as owner of the collections. That captured statement supports a narrowly scoped museum-specific holding check. Actual `propriété privée personne morale` source labels remain verbatim, alongside exact museum/location checks and exclusions for deposits or missing objects. Generic museum visitor information does not establish current display.

The final identity version002 covers 22,781 existing artwork candidates and 48,355 citations. Version001 is retained as superseded evidence: its surname logic stopped after DE in DE LA TOUR; version002 consumes all leading surname particles. All 176 literal current records and final comparisons were recomputed identically. Full creator-pool translated-title searches supplemented the ranked leads for fan, sitter, bridge and study identities. Close-format Carracci/Baylon/Pompadour works, Rossi portraits, multi-object services/vases/mounted prints, conflicting Josephine chronology, doubtful impression dates and the drawing/print conflict remain held. Unknown makers, qualified attributions and literal source inconsistencies remain explicit.

Thirty-three Jouas drawings have individual accessions, measurements and dated views. The 1883 sheet keeps its date; near-format 1917 views retain separate signed days and orientations. Two Andrieu-Geze market sheets retain different wash colors, accessions and inscriptions. Delacroix-related Scio copies retain their distinct Andrieu and Planet copyists, sizes and dates. Bonneterre's drawing dates to 1959, while circa 1900 describes the represented guards. One before 1762 design keeps an unknown lower creation bound.

The atomic import protected 1,897 scoped existing artworks and all 6,539 earlier campaign records, including media, artist links, identifiers, citations, holdings and publication. Backups are under the Artline Library backup directory. Every new object, source identifier, citation and accepted collection holding was read back, remains eligible and stays in review. Replay made zero writes. Seventeen fresh offline regressions passed; 887 historical verified checks remain pinned, for 904 cumulative checks, not 904 tests rerun. These are correctness/evidence checks, not capacity benchmarks.

Mantes and Toulouse receive their first approved campaign additions, bringing expanded institutions to 167; all five museums were already in the 350-museum source-pass total. Campaign totals are 5,886 additions and 785 existing-object links. The fresh global audit has 1,186 canonical museum entries below 100 linked records and 1,288 below 200. The separate minimum-100 job is unchanged. The overall goal remains active; continue other underfilled museums and retain unresolved leads. Baltimore's access-control hold remains in force without alternate-host or transport retries.

Evidence: [decisions](editorial-reviewed-001.json.gz), [plan](france-second-additions-001-plan.json.gz), [read-back](france-second-additions-001-applied.json), [checks](checks-001.json), [wave57 verification](../../verification-after-wave-57.json), [checkpoint](delivery-checkpoint-001.json).
