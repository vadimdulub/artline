# Byzantine / Russian icon catalogue update

20 September 2026 — applied after the owner's instruction to upload the reviewed images and update the catalogue.

## Delivered

**3 licensed images uploaded and attached, and 19 existing artwork records updated in both local and cloud catalogues.** No new artwork records, publication, deployment or deletion. All affected records remain in review.

| New image | Source permission | Served size |
| --- | --- | ---: |
| [Mother of God Icon with Oklad, 44.817](https://art.thewalters.org/object/44.817/) | Museum CC0 | 94,389 bytes |
| [Kazan Mother of God Icon with Oklad, 44.819](https://art.thewalters.org/object/44.819/) | Museum CC0 | 95,869 bytes |
| [Dionysius the Areopagite, NG.M.01774](https://www.nasjonalmuseet.no/en/collection/object/NG.M.01774) | Exact museum reproduction on Commons, CC BY 4.0 | 94,359 bytes |

The Oslo image retains its photographer/museum credit, [file source](https://commons.wikimedia.org/wiki/File:Emmanuel_Tzanes_-_Dionysius_the_Areopagite_-_NG.M.01774_-_National_Museum_of_Art,_Architecture_and_Design.jpg), licence link and compression notice. All three images were visually checked and proportionally resized without cropping; originals are separately archived.

## Catalogue updates

- **7 Chourri works:** added the source-supported icon form and post-Byzantine Cypriot context. Unknown media and source reproduction restrictions remain intact.
- **2 Walters icons:** added icon/composite-cover context, Moscow creation-place evidence and accepted museum holdings. Clarified that Semenov's explicit credit on 44.819 is for its metal cover, not necessarily the underlying painting. The legacy primary-creator association remains, with a component-specific note: the schema currently lacks a component-maker role. No unsupported new painter identity was created.
- **3 Tzanes icons:** added post-Byzantine context. Oslo's official record now supports painting type, tempera on wood, dimensions and a mid-17th-century creation date. The stored 1600–1699 interval is conservative century containment, not exact dating or an artist-lifespan substitute. The two undated Met heads retain unknown dates.
- **4 Rublev-attributed images:** classified the visibly identified manuscript-miniature format and added explicit attribution/folio uncertainty notes. Existing creator links and source dates remain; no exact manuscript identity or museum holding was invented.
- **3 anonymous icons:** added review warnings for the unresolved dating/object-identity issues concerning Menas, Nativity and Blachernitissa. Their existing dates, source rights labels and images were not replaced.

Existing descriptions and creator notes were retained with dated review additions. Each updated object received a provenance citation. No current-display assertions or museum masterpiece designations were added.

## Still unfilled

**22 of the original 25 image gaps in the main review groups remain:** seven Chourri, nine Athens and six Kremlin works. The Chourri source requires written permission. No exact, sufficiently rights-supported reproduction was selected for the other 15 in this delivery. This does not mean that no licensable photographs exist.

Two additional Athens Commons leads were held because their museum/WGA-derived photographic provenance did not establish the required permission for this delivery. The six previously restricted/unknown image records were preserved, not relabelled or removed. See [every image-gap outcome](image-gap-dispositions.json).

## Verification and recovery

- [Database and public-file checks](verified.json): all 19 planned changes and three attachments verified in each database; unplanned artwork fields unchanged; all records still in review; zero new display claims. Public bytes match the stored SHA-256 checksums.
- [Public catalogue API checks](public-api-verified.json): each new image's artwork response exposes the expected image, source, licence and review status.
- [Pinned visual approval](visual-approval.json), [source evidence](source-selection.json), [exact change plan](plan.json), [local commit receipt](local-applied.json), [cloud commit receipt](cloud-applied.json).
- Local and cloud use different UUIDs for the two Walters candidates. Exact museum identifiers, accessions, titles and source dates were reconciled independently; no duplicate records were created.
- Exact pre-mutation artwork, creator-link, citation, identifier, holding, media and rights-evidence records are under `/Users/vadimdulub/Library/Application Support/Artline/backups/byzantine-icon-review-delivery-20260920/`. Recovery-file hashes are pinned in the plan. This is a targeted recovery archive, not a full database dump.
- Original downloaded images are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/byzantine-icon-review-delivery-20260920/`. Served assets are in `apps/web/public/assets/artworks/reviewed-icons-20260920/` and the matching GCS paths. No previous assets or backups were removed.

Operation: `ops/apply-byzantine-icon-review.py` — separate research, plan, prepare, apply and verification phases. Syntax compilation, proposal-scope checks, recovery/manifest hash validation, image decoding and public delivery checks passed. No fixture database, real-database test data or broad collection query was used for this delivery.
