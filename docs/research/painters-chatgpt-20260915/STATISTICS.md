# Artline catalogue statistics — 15 September 2026

Production snapshot: 2026-09-15 18:14:59.167835+00:00. Local snapshot: 2026-09-15 21:14:54.337455+03:00. Both audited using read-only, repeatable-read transactions. No database rows were changed.

| Metric | Production | Local |
|---|---:|---:|
| Active painter profiles | 13,152 | 13,152 |
| Named people | 13,150 | 13,150 |
| Popular painters | 100 | 100 |
| Painters with linked active artworks | 13,007 | 13,007 |
| Painters without linked active artworks | 145 | 145 |
| Painters missing cultural country | 3,561 | 3,561 |
| Painters missing biography | 10,027 | 10,027 |
| Painters without external authority ID | 2,228 | 2,228 |
| Active artworks, all types | 235,681 | 235,683 |
| Artworks with DB-displayable primary image | 25,840 | 25,842 |
| Artworks with no DB-displayable primary image | 209,841 | 209,841 |
| Artworks with no primary image attached | 209,839 | 209,839 |

Active means status is not archived; it does not mean published. Profile counts include two anonymous-master profiles. Artwork counts are distinct physical catalogue records; counts summed across painters or countries can overlap because of multiple attributions/affiliations.

## Production artwork and image coverage

| Current type | Active records | DB-displayable image | No displayable image | No image attached | Image coverage |
|---|---:|---:|---:|---:|---:|
| painting | 77,160 | 13,549 | 63,611 | 63,609 | 17.6% |
| print | 61,884 | 8,048 | 53,836 | 53,836 | 13.0% |
| unknown | 53,227 | 0 | 53,227 | 53,227 | 0.0% |
| drawing | 43,124 | 4,179 | 38,945 | 38,945 | 9.7% |
| watercolor | 220 | 9 | 211 | 211 | 4.1% |
| fresco | 66 | 55 | 11 | 11 | 83.3% |

Painting means the database type `painting`; frescoes and watercolours are separate. Unknown-type records need classification before selecting reproductions. An attached image may fail the verification, rights-status or alt-text gate. Displayable counts follow the database image gate and require a nonempty storage path; they do not prove current HTTP availability or independently reverify licences. Existing `licensed` assets can pass that gate; new research accepts only the four rights classes in the prompt.

| Popular-painter linked works | Active records | No displayable image | No primary image |
|---|---:|---:|---:|
| painting | 4,790 | 2,983 | 2,983 |
| print | 11,967 | 5,003 | 5,003 |
| unknown | 855 | 855 | 855 |
| drawing | 7,415 | 6,211 | 6,211 |
| watercolor | 11 | 4 | 4 |
| fresco | 29 | 7 | 7 |

Popular linkage includes recorded attribution relationships, including historical/qualified ones; it is a research priority signal, not a fresh attribution decision.

## Painter country coverage

3,561 of 13,152 active profiles (27.1%) have no recorded cultural-affiliation country. A populated country is not proof that it has been editorially verified; the painter CSV retains geography review state. Country means artist cultural affiliation, not museum location.

A further 652 profiles have countries recorded but geography still marked not reviewed. They are provided separately in `painters_existing_countries_to_verify.csv`. In total, 4,213 profiles have unreviewed geography; 8,939 are marked classified.

| Largest recorded affiliations | Profiles | Popular profiles |
|---|---:|---:|
| United States (US) | 2,711 | 3 |
| Germany (DE) | 902 | 4 |
| France (FR) | 875 | 31 |
| United Kingdom (GB) | 705 | 1 |
| Italy (IT) | 649 | 25 |
| Russia (RU) | 590 | 3 |
| Netherlands (NL) | 558 | 6 |
| Denmark (DK) | 531 | 0 |
| Sweden (SE) | 261 | 0 |
| Norway (NO) | 231 | 1 |
| Poland (PL) | 215 | 0 |
| Switzerland (CH) | 197 | 0 |
| Belgium (BE) | 166 | 1 |
| Spain (ES) | 160 | 7 |
| Finland (FI) | 126 | 0 |

All country rows are in `statistics_by_country.csv`. Profiles with multiple affiliations appear in multiple country counts.

## Other gaps and review state

| Production gap | Active artworks |
|---|---:|
| no recorded institution | 94,777 |
| no accession | 93,338 |
| date requires review | 27,749 |
| no linked creator | 69,442 |

These categories overlap; a blank accession is not automatically invalid. All creation-date classifications follow the existing backend function. The research prompt narrows new painted-work selections to 1000–1970, while uncertain dates remain review candidates.

Painter status totals: 2 anonymous_master/review, 66 person/archived, 13,150 person/review.

Artwork status totals: 475 archived, 235,681 review.

The image/metadata research queue contains 118,137 existing active works with at least one relevant gap. It includes uncertain dates and unknown types for verification; it is not an approved import list. The full identity index contains 236,156 records, including 475 archived records, to support duplicate checks.

Local and production are separate snapshots. Matching totals alone do not prove record-level parity. Research rows come from production; local UUIDs are matched by stable slug. No reconciliation or import was performed.
