# Individual WikiArt review preserving incomplete catalogue data — 6 October 2026

**Ten images are saved locally and attached to existing local artworks.** Nine retain unknown creation dates and PostgreSQL creation scope `review`; the tenth retains its existing circa-1819 date. All ten remain review records. This image-only operation fills no dates, changes no creator links or holdings, and authorizes no publication.

| Existing artwork | Individually reviewed identity |
| --- | --- |
| Titian, *Danaë* | Q3701422 / KHM GG_90; reclining figure, attendant, dish and storm cloud match. |
| Joachim Patinir, *The Baptism of Christ* | Q18686599 / KHM GG_981; figures, preaching group and distinctive rock landscape match. |
| Raphael, *Saint Margaret and the Dragon* | Q3464523 / KHM GG_171; saint, dragon and rocky setting match. |
| Penry Williams, *Sgwd Gwladys, Vale of Neath* | Q110249833 / NMW A 526; waterfall, layered rock, trees and sky match. Existing circa-1819 date retained. |
| Maarten van Heemskerck, *The Triumphal Procession of Bacchus* | Q25442947 / KHM GG_990; figures, temple, animals and foreground objects match. |
| Pieter Bruegel the Elder, *The Suicide of Saul* | Q3976754 / KHM GG_1011; rocky ledge, army, fortress and coast match. |
| Jan van Eyck, *Portrait of Cardinal Niccolò Albergati* | Q3399498 / KHM GG_975; face, collar and red robe match. |
| Aleksey Antropov, *Portrait of Catherine II* | Q123000632 / Tretyakov Ж-10; seated figure, sceptre, crown, robe, throne and columns match. |
| Hieronymus Bosch, *The Last Judgment* | Q1387483 / Academy GG-579-581; all three interior panels match. Exterior wings are not shown. |
| Giovanni Bellini, *Naked Young Woman in Front of the Mirror* | Q3766167 / KHM GG_97; figure, mirror, headdress, landscape opening and textile match. |

The selection completes individual review of the ten date/identity leads deferred by the [prior-delivery audit](../local-wikiart-prior-delivery-audit-20261006/README.md). Current artwork authorities identify the existing local creators and inventories. Current WikiArt pages, creator profiles, source dates, image identities and actual rights labels were independently checked. Every application image was visually compared against a freshly captured, exact-artwork authority-linked reference photograph. Those comparison photographs remain private and were not attached.

The Penry Williams and Antropov prior research used different painter UUIDs. Fresh artwork creator claims and the existing local creator's verified WikiArt profile resolve image identity without merging or changing artist records. Cardiff's local institution has no Wikidata ID; its exact name and official website match the current Q1321874 collection authority. That evidence is recorded separately, and the institution's blank ID and all other fields remain unchanged.

The nine unknown-date cases received individual pre-1970 source-scope review. WikiArt's dates are retained as source assertions alongside the other authority evidence, not copied into the catalogue. Antropov's source date of 1760, for example, remains explicitly WikiArt's assertion while the catalogue date stays unknown. No general eligibility or publication gate was relaxed.

Bosch's image has an explicit **Three interior panels** view label, accessible text and attribution note. The supplied white gaps remain intact; the image makes no claim to show the exterior wings or a complete front-and-back reproduction.

All ten originals were reused only after checking their archived source bytes, original download receipts and current source-image identity. Newly generated application JPEGs retain the full source frame and are at most **92,540 bytes**. All ten WikiArt pages assert general public-domain status. Those actual labels and credits remain separate from the user's [explicit WikiArt source approval](../../ARTLINE_IMAGE_USE.md).

The local transaction checked unchanged records and missing images, saved locked preimages, then added only media and image associations. Verification checked all ten files, originals, complete stored evidence, creator links, holdings, existing identifiers and review states, including all nine preserved unknown dates and the unchanged Cardiff institution. All 101 identity, source, scope and view controls passed. The final test harness treats an omitted required view key as a rejected malformed candidate; the earlier harness stopped on that expected exception. No invalid candidate was accepted and no database test fixtures were used.

No production changes were made. This operation has no new HTTP delivery receipt following the earlier local server timeouts.

Application images: `apps/web/public/assets/artworks/imported/local-wikiart-catalogue-review-images-20261006/`.

Originals, private comparisons, review sheets and preserved procedures: `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-wikiart-catalogue-review-images-20261006/`.

Locked preimages: `/Users/vadimdulub/Library/Application Support/Artline/backups/local-wikiart-catalogue-review-images-20261006/`.

- [Attached images and paths](attached-images.csv)
- [Individual version and source-scope decisions](object-version-review.json)
- [Visual review](visual-review.json)
- [Triptych view decision](view-scope-review.json)
- [Cardiff identity evidence](institution-identity-review.json)
- [Validation controls](guard-verification.json)
- [Unknown-date and identity preservation verification](catalogue-review-database-verification.json)
- [Complete source and database verification](source-rights-verification.json)
- [Operation counts](report.json)
- [Combined recovery report](../local-image-recovery-20261006/README.md)
