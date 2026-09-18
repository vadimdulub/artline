# Additional image research round

Completed 2026-09-16T10:20:19Z; elapsed 2.92 hours, including the recorded network interruption.

- **3,138 additional images** verified in both databases and Google Storage.
- **125 images for popular painters**.
- **1,037 new artworks**, plus one existing work with additional official provenance. No new artists.
- All artworks remain **in review**. The existing schema was reused.

| Artwork type | Additional images |
| --- | ---: |
| drawing | 484 |
| painting | 473 |
| print | 2,181 |

Evidence:

- [Aggregate report](final-aggregate-report.json)
- [Approved image manifest](approved-image-manifest.jsonl)
- [Local audit](final-local-image-audit.json)
- [Production and storage audit](final-production-image-audit.json)
- [Metadata and country parity](metadata-parity-audit-corrected.json)
- [Public checks](public-delivery-canaries-final.json)
- [Duplicate image check](cross-catalogue-image-check-final.json)
- [Artifact scan](artifact-safety-scan-final.json)
- [Final test evidence](test-evidence-final.json)
- [Source batches and held candidates](source-batches-final.json)
- [Catalogue statistics](catalogue-statistics-final.json)
- [New artwork image coverage](new-artwork-image-coverage-final.json)

Notes:

- Elapsed time includes a network interruption; source requests and production delivery resumed from saved checkpoints.
- Artwork type counts distinguish paintings, prints and drawings.
- Current museum or Commons file evidence must approve each exact image. Access-denied museum image endpoints were left paused; independently licensed Commons files were verified separately.
- All delivered records were checked automatically against source evidence, local files, production references and storage checksums. Visual checks were sampled.
- Museum country is distinct from artist nationality. Existing unresolved artist-country fields remain unchanged and in review.
- Exact image hashes and authoritative object identifiers were checked for duplicates; this is not an exhaustive near-duplicate visual analysis.
- No commit, deployment, Terraform change or editorial publication was performed.
- A National Gallery of Art museum-detail canary failed during ingestion, then passed after delivery settled. This does not prove that the previously identified route performance issue is fixed; no deployment was performed.

Recovery backups are under `~/Library/Application Support/Artline/backups/images-followup-20260916/`. Source captures and append-only journals preserve both accepted and held candidates. Pending source research may be resumed with the same run directory and a future deadline; do not replace evidence to conceal failures.
