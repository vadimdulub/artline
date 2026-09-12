# Research findings and unresolved candidates

The [session progress ledger](PROGRESS.md) is the live checkpoint. The [100-painter source-review checklists](review-v1/PAINTERS.md) distinguish actual source decisions from automated inventory checks. The [inventory snapshot](inventory-v1/PAINTERS.md) contains every popular-painter artwork as of its export; it predates the later Athens and Repin additions.

## Athens: checked individually

- Five Goulandris paintings imported and API-verified: [Kandinsky, Both Striped](https://goulandris.gr/en/artwork/kandinsky-wassily-both-striped), [Klee, Dynamics of a Head](https://goulandris.gr/en/artwork/klee-paul-dynamics-of-a-head), [Monet, Rouen Cathedral in the Morning (Pink Dominant)](https://goulandris.gr/en/artwork/monet-claude-rouen-cathedral-pink-dominant), [Ernst, While the Earth Sleeps](https://goulandris.gr/en/artwork/ernst-max-while-the-earth-sleeps), [Miró, The Grasshopper](https://goulandris.gr/en/artwork/miro-joan-the-grasshopper). Each notice explicitly identifies the Athens branch. No accession number is published, so none is invented; a stable source-page identifier is retained. No image grant was found. The foundation's copyright notice and [visitor reproduction conditions](https://goulandris.gr/en/visitor-terms) are not an open licence.
- Miró title collision resolved: the two existing *The Grasshopper* records are Rudy Pozzatti prints dated 1954, not this 1926 painting. Strong source identifiers are checked globally; generic shared titles do not imply identity.
- [El Greco, St Peter](https://www.nationalgallery.gr/en/artwork/st-peter/): added, accession Π.9027; approximate range 1600–1607, represented as `circa_range`. Preview rejected the earlier `circa` single-year label, before mutation. New `athens-national-v3` passed preview, import, preservation and API checks. Other existing *Saint Peter* records are different creators, media or dates; no El Greco equivalent was found.
- [El Greco, Veil of Saint Veronica](https://goulandris.gr/en/artwork/el-greco-the-holy-face): deferred while the literal early-1580s date is mapped explicitly; not silently narrowed to an invented exact interval.
- [Chagall, Portrait of E.B.G.](https://goulandris.gr/en/artwork/chagall-marc-portrait-of-elise-goulandris): 1969, oil on canvas, collection connection confirmed, but the notice explicitly says not currently displayed and gives no current branch. Collection membership is not a substitute for branch-level holding evidence. Image credit names ADAGP/OSDEETE; no download.
- Bonnard's *Getting Out of the Bath* was inspected, but Bonnard is not currently in the popular cohort. Preserved as an out-of-batch lead, not silently added to this task's cohort.

## El Greco: further Greek and regional leads

- National Gallery [Entombment](https://www.nationalgallery.gr/en/artwork/the-entombment-of-christ/), Π.9979, circa 1568–1570: exact direct-creator page; additional capture/import still queued.
- National Gallery [Concert of the Angels](https://www.nationalgallery.gr/en/artwork/the-concert-of-the-angels/), Π.152, circa 1608–1614: the museum identifies it as a separated upper section of an Annunciation. Retain fragment/parent relationship before import; do not invent an independent complete composition.
- Historical Museum of Crete [collection page](https://www.historical-museum.gr/en/collections/el-greco) gives Baptism 1567, while its [visitor leaflet page](https://www.historical-museum.gr/en/visit/filladio-istorikoy-moiseioi-kritis) gives 1569. Deferred conflict, not a 1567–1569 interval synthesized from disagreement. *View of Mt Sinai* is consistently listed as 1570 and remains an individual-source capture lead.
- [Modena triptych national catalogue](https://catalogo.beniculturali.it/detail/HistoricOrArtisticProperty/0800675920) uses an attribution qualifier. Existing local record needs attribution comparison, not another import; panels and reverse scenes are not six automatically separate artworks.
- J.F. Willumsens Museum's El Greco *Adoration of the Shepherds* remains a regional Denmark lead. Search results in historic notebooks are not enough for an exact current object import.

## Russian collection follow-up

Five Repin notices are captured and selected in `repin-v1`; consult apply/verification receipts before counting them as imported. The [Russian Museum's terms](https://rusmuseumvrm.ru/terms/index.php?lang=en) require written permission to obtain and publish reproductions. No museum images were downloaded; robots-disallowed image/full-image paths are excluded from the collector.

- *Storm on the Volga*, Ж-4054: source says started in 1870 and repainted later, 1891 uncertain. Deferred; do not flatten two creation phases into an exact single year.
- Malevich's [Black Square, Ж-9484](https://rusmuseumvrm.ru/data/collections/painting/19_20/zh_9484/index.php?lang=en) is circa 1923, not the Tretyakov 1915 version. The source artist lifespan begins 1878; local authority begins 1879. This discrepancy needs explicit authority review. Neither birth date nor image permission is changed automatically.

## Required follow-up

[Updated continuation prompt](../../POPULAR_RESEARCH_CONTINUATION_PROMPT.md): after the current research task, audit **actual UI picture visibility**, starting with Monet. Database image counts do not establish that users can see images. Trace API results, pagination, media references, permissions and asset delivery before deciding whether the issue is absent images or application behavior.
