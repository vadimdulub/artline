# Additional image recovery and coverage — 16 September 2026

Completed 2026-09-16T11:32:01.321724+00:00.

**18 additional painting images** are attached to existing artworks in both local and production databases and verified in Google Storage. Every image has an independently checked Public Domain Mark from a Nationalmuseum contribution on Wikimedia Commons. All artworks remain in review.

The recovery examined 73 existing museum artwork gaps. Eighteen passed; 55 remain for identity or rights review. Four candidates belonged to currently designated popular painters; none of those four passed this round.

| Production records | Total | Displayable picture | Missing picture | Coverage |
| --- | ---: | ---: | ---: | ---: |
| All artworks | 262,721 | 79,736 | 182,985 | 30.35% |
| Paintings | 78,999 | 22,043 | 56,956 | 27.90% |
| Popular painters: all artworks | 28,461 | 15,318 | 13,143 | 53.82% |
| Popular painters: paintings | 4,962 | 2,127 | 2,835 | 42.87% |
| Eligible works with source evidence | 171,036 | 79,185 | 91,851 | 46.30% |
| Eligible paintings with source evidence | 41,816 | 21,531 | 20,285 | 51.49% |
| Eligible popular-painter paintings with source evidence | 3,938 | 2,023 | 1,915 | 51.37% |

These rows overlap and must not be added together. “Paintings” uses the existing painting type; other painted media are not silently reclassified. “Eligible” requires the creation-date policy and existing accepted museum holding evidence or qualifying curated selection.

Local has 79,738 displayable pictures across 262,723 records; production has 79,736 across 262,721. This two-record difference predates the round. Both gained 18 and have the same 182,985 remaining picture gaps. Two historic attached images remain excluded by their existing rights holds.

The most actionable missing-picture queue is **91,851 eligible, source-supported works**, including **20,285 paintings**. Within currently popular painters, **1,915 eligible paintings** with source evidence still lack a picture. Reusable rights and exact artwork identity still need checking.

## Popular painter painting gaps

| Painter | Paintings without an attached image |
| --- | ---: |
| Pablo Picasso | 370 |
| J. M. W. Turner | 268 |
| Claude Monet | 210 |
| Henri Matisse | 159 |
| Gustave Courbet | 108 |
| Jean-Baptiste-Camille Corot | 81 |
| Marc Chagall | 77 |
| Georges Braque | 70 |
| Jean-François Millet | 66 |
| Ilya Repin | 63 |

Per-painter rows count distinct works for each painter; shared attributions can appear under multiple painters. These painter rows use attached media, while the overall table uses displayable media.

## Verification and evidence

- All 18 local files, local database references, production references and Google Storage objects passed source, rights and checksum checks.
- Public image delivery and artist/museum artwork API checks passed.
- All 18 images were visually inspected. Two are museum-provided monochrome reproductions; one portrait retains its frame.
- No exact image-hash duplicates were found against existing catalogue primary images.
- 40 Nationalmuseum source-safeguard tests passed without database fixtures.
- The recovery fixed empty accession-field parsing, accession-link template handling and Creator authority redirects; exact source identity and image licence checks remain mandatory.

- [Full aggregate report](final-aggregate-report.json)
- [Coverage snapshot and definitions](coverage-final.json)
- [Approved image manifest](approved-image-manifest.jsonl)
- [Production and storage audit](final-production-image-audit.json)
- [Local audit](final-local-image-audit.json)
- [Public delivery checks](public-delivery-final.json)
- [Duplicate check](cross-catalogue-image-check-final.json)
- [Visual review](visual-review-final.json)
- [Artifact scan](artifact-safety-scan-final.json)

Backups are recorded in backups.json and stored in the established Artline backup directory. The earlier 452 image holds remain preserved; they are not new withdrawals from this round. No unrelated data was changed.
