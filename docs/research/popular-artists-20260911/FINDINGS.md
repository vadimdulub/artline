# Popular artists: museum research and remaining gaps

11 September 2026

[All 100 popular artists and their artwork checklists](inventory-v6/PAINTERS.md) · [Claude Monet](inventory-v6/painters/claude-monet.md)

## Latest: all-popular automated cycle and 27 images

The [new backend cycle](../popular-cycle-20260911/PAINTERS.md) processed all 100 popular painters and all 22,232 linked artworks, with 100 bounded official catalogue searches and 134 returned candidates. It records 11 possible additions for review, not automatic import. Twenty-seven exact-object Cleveland CC0 images were attached across 27 painters, all under 100,000 bytes. Corot's source/local date conflict remains deferred.

Current totals: **106,195 artworks, 608 pictures**; popular cohort **22,232 works, 410 pictures**. Monet has **298 works and 31 pictures**. No new artwork or masterpiece selection was added. All 27 image decodes/checksums, 83 API checks and preservation checks passed. [Detailed report and limitations](../popular-cycle-20260911/FINDINGS.md). Inventory v6 is current; all counts below refer to earlier snapshots.

## Previous follow-up: Nationalmuseum date and image research

Ten Swedish museum object notices were checked. Monet's [View over the Sea](https://collection.nationalmuseum.se/en/collection/item/19182/) now has a verified creation year of 1882: the museum's narrative supports when this painting was made independently of its signature. Existing editorial text and signature wording were preserved; a source citation explains the date resolution. Six further Monet/Renoir object leads need date or edition review before import.

Three museum image links returned HTTP 403 in one retrieval batch; further image requests stopped. Per-photograph Public Domain and CC BY-SA labels were recorded separately. No artwork or image counts changed. The [detailed Nationalmuseum report](NATIONALMUSEUM-FOLLOWUP.md) lists all ten notices, remaining discovery gaps and verification evidence. That pass produced inventory v5.

## Previous follow-up: Copenhagen museum images

Thirteen authentic SMK images are now attached locally to works by Modigliani, Munch, Tiepolo, Cranach, Poussin, Rubens and Rembrandt. Each is below 100,000 bytes and carries exact-object permission evidence from the museum's [official catalogue API](https://www.smk.dk/en/article/smk-api/). The pass checked 41 image gaps across 18 popular artists: 16 notices supplied no photograph, 11 supplied no downloadable IIIF URL, and one further image was deferred because its date notes rely partly on artist years. Those 28 gaps are not marked fixed.

The [detailed report](SMK-FOLLOWUP.md) lists every checked object, date-basis concerns, source citations and verification receipts. Four suspected Matisse duplicates proved to be paired source identifiers on the same local artwork records; no merge was needed. No new artworks or masterpiece designations were added in this image-only pass.

Current totals: **106,195 artworks and 581 pictures** across the catalogue; **100 popular artists, 22,232 works and 383 pictures** in the popular inventory. Preservation checks, 41 API checks, 13 full image decodes/checksums, all Go tests and targeted vet passed. Earlier follow-up counts below are historical snapshots.

## Follow-up: French deposits and Impressionist pictures

