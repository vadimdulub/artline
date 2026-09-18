Five additional popular-painter painting images were delivered to local PostgreSQL, production PostgreSQL and Google Storage. All ten unauthenticated image/artwork API checks passed. The research covers 20 source routes; see [the source matrix](SOURCES.md) for current policies, actual gap overlap and follow-up priorities.

| Painter | Painting | Museum | Image rights |
| --- | --- | --- | --- |
| Claude Monet | [Häuser am Ufer der Zaan](https://sammlung.staedelmuseum.de/de/werk/haeuser-am-ufer-der-zaan) | Städel Museum | [Public Domain Mark 1.0](https://creativecommons.org/publicdomain/mark/1.0/) |
| Claude Monet | [The Luncheon](https://sammlung.staedelmuseum.de/en/work/the-luncheon) | Städel Museum | [Public Domain Mark 1.0](https://creativecommons.org/publicdomain/mark/1.0/) |
| Paul Gauguin | [Landscape from Brittany](https://collection.nationalmuseum.se/en/collection/item/19216/) | Nationalmuseum | [Public Domain Mark 1.0](https://creativecommons.org/publicdomain/mark/1.0/) |
| Pierre-Auguste Renoir | [La Grenouillère](https://collection.nationalmuseum.se/en/collection/item/19486/) | Nationalmuseum | [Public Domain Mark 1.0](https://creativecommons.org/publicdomain/mark/1.0/) |
| Rembrandt van Rijn | [Self-Portrait](https://collection.nationalmuseum.se/en/collection/item/22374/) | Nationalmuseum | [Public Domain Mark 1.0](https://creativecommons.org/publicdomain/mark/1.0/) |

The new direct Städel adapter verifies the current object-specific download statement and the exact full-frame museum image. The Nationalmuseum route follows the museum’s own Commons donation links. Its matching now understands explicitly declared multilingual titles and two narrowly defined legacy date/accession formats, without changing existing catalogue fields.

| Coverage, equal in local and production | Total paintings | With usable images | Still missing |
| --- | ---: | ---: | ---: |
| All popular-painter paintings | 5,242 | 2,298 (43.84%) | 2,944 |
| Popular paintings with eligible dates and selection evidence | 4,158 | 2,184 (52.53%) | 1,974 |

This round accounts for five image attachments and no new artwork records. One additional popular painting with an image appeared in both catalogues during the task; it is outside this round’s completion receipts. The 970 other missing popular-painter paintings need separate eligibility/record review. Coverage is the backend usable-media count; it is not a fresh rights audit of every historical image.

The programmatic probe covered 23 existing paintings: two Städel, eight Nationalmuseum, ten selected Met/Chicago/Cleveland records and three SMK records. There was no exhaustive collection download. Seven Met objects expose neither an open-access flag nor a primary image; two Chicago objects have image IDs but are not marked public domain; the Cleveland component has no web image; three SMK works have PDM but no image. The source matrix includes targeted additional NGA and Mauritshuis web checks.

Five Nationalmuseum gaps remain held: three have no current outward donation link and their earlier discovery files lacked sufficient evidence; one has a conflicting physical-object Wikidata identifier; one lacks an explicit photographic-donation licence in the linked file. The Städel route filled both existing eligible gaps at that museum.

Validation: 83 popular-image tests and 40 Nationalmuseum tests passed, using synthetic fixtures. Both database audits verified all five additions, storage checks verified all five objects, and all ten anonymous public checks passed. Five artwork/creator/native-identifier preimages matched in each database except the intended media/revision/audit timestamps. No matching approved JPEG checksum was found on another primary artwork. All five artworks remain in review; no schema migration, deployment or commit was made.

Backups are under the established Application Support/Artline/backups directory, indexed by the round’s `*-backups.json` manifests. Source and rights captures, completion receipts, rejected-candidate reasons and final audit JSON files are retained here. Temporary visual contact sheets and execution helpers stay under `/tmp`.

The Städel preparation is resumable with `python ops/popular-staedel-images.py --run docs/research/popular-painting-source-research-20260917/staedel` in the research Python environment. Candidate selection and preimages already exist. Use the reviewed-image manifests with the existing attachment/uploader commands; their receipt and existing-primary checks preserve completed images. Final machine-readable results are in [final-aggregate-report.json](final-aggregate-report.json).
