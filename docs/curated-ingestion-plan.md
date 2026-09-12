# Curated historical-painter import

Requested 2026-09-08. Local database/assets only; no publication, commits or deployment.

## Sequence

1. Enforce the inclusive 1970 creation cutoff and sourced selection at the Go
   import/publication boundaries. Preserve existing research records. Unknown,
   open-ended and crossing-cutoff dates need review.
2. Scope museum queries before artwork enrichment; add relevant search indexes
   and regression/query-plan checks. Do not claim 10-million-row readiness.
3. Select a reproducible cohort of 1,000 historical painters. Pantheon 2025 HPI
   is a popularity proxy, not an objective artistic ranking or a complete canon.
   Retain source identities, source date precision, ranking and attribution.
4. Discover only museum-designated highlights through documented public APIs.
   Match stable authorities, or unambiguous names plus life dates. Do not fuzzy
   merge identities or substitute ordinary holdings to meet an image quota.
5. Import bounded selections in review, with source payload hashes, resumable
   jobs, per-record outcomes and identity constraints. Preserve existing edits.
6. Download only eligible, explicitly reusable selected images, with allowlisted
   HTTPS hosts, byte/dimension limits, checksums, source-policy evidence and credits.
7. Verify idempotence, policy/date/rights/identity gates, database counts, assets
   and bounded API responses; report painters without matched highlights/images.

## Source and licence basis

- [Pantheon datasets](https://pantheon.world/data/datasets),
  [permissions](https://pantheon.world/data/permissions): Datawheel, CC BY-SA 4.0.
  Cite Yu et al. (2016), *Pantheon 1.0, a manually verified dataset of globally
  famous biographies*, Scientific Data 2:150075, doi:10.1038/sdata.2015.75.
  Keep the adapted cohort under CC BY-SA 4.0, distinct from application code.
- [Met API](https://metmuseum.github.io/) and
  [Open Access](https://www.metmuseum.org/hubs/open-access): `isHighlight` is an
  institutional designation; images require `isPublicDomain` and no conflicting
  copyright notice. Use the paginated v1.1 discovery endpoint.
- [Cleveland API](https://openaccess-api.clevelandart.org/): `is_highlight` selects
  institution highlights; the exact record must specify CC0 for image downloading.
- [AIC API](https://api.artic.edu/docs/): investigate explicit institutional
  selection semantics before using search-boost flags as masterpiece evidence.

Museum holdings never imply current display. Imported painters and artworks stay
in review. A painter without a qualifying reproducible image remains an explicit
coverage gap; neither a substitute image nor a masterpiece designation is invented.