Two previously deferred Marmottan records are now in the local catalogue:
[Sisley's Été de la Saint-Martin, environs de Moret-sur-Loing](https://www.marmottan.fr/notice/D.2018.1.12/), dated 1891, and
[Renoir's Jeune fille et enfant dans un cadre champêtre](https://www.marmottan.fr/notice/D.2018.1.14/), dated circa 1900. In both notices, the inventory number runs directly into the Fondation Ephrussi de Rothschild depositor label. Exact identification resolves this markup issue without changing the attribution or inventing a date. The museum relationship remains a deposit/holding connection, not an ownership or current-display assertion. The third similar notice, D.2018.1.13, remains deferred because its date wording is ambiguous.

Sixty-five additional NGA photographs are now stored locally: 44 Renoir, 16 Pissarro and five Sisley. Each is below 100,000 bytes, retains the full composition and has per-image permission evidence. Their local picture counts are now 50, 19 and seven respectively. No museum highlight or owner-favourite designation was inferred. These are NGA works, not substitute photographs attached to different Chicago objects. The applicable source is the NGA's [open-access programme](https://www.nga.gov/artworks/free-images-and-open-access).

Chicago's official API supplied verified metadata and public-domain flags for 46 selected paintings: 31 Monet, nine Pissarro and six Sisley. The museum's [API documentation](https://api.artic.edu/docs/#scraping-images) supports separate metadata selection and one-at-a-time image access. However, its image server returned HTTP 403 on the first request; subsequent image requests were paused. **No Chicago pictures were downloaded.** All 46 exact-object leads and the access block are recorded in the artist checklists. This does not establish a rights problem or absence of images; it is an access limitation. Monet remains at 298 works and 30 local pictures.

Marmottan's [photograph-request page](https://www.marmottan.fr/presse-et-professionnels/commandez-vos-photos/) directs image enquiries to the museum and offers files labelled as museum views and ambiences. Those offered files do not establish a blanket reuse licence for individual artwork reproductions. No photograph permissions were inferred from that page, and no permission request was sent.

The live catalogue now contains **106,195 artworks and 568 pictures**. The popular-only inventory contains **100 artists, 22,232 distinct works and 370 pictures**. Of the original 41 deferred Marmottan notices, two are resolved and 39 remain open. Earlier pass statistics below describe the preceding snapshot.

Verification: [two-record import](../../../output/popular-deposits-apply/chunk-001.json), [preservation checks](../../../output/popular-deposits-verification.json), [object/API access checks](../../../output/popular-deposits-api.json), [idempotent import replay](../../../output/popular-deposits-replay/chunk-001.json), [Chicago blocked-download receipt](../../../output/popular-chicago-followup/apply.json), [NGA batch A image/API checks](../../../output/popular-nga-followup/a-api.json), [NGA batch B image/API checks](../../../output/popular-nga-followup/b-api.json), and [refreshed inventory checks](../../../output/popular-inventory-followup-verification.json). Go tests and vet passed. The pre-follow-up PostgreSQL backup is `/Users/vadimdulub/Documents/artline-popular-followup-backup-20260911.KVoZS1/before-followup.dump`, SHA-256 `e64cb1b4e8c5b33af6d2c6ade5d60f9871bdda487d0caf60bc7695bf33abc0c1`.

## Initial pass: results and scope

This pass focuses on the 100 artists already marked popular in Artline. No popularity flags were changed. The inventory lists all 22,230 distinct artworks currently linked to those artists, with recorded external catalogue URLs, museum associations, accessions and image investigation status. That is a complete inventory of the current local cohort, not a complete catalogue of each artist's oeuvre.

Musée Marmottan Monet provided the largest verified addition: 274 individual notices examined, 233 eligible records selected, 232 new artworks added and one existing work enriched with missing material/dimension metadata. All additions remain in review. There were no new artists, museums, inferred museum highlights, owner favourites or published records.

Monet now has 298 artworks in the database, up from 179. His Marmottan coverage increased from one work to 120. This includes drawings as well as paintings, and one deposit; it must not be described as 120 owned paintings or works currently on display. The museum's [Monet collection introduction](https://www.marmottan.fr/collections/claude-monet/) describes its collection and family bequest, while the individual notices establish the imported object identities.

The 233 selected Marmottan records comprise 132 paintings, 94 drawings and seven prints. The following counts include the one previously recorded Monet painting.

| Popular artist | Marmottan records selected |
|---|---:|
| Claude Monet | 120 |
| Berthe Morisot | 78 |
| Pierre-Auguste Renoir | 9 |
| Camille Pissarro | 4 |
| Édouard Manet | 4 |
| Paul Signac | 4 |
| Jean-Baptiste-Camille Corot | 3 |
| Edgar Degas | 3 |
| Eugène Delacroix | 3 |
| Alfred Sisley | 2 |
| Paul Gauguin | 2 |
| Jean-François Millet | 1 |

## Museum discovery and identity checks

The museum's [public collection search](https://www.marmottan.fr/collection-en-ligne/) supplied 273 notices for 18 source artist labels matching popular artists. The featured Monet page supplied one additional deposit, [Bras de Seine près de Giverny, soleil levant, D.11-1993](https://www.marmottan.fr/notice/D.11-1993/). Full names, aliases and available lifespan labels were checked against existing artist authorities in Go. Discovery-name matches alone were not sufficient to import a work.

Inventory numbers distinguish repeated titles. For example, the two separate notices [Nymphéas, 5098](https://www.marmottan.fr/notice/5098/) and [Nymphéas, 5164](https://www.marmottan.fr/notice/5164/) remain distinct physical records. Generic canonical links on some museum notices were not used as shared object identities. Source wording for uncertain dates was retained; no date was inferred from acquisition, exhibition or the artist's lifespan.

The existing [Impression, soleil levant, 4014](https://www.marmottan.fr/notice/4014/) record was reused rather than duplicated. Its existing title, date and image were preserved. The new source evidence only filled empty medium/dimension fields and added citations.

The Orsay catalogue remains a priority gap. The [Monet artist index](https://www.musee-orsay.fr/en/artistes/oeuvres/127194/A) returned HTTP 403 on the first direct request in this pass. Access was paused immediately, without retrying through alternate languages or hosts. This is an access limitation, not evidence that Orsay has no additional Monet works. Previously discoverable primary object references such as [Femmes au jardin](https://www.musee-orsay.fr/fr/oeuvres/femmes-au-jardin-807) remain leads, not new imports from this blocked run.

## Pictures

Eighty-five authentic NGA photographs were downloaded for 59 popular artists, including 27 Monet photographs. Each derivative is at most 100,000 bytes, keeps the full composition and has a stored checksum and image-specific rights evidence. Monet's local image count increased from three to 30. No AI-generated painting images were used.

The NGA checks used exact object identifiers, a unique primary-image entry and the per-image open-access flag in its official dataset. The museum distinguishes its factual-data licence from image availability in its [open-access policy](https://www.nga.gov/artworks/free-images-and-open-access). Fourteen of the 99 proposed image targets were deferred because the primary image was absent/ambiguous or was not cleared for open reuse.

All popular-cohort NGA works were checked against the pinned image metadata feed for image leads, not all downloaded. These cached results are timestamped research leads; future downloads require fresh permission checks. Remaining non-NGA/non-Marmottan records are explicitly labelled pending unless a local-file audit supplies a narrower result.

Across the 274 Marmottan notices, 229 contain photograph URLs and 45 supply no artwork photograph. A publicly visible photograph is not an open-reuse grant. The museum's [legal information](https://www.marmottan.fr/mentions-legales/) did not establish an open licence for those reproductions in this research. Candidate URLs are recorded, but no Marmottan photographs were downloaded, hotlinked into the app, or presented as cleared.

## Candidates requiring further research

The 41 notices below were initially retained outside the imported catalogue. Two are now resolved as noted in their rows; 39 remain outside the imported catalogue. Their source links, museum association and image leads are retained for further investigation.

Important conflicts include Morisot's source lifespan in [Autoportrait, 6022](https://www.marmottan.fr/notice/6022/), Fragonard's source birth year in [4006](https://www.marmottan.fr/notice/4006/), and Chagall's caption/inscription dating in [5390](https://www.marmottan.fr/notice/5390/). Twelve sketchbooks require an explicit physical-unit decision; they were not split into invented individual artworks. The raw source labels remain in the deferred JSON for all cases, including missing-date notices whose compact captions shift the field positions.

| Source artist label | Artwork / museum notice | Unresolved issue | Picture |
|---|---|---|---|
| MONET Claude (Paris, 1840 ; Giverny, 1926) | [carnet ; dessin](https://www.marmottan.fr/notice/5131/) | bound volume physical unit review | No photograph in notice |
| MONET Claude (Paris, 1840 ; Giverny, 1926) | [carnet ; dessin](https://www.marmottan.fr/notice/5134/) | bound volume physical unit review | No photograph in notice |
| MONET Claude (Paris, 1840 ; Giverny, 1926) | [carnet ; dessin](https://www.marmottan.fr/notice/5132/) | bound volume physical unit review | No photograph in notice |
| MONET Claude (Paris, 1840 ; Giverny, 1926) | [carnet ; dessin](https://www.marmottan.fr/notice/5129/) | bound volume physical unit review | No photograph in notice |
| MONET Claude (Paris, 1840 ; Giverny, 1926) | [carnet ; dessin](https://www.marmottan.fr/notice/5133/) | bound volume physical unit review | No photograph in notice |
| MONET Claude (Paris, 1840 ; Giverny, 1926) | [carnet ; dessin](https://www.marmottan.fr/notice/5135/) | bound volume physical unit review | No photograph in notice |
| MONET Claude (Paris, 1840 ; Giverny, 1926) | [carnet ; dessin](https://www.marmottan.fr/notice/5130/) | bound volume physical unit review | No photograph in notice |
| MONET Claude (Paris, 1840 ; Giverny, 1926) | [carnet ; dessin](https://www.marmottan.fr/notice/5128/) | bound volume physical unit review | No photograph in notice |
| MONET Claude (Paris, 1840 ; Giverny, 1926) | [Reflets de saule](https://www.marmottan.fr/notice/5136.1/) | creation date review | No photograph in notice |
| CHAGALL Marc (1887 ; 1985) | [Fiancée au visage bleu](https://www.marmottan.fr/notice/5390/) | caption 1956 inscription 1956 7 review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/5390.jpg); permission unresolved |
| DAUMIER Honoré (1808 ; 1879) | [Un avocat vu de face](https://www.marmottan.fr/notice/6135.1/) | medium review | No photograph in notice |
| DAUMIER Honoré (1808 ; 1879) | [Deux accusés](https://www.marmottan.fr/notice/6135.2/) | medium review | No photograph in notice |
| DAUMIER Honoré (1808 ; 1879) | [Un avocat plaidant](https://www.marmottan.fr/notice/6135.3/) | creation date missing | No photograph in notice |
| DAUMIER Honoré | [La pipe matinale [titre inscrit]](https://www.marmottan.fr/notice/4390.2/) | creation date missing | No photograph in notice |
| DAUMIER Honoré | [Quinze centimes un bain complet...parole, c\'est pas payé ! [titre inscrit]](https://www.marmottan.fr/notice/4390.3/) | creation date missing | No photograph in notice |
| DAUMIER Honoré | [Tous les entrepreneurs d’affaires, ça adore le veau d\'or ! [titre inscrit]](https://www.marmottan.fr/notice/4390.4/) | creation date missing | No photograph in notice |
| DAUMIER Honoré | [Nouvelle tenue des huissiers [titre inscrit]](https://www.marmottan.fr/notice/4390.5/) | creation date missing | No photograph in notice |
| DAUMIER Honoré (1808 ; 1879) | [Moine lisant](https://www.marmottan.fr/notice/4004/) | medium review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/4004.jpg); permission unresolved |
| DAUMIER Honoré | [Tête d’homme](https://www.marmottan.fr/notice/5380/) | medium review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/5380.jpg); permission unresolved |
| DEGAS Edgar (1834 ; 1917) | [La coiffure](https://www.marmottan.fr/notice/6091/) | medium review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/6091.jpg); permission unresolved |
| DEGAS Edgar | [Le fauconnier](https://www.marmottan.fr/notice/5246/) | medium review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/5246.jpg); permission unresolved |
| DELACROIX Eugène (Charenton-Saint-Maurice, 1798 ; Paris, 1863) | [Casbah de Tanger](https://www.marmottan.fr/notice/6138/) | medium review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/6138.jpg); permission unresolved |
| FRAGONARD Jean-Honoré (1712 ; 1806) | [Jeune fille consultant un nécromancien](https://www.marmottan.fr/notice/4006/) | popular authority or lifespan review | No photograph in notice |
| GERICAULT | [Deux hommes et deux chevaux](https://www.marmottan.fr/notice/1571/) | caption layout review | No photograph in notice |
| MILLET Jean-François | [Femme avec coiffe](https://www.marmottan.fr/notice/5325/) | creation date missing | No photograph in notice |
| MORISOT Berthe (1871 ; 1895) | [Autoportrait](https://www.marmottan.fr/notice/6022/) | popular authority or lifespan review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/6022.jpg); permission unresolved |
| MORISOT Berthe | [carnet ; dessin](https://www.marmottan.fr/notice/D.5-1986.2014.1/) | bound volume physical unit review | No photograph in notice |
| MORISOT Berthe | [carnet ; dessin](https://www.marmottan.fr/notice/D.5-1986.2014.2/) | bound volume physical unit review | No photograph in notice |
| MORISOT Berthe | [carnet ; dessin](https://www.marmottan.fr/notice/D.5-1986.2014.3/) | bound volume physical unit review | No photograph in notice |
| MORISOT Berthe | [carnet ; dessin](https://www.marmottan.fr/notice/D.5-1986.2014.4/) | bound volume physical unit review | No photograph in notice |
| MORISOT Berthe (1841 ; 1895) | [Fillettes](https://www.marmottan.fr/notice/2018.3.3/) | creation date missing | No photograph in notice |
| PISSARRO Camille | [Clocher de Bazincourt. Coucher de soleil.](https://www.marmottan.fr/notice/5244/) | medium review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/5244.jpg); permission unresolved |
| POUSSIN Nicolas (1594 ; 1665) | [Vue de Rome](https://www.marmottan.fr/notice/6128/) | medium review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/6128.jpg); permission unresolved |
| RENOIR Auguste | [Portrait de Coco](https://www.marmottan.fr/notice/5112/) | medium review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/5112.jpg); permission unresolved |
| RENOIR Auguste | [Nature morte au sucrier](https://www.marmottan.fr/notice/5234/) | medium review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/5234.jpg); permission unresolved |
| RENOIR Auguste | [Baigneuse assise sur un rocher](https://www.marmottan.fr/notice/5017/) | creation date review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/5017.jpg); permission unresolved |
| RENOIR Auguste (1841 ; 1919) | [L'Étang, Cagnes ou Paysage de Cagnes-sur-mer](https://www.marmottan.fr/notice/D.2018.1.13/) | inventory caption mismatch | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/D.2018.1.13.jpg); permission unresolved |
| RENOIR Auguste (1841 ; 1919) | [Jeune fille et enfant dans un cadre champêtre](https://www.marmottan.fr/notice/D.2018.1.14/) | Resolved: exact inventory/depositor separator; imported circa 1900 | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/D.2018.1.14.jpg); permission unresolved |
| SIGNAC Paul | [Rouen](https://www.marmottan.fr/notice/5058/) | medium review | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/5058.jpg); permission unresolved |
| SISLEY Alfred | [Été de la Saint-Martin, environs de Moret-sur-Loing](https://www.marmottan.fr/notice/D.2018.1.12/) | Resolved: exact inventory/depositor separator; imported 1891 | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/D.2018.1.12.jpg); permission unresolved |
| TOULOUSE-LAUTREC Henri de (Albi, 1864 ; Gironde, 1901) | [Jeune femme au bord de la mer](https://www.marmottan.fr/notice/5236/) | creation date missing | [Image candidate](https://www.marmottan.fr/wp-content/themes/marmottan2019/collection/full/5236.jpg); permission unresolved |

## What remains open

The popular cohort now has 383 local pictures: 275 pass file/size/rights-evidence checks, 107 legacy files exceed 100 KB and one legacy file needs rights-evidence review. These existing gaps were not silently marked fixed. The 85 initial, 65 NGA follow-up and 13 SMK photographs passed the checks; 21,849 cohort works still have no local picture. The [current inventory verification receipt](../../../output/popular-nationalmuseum-followup/inventory-verification.json) checks every Markdown artwork row and all local file links against the database.

The other artists have complete current-database inventories, not completed worldwide museum searches. No painter or full-catalogue research round was marked finished. Further work should prioritize:

1. Orsay and Orangerie: exact Monet object records and separate panel/ensemble identities, with access and reuse permissions respected.
2. French regional collections already represented in the database: source-checked Monet, Pissarro, Sisley and Morisot additions and reusable reproductions.
3. The 39 remaining deferred Marmottan notices: independently resolve conflicts, missing dates and physical units before importing.
4. Other popular artists: revisit their museum source links, document unsearched catalogues, and process permitted image candidates in bounded batches.

## Reproducible evidence and verification

- [Reviewed metadata manifest](marmottan-v2/manifest.json), [source crosswalk](marmottan-v2/crosswalk.json), [deferred records](marmottan-v2/deferred.json).
- [Local import receipt](../../../output/popular-marmottan-apply-v2/chunk-001.json) and [idempotent replay receipt](../../../output/popular-marmottan-replay-v2/chunk-001.json).
- [Metadata preservation checks](../../../output/popular-metadata-after.json): 232 additions; all non-target prior artwork rows unchanged; existing nonempty values in the reused target preserved; popularity, artists, institutions, media and curated selections unchanged.
- [All 233 museum-detail API checks](../../../output/popular-marmottan-api.json), including two unauthenticated-access checks.
- [Image batch A verification](../../../output/popular-images-a-api.json) and [image batch B verification](../../../output/popular-images-b-api.json): detail access, full image decoding, dimensions, size, checksum, served bytes and bounded museum pagination.
- [Image batch A preservation checks](../../../output/popular-images-a-after.json) and [batch B preservation checks](../../../output/popular-images-b-after.json): image attachments only; titles, dates, attribution and holding metadata preserved.
- Source captures are stored privately under `content/imports/popular-marmottan-20260911/`; the failed Orsay attempt is recorded under `content/imports/popular-orsay-20260911/`. The initial zero-result Marmottan extraction is retained as a parser-failure artifact, not a negative museum finding.
- Go tests and vet cover the touched research, import, inventory and image commands. These offline tools do not alter public endpoint logic. The popular inventory refuses cohorts exceeding 200 artists or 50,000 attribution links; it is not a claim of ten-million-artwork load testing.
- Pre-import PostgreSQL backup: `/Users/vadimdulub/Documents/artline-popular-backup-20260911.1aUWbM/before-popular.dump`; SHA-256 `55456968f3605f61c77e2d49d6157e2f652236548da2cf934de483a31c7c7230`.

Nothing was committed, published, deployed or applied in Terraform.
