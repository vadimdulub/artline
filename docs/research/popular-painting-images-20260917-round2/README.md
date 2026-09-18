# Popular painters’ painting images — 17 September 2026, round 2

**18 additional licensed photographs for 11 popular painters** were added to both local and production, uploaded to Google Storage and verified through the public application. Every artwork remains in review. These are new additions after the previous round’s 27.

Highlights: Bruegel’s *The Hunters in the Snow*, *The Peasant Wedding* and *The Peasant Dance*; Monet’s *Poppies (Coquelicots)*; Rousseau’s *Surprised!*; Gauguin’s *Café at Arles*; and five Titian paintings.

## Current coverage

| Database | Popular painters’ paintings | With usable images | Still missing | Coverage |
|---|---:|---:|---:|---:|
| Production | 5,241 | 2,260 | 2,981 | 43.12% |
| Local | 5,241 | 2,260 | 2,981 | 43.12% |

Local popular-painting count stayed at 5,241 and usable images increased by exactly 18. Production also gained 35 painting records and one additional pictured record outside this delivery, becoming equal to local coverage. This round added no artwork records and did not perform that broader catalogue synchronization.

The date-eligible, supported popular-painting subset has **2,155 of 4,157** images, with **2,002** still missing. Missing does not imply that a reusable reproduction exists.

## Delivered images

| Painter | New images |
|---|---:|
| Bronzino | 1 |
| Claude Lorrain | 1 |
| Claude Monet | 1 |
| Gustave Courbet | 1 |
| Henri Rousseau | 1 |
| Jean-Baptiste-Camille Corot | 2 |
| Paolo Veronese | 1 |
| Paul Gauguin | 1 |
| Pieter Bruegel the Elder | 3 |
| Rogier van der Weyden | 1 |
| Titian | 5 |

## Research completed

- 204 selected existing paintings received a new structured artwork-tag search: 94 with existing museum authority IDs and 110 with independently verified museum authority mappings. None had been attempted through this structured route in the preceding round.
- The first group produced 10 approved photographs; the museum-authority group produced 8. All 18 passed full-painting visual review and were delivered. The other 186 stayed without a new image.
- Several stored museum records lack authority IDs. Their official website hosts were checked against public authority records to enable this research; no institution fields were changed.
- An additional 122 existing Russian Museum painting records by Repin, Malevich and Kandinsky were compared with source inventories. Three exact object matches passed creator, holding, accession and date checks, but their image searches did not establish a reusable photograph. The other 119 remained unresolved or needed date review. No new artwork or authority link was imported.
- Previously rejected image files remain rejected. **5** inherited image blocks were resolved only for different original photographs after source, licence, checksum and visual checks; evidence is in [verified-source-replacements.json](verified-source-replacements.json).

A Commons depicts tag was not sufficient by itself. Each imported photograph also required the artwork category, creator, holding context, physical-object consistency, identified original photographer and exact approved image licence. Copies, details, diagrams and annotated reproductions remained excluded. Rights and original source were checked separately, consistent with [Wikimedia’s reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia).

## Validation

- 18 source/file checks and 18 database associations passed independently in each target.
- 18 Google Storage objects passed content size, checksum and provenance checks.
- 36 anonymous image/API requests passed, including exact artwork title, image URL, licence and source page.
- Saved preimages matched all artwork fields except the image association and revision audit fields. Creator links were also compared for the 10 records whose initial backups included them.
- No new rendition hash was shared with another artwork’s primary image in either database; no artwork was merged or deleted.
- Nine synthetic tests passed for the structured-tag adapter, including rejection of mislabelled objects, copies, conflicting identities and analysis overlays. Selection output was checked to exclude the previous structured-search set.
- Final artifact scanning covers this round’s evidence, related operational code and all delivered JPEG metadata. See the separate scan result.

## Evidence

- [Approved image manifest](approved-image-manifest.jsonl): source URLs, exact licence versions, photographer credit, attribution, dates, retrieval and rights-check timestamps, file hashes and public image URLs.
- [Aggregate report](final-aggregate-report.json) and [coverage snapshot](coverage-both-final.json).
- [Local audit](local-final-audit.json), [production/storage audit](production-final-audit.json), [public checks](public-all-images-final.json), [preimage/duplicate checks](final-preimage-and-duplicate-audit.json) and [artifact scan](artifact-safety-scan-final.json).
- [Museum-authority verification](institution-authorities/selection.json) and [Russian Museum inventory research](russian-inventory/report.json).

Only selected, rights-cleared photographs were downloaded. Reproductions were proportionally resized and JPEG-compressed within the existing 100 KB display budget, with no generated content or crop introduced. Some visitor photographs retain frames or gallery reflections.

The existing image schema and attachment workflow were reused. No schema migration, deployment, publication, commit, artwork creation or broad database synchronization was performed by this round. Backups remain in the designated Artline Application Support backup directory.
