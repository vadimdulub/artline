# Overnight image research and delivery

Completed 2026-09-16T03:59:21Z after 8.21 hours. Both databases and Google Storage were checked after delivery.

- **50,740 artwork image attachments** verified in local and production.
- **50,725 unique delivered image files by SHA-256**; 5,189 attachments belong to popular painters.
- **26,003 new artworks**, 11 existing metadata enrichments and **49 new artists** verified in both databases.
- New artist country affiliations are source-backed. All additions remain **in review**.
- 452 image associations with identity, origin or attribution concerns withheld; physical artworks and evidence preserved.

| Artwork type | Delivered images |
| --- | ---: |
| drawing | 11,148 |
| fresco | 2 |
| painting | 8,003 |
| print | 31,549 |
| watercolor | 38 |

| Source adapter | Delivered images |
| --- | ---: |
| night-smk | 11,199 |
| night-nga-commons | 10,231 |
| met | 9,153 |
| night-mia | 4,815 |
| night-fng | 3,710 |
| night-saam | 3,457 |
| cleveland | 3,203 |
| night-cleveland | 1,706 |
| night-rijks | 1,119 |
| night-commons | 764 |
| chicago | 714 |
| night-fsg | 197 |
| night-joconde | 184 |
| night-walters | 150 |
| smk | 136 |
| night-met-commons | 2 |

Files:

- [Aggregate results](final-aggregate-report.json)
- [Approved image manifest](approved-image-manifest.jsonl)
- [Local audit](local-image-audit-final.json)
- [Production and storage audit](production-storage-audit-final.json)
- [Metadata and country audit](metadata-parity-final.json)
- [Public delivery checks](public-delivery-final.json)
- [Shared-image review](shared-image-review-final.json)
- [Final catalogue statistics](catalogue-statistics-final.json)
- [Campaign artifact scan](artifact-safety-scan.json)
- [Test evidence locations](test-log-locations.json)
- [Withheld image associations](withdrawn-images.json)
- [Unresolved-origin public copy retirement](commons-origin-withdrawal-completed.json)
- [Photographer credit corrections](cc-attribution-corrections-verified.json)
- [Unresolved photographer credit holds](cc-attribution-holds-completed.json)
- [Prepared API performance fix](api-detail-fix/review.json)

Validation and limits:

- Artwork attachments, unique compressed image hashes and unique downloaded source hashes are different counts; shared views of museum sets/parts are retained only with documented review.
- Most additions include prints and drawings; paintings and painted works are reported separately.
- All automated source/rights/database/storage checks are complete; visual inspection was sampled, supplemented by duplicate-image review.
- Country totals describe museum locations, using an institution place or unanimous known venue countries. They are never painter-nationality inferences.
- Historical local/production catalogue differences are outside this campaign; imported metadata and delivered images were explicitly matched.
- Museum detail routes previously timed out during heavier ingestion. Current canaries and any remaining failures are recorded. A UUID-scoped performance fix is prepared but remains undeployed pending explicit deployment authorization.

Recovery and resumption:

Recovery manifests and per-batch preimages are under `~/Library/Application Support/Artline/backups/overnight-images-20260915/`. The run stores immutable selected-source receipts, image files and append-only outcome journals. `apply-night-prepared-local.py --once` attaches pending prepared local images; `upload-overnight-prepared-images.py --once` delivers a bounded pending page. Both need `--run` and a future `--deadline`; rerun fresh audits before regenerating a completion report. Never replace evidence files to hide failed or superseded checks.

No commit, Terraform apply, deployment or change from review to published status was performed by this campaign. ART500K and the cancelled private reference dataset were not used.
