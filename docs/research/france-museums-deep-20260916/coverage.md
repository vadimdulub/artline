# Measured French catalogue coverage

Snapshot: 2026-09-16 23:07:30.210472+03:00. Database: local `artline`; transaction read-only `on`. **Not a production visibility audit.**

264 French-linked institution records; 31,597 distinct active linked artworks of all types/dates; 10,444 paintings with a stored creation-end year <=1970; 670 have attached primary media (6.42%); 9,774 do not.

These are stored catalogue facts, not editorially validated/publication-ready counts. Holding assertions in review are included; a media attachment does not prove a working public image, adequate resolution or valid licence.

## Priority institutions

Local rows are de-duplicated by artwork UUID across the research museum identity crosswalk. Source columns count Joconde painting-domain notices across **all dates**, not all physical paintings or eligible additions. A zero local count means no linked work found through this crosswalk, not a complete global identity proof.

| Museum | Local paintings <=1970 | With primary media | Joconde painting notices | Notices with source image |
|---|---:|---:|---:|---:|
| Paris: [musée du Louvre](https://pop.culture.gouv.fr/notice/museo/M5031) (M5031) | 15 | 10 | 5446 | 4885 |
| Paris: [musée national d'art moderne (centre national d'art et de culture Georges Pompidou)](https://pop.culture.gouv.fr/notice/museo/M5050) (M5050) | 0 | 0 | 0 | 0 |
| Paris: [musée d'Orsay](https://pop.culture.gouv.fr/notice/museo/M5060) (M5060) | 326 | 53 | 2224 | 2133 |
| Paris: [musée d'art moderne de la ville de Paris](https://pop.culture.gouv.fr/notice/museo/M1101) (M1101) | 7 | 6 | 1510 | 1172 |
| Paris: [Petit Palais, musée des beaux-arts de la ville de Paris](https://pop.culture.gouv.fr/notice/museo/M1111) (M1111) | 42 | 20 | 1521 | 1490 |
| Dieppe: [château-musée](https://pop.culture.gouv.fr/notice/museo/M0712) (M0712) | 43 | 4 | 270 | 194 |
| Le Havre: [musée Malraux](https://pop.culture.gouv.fr/notice/museo/M0720) (M0720) | 52 | 1 | 452 | 343 |
| Nice: [musée des beaux-arts Jules Chéret](https://pop.culture.gouv.fr/notice/museo/M0880) (M0880) | 48 | 2 | 176 | 125 |
| Nice: [musée Matisse](https://pop.culture.gouv.fr/notice/museo/M0884) (M0884) | 22 | 0 | 32 | 0 |
| Nice: [musée d'art moderne et d'art contemporain](https://pop.culture.gouv.fr/notice/museo/M0888) (M0888) | 21 | 0 | 253 | 0 |
| Nice: [musée national Message biblique Marc Chagall](https://pop.culture.gouv.fr/notice/museo/M5029) (M5029) | 59 | 0 | 131 | 0 |
| Rouen: [musée des beaux-arts](https://pop.culture.gouv.fr/notice/museo/M0729) (M0729) | 141 | 2 | 3042 | 1554 |
| Caen: [musée des beaux-arts](https://pop.culture.gouv.fr/notice/museo/M0657) (M0657) | 183 | 4 | 1258 | 701 |
| Grenoble: [musée de Grenoble](https://pop.culture.gouv.fr/notice/museo/M0994) (M0994) | 14 | 13 | 1336 | 1302 |
| Lyon: [musée des beaux-arts](https://pop.culture.gouv.fr/notice/museo/M1031) (M1031) | 14 | 3 | 92 | 92 |
| Nantes: [musée des beaux-arts](https://pop.culture.gouv.fr/notice/museo/M0743) (M0743) | 252 | 7 | 2231 | 1188 |
| Reims: [musée des beaux-arts de Reims](https://pop.culture.gouv.fr/notice/museo/M0311) (M0311) | 66 | 6 | 1480 | 1474 |
| Marseille: [musée Cantini](https://pop.culture.gouv.fr/notice/museo/M0915) (M0915) | 128 | 1 | 807 | 21 |
| Strasbourg: [musée d'art moderne et contemporain de Strasbourg](https://pop.culture.gouv.fr/notice/museo/M0016) (M0016) | 115 | 15 | 1579 | 240 |
| Céret: [musée d'art moderne](https://pop.culture.gouv.fr/notice/museo/M0488) (M0488) | 42 | 0 | 467 | 4 |
| Toulouse: [Les Abattoirs, musée d'art moderne et contemporain](https://pop.culture.gouv.fr/notice/museo/M0566) (M0566) | 6 | 0 | 393 | 0 |
| Villeneuve-d'Ascq: [LaM - Lille Métropole Musée d'art moderne, d'art contemporain et d'art brut](https://pop.culture.gouv.fr/notice/museo/M0639) (M0639) | 20 | 1 | 332 | 6 |
| Le Cateau-Cambrésis: [musée Henri Matisse](https://pop.culture.gouv.fr/notice/museo/M0627) (M0627) | 37 | 1 | 44 | 44 |
| Saint-Tropez: [L’Annonciade, musée d’art moderne de Saint-Tropez ](https://pop.culture.gouv.fr/notice/museo/M0941) (M0941) | 45 | 2 | 142 | 130 |

## National source census

Streamed all 1,046,260 rows of the existing, checksum-verified September 9 Joconde export. Found 92,518 painting-domain notices, 64,949 image-bearing painting notices attached to directory codes, and 9,638 painting source references already represented among the scoped local works. These sets are not interchangeable denominators.

Retained 1,328 bounded candidate records across 342 source museum codes. A missing exact source ID does not prove a new physical object. Numeric creation fields pass an initial cutoff screen; century qualifiers, attribution, medium and source contradictions still require review.

## Reconciliation and data quality

- MuMa and Orsay each have two institution identities in this audit; counts above union their artwork UUIDs. No database merge was performed.
- French institutions lacking place/country links are recorded with research geography evidence, including MAM Paris and Petit Palais Paris. Stored code, exact directory-website match and manual crosswalk methods remain distinguishable in JSON.
- Joconde identifiers may contain letters (for example `000PE015361` and `M0923004645`); numeric-only matching substantially understates existing coverage.
- Accession years, deposit years, signature dates and exhibition dates are not creation dates.
- Anonymous/workshop/attributed records remain research-visible. They need explicit attribution support before an import; named unresolved creators should retain labels and unknown fields.
- Country/alias discovery remains a lower bound: unlinked artworks and unidentified museum aliases may exist outside the scoped inventory.
- This source-census query is not evidence of 10-million-row performance. No catalogue endpoint, query plan or production code was changed.

## Source receipts

- `content/imports/museofile-20260909/museofile.csv`: SHA256 `a66c722741045879ccdbd32d904462e6bb5d76fdddd9a9bde4751b75250354f1`; [official export](https://ministere-culture.s3.sbg.io.cloud.ovh.net/POP/museofile.csv).
- `content/imports/joconde-20260910/joconde.csv`: SHA256 `499aab59e4c9fb4bea94ed7066d4dce1f51092c74d3c8a370b8fab53039767ef`; [official export](https://ministere-culture.s3.sbg.io.cloud.ovh.net/POP/joconde.csv).
