# Seventeen additional Russian Museum artists — 7 October 2026

A read-only audit found **578 eligible existing artworks missing images** across seventeen creator authorities. Their complete, checksum-pinned WikiArt indexes yielded **68 exact-title metadata leads**, none previously reviewed in this local recovery. These are candidates for individual object/version review, not approved images. Discovery downloaded no images and made no database changes.

| Artist | Title leads |
| --- | ---: |
| Alexei Savrasov | 15 |
| Konstantin Somov | 7 |
| Léon Bakst | 1 |
| Mstislav Dobuzhinsky | 1 |
| Nikolai Ge | 7 |
| Pyotr Konchalovsky | 25 |
| Vasily Tropinin | 5 |
| Vasily Vereshchagin | 1 |
| Victor Borisov-Musatov | 1 |
| Viktor Vasnetsov | 2 |
| Vladimir Borovikovsky | 3 |

The [25-record Konchalovsky review](../local-wikiart-konchalovsky-images-20261007/README.md) compared thirty-one source originals against all twenty-five native references. The subsequent [Savrasov, Somov and Bakst review](../local-wikiart-savrasov-somov-bakst-images-20261007/README.md) adds fourteen images from twenty-three records, with nine other versions held. The [remaining seven-artist review](../local-wikiart-russian-next-final-leads-images-20261007/README.md) adds seven images from the final twenty records, including three matches found through eight additional individually selected source pages. **All 68 leads are reviewed: 41 attached, 27 unresolved and zero pending.** One native creator conflict remains unchanged; unknown source dates, biography discrepancies and source-view limitations are recorded individually. The [live queue checkpoint](recovery-progress.json) verifies every reviewed outcome and pending eligible gap. Nine retained source watermarks and fourteen source-view qualifications are documented individually. Unknown local artist life fields are retained; source biographies are evidence, not catalogue edits. Unknown artwork/source dates and repeated titles require individual assessment.

The [query plan](scoped-query-plan.json) uses the institution index and a bounded institution artwork lookup, then indexed artist-link, artist and identifier lookups. This is evidence from the current local catalogue, not a ten-million-row load test. Eligible artworks retain documented museum connection and review state. Other missing records without exact-title leads are not claimed as reviewed.

[Discovery and source pins](discovery.json) · [Eligible gaps](eligible-gaps.json) · [Combined recovery](../local-image-recovery-20261006/README.md)
