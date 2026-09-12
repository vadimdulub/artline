# SMK popular-artist image follow-up

11 September 2026. This is a bounded image investigation of 41 existing painting records for 18 popular artists, not a new catalogue import or a completed painter/oeuvre review.

## Result

Thirteen authentic museum images were attached to existing artworks by seven artists: Modigliani, Munch, Tiepolo, Cranach, Poussin, Rubens and Rembrandt. Sixteen notices report `has_image=false`; eleven report an image but supply no downloadable IIIF URL. One additional image candidate was deferred for dating review. No replacement URL was guessed. No artwork, artist, holding, favourite, museum-highlight or publishing status was added or changed.

The [SMK API documentation](https://www.smk.dk/en/article/smk-api/) describes the exact-object endpoint used. Each capture came from `https://api.smk.dk/api/v1/art/?object_number={inventory}&lang=en`. The selected notices explicitly identify their images with the [Public Domain Mark](https://creativecommons.org/publicdomain/mark/1.0/). Only that object-specific evidence cleared a download. SMK's [supplemental-data explanation](https://www.smk.dk/en/article/where-does-extra-data-on-smk-open-come-from/) distinguishes enriched data; this pass used the museum catalogue, not the separate generated-enrichment service.

Every new derivative is below 100,000 bytes, with no additional composition crop. Source image filenames can include “crop” or “reconstructed”; these are museum-provided reproductions, not evidence that the original physical painting was independently inspected. Retained aliases include Munch's former title *Workers Coming Home* and Rembrandt's former title *The Crusader*; matching the museum's previous-title field did not silently replace editorial titles.

## Exact-object outcomes

The source check date is 2026-09-11. “No photograph” means absent from this API notice, not absent everywhere. Existing museum associations do not establish current display.

| Artist | Artwork / museum inventory | Image outcome |
|---|---|---|
| Alfred Sisley | [The Waterworks at Bougival: KMS3272](https://open.smk.dk/artwork/image/KMS3272) | No photograph supplied by this API notice. |
| Amedeo Modigliani | [Alice: KMSr145](https://open.smk.dk/artwork/image/KMSr145) | Attached; bytes, checksum, rights evidence and API access verified. |
| Anthony van Dyck | [Sketch for The Supper at Emmaus: KMS3223](https://open.smk.dk/artwork/image/KMS3223) | Image flagged present, but no IIIF download URL supplied. Dating basis also requires review: broad bounds match birth + 15 through death; note supplies no explicit year. |
| Anthony van Dyck | [Virgin and Child with Saint Francis: KMSsp242](https://open.smk.dk/artwork/image/KMSsp242) | Image flagged present, but no IIIF download URL supplied. Dating basis also requires review: broad bounds match birth + 15 through death; note supplies no explicit year. |
| Anthony van Dyck | [The Entombment of Christ: KMSsp243](https://open.smk.dk/artwork/image/KMSsp243) | Image flagged present, but no IIIF download URL supplied. Dating basis also requires review: broad bounds match birth + 15 through death; note supplies no explicit year. |
| Camille Pissarro | [Landscape near Pontoise. A Peasant Walking along the Path: KMS3573](https://open.smk.dk/artwork/image/KMS3573) | No photograph supplied by this API notice. |
| Camille Pissarro | [Woodland scene. Spring: KMS3574](https://open.smk.dk/artwork/image/KMS3574) | No photograph supplied by this API notice. |
| Camille Pissarro | [View of Pont-Neuf with Statue of Henri IV: KMS4323](https://open.smk.dk/artwork/image/KMS4323) | No photograph supplied by this API notice. |
| Edgar Degas | [Village Street. Saint-Valéry-sur-Somme: KMS4324](https://open.smk.dk/artwork/image/KMS4324) | No photograph supplied by this API notice. |
| Edvard Munch | [Death Struggle: KMS3325](https://open.smk.dk/artwork/image/KMS3325) | Image flagged present, but no IIIF download URL supplied. |
| Edvard Munch | [Workers Coming Home: KMS3823](https://open.smk.dk/artwork/image/KMS3823) | Attached; bytes, checksum, rights evidence and API access verified. |
| Edvard Munch | [Portrait of Professor Daniel Jacobson: KMS4179a](https://open.smk.dk/artwork/image/KMS4179a) | Image flagged present, but no IIIF download URL supplied. |
| Eugène Delacroix | [Peonies: KMS1956](https://open.smk.dk/artwork/image/KMS1956) | No photograph supplied by this API notice. |
| Giovanni Battista Tiepolo | [Apollo and Marsyas: KMS4548](https://open.smk.dk/artwork/image/KMS4548) | Attached; bytes, checksum, rights evidence and API access verified. |
| Giovanni Battista Tiepolo | [The Brazen Serpent: KMS6683](https://open.smk.dk/artwork/image/KMS6683) | Image flagged present, but no IIIF download URL supplied. Dating basis also requires review: broad bounds match birth + 15 through death; note supplies no explicit year. |
| Gustave Courbet | [Fighting Stags in a Forest: KMS1957](https://open.smk.dk/artwork/image/KMS1957) | Image flagged present, but no IIIF download URL supplied. Dating basis also requires review: broad bounds match birth + 15 through death; note supplies no explicit year. |
| Gustave Courbet | [The Interior of a Forest: KMS3436](https://open.smk.dk/artwork/image/KMS3436) | Image flagged present, but no IIIF download URL supplied. Dating basis also requires review: broad bounds match birth + 15 through death; note supplies no explicit year. |
| Honoré Daumier | [Don Quixote and Sancho Panza Resting Beneath a Tree: KMS3268](https://open.smk.dk/artwork/image/KMS3268) | No photograph supplied by this API notice. |
| Jean-Baptiste-Camille Corot | [Study from Rome: KMS1804](https://open.smk.dk/artwork/image/KMS1804) | No photograph supplied by this API notice. Dating basis also requires review: broad bounds match birth + 15 through death; note supplies no explicit year. |
| Lucas Cranach the Elder | [Virgin and Child Adored by the Infant St John: KMS3674](https://open.smk.dk/artwork/image/KMS3674) | Attached; bytes, checksum, rights evidence and API access verified. |
| Lucas Cranach the Elder | [The Judgement of Paris: KMSsp718](https://open.smk.dk/artwork/image/KMSsp718) | Attached; bytes, checksum, rights evidence and API access verified. |
| Lucas Cranach the Elder | [Portrait of Martin Luther: KMSsp720](https://open.smk.dk/artwork/image/KMSsp720) | Attached; bytes, checksum, rights evidence and API access verified. |
| Lucas Cranach the Elder | [Melancholy: KMSsp722](https://open.smk.dk/artwork/image/KMSsp722) | Attached; bytes, checksum, rights evidence and API access verified. |
| Lucas Cranach the Elder | [Portrait of the Elector John Frederic the Magnanimous of Saxony (1503-1554): KMSsp725](https://open.smk.dk/artwork/image/KMSsp725) | Image flagged present, but no IIIF download URL supplied. |
| Lucas Cranach the Elder | [Portrait of the Electress Sibyl of Saxony (1510-1569): KMSsp726](https://open.smk.dk/artwork/image/KMSsp726) | Attached; bytes, checksum, rights evidence and API access verified. |
| Lucas Cranach the Elder | [The Mystic Marriage of Saint Catherine: KMSsp731](https://open.smk.dk/artwork/image/KMSsp731) | Attached; bytes, checksum, rights evidence and API access verified. |
| Nicolas Poussin | [The Testament of Eudamidas: KMS3889](https://open.smk.dk/artwork/image/KMS3889) | Attached; bytes, checksum, rights evidence and API access verified. |
| Nicolas Poussin | [Joseph Interprets Pharaoh's Dream: KMSsp691](https://open.smk.dk/artwork/image/KMSsp691) | Image flagged present, but no IIIF download URL supplied. Dating basis also requires review: broad bounds match birth + 15 through death; note supplies no explicit year. |
| Paolo Veronese | [The Marriage of St Catharine: KMSsp149](https://open.smk.dk/artwork/image/KMSsp149) | Image flagged present, but no IIIF download URL supplied. Dating basis also requires review: broad bounds match birth + 15 through death; note supplies no explicit year. |
| Paul Gauguin | [Garden in Snow: KMS2019](https://open.smk.dk/artwork/image/KMS2019) | No photograph supplied by this API notice. |
| Paul Gauguin | [Figures in a Garden: KMS3098](https://open.smk.dk/artwork/image/KMS3098) | No photograph supplied by this API notice. |
| Paul Gauguin | [Landscape from Pont-Aven, Brittany: KMS3142](https://open.smk.dk/artwork/image/KMS3142) | No photograph supplied by this API notice. |
| Paul Gauguin | [Still Life with Flowers: KMS3147](https://open.smk.dk/artwork/image/KMS3147) | No photograph supplied by this API notice. |
| Paul Gauguin | [Woman Sewing: KMS3453](https://open.smk.dk/artwork/image/KMS3453) | No photograph supplied by this API notice. |
| Paul Gauguin | [Winter Scenery: KMS3567](https://open.smk.dk/artwork/image/KMS3567) | No photograph supplied by this API notice. |
| Paul Gauguin | [Coast at Dieppe: KMS3568](https://open.smk.dk/artwork/image/KMS3568) | No photograph supplied by this API notice. |
| Peter Paul Rubens | [Matthaeus Yrsselius (1541-1629), Abbot of Sint-Michiel's Abbey in Antwerp: KMSsp191](https://open.smk.dk/artwork/image/KMSsp191) | Attached; bytes, checksum, rights evidence and API access verified. |
| Peter Paul Rubens | [Francesco I de' Medici (1541-1587): KMSsp197](https://open.smk.dk/artwork/image/KMSsp197) | Attached; bytes, checksum, rights evidence and API access verified. |
| Peter Paul Rubens | [Johanna of Austria: KMSsp198](https://open.smk.dk/artwork/image/KMSsp198) | Deferred: source dating partly based on artist years. |
| Rembrandt van Rijn | [The Crusader: KMS1384](https://open.smk.dk/artwork/image/KMS1384) | Attached; bytes, checksum, rights evidence and API access verified. |
| Vincent van Gogh | [Landscape from Saint-Rémy: KMS1840](https://open.smk.dk/artwork/image/KMS1840) | No photograph supplied by this API notice. |

## Dating and identity findings

[Johanna of Austria, KMSsp198](https://open.smk.dk/artwork/image/KMSsp198), has an image but the source note explicitly bases the beginning of its date interval on artist-year information. It was excluded from the image selection; the existing record was preserved and is **not** marked date-validated.

Nine other records listed above have broad numeric bounds that match the creator's birth year plus fifteen through their death year, with only the generic source date note. This is a reason to investigate possible career-bound fallback, not proof of the actual creation interval. Those pre-existing dates were not silently corrected, published, or presented as newly verified.

Four Matisse records initially looked duplicated in a source-identifier join. A read-only artwork-ID check established that each old/new identifier pair already refers to the **same** local artwork:

| Old SMK object identifier | Inventory identifier | Shared local artwork UUID |
|---|---|---|
| 1170012458_object | KMSr171 | 300fe5c0-600d-476b-b9be-2ff67ede153a |
| 1170018741_object | KMSr83 | 8913b624-995a-4c00-b379-123a4a1b990d |
| 1170018750_object | KMSr79 | f307b1ca-779c-4cb4-bce6-6fb638abd914 |
| 1170021257_object | KMSr82 | f6d9a660-df4d-4fa0-9968-e2393b9d20d8 |

No merge or deletion was needed. Matisse image acquisition remains outside this batch.

## Next European source

Nationalmuseum Sweden's [official image guide](https://www.nationalmuseum.se/en/explore-art-and-design/images) links its media portal, object catalogue and a museum-provided public-domain Commons collection. That is a promising independent next source, but this pass did **not** inspect its individual objects or attach its images. Each future file still needs exact artwork/accession and permission checks. Chicago and Orsay access restrictions were not retried or bypassed.

## Reproducibility and verification

- [41 source facts](../../../content/imports/popular-smk-20260911/facts.json), SHA-256 `f4ddb3996d609276c4fab3754988665baf4d445d34cf7b0a99903670dd0da044`. Each full object response has its own URL, retrieval time and SHA sidecar in that directory.
- [Pinned 13-object selection](../../../output/popular-smk-followup/selection.json), SHA-256 `a55bde271d366bd97abccbdac1e44829f3f253a91bbaf25a5cbce7312175a702`.
- [Read-only preview](../../../output/popular-smk-followup/preview.json), [attachment receipt](../../../output/popular-smk-followup/apply.json), [preservation verification](../../../output/popular-smk-followup/after.json), [41 API checks and 13 complete image decodes/checksums](../../../output/popular-smk-followup/api.json).
- [Updated inventory](inventory-v4/PAINTERS.md). 100 artists, 22,232 works, 383 pictures; 275 pictures pass current file/size/rights-evidence checks. The remaining 107 oversized legacy files and one rights-evidence issue were not overwritten.
- Catalogue total: 106,195 artworks and 581 pictures. Monet remains 298 works / 30 pictures. This pass added images, **zero new artworks**.
- All Go tests and targeted vet passed, including changed-creator, qualifier, title, date and career-note rejection tests.
- Pre-write backup: `/Users/vadimdulub/Documents/artline-popular-smk-backup-20260911.LNLOsL/before-smk.dump`; SHA-256 `245800fa4c8f1de660fa81d8cdacd0e9f92580bef079e41f217a4ac34f231ef7`.
