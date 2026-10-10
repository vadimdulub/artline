# Musée Girodet — production museum expansion, 9 October 2026

Added **50 new production review artworks**, bringing this museum from **89 to 139 linked works**. Dates within the pre-1971 scope increased from **82 to 113**: 31 additions have eligible dates, 11 are undated and eight retain Joconde's twentieth-century range (1901–2000). Creator lifetimes were not substituted for artwork dates. The real local catalogue remains unchanged at 89 linked / 82 eligible works.

- [50 delivered artworks](added-production-artworks-001.csv)
- [All 205 source-record decisions](all-source-decisions-001.csv)
- [Production institution register and explicit count gaps](production-institution-register-001.csv)
- [Verification and museum counts](delivery-001.json)
- [Reviewed source and identity evidence](editorial-reviewed-001.json.gz)

The official [Ministry of Culture museum record](https://pop.culture.gouv.fr/notice/museo/M0284) identifies the collection. Its current Joconde dataset returned 205 museum-scoped records in two bounded pages. Of these, 84 were already catalogued, 50 were accepted, four remain held after individual review and 67 require separate source, physical-object or scope review. No exhaustive artwork or image download was performed.

New works include Girodet drawings and oil studies, Luce drawings and a lithograph, Charpentier's plaster portrait relief and individually inventoried Triqueti models and tarsias. Counterproofs, preparatory works and recto/verso sheets retain their identities; three head studies on one sheet count as one object. Museum holdings do not imply current display, physical custody or legal ownership, including historical usufruct qualifications. Matching confidence is an editorial assessment, not a calibrated probability.

The four individual holds are the two Janssens gallery pendants (one ambiguous existing record lacks an inventory), the full-size Ferdinand d'Orléans plaster (1842/1844 source conflict), and an anonymous portrait with conflicting support descriptions. Bound sketchbooks and separately described pages were not multiplied. The missing Circassienne, deposits, photographs, correspondence, lithographic stone matrix and other scope cases remain in the full ledger. Historical records were preserved.

Twelve offline date and source-boundary tests passed. The batch used a pinned plan, successful Cloud SQL backup **1791542644400**, an atomic transaction with readback, unchanged-existing-record comparisons and a zero-write replay. The review examined 4,136 existing production artworks and 8,928 citations. No new images, artist-authority links, publication or current-display claims were added. One approved WikiArt comparator image was inspected solely for identity research.

The target remains unfinished. Girodet needs another **61 linked works** to reach 200, or 87 more with eligible dates to reach 200 eligible works. The complete production institution directory is retained, but a fresh global count refresh is **not complete**: both the whole-catalogue query and a bounded 50-institution count query exceeded their 120-second statement timeout. Exact Girodet counts were verified separately. The register labels historical local counts explicitly; they are not presented as current production counts. Further count-query diagnostics and representative load testing remain open.


Earlier provider-access holds and research queues remain in the [wave 100 checkpoint](../augustiner-20261009/delivery-checkpoint-001.json). Public Girodet guides were accessible; the teacher PDF lead returned 404. Continue independent object sources and other underfilled museums without retrying held providers or creating quota placeholders.
