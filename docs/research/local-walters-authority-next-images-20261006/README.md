# Further Walters authority follow-up — 6 October 2026

**Forty CC0 photographs were saved locally and attached to forty existing missing-image artworks.** The selected date bounds span 1867–1888. Seven source photographs are archival monochrome reproductions, explicitly identified in the database attribution. All forty artworks remain in review with their catalogue metadata unchanged.

The exact museum inventories, titles, dates and existing creator authorities were checked against current native pages and pinned museum object/creator records. Seven Fortuny works use the native name Mariano Fortuny and the existing catalogue name Marià Fortuny; the same stable museum person ID and reciprocal object membership resolve the difference. No artist records or creator links were changed.

Inness's *Visionary Landscape* (37.2775) retains the exact date phrase `1867/1880`, its existing range and the native authority's identical date bounds. The museum describes the current work as a surviving fragment reworked after damage to a larger painting. The photograph represents this catalogue object, not the former complete larger painting. The date parser permits this exact slash-date case only; it does not normalize arbitrary slash dates.

Six treatment-view filename exceptions were inspected individually: Bouguereau's *The Cherry Picker*, two Baker portraits, Jones's *Hunting Scene*, and Fortuny's *Faithful Friends* and *Don Quixote*. The selected views show clean full fronts without calibration targets. The latter two use the museum's before-treatment front photographs.

Two initial image URLs returned empty bodies. Each was replaced by a licensed full front from the same exact object page: Fortuny's *Arab Fantasia* uses a colour photograph, and Rico's *La Huerta del Retiro, Seville* uses an archival monochrome photograph. The empty responses and previous selection evidence remain private and in `history/before-empty-resource-fallback/`; neither empty file was attached.

Gifford's *The Arch of Nero (Ruined Aqueduct near Tivoli)* has a 7,959 × 8,914-pixel source JPEG exceeding the ordinary decoder limit. Only this file's pinned SHA-256 is permitted to use JPEG decoder reduction before loading pixels. The reduced decode is bounded to 1,990 × 2,229, followed by the ordinary full-frame JPEG compression. The original source bytes remain intact. A changed-byte negative control still triggers the default size guard. No generic pixel-limit exemption or crop was introduced.

Files, original hashes, database links, complete stored rights evidence and unchanged artist authorities passed verification. Four negative controls cover altered object identity/date indexing, an incorrect museum person ID and changed large-source bytes. No database fixtures or catalogue records were created. Production was not changed. HTTP delivery has no new receipt following the earlier local-server timeout.

Application JPEGs use `apps/web/public/assets/artworks/imported/local-walters-authority-next-images-20261006/`, with every image below 100,000 bytes. Originals, empty responses and final contact sheets use `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-walters-authority-next-images-20261006/`; locked preimages use the corresponding `backups/` operation directory.

- [Visual decisions](visual-review.json)
- [File and database verification](verification.json)
- [Exact native rights evidence](source-rights-verification.json)
- [Unchanged artist authorities](creator-authority-verification.json)
- [Large-source decoder plan](large-source-decoder-plan.json)
- [Validator controls](validator-controls.json)
- [Operation counts](report.json)
- [Latest combined checkpoint](../local-image-recovery-20261006/README.md)
