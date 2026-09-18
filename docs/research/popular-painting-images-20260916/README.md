# Popular-painter painting images — 16 September 2026

**All 58 images from this round are now attached in both local and production databases and hosted in Google Storage.** The final 22 uploads completed after authentication was restored. The queue is empty.

Every addition illustrates an existing popular-painter painting. Records remain in review. No artwork or artist was added, deleted, merged or published during this round.

## Picture coverage

Fresh read-only counts from both databases agree for popular-painter paintings:

| Popular-painter paintings | Before | Local and production after |
| --- | ---: | ---: |
| Total records | 4,962 | 4,962 |
| With usable pictures | 2,127 | 2,185 |
| Still without usable pictures | 2,835 | 2,777 |
| Missing pictures among eligible, supported records | 1,915 | 1,857 |

Popular-painter painting coverage is **44.03%**. Among the 3,938 paintings with eligible dates and selection evidence, 2,081 have pictures (**52.84%**). Missing-picture counts describe catalogue gaps; they do not imply a licensed image can be found for every work. Aggregate coverage uses backend display eligibility and does not freshly audit every historical image's rights.

## Additions by painter

These counts apply equally to local and production:

| Painter | Images added |
| --- | ---: |
| Alfred Sisley | 2 |
| Camille Pissarro | 1 |
| Claude Monet | 33 |
| Jean-François Millet | 1 |
| Lucas Cranach the Elder | 1 |
| Paul Cézanne | 2 |
| Paul Gauguin | 3 |
| Paul Klee | 1 |
| Peter Paul Rubens | 1 |
| Pierre-Auguste Renoir | 4 |
| Raphael | 1 |
| Rembrandt van Rijn | 1 |
| Vincent van Gogh | 5 |
| Édouard Manet | 2 |

## Research and validation

- Examined all 249 selected paintings with exact artwork and institution authority context. Follow-up searches retried 25 of those works using native museum links; these are not additional paintings.
- Separately investigated 30 SMK native-inventory gaps across 12 artist/museum groups. Two authority leads were found, but neither yielded an approved exact photograph. No SMK metadata was changed.
- Confirmed physical-object identity using exact Wikidata/Commons statements, or a museum object URL plus labelled accession and matching artist. Separate paintings and versions remain separate.
- Stored exact image source URLs, file revisions, approved licence URIs and versions, attribution, rights-check dates and checksums.
- Visually reviewed all 58 accepted photographs. Some visitor photos include frames or glare. Nine prepared files were held before import because of provenance or rights conflicts, digital alterations, or partial/multi-object compositions. Their bytes and evidence remain in the established Artline backup directory.
- The source checks reject editor/transfer credits as photographic provenance, unspecified book scans, restricted website copies, unverified mirror credits and explicit copyright-conflict notices. The [Pushkin website policy](https://pushkinmuseum.art/usage_policy/index.php?lang=ru) prevents automatic use of its website copies in this workflow; independently photographed, separately licensed images remain eligible.
- All **58 local database attachments**, **58 production attachments**, and **58 Google Storage objects** passed the final audits. Checks cover source evidence, identity, scope, review status, licence, attribution, byte size, checksums and storage provenance metadata.
- All **58 public image URLs** returned the expected bytes, and all **58 public artwork API records** returned the correct image, title, licence and review status.
- The earlier implementation checks passed 77 synthetic unit tests. Exact approved display-image hashes found no duplicate groups against other local catalogue primary images. This is not a full perceptual duplicate audit of historical assets.
- The research worker resumed after an empty structured-data response exposed a parser edge case and respected MediaWiki `maxlag` backoff. The production uploader resumed from saved receipts after reauthentication, with no repeat image research or source downloads.

## Evidence

- [Final aggregate report](final-aggregate-report.json)
- [Approved image manifest — all 58 delivered](approved-image-manifest.jsonl)
- [Production database and Google Storage audit](production-resumed-full-audit.json)
- [Local database and file audit](local-resumed-full-audit.json)
- [Public image and API audit](public-resumed-full-audit.json)
- [Fresh local and production coverage](coverage-both-final.json)
- [Source and visual review](final-source-and-visual-audit.json)
- [Exact duplicate-image audit](final-local-exact-duplicate-audit.json)
- [Artifact safety scan after completion](artifact-safety-scan-completed.json)
- [Empty production queue](pending-production-images.json)

The previously cancelled reference dataset was not accessed or used. This round relies on independently sourced museum/Wikimedia evidence. Backups, including the earlier interrupted-delivery reports, remain under the documented Artline backup location outside the repository. No background worker is running.
