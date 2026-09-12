# Ten-round research programme

Latest continuation, 11 September: the user's popular-only pass has its own
[100-artist inventory](../popular-artists-20260911/inventory-v5/PAINTERS.md) and
[museum/image findings](../popular-artists-20260911/FINDINGS.md). Across these passes
it added 234 works and 163 images, including 13 in the latest SMK image follow-up;
the live catalogue now contains 106,195 works and 581 images.
Chicago's 46 image candidates remain blocked on HTTP 403.
The latest [Nationalmuseum follow-up](../popular-artists-20260911/NATIONALMUSEUM-FOLLOWUP.md)
resolves one Monet creation date and documents further date/image gaps; it adds no works or images.
The counts and round decisions below describe the preceding immutable full
snapshot. They were not promoted to completed reviews by this new import.

The requested task is ten **complete** repetitions of painter discovery, individual
painter research, individual artwork research, permitted image acquisition and
verification. This is a persistent work ledger, not a claim that ten rounds ran.
Twelve bounded first-pass painter reviews and eighteen first-pass artwork reviews
are recorded across two Greek cohorts. Both cohorts belong to round 1.
Round 2 has independently started with Anna Ancher, Elisabeth Jerichau-Baumann
and two El Greco works: fourteen artwork reviews completed, five blocked. Round 1
remains open; starting another evidence pass does not complete an earlier round.

## Files

- [Current full index](snapshots/round-02-smk-cleveland/PAINTERS.md): every painter,
  including those with no artworks, links to a complete individual artwork checklist.
- [Initial inventory](snapshots/round-01-start/PAINTERS.md): immutable pre-addition baseline.
- [Anonymous/unlinked creator checklist](snapshots/round-02-smk-cleveland/UNLINKED_ARTWORKS.md).
- [Current combined decisions](round-02-decisions.json): reviewed facts,
  fingerprints, checked dates, outcomes and evidence URLs; not automatic import flags.
- [Latest Greek source selection](greek-round-01-selection-v2.json): exact museum identities
  and checksum-pinned source captures, outside public assets.
- [Second-cohort report](greek-round-01-report-v2.md): additions, unresolved source
  conflicts, image-permission leads and verification receipts. Earlier snapshots,
  source selections and decisions are retained unchanged.
- [Round-2 research](round-02-research.md) and [implementation audit](round-02-audit.md):
  selected SMK/Cleveland images, date/attribution conflicts and verification.

## Repeat this process in every round, 1–10

1. Export the live local catalogue into a new immutable snapshot. Check exact
   counts and all artist/artwork relationships; do not drop anonymous, qualified,
   non-popular or geographically unclassified records.
2. Work painter by painter. Check identity, alternate names, source dates,
   attributions and the current artwork list. Search documented museum catalogues
   for eligible additions. Record the exact sources searched and their limits.
3. Review every linked artwork in that painter's current database scope: accession,
   title, date precision, attribution, medium, collection credit and holding evidence.
   Preserve uncertain dates and separate holdings from current display.
4. Attempt image research for each work: match the exact object, determine
   per-file reuse permission, then download only an eligible selected reproduction.
   Keep new derivatives at or below 100,000 bytes. No image means an explicit
   permission/identity/access/no-source reason, never a fictional “download done”.
5. Apply only reviewed factual additions locally. Preserve existing data and
   owner selections. Do not infer museum masterpiece status from popularity,
   online availability, or a personal study selection. Do not publish catalogue records.
6. Record human decisions against current fingerprints. A painter can be checked
   done only after all their current works have a completed decision for that round.
   New/changed records reopen that decision. A fully documented missing-image
   outcome may complete research, but never checks the image-file box.
7. Validate row preservation, image bytes/hashes/rights evidence, attribution
   qualifiers, dates, preview access and bounded API pagination. Inventory/file
   audits are not substitutes for source research.
8. Review the discovery gaps again. Prioritize lesser-known Greek and Cypriot
   painters, women artists, Russian icons and Byzantine/post-Byzantine traditions;
   retain workshop and anonymous attribution. Then cover the other regions.
9. Regenerate the list with additions and decisions. Mark a full round complete only
   when every painter and distinct artwork is reviewed, including unlinked creators.
   Separate later-round evidence passes may start while an earlier round is open;
   their completion decisions remain independent and never fill earlier checkboxes.
   Repeat using new evidence and unresolved leads, not copied completion flags.

## Round status

| Round | Status |
|---|---|
| 1 | In progress: 12/5,328 painters and 18/105,961 artworks completed |
| 2 | In progress: 0/5,328 painters and 14/105,961 artworks completed; 5 artwork blocks |
| 3 | Not started |
| 4 | Not started |
| 5 | Not started |
| 6 | Not started |
| 7 | Not started |
| 8 | Not started |
| 9 | Not started |
| 10 | Not started |

## Continue safely

The Go command lives in `apps/server/cmd/review-painters`. From `apps/server`:

```sh
DATABASE_URL='postgres://localhost/artline?sslmode=disable' go run ./cmd/review-painters \
  -mode export -out ../../docs/research/painter-review/snapshots/NEW-SNAPSHOT \
  -decisions ../../docs/research/painter-review/round-02-decisions.json
```

Always use a new output directory; existing snapshots and decisions are never
silently overwritten. Update the stable `docs/PAINTER_REVIEW.md` link only after
the new snapshot passes verification. Future batches need a new reviewed decision
file containing retained prior decisions plus the new evidence-backed decisions.

The offline exporter uses a read-only repeatable-read transaction, a streamed
database traversal and at most one painter's detailed work list in memory. This
is not a public endpoint and no catalogue-sized response goes to Next.js. The
output itself necessarily grows with the inventory; it is not a 10-million-row
performance benchmark or a justification for repeated full scans in API requests.

## Open issues surfaced by the baseline audit

- 418 existing artwork pictures: 256 passed the local file/rights-evidence check;
  161 older files exceed 100,000 bytes; one needs rights-evidence review. No existing
  images were overwritten to make the checks green. Source identity review is separate.
- Round 2 found SMK creation-date basis/notation questions, a Queen Olga attribution
  discrepancy and an oversized legacy Skagens image lacking stored rights evidence.
  The detailed decisions preserve these blocks rather than treating image presence
  as a completed record review. See the round-2 report for each exact object.
- 21 artworks have no linked painter; their source creator labels are preserved.
- Many painter country links are absent; these are coverage gaps, not proof of
  nationality or reason to exclude a painter from research.
- An existing opt-in 100k-row European identity query-plan test failed before
  this programme: the institution/accession branch chose a sequential scan.
  That is a separate unresolved performance issue; do not claim 10m-row readiness.
