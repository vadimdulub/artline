# Second seven-round image campaign: completed

Completed seven further sequential research rounds on 13 September 2026. Added **1,084 images** to **1,400 distinct existing artworks reviewed**, with **zero overlap** with candidate records from prior image campaigns. Each round passed file, storage and database verification before the next began.

| Round | Collection | Scope | Reviewed | Images added | Deferred |
| --- | --- | --- | ---: | ---: | ---: |
| 1 | Cleveland Museum of Art | Drawings | 200 | 186 | 14 |
| 2 | Metropolitan Museum of Art | Drawings | 200 | 25 | 175 |
| 3 | National Gallery of Art | Drawings | 200 | 144 | 56 |
| 4 | Art Institute of Chicago | Drawings | 200 | 140 | 60 |
| 5 | Cleveland Museum of Art | Prints | 200 | 200 | 0 |
| 6 | Metropolitan Museum of Art | Prints | 200 | 192 | 8 |
| 7 | National Gallery of Art | Prints | 200 | 197 | 3 |
| **Total** | | | **1,400** | **1,084** | **316** |

## Saved and checked

All images are saved under `apps/web/public/assets/artworks/open-museums/` and uploaded to matching object paths in `gs://artline-508319-images/assets/artworks/open-museums/`. Total derivative size: **96,068,558 bytes**. Largest file: **99,994 bytes**, below the requested 100,000-byte ceiling. Derivatives retain the source framing without an added crop or generated content.

Every image passed local decoding, size and SHA-256 checks; Google Storage size and MD5 checks; and media, rights-evidence and exact artwork-link checks in local PostgreSQL and Cloud SQL. One sample from each of the seven rounds was visually inspected. All seven samples returned HTTP 200 from the live website with bytes matching their local copies; see [sample checks](sample-checks.json).

Per-round before/after snapshots match for all non-media artwork metadata and creator links in both databases. A final read-only audit checked all 1,400 selected artworks again: exactly 1,084 expected image associations exist in each database, all 316 deferred records still have no primary image, and every selected artwork remains in review. Verification errors: **zero**.

## Research decisions

- **257** selections had no explicitly open image in the checked museum source.
- **21** Chicago image URLs returned HTTP 403 and remain unavailable for review.
- After eight consecutive Chicago refusals, **38** remaining selections were reviewed using already captured official metadata. Their dates and open-image metadata passed, but their image requests were **not attempted**. They have the separate `source_paused_review` outcome; [the pause decision](round-04-chicago-drawings/source-pause-review.json) retains the evidence. No alternate access route was attempted.
- **34** selections carried the existing Russian/Greek creator-priority flag: **18 images added**, with 16 rights/availability skips. Country associations were used as existing selection evidence; no cultural identity or biography was invented.

Rights receipts cover **743 CC0** images and **341 NGA open-access public-domain** images. Per-image source evidence was pinned before downloads. Current museum creation dates were checked for Cleveland, the Met and Chicago; NGA uses eligible catalogue dates and its pinned published-image index. Missing or conflicting rights/dates did not authorize publication or invented metadata. See [the plan and source policies](README.md).

## Preservation and reproducibility

No artworks or painters were created, deleted or published by this image task. Dates, holdings and creator links were preserved. No current-display claim was inferred. Other catalogue and Russian research work in the shared workspace was left intact; no commit, deployment or Terraform operation was performed.

Fresh local and Cloud SQL backups preceded the first media write. The local archive is 355,729,150 bytes under `~/Library/Application Support/Artline/backups/image-research-seven-rounds-20260913-pass2/`; Cloud SQL backup `1789306070238` succeeded at 13:29:21 UTC. [Backup receipts](backups.json) retain the checksum and paths.

The existing coordinator `ops/run-selected-image-rounds.py` was extended to recognize the explicitly reviewed source-pause outcome when resuming. Its five offline date/source-failure tests passed. No test database or fixtures were created. The final diff whitespace check passed. No new query algorithm was introduced; performance at ten million artworks remains an outstanding load test.

Each `round-*` directory retains candidates, cached museum metadata, rights selections, image receipts, event history, database snapshots, `verification-final.json` and `round-complete.json`. [Machine-readable completion evidence](completion.json) records totals, source refusals and the final database audit.

These counts cover this second seven-round campaign only. The preceding 1,171-image campaign and earlier additions are excluded.
