# Authorized production influence import — 8 October 2026

**Subsequent publication:** the user explicitly approved these records. All 6,379 imported claims were published at **2026-10-08 18:35:05 UTC**, preserving their citations and confidence. The [publication report](production-publication.md) explains the live API checks and the separate painter-profile visibility requirement. The import receipts below describe the earlier review-state transaction and remain immutable.

The user authorized production delivery with “go ahead! update the prod db”. The import transaction committed at **2026-10-08 18:14:10 UTC**. All new claims initially had **review** status and were not publicly displayed by the published-only influence API.

| Production addition | Rows |
|---|---:|
| Artistic influence relationships | 2,192 |
| Teaching relationships, kept separate | 4,179 |
| Documented admiration relationships | 8 |
| **Total new relationships** | **6,379** |
| Source citations | 7,427 |
| Source registry entries | 10 |

Immediately after the import, the database had 6,389 influence-claim records: 6,379 new review records and the 10 existing published claims. The researched Eugène Boudin → Claude Monet influence already existed, so it was skipped. Its record and citations were preserved. All 6,380 research rows are accounted for; no additional identity or chronology holds arose during production mapping. These are catalogue-record counts, retaining the separate existing painter records rather than merging identities.

The import used pinned production painter IDs and checked them against current records and authority identifiers. Inspiring painters absent from the catalogue remain source labels with supporting authority evidence; no placeholder painter records were created. Original source labels, URLs, statement IDs, available references, revision links, source dates, passage hashes and qualifications remain in the citations. Wikipedia citations include contributor attribution and the CC BY-SA 4.0 licence link.

Evidence grades use the existing database vocabulary conservatively: 64 claims have `documented` evidence and high confidence; 1,357 have medium confidence and 4,958 have low confidence. The latter groups use `editorial_inference` because the current vocabulary has no separate “source assertion awaiting independent verification” category. Their notes explain the actual source-review status. A single scholarly interpretation is not promoted to scholarly consensus. Every imported claim initially remained in review, including the museum-supported claims; subsequent publication preserved all these evidence grades.

The import preserved the 10 original claims and their citations, all 3,745 referenced painter rows and their identifiers, and reused the existing Wikidata source. The new registry entries identify the actual museums, WikiArt, Wikipedia contributors and the scholarly publication. Artist review states, publication states, metadata, artworks, images, holdings and display claims were not updated. The real local database was accessed read-only and still has zero influence claims.

The affected production data was backed up before writing:

`/Users/vadimdulub/Library/Application Support/Artline/backups/painter-influences-20261008/production-plan-v1-before.json.gz`

Backup SHA-256: `2d6bd2aeaac0c697c49945ab0ca15b5b5d09e3c9b6f3025f8798cbbf634edc3b`.

The [immutable plan](production-plan-v1.json.gz) pins the input files, importer and backup. Its SHA-256 is `fef16ec93f0088bb45050fe091c5b8b28e0c6c7b3b815265ce9951db664324fb`. Full protected preimages are stored in the backup directory, not duplicated in the project. The [plan summary](production-plan-v1-summary.json), [commit receipt](production-plan-v1-applied.json) and [independent readback receipt](production-plan-v1-verified.json) record the resulting counts and content hashes.

Seven pure import-policy tests and fourteen research-consistency checks passed. The complete prepared data was checked for source/target direction, production identity mapping, type preservation, citation coverage and review status. The production transaction checked exact preimages, inserted in bounded batches, and verified all new content before commit. A separate read-only transaction confirmed that every new claim is cited, audited and in review, and that the protected existing content is unchanged. Catalogue cache revision advanced from 830 to 831 through the existing invalidation triggers.

The [importer](../../../ops/apply-painter-influences-20261008.py) uses deterministic IDs, an advisory lock and an influence-table write lock. It performs inserts only, without conflict-upserts or schema changes. Its replay verification is specific to the original review state: after publication, use the separate [publication verifier](../../../ops/publish-painter-influences-20261008.py), because the original importer intentionally rejects the changed status. The import itself used no fixtures, local-database mutations, publication, deployment or commits. The [original research limitations](README.md) still apply; unreviewed biography leads and the research hold file were not ingested as confirmed relationships.
