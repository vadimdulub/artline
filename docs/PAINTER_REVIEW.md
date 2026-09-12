# Painter-by-painter research checklist

[Active European research session and verified additions](research/popular-europe-session-20260911/PROGRESS.md)
· [Current source decisions for all 100 popular painters](research/popular-europe-session-20260911/review-v1/PAINTERS.md)
· [Latest exported inventory, before Athens additions](research/popular-europe-session-20260911/inventory-v1/PAINTERS.md)
· [Required follow-up: Monet and other painters' image visibility](POPULAR_RESEARCH_CONTINUATION_PROMPT.md)

The older snapshots below are retained as history, not current totals.

[Open the latest popular-artists inventory](research/popular-artists-20260911/inventory-v6/PAINTERS.md)
· [Monet's artwork and museum checklist](research/popular-artists-20260911/inventory-v6/painters/claude-monet.md)
· [Research findings and unresolved candidates](research/popular-artists-20260911/FINDINGS.md)

[Last full-catalogue snapshot, before the popular-artist additions](research/painter-review/snapshots/round-02-smk-cleveland/PAINTERS.md)

Each painter links to their own Markdown file containing **every artwork currently
linked to them**, source references, image checks and ten research-round checkboxes.
Works without a named linked creator have a separate checklist and are not omitted.

## Current progress

- Implemented and ran the [resumable all-popular cycle](research/popular-cycle-20260911/PAINTERS.md):
  **100/100 painters, 22,232 artworks**, 100 bounded official catalogue searches,
  134 returned candidates. Added **27 authentic CC0 images across 27 painters**,
  all under 100 KB; Corot's date conflict remains deferred. Current totals:
  **106,195 artworks, 608 pictures**; popular cohort **410 pictures**.
  Monet now has **298 works and 31 pictures**. No new artwork imports in this cycle.
  [Method, limits and resuming](POPULAR_RESEARCH_CYCLE.md). Full research remains open.
- Earlier pass outcomes below are historical snapshots.
- Latest [Nationalmuseum follow-up](research/popular-artists-20260911/NATIONALMUSEUM-FOLLOWUP.md):
  ten object notices checked; Monet's *View over the Sea* now has a source-supported
  creation year of 1882. Six further leads require dating review. Image requests
  returned HTTP 403 and were paused; no new artworks or images in this pass.
- Popular-artists passes, 11 September: **100 artists and all 22,232 linked artworks**
  inventoried in individual Markdown files; every work has recorded holding evidence.
  This is not a claim that every museum association was independently rechecked.
- Across the popular-artist passes, added **234 Marmottan works**, enriched one existing work
  and added **150 NGA images plus 13 SMK images**, all below 100,000 bytes.
  The latest [SMK follow-up](research/popular-artists-20260911/SMK-FOLLOWUP.md)
  checks 41 image gaps; 28 remain unresolved. It adds no new artwork records.
  Current catalogue: **5,328 artists, 106,195 artworks and 581 pictures**.
  Nothing was published.
- Monet: **298 works and 30 pictures**; Marmottan coverage grew from 1 to 120 works.
  Thirty-nine Marmottan source candidates remain deferred; Orsay access and
  Marmottan image permission remain open. Forty-six Chicago image candidates
  are documented but downloads were stopped on HTTP 403. No painter or full
  round was automatically marked done.

Earlier full-catalogue round history (counts refer to those immutable snapshots):

- Initial inventory: 5,315 painters and 105,943 distinct artworks.
- Two Greek additions: thirteen new painters and eighteen artworks; now **5,328
  painters and 105,961 artworks**. All new catalogue records remain in review.
- Latest cohort: Anna Ancher, Elisabeth Jerichau-Baumann and two El Greco works;
  fifteen authentic museum images added, each below 100,000 bytes. Now 418 pictures.
- Round 1: twelve bounded painter reviews completed; eighteen artwork reviews
  completed. Michael Economou and Sofia Laskaridou remain blocked on birth dating.
- Round 2 has started independently while round 1 remains open: fourteen artwork
  reviews completed, five blocked. No painter in this new cohort is marked finished.
- **No full-catalogue research round is complete. Rounds 3–10 have not started.**
- The two new El Greco images are Cleveland CC0 reproductions. Earlier Greek-museum
  image-permission gaps remain open; an image investigation is not a downloaded file.

[Method, ten-round plan and continuation instructions](research/painter-review/README.md)
· [Latest Greek findings and evidence](research/painter-review/greek-round-01-report-v2.md)
· [Round-2 research and source conflicts](research/painter-review/round-02-research.md)
· [Round-2 changes and verification](research/painter-review/round-02-audit.md)
· [First Greek cohort](research/painter-review/greek-round-01-report.md)

## Meaning of “done”

Research checkboxes require an explicit source-backed decision for the exact
version of the record. An image, an empty artwork list, a successful SQL query or
a script rerun does **not** complete a painter review. Adding an artwork or
changing reviewed facts makes the corresponding old review stale.

An individual painter's first pass covers their current database works plus the
documented source search for additions. It does not claim to exhaust their oeuvre
or every museum's catalogue. Full rounds require all painters and artworks,
including anonymous/unlinked records, to have matching review decisions.

Nothing was committed, published, deployed or applied in Terraform.
