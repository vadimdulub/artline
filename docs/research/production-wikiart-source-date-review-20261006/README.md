# Production WikiArt museum images — second round, 6 October 2026

**315 retained production image additions across 43 museums in this round;
634 retained additions across both rounds.** Louvre and Prado were excluded.
These counts describe artwork records receiving images; this round uses 314
distinct WikiArt objects because two existing records describe the same work.

The user authorized production updates for matches with at least 90% confidence,
then requested another round and said WikiArt is the source of truth and to add
as much as possible. This preference is recorded in [AGENTS.md](../../../AGENTS.md)
and [ARTLINE_IMAGE_USE.md](../../ARTLINE_IMAGE_USE.md). Confidence is implemented
through corroborating identity checks and editorial review, not a calibrated
probability.

The complete audit covers 253,437 non-archived museum artwork records. The search
expanded exact creator identities, surname-first labels, translated titles in
French, Russian, German, Spanish and Portuguese, and verbatim original titles.
1,649 artist indexes contain 127,377 source works. Only selected reproductions
were downloaded and visually reviewed.

The expanded matching batch retains 205 attachments. An additional source-date
review retains 110 attachments after reconciling eligible WikiArt dates with
missing, unparsed or nearby conflicting catalogue dates. All catalogue dates,
creator relations, holdings and publication/review states were preserved.
Complete-frame application derivatives are at most 100,000 bytes. Per-object
WikiArt rights labels and source evidence were retained; no independent licence
or current-display status was inferred.

Version review corrected the Mariana and Cézanne self-portrait selections before
their respective delivery. Three links were retracted with exact before/after
recovery evidence: Dock at Newport from this round, and two Fear print records,
one from each round. The latter WikiArt article identifies a different Chicago
impression. The prior round therefore retains 319 of its original 320 links.
Source assets and files were preserved. Three additional date-review candidates
remain held for different or unresolved versions, and a watermarked reproduction
was held in the expanded batch.

Final verification checked all 634 retained database links, their source
citations and image/rights records, all three retractions, unchanged artwork
metadata and creators, and fresh live API responses and image bytes for all 43
museums updated this round. No verification errors remain. All 18 offline
identity tests passed; no local catalogue fixtures or writes were used.

- [Combined report with every retained second-round attachment](combined-round2-report.html)
- [Combined counts and museum totals](combined-round2-summary.json)
- [Final current-state production verification](combined-production-verification.json)
- [All 253,437 artwork outcomes](combined-all-artwork-results.json.gz)
- [Editorial version decisions](editorial-version-decisions.json)
- [Date-review visual decisions](visual-review.json)
- [Source-version substitutions](manual-version-resolution.json)
- [Dock at Newport correction](../production-wikiart-authoritative-20261006/version-correction.json)
- [Current-round Fear correction](impression-correction.json)
- [Previous-round Fear correction](../production-wikiart-images-20261006/impression-correction.json)

Earlier batch reports and apply/verification receipts retain their historical
pre-correction counts; the combined report and final verification above are the
current totals. Unmatched or held records remain research outcomes, not evidence
that WikiArt has no image.

Recovery backups are under
`~/Library/Application Support/Artline/backups/`, and originals/contact sheets
under `~/Library/Application Support/Artline/source-images/`, in the matching
operation directories. Cloud SQL backups 1791276936386 and 1791277741792 cover
the second-round batches. No commit or application deployment was performed.
