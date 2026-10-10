# A. G. Leventis Gallery — deep research, 8 October 2026

## Verified production result

Committed on 8 October 2026 and checked against production and live HTTP endpoints:

- 64 new artworks (8 online catalogue entries and 56 published-report acquisitions).
- 96 existing records enriched; 51 verified painter links added.
- 74 images attached, bringing the gallery from 6 to 80 illustrated records.
- 167 total catalogue records, all in review; 93 now have source-backed date bounds.
- 160 artwork audit records verified; 10 live object responses and all 74 public image checksums passed.
- Existing images/publication states preserved; no local database writes, app deployment or Git commit.

The in-app browser tool failed before connection because session sandbox metadata was unavailable. No browser-rendering verification is claimed; live API and full image-delivery checks passed.

## Sources and selection

Read all 118 current official object entries, their HTML metadata and catalogue notes; inspected selected native media records by accession. Read the gallery’s Reports 2017–2022 and rendered acquisition pages to verify captions and plates. The Foundation’s News & Grants 2013 confirms the Paris catalogue’s publication and scope.

The paid Paris (2013, ISBN 978-9963-732-01-2), Greek (2012, ISBN 978-9963-560-97-4) and Cyprus (2015, ISBN 978-9963-732-14-2) catalogues were located in the official shop. Their full texts were not available in the accessed sources and are not claimed as read. Published reports and online catalogue entries supply the object-level evidence used here.

Primary sources:

