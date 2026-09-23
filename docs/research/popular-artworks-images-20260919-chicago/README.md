# Popular painters: Chicago catalogue and image round

Research and local import completed on 19 September 2026. **Production delivery is pending Google Cloud reauthentication.** No production rows or images were written by this round.

The round added **1,381 artworks across 60 existing popular painters** and **85 CC0 images across 20 painters** to the local Artline catalogue. All artwork records remain **in review**. The existing database schema is reused; no application deployment or migration is needed.

| Work type | New artwork records | New images |
| --- | ---: | ---: |
| Paintings | 38 | 8 |
| Drawings | 228 | 26 |
| Prints | 1,115 | 51 |
| **Total** | **1,381** | **85** |

The remaining **1,296 new records are metadata-only**. All 85 images illustrate newly added works; this round did not close an image gap on a previously existing artwork. Drawings and prints are not counted as paintings.

## Catalogue coverage

The starting roster was the 100 active artists in Artline's existing popular selection. Exact names or aliases and corroborating life dates established 76 native artist matches in the Art Institute of Chicago API. The capture contains 6,680 artist–object associations representing 6,679 unique museum objects.

For 75 matched artists, the returned count agrees with the museum's reported catalogue total. Whistler's capture is partial: 1,000 of 1,096 associations. The remaining search pages were unavailable and were not bypassed. The 24 artists without an exact corroborated match are unresolved in this source, not proven absent from the museum. This is a museum-specific round, not a claim to have found every artwork worldwide.

[Artist coverage](artist-coverage.json) records the captured count, completeness and additions for each painter. Metadata selection required museum classification, an unqualified artist association, an accession and collection credit, and creation dates within scope. Qualified attributions, uncertain identities, later impressions, loans and unresolved dates were held for review. Another 865 same-artist/title candidates require duplicate or version review before import; separate physical works were not merged.

Eight newly imported date ranges were corrected from abbreviated source text, such as `1916–17`, where the native numeric end omitted the final year. Original wording and museum numeric uncertainty were preserved. The audit checked the museum's deaccession field for every imported object. Holding evidence does not imply that an object is currently on display. The holding country is United States; it is not the artist's nationality.

## Image sources and rights

The [museum API documentation](https://api.artic.edu/docs/) supports factual metadata retrieval. Museum prose descriptions were not imported. Policy evidence was captured from the museum's published [image licensing page through its API](https://api.artic.edu/api/v1/generic-pages/184) and [open-access page through its API](https://api.artic.edu/api/v1/generic-pages/410).

For 84 delivered files, an exact native image-resource record names the object and explicitly says `CC0 Public Domain Designation`. An underlying artwork's public-domain flag alone was insufficient: 937 examined image resources without an explicit resource credit were held for further rights verification. A separately eligible Munch file returned HTTP 403 and was not attached.

The additional image is Velázquez's [Kitchen Scene, accession 1935.380](https://www.artic.edu/artworks/21934). Its [Commons file page](https://commons.wikimedia.org/wiki/File:Diego_Vel%C3%A1zquez_-_Kitchen_Scene_-_1935.380_-_Art_Institute_of_Chicago.jpg) explicitly links the native museum object and licenses the reproduction under CC0. The file's structured data and rendered licensing page were checked at the same revision. All 85 files retain source, exact licence URI, attribution and rights-check evidence. Each was visually inspected. Images preserve the full frame, with proportional resizing and JPEG compression.

A Pissarro Commons photograph remains a lead because its current record did not establish the exact museum inventory match. Repeated Wikimedia replication-lag responses were respected; unavailable metadata was not treated as freshly verified.

## Verified local result

- 1,381 artwork rows agree with the approved source-backed import plan and remain unpublished/in review.
- 85 image receipts, local files, database media and rights references passed the audit.
- All 255 local HTTP checks passed: each image, painter artwork detail and museum artwork detail.
- Before/after checks confirm that attaching the images preserved artwork metadata, creators and native identifiers.
- 31 synthetic verifier and campaign tests passed. No test fixtures were inserted into the real catalogue.
- The import was rerun locally and recognized all 1,381 existing rows without reinserting them.
- Approved image checksums have no within-round duplicates. This does not establish the absence of all visual or physical-object duplicates in the wider catalogue.

External preimage backups are recorded by checksum in the backup manifests and remain under the user's Library/Application Support/Artline/backups directory.

The final local snapshot reports **5,314 paintings by popular painters: 2,343 with usable images and 2,971 without**. Of the paintings already meeting the backend date and selection-evidence conditions, **1,990 lack usable images**. A missing image is a research task, not evidence that a reusable reproduction exists. These are local counts, including concurrent catalogue additions; this batch's attributable changes are the 38 paintings and eight painting images above.

## Evidence and reusable output

- [Aggregate report](final-report.json)
- [Verified artwork JSONL](verified-artworks.jsonl): independent factual metadata and approved image provenance for all 1,381 additions; explicitly marked review/local-imported/production-pending.
- [Final local image audit](local-final-audit-85.json)
- [Metadata audit](local-metadata-final-audit.json)
- [Metadata preservation audit](local-preimage-preservation-audit.json)
- [Local coverage snapshot](local-popular-coverage-final.json)
- [Source-response integrity](source-evidence-integrity.json)

The active `plan.json` and `plan-manifest.json` govern database writes. `review-drafts/` preserves superseded research plans as evidence; those drafts must not be imported. Receipt and export files are research artifacts, not application API responses.

## Resume production delivery

Production remains queued because `gcloud` reported reauthentication failure for `vadim@alingva.com`. Sign in using `gcloud auth login vadim@alingva.com`; select project `artline-508319`. Do not share tokens. These commands use the existing Python environment with the project's ingestion dependencies and must run from the repository root:

```sh
ARTLINE_CHICAGO_RUN=docs/research/popular-artworks-images-20260919-chicago
python ops/import-popular-chicago-catalogue.py --run "$ARTLINE_CHICAGO_RUN" --target cloud
python ops/prepare-popular-chicago-delivery.py --run "$ARTLINE_CHICAGO_RUN"
ARTLINE_CHICAGO_DEADLINE=$(python -c 'import time; print(time.time()+7200)')
python ops/upload-overnight-prepared-images.py --run "$ARTLINE_CHICAGO_RUN" --deadline "$ARTLINE_CHICAGO_DEADLINE" --once --per-provider 150
python ops/audit-overnight-local-images.py --run "$ARTLINE_CHICAGO_RUN" --output "$ARTLINE_CHICAGO_RUN/production-audit.json" --target cloud --verify-gcs
```

Stop on any command failure. Native identity and current production collision checks precede writes. The preparation step creates an external production preimage backup before image attachment. Do not bypass a conflict or a rights failure. Audit output filenames are intentionally exclusive; use a new name when auditing again.

Finally, verify the production image bytes and anonymous painter/museum detail responses, and update the report with actual delivery counts. No production verification has yet occurred for this round, and no background uploader is being claimed as running.
