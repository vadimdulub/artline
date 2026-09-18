# Popular painters: museum-inventory photograph round, 17 September 2026

**Two additional photographs were attached to the existing artwork records in local and production and uploaded to Google Storage. All six anonymous public image/artwork requests passed.**

| Painter | Painting | Holding museum | Photograph licence |
|---|---|---|---|
| Claude Monet | [En promenade près d’Argenteuil](https://www.marmottan.fr/notice/5332/) | Musée Marmottan Monet | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Pierre-Auguste Renoir | [Dancing Girl with Tambourine](https://www.nationalgallery.org.uk/data/0CZ7-0001-0000-0000) | National Gallery | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |

The Monet photograph is by GFreihalter; the Renoir photograph is by Sailko. Both show the complete painting and retain its frame. The Monet visitor photograph has some glare. Required photographer credit, licence version, source, transformation notice and ShareAlike terms are stored with each image. These are independently licensed visitor photographs, not museum-supplied image files.

## Research and fixes

- Selected 120 existing paintings for exact Commons searches, including 40 Monets. The bounded searches considered 2,073 distinct candidate files; search results include unrelated files and are not all artwork matches.
- Checked another 40 existing paintings through Met and Chicago APIs. All 40 currently lacked an explicitly open available image.
- Added a native museum-inventory route that verifies creator, accession, holding institution and dates without requiring new production Wikidata fields. It preserves the existing database schema and identifiers.
- Fixed recognition of an exact museum object link and labelled accession in a Commons image description. An original photographer may correctly occupy the Artist credit field while the artwork creator is named in the description. Museum homepages, partial accessions, another creator, conflicting object IDs, copies and details remain insufficient.
- Fixed two narrow photo-licence parser omissions: the spaced self-photographed template alias and a named attribution parameter. The exact file revision must still render both the underlying artwork PDM and the separate approved photo licence. Conflicting or restrictive licences remain held.
- Initial automatic decisions held all 120 Commons targets. Revalidation with these fixes recovered the two delivered paintings. Earlier decisions remain preserved; they were not silently rewritten.

## Coverage

| Same in local and production | Paintings | With usable images | Missing |
|---|---:|---:|---:|
| All popular-painter paintings | 5,261 | 2,310 | 2,951 |
| Eligible, supported popular-painter paintings | 4,158 | 2,186 | 1,972 |

The round baseline was 5,261 popular-painter paintings with 2,308 images and 2,953 gaps. This round filled two gaps. Compared with the earlier 5,242-painting snapshot, separate catalogue work had already added 19 paintings and ten images. Those changes are not counted as this round’s result. The 979 gaps outside the eligible/supported subset still need date or selection/holding review.

## Delivery and verification

Both artwork/creator/identifier preimage audits passed. Only primary media, revision and audit timestamps changed. Both records remain in review and unpublished. No new artwork records, schema migration, deployment or commit was made. No identical approved JPEG checksum was found as another artwork’s primary image; this is not an exhaustive catalogue deduplication.

The local and production source/media audits each verified both images. Google Storage checksum and provenance checks passed for both objects. Anonymous requests passed for both JPEGs and both museum and painter artwork endpoints (six requests). Synthetic tests: 104 popular-image tests and 33 Commons regression tests; no real-catalogue fixtures or test database were created.

Google Cloud initially required reauthentication; production delivery completed after the user renewed it. A separate fresh Russian-museum authority discovery stopped on persistent Wikidata replication lag. Its completed group covers eight gaps and is preserved in the sibling round5-native directory. This round continued with intact public authority API captures less than 48 hours old, followed by independent Commons image checks. No source access restriction or cooldown was bypassed.

No research worker remains running. The selected preparation is checkpointed. Backup manifests reference the designated Application Support/Artline/backups directory. Source captures, initial holds, reviewed checksums, local attachments and production completion receipts remain here.

See [the image manifest](approved-image-manifest.jsonl), [aggregate report](final-aggregate-report.json), [local audit](local-final-audit.json), [production and storage audit](production-final-audit.json), [public delivery checks](public-all-images-final.json), and [preimage/duplicate audit](final-preimage-and-duplicate-audit.json).