- [Official collection catalogue](https://leventisgallery.org/artworks/)
- [Report 2017](https://www.leventisgallery.org/assets/uploads/Annual_Report_2017.pdf), PDF p. 55: Renoir etching and copy after Titian.
- [Report 2018](https://www.leventisgallery.org/assets/uploads/Annual-Report_2018.pdf), PDF pp. 50–51: Saripolou, Asteriadis, Gaitis and Savva.
- [Report 2019](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf), pp. 60–69: named acquisitions and engravings.
- [Report 2020](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf), PDF pp. 53–55: individually accessioned Loukia Nikolaides-Vasiliou donations.
- [Report 2021](https://www.leventisgallery.org/assets/uploads/Annual-Report_2021.pdf), PDF p. 38 (printed p. 36): Pantazis, Ralli and Venetian School. This page required visual reading; text extraction returned no captions.
- [Report 2022](https://www.leventisgallery.org/assets/uploads/Annual-Report_2022.pdf), PDF p. 52: Pantazis acquisition; the adjacent long-term loan discussion is kept separate.

## Editorial decisions

- No publication-state changes or local database writes. New artworks remain in review, including undated records. Holdings have dated evidence; no new current-display claims.
- Exact institution accession plus creator/title and composition resolve object identity. All 6 existing primary images are preserved.
- 49 first-pass website social preview images were gallery logos. All were rejected before upload; 48 were replaced by accession-matched official media assets. AGLG 571 remains without an image.
- The final set contains 74 images: 54 official catalogue/media images and 20 native embedded report images. Derivatives retain the source frame and are <=100,000 bytes. Report thumbnails remain at their original resolution, without upscaling. Source rights labels and the separate user authorization are retained.
- Harmony: use museum-authored [Smartify record](https://app.smartify.org/en-GB/objects/harmony-4), AGLG 223, 1893. Current website 1983 conflicts with creator chronology and its own discussion of the 1894 competition. The Smartify text was available through search indexing; direct HTTP access returned 403.
- Huet AGLG 311: signed 1783 overrides form field 1782. Bruandet AGLG 434: signed 1789 overrides 1788. Ghika AGLG 742: authored note says 1955, overriding form field 1954.
- Craen AGLG 315: reconcile duplicate pages and use 1650; reject 1950 typo. Canaletto AGLG 454 and Boudin AGLG 276 also have duplicate web pages, not new objects.
- Gainsborough: retain mid- to late 1760s, not exact 1765. Van Brussel and Bonvin signatures retain question marks. Ducayer sitter lifespan 1611–1657 is not an artwork creation date.
- Women’s Bazaar is explicitly dated 1971, outside the addition cutoff. Its existing record is retained and its previously missing date filled. Invalid dimensions text “testing” was not imported.
- Preserve school/studio/after/attributed creator labels. The possible Louis-Auguste or Jacques-Sébastien le Clerc authorship stays qualified. Do not link John Thomson (1879 painting) to the existing namesake who died in 1840.
- New AGLG 321A-B is one physical recto/verso sheet, with its recto image clearly labelled. AGLG 267/268 and 269/270 are separately accessioned pendant compositions.

## Remaining gaps

- AGLG 531 (Daughters of God) already had two production records. Enrichment uses the illustrated canonical candidate; the other pre-existing record is preserved for a separate merge with relationship review. No duplicate was added.
- Guardi AGLG 302/303/304 and Huet AGLG 309/310 are pre-existing multi-object aggregates. Their current records were preserved. Native media now distinguishes the Guardi inventories, but splitting the aggregate requires a separate relationship-aware reconciliation.
- Charlier pages collide on AGLG 557; Miró Cosmonaut page has an Othon Friesz creator field and lacks core metadata. These were excluded from new records pending resolution.
- Undated report donations remain genuine review records; publication/acquisition years and artist life dates are never substituted as creation years. Their images remain held under the existing by-1955 Cyprus image policy.
- Known post-1955 museum-source images were not included in this approved-source pass. No new blanket rights claim was made.

## Delivery evidence

Cloud SQL backup `1791473692262` completed before writes. `plan-pin.json`, `applied.json` and `verification.json` record actual delivery counts and checks. Full scoped before/after snapshots, original source HTML/PDFs and production plan are under the Artline backups directory; original images are under Artline/source-images. `visual-review.json` records inspection decisions.

## Selected new artworks

| Accession | Creator | Artwork | Date | Picture | Source |
|---|---|---|---|---|---|
| AGLG 355 | Camille Pissarro | Promenade dans le Verger / A Walk in the Orchard | 1901 | Yes | [Source](https://leventisgallery.org/artworks/promenade-dans-le-verger-a-walk-in-the-orchard/) |
| AGLG 340A-B | Attributed to Michel-Barthélémy Ollivier | A Rustic Girl Seated and Asleep in a Chair (recto) and Study of a Pair of Hands (verso) | Creation date unknown | Pending | [Source](https://leventisgallery.org/artworks/a-rustic-girl-seated-and-asleep-in-a-chair-recto-and-study-of-a-pair-of-hands-verso/) |
| AGLG 321A-B | André(-Jean) Le Brun | Designs for Two Herms (recto) and Designs for Three Female Statues, Two of them of Minerva (verso) | 1773–1774 | Yes | [Source](https://leventisgallery.org/artworks/designs-for-two-herms-recto-and-designs-for-three-female-statues-two-of-them-of-minerva-verso/) |
| AGLG 317 | Pierre Laprade | Le Couple d’Amoureux / The Pair of Lovers | Creation date unknown | Pending | [Source](https://leventisgallery.org/artworks/le-couple-damoureux-the-pair-of-lovers/) |
| AGLG 270 | Louis Belanger | A Pair of Park Landscapes, with Artificial Water | 1798 | Yes | [Source](https://leventisgallery.org/artworks/a-pair-of-park-landscapes-with-artificial-water-2/) |
| AGLG 269 | Louis Belanger | A Pair of Park Landscapes, with Artificial Water | 1798 | Yes | [Source](https://leventisgallery.org/artworks/a-pair-of-park-landscapes-with-artificial-water/) |
| AGLG 268 | Louis Belanger | A Pair of River Landscapes, each with a Bridge and Exotic Buildings | 1787 | Yes | [Source](https://leventisgallery.org/artworks/a-pair-of-river-landscapes-each-with-a-bridge-and-exotic-buildings-2/) |
| AGLG 267 | Louis Belanger | A Pair of River Landscapes, each with a Bridge and Exotic Buildings | 1787 | Yes | [Source](https://leventisgallery.org/artworks/a-pair-of-river-landscapes-each-with-a-bridge-and-exotic-buildings/) |
| AGLG 765 | Pierre-Auguste Renoir | Nude / Venus, frontispiece for Stéphane Mallarmé’s Pages | 1890–1891 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual_Report_2017.pdf) |
| AGLG 766 | Copy after Titian | Caterina Cornaro | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual_Report_2017.pdf) |
| AGLG 775 | Athena N. Saripolou | Office of N. I. Saripolos | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2018.pdf) |
| AGLG 779 | Agenor Asteriadis | Still Life with Watermelon | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2018.pdf) |
| AGLG 780 | Yannis Gaitis | Figure | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2018.pdf) |
| AGLG 784 | Christoforos Savva | Still Life (No Title) | 1957 | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2018.pdf) |
| AGLG 912 | Tristram Ellis | Saint Paul’s Column, Paphos | 1879 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 913 | John Thomson | Famagusta Harbour | 1879 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1004 | Athina N. Saripolou | Ground-floor Corridor | 1882 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1005 | Athina N. Saripolou | Piano Room | 1882 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1006 | Athina N. Saripolou | The Bedroom of My Sister, Penelope | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1007 | Athina N. Saripolou | The N. I. Saripolou Family Gathering with Music | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1008 | Athina N. Saripolou | My Father’s and Mother’s Bedroom | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1009 | Athina N. Saripolou | Bedroom | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1010 | Athina N. Saripolou | Entrance to the Stairs | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1011 | Athina N. Saripolou | The Living Room of My Father’s House | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1012 | Athina N. Saripolou | Bedroom with Blue Curtains | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1023 | Pericles Pantazis | Boats on the Scheldt River | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1024 | Pericles Pantazis | Self-portrait of the Artist | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 943 | Samuel Davenport | Constantinople: The Sultan Going to the Mosque | 1843 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 944 | William Henry Capone | State Prison of the Seven Towers, Looking over the Sea of Marmora | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 948 | Edward J. Whymper | Views in Constantinople | c. 1876 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 949A | Augustin François Lemaître | View of Pera, Constantinople | 1838 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 949B | Edward Finden | Constantinople from Pera | 1856 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 950 | John Chapman | Alexander the Great | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 951 | John Cochran | Victoria, Aug. 10th 1835 | 1836 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 952 | William Holl the Younger | Her Most Gracious Majesty Queen Victoria | c. 1838–1844 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 953 | Charles Edward Wagstaff | Her Majesty the Queen | 1838 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 954 | John Henry Robinson | Queen Victoria | 1847 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 955 | Unrecorded | Queen Victoria, Golden Jubilee Portrait | 1887 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 957 | Pierre Guillaume Metzmacher | Franz Joseph I, Emperor of Austria | 1867 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 958 | Matthew Dubourg | His Majesty King George III Returning from Hunting | 1820 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 959 | Unrecorded | Campaign Poster of Theodore Roosevelt | 1912 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 960 | François Müller | Alexander the Great Framed by War Scenes and Portraits of His Generals | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2019.pdf) |
| AGLG 1099 | Loukia Nikolaides-Vasiliou | Untitled | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1100 | Loukia Nikolaides-Vasiliou | Untitled | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1101 | Loukia Nikolaides-Vasiliou | Untitled | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1102 | Loukia Nikolaides-Vasiliou | Untitled | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1103 | Loukia Nikolaides-Vasiliou | Untitled | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1104 | Loukia Nikolaides-Vasiliou | Untitled | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.1 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.2 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.3 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.4 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.5 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.6 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.7 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.8 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.9 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.10 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.11 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1105.12 | Loukia Nikolaides-Vasiliou | Untitled watercolour sketch | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2020.pdf) |
| AGLG 1115 | Pericles Pantazis | Young Drinker | 1871 | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2021.pdf) |
| AGLG 1116 | Theodore Ralli | Resting by a Haystack | 19th century | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2021.pdf) |
| AGLG 1117 | Venetian School | The Queen of Cyprus, Caterina Cornaro, and Her Sister Cornelia | 16th century | Yes | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2021.pdf) |
| AGLG 1133 | Pericles Pantazis | Vase with Flowers and Apples | Creation date unknown | Pending | [Source](https://www.leventisgallery.org/assets/uploads/Annual-Report_2022.pdf) |
