# Rhodes — preferred target reached, 9 October 2026

Added **43 production review artworks** and linked **one existing artwork** to the Municipal Art Gallery of Rhodes / Museum of Modern Greek Art. The museum now has **216 catalogue works**, including **209 with eligible creation dates**, up from172/166. Both200-work targets are reached. The real local catalogue remains unchanged at3linked works/1date eligible.

- [43 added artworks](added-production-artworks-001.csv)
- [Existing-work holding link](linked-existing-artworks-001.csv)
- [All100 source decisions](all-source-decisions-001.csv)
- [Dated museum register](production-institution-register-001.csv)
- [Verification and next work](delivery-001.json)

The [official museum collection](https://portal.mgamuseum.gr/) supplies individual identities,inventory numbers,creation statements and holdings. The existing [institution reconciliation](../rhodes-20261009/institution-reconciliation-001.json) remains applicable. A holding does not assert current display,venue,custody or legal ownership.

The100 reviewed records yielded43 new works,one existing-work link,41 unknown-date research leads and15 explicit post1970 exclusions. Across the three Rhodes selections,380 of1502 reported native objects have individual metadata reviewed;1122 remain unexamined. Reaching the target does not imply complete museum coverage. All earlier date/version holds remain in their source ledgers.

New works include Vasiliou painted manuscript sheets; Vitsoris,Vourloumis,Vyzantios,Galanis,Germenis,Gioldasis,Gaitis and Engonopoulos paintings; Giallinas watercolour; Chalepas pencil sheets; and Zepos drawings and paintings. One double-sided Chalepas sheet counts as one physical artwork. The literal qualified attribution “Σπυρίδων Βικάτος(;)” remains unresolved. Material discrepancies in Galanis and Zepos records are explicit; missing media remain unknown. Exact1970 is eligible. Exhibition dates,depicted events and biography errors do not date the physical works.

Twelve selected reference images were inspected. [Boat with Sails](https://www.wikiart.org/en/periklis-vyzantios/boat-with-sails) is the same work as museum1071,so its existing record receives only the holding. Its existing unknown date remains unchanged; museum1962 is retained as citation evidence. Hydra1072 is visually different from [Ydra1959](https://www.wikiart.org/en/periklis-vyzantios/ydra-1959) and three other harbour compositions. Giallinas’s Pontikonisi differs from the National Gallery landscape. Three similar Zepos life drawings depict different models and poses. Images and observations are pinned in [visual assessment](visual-assessment-001.json); no images were attached or changed.

Eighteen offline tests passed. Cloud SQL backup1791563475112 preceded the atomic write; readback verified all43 new records and the single existing-work link, and replay made zero writes. The289 protected existing records changed only by that reviewed holding/citation; all777 prior production additions were preserved. Existing metadata,dates,images and statuses were unchanged. Identity checks used995 bounded candidates,1828 citations and129 focused full-row comparators. Their query plans are recorded; this is not a10million-row load proof.

The selected production phase now totals **820 additions and one existing-work link across six museums**, separate from historical local work. Only Rhodes counts were refreshed. The full every-museum goal remains active.

Next is Nikos Kazantzakis Museum. [Discovery evidence](next-source-discovery-001.json.gz) captures30 index leads from each of two public catalogues: [144 mixed art/object records](https://www.searchculture.gr/aggregator/portal/collections/DigKazantzakis?language=en) and [2772 theatre archive records](https://www.searchculture.gr/aggregator/portal/collections/Kazantzakis). These are source counts,not eligible-artwork counts. The [museum repository](https://repository.kazantzaki.gr/) exposes art and theatre categories. Review actual physical designs and drawings,distinguish performance dates and related-person fields,and preserve unknown creators. The main website archive page returned403 and remains on hold; it was not retried. No archive-wide metadata or image download was performed.
