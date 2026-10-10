# Chinese paintings, scrolls, prints and murals — 8 October 2026

Researched **3,832 source records** and retained **3,386 pre-1971 or unresolved-date candidates** from **16 museums**. **446 explicitly later works are excluded.** The wider coverage map tracks **34 priority museums, galleries and mural sites**; it is not a claim that all are already represented in Artline.

Found **938 priority image candidates** with source-backed pre-1971 dates/periods and open image labels, after omitting obvious loans and Cleveland part/ensemble records. Taipei contributes **169 additional records with open image tiers** whose attribution, date, view and resolution require selection. These counts describe research, not approved/visually reviewed attachments.

Separately documented **162 painted surfaces in 12 Mogao caves**. Cave containers, walls, individual scenes, repainted layers and detached panels are kept distinct. Surfaces are not added to the artwork-record total.

## Files

- [Artwork register](artwork-register.csv): every record, museum, source title/creator/date, object identity, source page, image URL, rights label and decision.
- [Priority images](priority-images.csv): the conservatively dated open-image shortlist.
- [Museum coverage](museum-coverage.json): all 34 target collections with actual research depth, failures and remaining gaps.
- [Dunhuang surfaces](dunhuang-surfaces.json): cave/surface references and exact captured descriptions.
- [Priority mural scenes](priority-mural-scenes.json): nine named scene leads, including the Nine-Coloured Deer, Mount Wutai and Medicine Buddha tableaux.
- [Selected highlights](selected-highlights.json): 20 separately reviewed captions, including two explicit later-work exclusions.
- `all-records.json.gz`, `in-scope-or-review.json.gz`, provider files and `captures/`: structured evidence and hashed source responses.
- [Verification](verification.json), [summary](summary.json), and [read-only local audit](local-audit.json).

## Individual-record coverage

| Museum | Retained candidates |
|---|---:|
| The Cleveland Museum of Art | 805 |
| National Art Museum of China | 793 |
| Minneapolis Institute of Art | 756 |
| Art Institute of Chicago | 488 |
| Ashmolean Museum | 202 |
| National Palace Museum, Taipei | 169 |
| Hong Kong Museum of Art | 92 |
| The Metropolitan Museum of Art | 63 |
| Hong Kong Heritage Museum | 6 |
| Palace Museum, Beijing | 5 |
| Hunan Museum | 2 |
| Tianjin Museum | 1 |
| Shaanxi History Museum | 1 |
| Harvard Art Museums | 1 |
| Musée Guimet | 1 |
| Tokyo National Museum | 1 |

## Selection and identity decisions

- Chinese art worldwide is included: scroll and album painting, ink landscapes, flowers/birds, portraiture, calligraphy, prints, ancient silk pictures and Buddhist/Daoist murals. Hong Kong China-trade records can have European makers; no Chinese nationality is invented.
- Exact source dates are retained. Anonymous creators, traditional/qualified attributions, missing dates and unknown accessions remain unknown or qualified. Artist lifespans, excavation years, webpage dates and digital-resource dates are not creation years.
- Palace Museum *Night Revels of Han Xizai* is explicitly a Song copy dated 1163–1224, not the lost Five Dynasties original. *A Thousand Li* retains the source's qualified discussion of 1113.
- Shaanxi *Polo Game* is a Tang work excavated in 1971. Hunan's exercise chart was excavated in 1973; neither excavation date disqualifies the ancient artwork. The chart's 44 figures are one work.
- The National Museum of China's *Founding Ceremony* page discusses the 1953 original, a 1972 copy and 1979 revision. Its reproduction is held for version resolution and is not included in the artwork shortlist.
- Penn's Medicine Buddha panels and Nelson-Atkins' transport sections must not inflate counts of complete mural compositions. Harvard and Guimet Dunhuang silk banners are portable paintings, not frescoes.
- CC0/PDM labels come from the individual museum records. Taipei explicitly offers 1-megapixel CC0 and 6-megapixel CC BY 4.0 tiers; an image tier is not selected merely because the page has a preview. Other museum photographs retain unresolved permission status. WikiArt remains approved under existing project policy; this pass used museum records directly.
- Holding evidence does not establish current display. No on-view claim was created. No candidate is automatically published.

## Coverage gaps and limits

The deepest enumerated scans cover Cleveland, Chicago, Minneapolis, the Met, Taipei, NAMOC, Hong Kong Museum of Art and the Ashmolean. Additional exact highlights cover Beijing, Tianjin, Hunan, Shaanxi, Harvard, Guimet, Tokyo and Hong Kong Heritage Museum. Wider source/discovery coverage includes Shanghai, Liaoning, Nanjing, Zhejiang, Shanxi, Yongle Palace, Boston, Freer/Sackler, Princeton, San Francisco, British Museum, V&A, Cernuschi, ROM and Penn; these are not all import-ready.

Some providers returned access restrictions, unavailable pages or timeouts; retrieval stopped at access restrictions. The Met capture is partial (63 accepted object records) after its API returned 403. Shanghai's search service did not return usable results. Liaoning/Nanjing and other dynamic or unavailable sites remain important gaps; a museum homepage does not count as artwork coverage.

The local audit compared exact native object IDs and institution-scoped accession numbers. A missing local match does not prove a new production identity. The existing production proxy was unavailable, so production deduplication remains outstanding. No catalogue records, attachments, publication states or application code were changed; no images were downloaded, no commits or deployments made.

This is a bounded research pass. Source result totals, captured candidates and actual catalogue additions are separate quantities. Research scripts are `ops/research-chinese-art-20261008.py`, `ops/research-chinese-museums-20261008.py` and `ops/report-chinese-art-20261008.py`.
