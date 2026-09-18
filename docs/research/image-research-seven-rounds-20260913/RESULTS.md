# Completed: seven image research rounds — 13 September 2026

Added **1,171 images** to existing artworks: 1,170 from seven sequential, bounded museum rounds and one additional Byzantine priority icon. Reviewed 1,401 distinct existing records. All seven rounds completed; each passed verification before the next began.

| Round | Collection | Scope | Reviewed | Images added | Held without image |
| --- | --- | --- | ---: | ---: | ---: |
| 1 | Cleveland Museum of Art | Drawings | 200 | 194 | 6 |
| 2 | Metropolitan Museum of Art | Drawings | 200 | 124 | 76 |
| 3 | National Gallery of Art | Drawings | 200 | 171 | 29 |
| 4 | Art Institute of Chicago | Drawings | 200 | 87 | 113 |
| 5 | Cleveland Museum of Art | Prints | 200 | 200 | 0 |
| 6 | Metropolitan Museum of Art | Prints | 200 | 195 | 5 |
| 7 | National Gallery of Art | Prints | 200 | 199 | 1 |
| Additional priority review | Athens / independent Commons photograph | Byzantine icon | 1 | 1 | 0 |
| **Total** | | | **1,401** | **1,171** | **230** |

## Saved and verified

All 1,171 derivatives are saved under `apps/web/public/assets/artworks/open-museums/` and uploaded to matching paths in the private `artline-508319-images` Google Storage bucket. Combined size: **105,211,284 bytes**; largest file: **99,985 bytes**, below the requested 100,000-byte ceiling. Compression preserves source framing and adds no crop or generated content.

Every derivative passed local decoding, size and SHA-256 checks, Google Storage size/MD5 checks, and media, rights-evidence and artwork-link checks in both local PostgreSQL and Cloud SQL. Eight visual examples were inspected, including one per round and the priority icon. Four live website asset requests returned HTTP 200 with bytes matching the local files. Verification reports contain zero unresolved errors.

Before/after snapshots match for all non-media artwork metadata and creator links in both databases. All 1,401 selected records remain in review. This campaign attached media without creating artwork/painter records, publishing entries, changing dates or holdings, committing code or deploying. Full local and Cloud SQL backups preceded writes; see [backup receipts](backups.json).

## Source decisions and remaining research

225 selected works had no explicitly open image in the checked source. Five Chicago image endpoints returned HTTP 403; those remain unavailable for review, with their errors retained. One additional Chicago image initially timed out, then succeeded in its single bounded retry batch. There are no unfinished or failed latest outcomes. Missing images did not cause records or source evidence to be removed.

Rights evidence covers 800 CC0 derivatives, 370 NGA open-access public-domain derivatives and one CC BY-SA 4.0 photograph. Per-object evidence was pinned before image download. Met, Cleveland and Chicago downloads also passed current museum creation-date checks; NGA uses existing eligible catalogue dates and its pinned published-image index. Neither missing dates nor museum holdings establish present-day display.

The priority addition is [Archangel Michael](priority-icon/README.md), Athens accession ΒΧΜ 01353: an exact-object, independent photograph by Yair-haklai under CC BY-SA 4.0. The photographer credit, license link and derivative notice are preserved. Further Greek/Byzantine leads remain documented in [additional leads](priority-icon/additional-leads.json); unresolved identity or image rights were not assumed.

## Evidence and reusable workflow

- [Machine-readable totals and per-round results](completion.json).
- [Selection plan and source policies](README.md).
- Each `round-*` directory retains its candidates, source metadata, rights selections, image receipts, event history, database snapshots, `verification-final.json` and `round-complete.json`.
- [Visual checks](visual-checks.json) and [live asset checks](live-image-checks.json).

The resumable coordinator is `ops/run-selected-image-rounds.py`; the single-icon adapter is `ops/enrich-priority-icon-image.py`. Offline validation passed: 12 existing image-pipeline tests, five date/source-failure guard tests, and four focused icon rejection checks. No test database or catalogue fixtures were created. The final source-failure guard accepts only known museum hosts; every held source response in this campaign was also independently checked against that guard. `git diff --check` passed.

The 200-record snapshot query used indexed bounded lookups and took 117.718 ms on the real local catalogue; [the read-only plan](round-01-cleveland-drawings/snapshot-query-plan.json) is retained. This is not a 10-million-artwork load test; that capacity validation remains outstanding.

These totals cover this seven-round campaign only. The preceding 400-image pass and earlier image campaigns are excluded.
