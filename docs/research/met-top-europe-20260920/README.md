# Met European-country image delivery — 20 September 2026

Follow-up: the [painter-by-painter continuation](round2/README.md) delivered **30 additional images**, bringing the two-batch total to **80**. It also records expanded creator-role checks and unresolved creator-date discrepancies. The counts below describe the original 50-image delivery.

## Delivered

**50 new museum artworks and 50 CC0 images, covering 13 existing painters.** Uploaded to cloud storage and attached in both local and production catalogues. All 50 live image URLs and artwork API responses passed verification at 12:31 UTC.

- Largest image: **99,117 bytes**; combined size: **3,902,682 bytes**.
- Nine paintings and 41 drawings, with museum-provided creation dates through 1970. Source wording and uncertainty are retained.
- All new artwork records remain **review / research candidate**, with no publication timestamp.
- Fifty source-backed museum holding assertions per database; **no currently-on-view claims**.
- Existing painter profiles and country relationships are unchanged. No existing artwork image was replaced or deleted.

## Ten-country scope

“Top ten” means European countries ranked by their distinct eligible artworks in the local Artline catalogue, using existing artist-country relationships. This is not a ranking of artistic merit or a newly inferred nationality assignment.

| Country | Eligible catalogue artworks at selection | New images delivered |
| --- | ---: | ---: |
| France | 49,945 | 31 |
| Denmark | 19,742 | 0 |
| Italy | 12,012 | 4 |
| Germany | 11,989 | 1 |
| United Kingdom | 9,539 | 0 |
| Netherlands | 8,314 | 11 |
| Russia | 7,864 | 0 |
| Spain | 6,487 | 3 |
| Finland | 3,728 | 0 |
| Switzerland | 1,817 | 0 |

All ten countries were included in discovery screening. No new work from Denmark, the UK, Russia, Finland or Switzerland cleared every selection/source check in this bounded batch. Zero does **not** mean that the Met has no suitable works from those countries. This was not exhaustive painter-by-painter research or image downloading.

Painters receiving images: Edgar Degas, Constantin Guys, Carlo Saraceni, Franciabigio, Scipione Pulzone, Wilhelm Trübner, Anthonie Palamedesz., Barent Fabritius, Cornelis Saftleven, Dirck Hals, Herman van Swanevelt, Francisco Rizi and Raimundo de Madrazo y Garreta.

## Selection and holds

The checksum-verified official Met index captured on 15 September was used only for discovery. Screening covered 4,306 existing painter authority records linked to the ten countries, producing 760 metadata leads. Duplicate checks retained 158; 120 were selected for current per-object API review on 20 September.

Fresh source review verified 53 objects and held 67: 50 without a confirmed unique primary maker, ten qualified attributions, three changed artist authorities, two missing endpoints, one changed accession and one without explicit current Open Access image rights. Three further same-artist title collisions were held after checking the fresh titles, leaving the 50 delivered records. Existing records involved in collisions were preserved.

Each downloaded image had a current exact Met object record with `isPublicDomain: true`, no conflicting reproduction-rights statement, an official primary image URL, a matched creator authority, source creation dates within scope and documented museum ownership. The supplied [Pollock collection page](https://www.metmuseum.org/art/collection/search/488978) was not imported; the delivered objects were individually checked under the [Met Open Access policy](https://www.metmuseum.org/hubs/open-access).

All fifty application derivatives were inspected on five contact sheets before import. The visual check covered gross subject/pose consistency, image errors and full-frame presentation; it is not scholarly authentication. Resizing and JPEG compression are proportional, with no cropping, restoration or generated content.

## Evidence and recovery

- [Country/painter inventory and source-index receipt](inventory.json).
- [Current-source candidates](fresh-selection/source-candidates.json), with per-object evidence in `fresh-selection/verified/` and holds in `fresh-selection/review-held/`.
- [Final selection and duplicate holds](delivery/plan.json).
- [Checksum-pinned visual review](delivery/reviewed-images.json); contact sheets [1](delivery/contact-sheet-1.jpg), [2](delivery/contact-sheet-2.jpg), [3](delivery/contact-sheet-3.jpg), [4](delivery/contact-sheet-4.jpg), [5](delivery/contact-sheet-5.jpg).
- [Image, storage, rights and both-database verification: zero errors](delivery/image-verification.json).
- [Artwork, holding, painter-preservation and public-URL verification: zero errors](delivery/catalogue-public-verification.json).

Recovery evidence is under `/Users/vadimdulub/Library/Application Support/Artline/backups/met-top-europe-20260920/delivery/`. Application derivatives are content-hashed files under `apps/web/public/assets/artworks/open-museums/met/`. Source metadata, receipts and selection evidence are retained in this research directory.

Thirty offline tests passed across the source-gating, museum-image campaign and compression suites. No test database, catalogue fixture, commit, deployment, Terraform operation or schema change was performed.

Separately, this session completed the earlier **161-image compression delivery** to production. [Its verification](../deep-image-review-20260920/size-limit/verification.json) confirms both catalogues had zero recorded oversized images, with original files and rights evidence preserved.
