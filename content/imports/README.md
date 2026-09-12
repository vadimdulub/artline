# Imported research data and licences

`historical-1000-2026-09/cohort-source.json` is an adapted selection from
[Pantheon 2025](https://pantheon.world/data/datasets), by Datawheel, licensed
**CC BY-SA 4.0** ([source permissions](https://pantheon.world/data/permissions),
[licence](https://creativecommons.org/licenses/by-sa/4.0/)). This adapted cohort
and Pantheon-derived portions of reports retain that licence, independently of
the application code and museum datasets.

Attribution: Yu, A. Z., et al. (2016). *Pantheon 1.0, a manually verified dataset
of globally famous biographies*. Scientific Data 2:150075.
doi:10.1038/sdata.2015.75. Source data version: 2025.

Changes: select 1,000 painter candidates by descending HPI (deterministic QID
tie-break); retain painters whose recorded lives intersect the atlas and who
were born before 1970. Leonardo, classified as INVENTOR by the dataset, is an
explicit exception supported by his existing sourced painter profile. This
candidate filter is NOT evidence that every painter produced qualifying work
before 1970. The creation cutoff is separately enforced on every artwork.

This is a popularity-based starting cohort, not a definitive canon or independent
verification of every primary-occupation classification. The dataset's taxonomy,
internet-language coverage and popularity biases remain editorial review items.
Hokusai's existing profile is retained outside the cohort (the dataset classifies
him as ARTIST). Source names and original raw records are preserved. No new
influence claims or long biographies were generated.

Wikidata enrichment uses CC0 data and keeps missing/redirected authorities as
conflicts. Descriptions are labelled short authority descriptions, not complete
biographies. P135 associations remain unreviewed and may need disambiguation
between artistic, literary or other movements before publication.

Museum object facts/images retain their own source-specific rights. Images are
downloaded only when the exact source record plus institutional policy permits
CC0, with no conflicting copyright notice. Rights/evidence rows and checksums
are stored in PostgreSQL. A museum highlight is not a current-display claim.

`cache/` stores reproducible source payloads, is ignored by Git, and is outside
the web public directory. Import reports are append-only per execution; the last
single-source report is not a whole-database coverage report. Use
`go run ./cmd/audit-curated` for aggregate current counts and image verification.
