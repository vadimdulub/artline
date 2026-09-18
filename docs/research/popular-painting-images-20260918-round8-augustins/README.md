# Popular-painter image follow-up — 18 September 2026

Five more existing paintings have working images locally and in production: four new attachments and one Géricault image restored after independently verifying its missing photographic credit. All fifteen anonymous live checks passed (five image byte checks, five museum detail endpoints and five painter detail endpoints). All five retain **in review** status.

| Painter | Painting / exact image source | Holding museum | Image licence |
|---|---|---|---|
| Alfred Sisley | [En hiver effet de neige](https://commons.wikimedia.org/wiki/File:En_hiver,_effet_de_neige,_Alfred_Sisley.jpg) | musée des beaux-arts — Lille | CC BY-SA 4.0 |
| Jacques-Louis David | [PORTRAIT DE NAPOLEON EN COSTUME IMPERIAL](https://commons.wikimedia.org/wiki/File:Jacques-louis_david,_napoleone_in_abiti_imperiali,_1805.jpg) | musée des beaux-arts — Lille | CC BY 3.0 |
| Paul Signac | [Antibes, le soir](https://commons.wikimedia.org/wiki/File:Paul_Signac-Antibes_le_soir.jpg) | musée d'art moderne et contemporain de Strasbourg — Strasbourg | Public domain |
| Pierre-Auguste Renoir | [Portrait de Marie Le Coeur](https://commons.wikimedia.org/wiki/File:Auguste_Renoir-Marie_Le_Coeur.jpg) | musée d'art moderne et contemporain de Strasbourg — Strasbourg | Public domain |
| Théodore Géricault | [Étude de toit éclairé par le soleil](https://commons.wikimedia.org/wiki/File:G%C3%A9ricault,_Etude_de_toit_%C3%A9clair%C3%A9_par_le_soleil.jpg) | musée des beaux-arts et d'archéologie — Besançon | CC BY-SA 4.0 |

## Coverage

Fresh counts agree in **local and production**: **2,326 of 5,266 popular-painter paintings have usable images; 2,940 remain without images**. Among eligible paintings with documented selection/holding evidence, **2,202 of 4,158 have images; 1,956 remain**. Before this round, the corresponding image counts were 2,321 and 2,197 in both databases. All five production database records, Google Storage objects and live images passed final verification.

## Research and verification

- Searched 119 selected regional French museum gaps using title and creator variants, plus six Toulouse inventory searches and additional Lyon leads. Discovery hits include similarly titled works and were never treated as matches without exact object evidence.
- Matched accepted files through Joconde identifiers, creator authorities, museum identities (including Museofile identifiers), complete inventory alternatives and current Commons artwork identities. Selected one full image per physical artwork.
- Fixed semicolon-separated historical inventory matching and multiline photographic credit extraction. Added a conservative reader for explicitly separated Art Photo licences; additional permission clauses remain on hold.
- Toulouse visitor photographs with additional use notices remain held. Similar titles with different accessions, creator conflicts, date conflicts and incompatible structured identities also remain held.
- **Géricault:** the file explicitly credits photographer **Eunostos** on a second line. Its earlier withdrawal concerned the missing photographer credit. That parsing problem is fixed; the live site now supplies the credit and CC BY-SA 4.0 link. Fresh evidence replaced the old held record in both local and production databases after preserving the previous evidence in external backups.
- Source licences: two Public Domain Mark, two CC BY-SA 4.0 and one CC BY 3.0. Source URLs, photographer credits, licence versions, checksums, retrieval/verification times and resize notices are retained.
- Prepared images were visually inspected individually. All complete compositions are visible; two retain their original photographic frames. No cropping, generation or colour alteration was performed.
- Read-only audits in both databases: all five source/file/DB checks pass, with no identical image hash groups. All five Google Storage objects match their sizes, MD5 checksums, SHA256 metadata, artwork/source identifiers and licence labels. Artwork, creator and identifier preimages match in both databases; only image associations and revision timestamps changed. Original rows are backed up outside the project in the approved Artline backup directory.
- 187 synthetic tests pass: 149 popular-image tests, 33 Commons regression tests and five evidence-refresh guard tests. No fixtures were inserted into a real database.

## Production verification complete

After the user renewed Google Cloud authentication, the Géricault provenance record was refreshed successfully in production. The final direct production database and Google Storage audit passed for all five images with zero errors. Both databases preserve the selected artwork, creator and identifier records, and all five remain in review. All fifteen anonymous public image/museum/painter requests passed again after the update.

The evidence refresh verified the exact existing artwork, image bytes, source, licence and photographer credit before writing; its previous rows remain in the approved external backup directory. No database schema change or application deployment was required.

## Evidence

- `approved-image-manifest.jsonl`: the five approved image records.
- `reviewed-images.json`: checksummed visual-review decisions.
- `production-resume/night-joconde/events.jsonl`: five completed local/production delivery receipts.
- `public-all-images-final.json`: the initial fifteen successful anonymous checks.
- `public-all-images-post-auth.json`: all fifteen public checks repeated successfully after production verification.
- `production-final-audit.json`: five verified production records and five verified Google Storage objects, with zero errors.
- `final-preimage-and-duplicate-audit.json`: both-target artwork/creator/identifier preservation and duplicate checks.
- `local-post-refresh-audit.json`: final passing local source/file/DB audit.
- `local-final-audit.json`: preserved initial audit identifying stale Géricault evidence; superseded locally by the post-refresh audit.
- `local-preimage-and-public-audit.json`: local artwork/creator/identifier preservation and duplicate checks.
- `coverage-both-final.json`: fresh final counts from both databases. Earlier local and both-target snapshots remain preserved.
- `regional/review-held-v2.json` and `regional/extra-held.json`: unresolved identity/rights cases.
- `artifact-safety-scan-post-auth.json`: final scoped credential/private-reference pattern and delivered JPEG audit, including the completed production reports. The initial artifact scan remains preserved.

Research started with Toulouse's [documented Wikimedia partnership](https://www.wikimedia.fr/celebration-du-domaine-public-et-1er-edit-a-thon-au-musee-des-augustins/), then expanded to independent photographs in other French collections. Each accepted image is supported by its own file-level evidence.
