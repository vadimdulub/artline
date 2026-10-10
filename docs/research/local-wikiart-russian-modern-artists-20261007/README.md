# Further Russian Museum artist discovery — 7 October 2026

A read-only, artist-scoped audit found **240 eligible missing-image review records** across seven existing artist authorities. Checksum-verified Russian WikiArt indexes provide **26 exact normalized-title leads**. These are metadata candidates, not accepted physical versions. Discovery downloaded no images and changed no database records. Previously reviewed six-artist and eight-artist queues remain separate.

| Artist | Eligible gaps | Exact-title leads |
| --- | ---: | ---: |
| Alexandre Benois | 91 | 9 |
| Boris Grigoriev | 5 | 0 |
| Kazimir Malevich | 32 | 14 |
| Mikhail Larionov | 19 | 0 |
| Natalia Goncharova | 57 | 0 |
| Pavel Filonov | 25 | 3 |
| Wassily Kandinsky | 11 | 0 |

Artist IDs, stored Wikidata identifiers, life fields and source indexes are frozen. Source names, current creator crosswalks, exact native objects and photographs still require individual review. Different versions, shared titles, source-date discrepancies and unknown source dates are not resolved by a title match. Non-exact-title records remain open for separate research.

The [query plan](scoped-query-plan.json) starts with the seven artist IDs through `artwork_artists_artist_work_idx`, followed by primary-key artwork/artist/institution lookups and indexed identifier lookups. No global artwork CTE is used. This is a real-catalogue read-only plan check, not proof of representative ten-million-row performance.

[Discovery and pinned indexes](discovery.json) · [Scoped gap snapshot](eligible-gaps.json) · [Combined recovery](../local-image-recovery-20261006/README.md)

The [Benois review](../local-wikiart-benois-images-20261007/README.md) attached eight images across nine records. The [Malevich and Filonov review](../local-wikiart-malevich-filonov-images-20261007/README.md) attached thirteen more across fifteen records. The [Suprematism review](../local-wikiart-malevich-suprematism-images-20261007/README.md) resolved the last two inventories after comparing five source images. **All 26 leads are reviewed: 23 attached, three unresolved and zero pending.** The unresolved works are Benois’s original alphabet cover, Malevich’s Black Square and Filonov’s Narva Gates; the selected source photographs show different versions. The [live checkpoint](recovery-progress.json) verifies all 26 outcomes. Discovery itself made no database changes; separate image operations hold the write receipts. Non-exact-title catalogue gaps remain open for separate research.
