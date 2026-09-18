# Popular painters’ painting images — 17 September 2026, round 3

**16 additional licensed images for 12 popular painters** were attached to both local and production, uploaded to Google Storage and verified through the public application. All artworks remain in review. These are new additions after the preceding round’s 18.

Highlights include Monet’s *Impression, soleil levant*, Titian’s *The Gypsy Madonna*, Turner’s *The Evening Star*, Munch’s *Coastal Landscape at Hvitsten* and two Cranach paintings. Four additions depict works held in Austrian institutions.

## Current coverage

| Database | Popular painters’ paintings | With usable images | Still missing | Coverage |
|---|---:|---:|---:|---:|
| Local | 5,241 | 2,276 | 2,965 | 43.43% |
| Production | 5,241 | 2,276 | 2,965 | 43.43% |

Both databases gained exactly 16 usable images within this category. The date-eligible, supported subset now has **2,171 of 4,157** paintings pictured, with **1,986** gaps remaining. The broader local catalogue has two additional, non-popular paintings compared with production; that pre-existing difference is outside this image attachment round.

## Delivered images

| Painter | Images added |
|---|---:|
| Anthony van Dyck | 1 |
| Claude Monet | 3 |
| Edvard Munch | 1 |
| Francisco Goya | 1 |
| J. M. W. Turner | 1 |
| Jacques-Louis David | 1 |
| Jean-Baptiste-Camille Corot | 2 |
| Lucas Cranach the Elder | 2 |
| Paul Gauguin | 1 |
| Pierre-Auguste Renoir | 1 |
| Titian | 1 |
| Édouard Manet | 1 |

## Research completed

- **150 distinct existing paintings** were researched through 155 source-route attempts; five exact files received a second rights review. Sixteen images were approved and delivered; 134 paintings remain without a new approved image from this round.
- New structured artwork-tag searches covered 82 paintings: nine with ready museum authorities and 73 with independently corroborated institution authorities. Six photographs passed all checks.
- Eight exact-file leads received fresh artwork, source and licence verification. One passed immediately, five passed subsequent explicit photographic-licence verification and two remained held.
- Sixty existing French national catalogue records were researched using exact Joconde identifiers, creator and holding evidence. Four original photographs passed. The existing catalogue keys were preserved.
- Previously rejected reproductions remain rejected. Six inherited artwork image blocks were resolved only for different, independently verified photographs; old source evidence is retained in [verified-source-replacements.json](verified-source-replacements.json).

## Rights and provenance

Every delivered image has an exact Commons file source, independent photographic origin, source-supported artwork identity and an approved image licence. File categories or depicts tags alone were insufficient: museum, creator and object context also had to agree. Copies, details, scans with unclear provenance and unresolved licences were excluded.

Five photographs required distinguishing the underlying painting’s public-domain statement from the photographer’s separate Creative Commons licence. The original source response is retained unchanged. The proof checks the exact rendered file revision, explicit photographic licence, original credit and matching structured licence authority. These images use the photographer’s CC BY or CC BY-SA terms, including attribution and ShareAlike where applicable.

For Manet’s photograph, the exact file revision explicitly states self-photography and credits “Images by 0x010C”; that credit was preserved alongside the painting artist. The uploading account alone was not used as evidence.

## Verification

- All 16 source/file checks and image associations passed independently in each database.
- All 16 Google Storage objects passed size, checksum and provenance checks.
- All 32 anonymous image and museum-artwork API requests passed, including the exact artwork title, image, licence and source page.
- Every delivered artwork was compared against its saved preimage; only the image association and revision audit fields changed. Creator and identifier preimages were also checked for the one delivered record whose initial backup included them.
- No new rendition checksum is shared with another artwork’s primary image in either database. No artwork was merged or removed.
- Fifty popular-image synthetic tests and 67 Commons regression tests passed; these suites overlap and are not an additive count of unique tests. No test database or catalogue fixture was created.

Only the selected, cleared images were downloaded. The existing schema and delivery workflow were reused. Images were proportionally resized and JPEG-compressed to the existing 100 KB display limit, without cropping or generated content. Visitor photographs can retain frames and reflections.

## Evidence

- [Approved image manifest](approved-image-manifest.jsonl): every artwork, source URL, licence/version, credit, attribution, timestamps, file hash and public image URL.
- [Aggregate processing report](final-aggregate-report.json) and [coverage snapshot](coverage-both-final.json).
- [Local audit](local-final-audit.json), [production/storage audit](production-final-audit.json), [public checks](public-all-images-final.json) and [preimage/duplicate checks](final-preimage-and-duplicate-audit.json).
- [Artifact scan](artifact-safety-scan-final.json): this round’s evidence, operational code and delivered JPEG metadata. Pattern scanning is an additional check, not a universal guarantee for unrelated repository contents.

Backups remain under the designated Artline Application Support backup directory. No publication, schema migration, deployment or commit was part of this round.
