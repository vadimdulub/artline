# Museum of Byzantine Culture — production expansion, 9 October 2026

Added **89 production review artworks**, taking the Thessaloniki museum from **31 to 120 catalogue records**. **83 additions have eligible creation dates**, taking that count from 30 to **113**. Five physical prints retain a 1900–1999 range crossing the cutoff, and one print remains undated. The real local catalogue remains unchanged at 27 records, 26 date-eligible.

- [89 delivered artworks](added-production-artworks-001.csv)
- [All 200 discovery decisions](all-source-decisions-001.csv)
- [Institution register with observation timestamps](production-institution-register-001.csv)
- [Verification and remaining research](delivery-001.json)

The source is the Greek Ministry of Culture’s [National Archive of Monuments](https://nationalarchive.culture.gr/), whose individual records explicitly identify Museum of Byzantine Culture provider 274 and museum location 6051. The museum’s [wooden icons](https://www.mbp.gr/en/collections/wooden-icons/) and [paper icons](https://www.mbp.gr/en/collections/chartines-eikones/) supplied independent collection and object context. Holdings are recorded separately from current display.

The initial 200 metadata records yielded 117 selected individual object reviews: 89 additions, 17 already catalogued, nine factual or scope holds and two further identity holds. Another 83 discovery records were deferred outside this selection. The public search reported 747 objects; 547 records remain beyond the first 200. This is a bounded selection, not a complete download.

The additions comprise 52 prints, 19 paintings (18 classified as icons), four carved sculptures, 11 fresco records and three floor-mosaic records. The current database lacks a mosaic type; those three use the permitted unknown category while preserving explicit floor-mosaic descriptions and source classification. Combined tomb-wall and floor-mosaic inventories each count once. The two-leaf iconostasis door counts once. Surviving central triptych panels and cut Joseph-cycle panels are described as fragments; complete parent works are not invented.

Physical edition dates control. A 1950 lithographic reproduction retains 1950 rather than the original engraving’s 1847 date; a 1936 copy retains its own date. Three explicitly dated 1977 impressions were excluded despite older plate dates in structured metadata. An uncertain 1846 inscription remains qualified. Prints with identical subjects retain distinct inventories and sheet measurements. A separate print with conflicting 1855/1885 dates remains held.

Three groups of loose decorative inlays and two fragments sharing parent inventory BT190 remain held. Two tomb records, BT170 and BT139, have overlapping descriptions, equal dimensions and the same findspot despite different inventories and dates; both remain held for stronger identity evidence.

Greek and English museum pages were compared where the English page for inventory 230 duplicated the narrative of a different Saint George engraving. Greek 230 describes an 1871 relic-procession lithograph; national 715484/127 corroborates the separate 1833 Saint George print. Inventory 230 was not added in this national selection. Its corrected source remains a follow-up lead.

Visual comparison confirmed a pre-existing duplicate: the unlinked “Brothers Sell Joseph into Slavery” image and the already linked “Joseph in the well” depict the same inventory 959. Neither was added again or merged in this pass. The new 958 and 956 cut panels depict different scenes. [Duplicate evidence and follow-up](poulakis-duplicate-review-001.json).

Twelve offline boundary checks passed. A successful Cloud SQL backup preceded atomic application and readback; replay verified the result with zero writes. All 85 protected existing records and 239 earlier production additions were preserved. No images, artist-authority links, publication changes or current-display claims were added.

This selected production phase totals **328 additions across four museums**. Historical local-only totals remain separate. Museum counts outside MBP retain their wave 104 audit timestamps; no new global count is claimed. MBP needs 80 more catalogue records, or 87 more date-eligible records, to reach 200. Continue at national search offset 200, review the remaining source gaps, and reconcile the confirmed existing duplicate before changing either record.
