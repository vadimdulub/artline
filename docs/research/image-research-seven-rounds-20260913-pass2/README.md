# Second seven-round image campaign — 13 September 2026

The user requested another five to seven sequential research rounds after the preceding seven-round campaign finished. This pass selects seven disjoint batches of at most 200 existing museum artworks, excluding all recorded candidates in previous image-expansion and image-research campaigns, including their skipped records.

The scopes are Cleveland drawings, Met drawings, NGA drawings, Chicago drawings, Cleveland prints, Met prints and NGA prints. Each selection requires existing eligible creation dates, museum/selection evidence and no primary image. Exact museum identities must exist in both databases before writes. Russian/Greek creators receive selection priority; unresolved source creator labels are supported without inventing artist records. The separate icon/source-scheme audit is retained in `additional-scheme-audit.json`. Ongoing Russian catalogue work in this shared workspace is preserved.

Only selected reproductions with explicit per-image reuse evidence are downloaded. Source evidence is pinned before download. Current museum dates are additionally checked by the Cleveland, Met and Chicago adapters; NGA uses eligible catalogue dates and its pinned official published-image index. Missing or contradictory evidence leaves the record for review.

Official policy references:

- [Cleveland open access](https://www.clevelandart.org/open-access).
- [Met open access](https://www.metmuseum.org/hubs/open-access).
- [NGA free images](https://www.nga.gov/artworks/free-images-and-open-access).
- [Chicago open access](https://www.artic.edu/open-access/open-access-images).

Derivatives retain source framing and are at most 100,000 bytes. Files are saved locally and uploaded create-only to the existing private Google Storage bucket, then attached to exact existing artwork identities in local PostgreSQL and Cloud SQL. Every round verifies file decoding/checksums, storage size/checksums, media and rights records, and database links. Non-media artwork fields and creator links are compared against before/after snapshots. The next round starts only after verification passes.

Source HTTP 403/404 and exhausted bounded museum-image timeout retries remain unavailable for review; cloud/database failures stop progress for inspection. The coordinator is resumable. No artwork/painter ingestion, publication, deployment or commits are part of this image task.

Fresh backup receipts are in `backups.json`; local backups live under `~/Library/Application Support/Artline/backups/image-research-seven-rounds-20260913-pass2/`. No test database or catalogue fixtures are created. Existing small-scale query checks do not establish performance at ten million artworks.

```sh
python -B ops/run-selected-image-rounds.py --root docs/research/image-research-seven-rounds-20260913-pass2 --rounds 7 --per-round 200
```

## Chicago source pause

Round 4 paused after eight consecutive HTTP 403 image responses. The 38 remaining records were reviewed using their already captured official metadata; all had open-image metadata and eligible dates, but no further image requests were made. They have the separate `source_paused_review` outcome. The 21 URLs actually refused remain `source_unavailable_review`, and one record lacked explicit open-image evidence. `round-04-chicago-drawings/source-pause-review.json` records the decision. The 140 successful images still receive the complete file/storage/database verification before the next round.
