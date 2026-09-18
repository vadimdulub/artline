# Popular painters’ painting images — 17 September 2026

Added **27 independently sourced, licensed photographs** for **14 popular painters** to the existing local and production artwork records. All images were uploaded to Google Storage and checked through the public application. All artworks remain in review.

The selected searches covered **373 distinct existing paintings**, with **402 source attempts** including follow-ups. These were bounded searches of museum APIs and Wikimedia Commons, with original-photographer, artwork-identity and per-image rights checks before delivery.

## Current coverage

| Database | Popular paintings | With usable images | Still missing | Coverage |
|---|---:|---:|---:|---:|
| Production | 5,206 | 2,241 | 2,965 | 43.05% |
| Local | 5,241 | 2,242 | 2,999 | 42.78% |

Within the date-eligible, supported subset, both databases now have **2,137 of 4,157** paintings illustrated, with **2,020** remaining. A missing image does not establish that a reusable reproduction exists.

All 27 delivered images are freshly verified. Four image-coverage losses on other artworks occurred between aggregate snapshots; this round did not modify those artworks. Net popular-painting coverage gain is therefore 23, rather than 27. Local and production already differed by 35 painting records and one usable image at baseline.
The other observed changes were Corot −1, Tiepolo −2 and Bronzino −1. Their cause was not investigated or changed by this image round.

## Images delivered

| Painter | New images |
|---|---:|
| Andrea Mantegna | 1 |
| Anthony van Dyck | 2 |
| Egon Schiele | 5 |
| Giorgione | 1 |
| Giuseppe Arcimboldo | 1 |
| Gustav Klimt | 2 |
| Jacques-Louis David | 1 |
| Lucas Cranach the Elder | 1 |
| Peter Paul Rubens | 5 |
| Pierre-Auguste Renoir | 1 |
| Pieter Bruegel the Elder | 3 |
| Tintoretto | 1 |
| Titian | 2 |
| Vincent van Gogh | 1 |

Highlights include Klimt’s *The Kiss* and *Death and Life*, Bruegel’s *The Tower of Babel*, van Gogh’s *The Church at Auvers*, Renoir’s *Bal du moulin de la Galette*, Titian’s *Violante* and five Schiele paintings.

## Search outcomes

| Pass | Artworks attempted | Prepared before visual review |
|---|---:|---:|
| direct-museums | 113 | 0 |
| commons-independent | 110 | 18 |
| commons-extended | 54 | 0 |
| commons-language-followup | 40 | 3 |
| commons-depicts | 56 | 8 |
| commons-depicts-extra | 29 | 3 |

The 54-record extended pass was deliberately stopped and its remaining 96 records divided into the 56-record corroborated-depicts pass and the 40-record language/category pass. The additional 29-record depicts pass revisited initial candidates. Counts across passes overlap; the unique total above removes that overlap.

Museum API checks covered Met, Chicago, Cleveland and SMK. None of those 113 selected records exposed a currently usable, explicitly open image. Commons searches found independent photographs, including files absent from the artwork’s primary-image field. A depicts tag alone was insufficient: the adapter also required artwork category, creator, holding context, exact-object consistency, photographer credit and file-specific approved rights.

Five prepared candidates were rejected: a commercial book scan, a detail, an uploader-only Tower of Babel copy, an uploader-only Tintoretto copy, and a Degas reproduction with analysis arrows. The Tower of Babel subsequently received a different, fully verified photograph. Held bytes and receipts were moved out of the web assets folder into the designated backup area. An initial permissive preparation was also superseded before any database delivery; its evidence and unattached bytes were preserved outside the public folder.

Three inherited image blocks were resolved only for different, separately licensed original photographs by Sailko. The previously rejected source files remain rejected. Exact replacement evidence is in [verified-source-replacements.json](verified-source-replacements.json).

The NGA check stopped when its source revision differed from the saved capture. No stale NGA image licence was used.

## Verification and evidence

- 27 source/file checks and database associations passed independently in each database; all stay in review, within scope and supported by holding/selection evidence.
- 27 Google Storage objects passed size, checksum and provenance checks.
- 54 anonymous public image/API requests passed, including titles, image paths, licences and source pages.
- Preimage comparisons found no catalogue-field changes beyond media associations and revision audit fields. Creator links were also compared for the 17 records whose initial backups included them.
- No new rendition hash was shared with a different artwork’s primary image in either catalogue. This is an exact-file check, not comprehensive physical-object deduplication.
- 57 synthetic unit tests passed; no real-catalogue test fixtures were inserted.
- The final artifact scan covers this round’s evidence, related operational code and delivered JPEG metadata; its complete result is recorded separately.

Files: [approved image manifest](approved-image-manifest.jsonl), [aggregate report](final-aggregate-report.json), [local audit](local-final-audit.json), [production and storage audit](production-final-audit.json), [public verification](public-all-images-final.json), [preimage and duplicate checks](final-preimage-and-duplicate-audit.json), [coverage](coverage-both-final.json), [artifact scan](artifact-safety-scan-final.json).

Source URLs, exact licence versions, photographer credits, attribution, retrieval and rights-check timestamps are present for every delivered image in the manifest and database evidence. Photographs were proportionally resized and JPEG-compressed to the existing 100 KB delivery budget. No crop or generated content was introduced. Some photographs retain their frames or gallery reflections.

Current-schema image attachment was reused. No schema migration, app deployment, publication, commit or unrelated catalogue synchronization was performed.
