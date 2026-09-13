# Expanded artwork research, round 4 — 13 September 2026

Started immediately after round 3's local, production and live verification, as requested. This round researches retained Italian museum artworks. It creates no artwork rows, downloads no images and publishes nothing.

## Reviewed plan

- Audited 82,729 remaining unlinked review artworks against a fresh painter inventory.
- Selected **1,102 paintings** for museum metadata enrichment and primary painter links.
- Uses **398 new named painters** with exact documented lifespans and **30 existing painters**.
- Plan SHA-256: `8e498217326ab5598b56c47c14c878c405acc75701f3cc5ff96779f1cfe9b9dc`.
- All records retain review/candidate status. Unknown and qualified date wording remains explicit; no inferred current-display claim or image claim is added.

## Evidence and rules

The source is [Regione Lombardia's official cultural catalogue](https://www.lombardiabeniculturali.it/opere-arte/), using its preserved region-wide CC0 dataset `ay8b-p38f`, captured 10 September 2026. The capture contains 54,488 selected painting/drawing/print/watercolor metadata objects. SHA-256: `0726630aee0ca6b9f81ccab962999f8305a9638dbca833d1ac534254e8f49e04`. Its dataset definition and capture receipts are included. This broader, later capture subsumes the earlier Milan-only metadata snapshot; no additional image assets were fetched.

Matching requires the full normalized creator name, title/subject, documented institution name and exact reconstructed source date wording to match the CSV. Institution variants combine only explicitly supplied institution and subsection fields; a building name alone does not establish a museum. The official [OA field schema](https://www.lombardiabeniculturali.it/docs/bc/oarl.pdf) distinguishes creator biographical data, artwork chronology and chronology qualifiers.

The source matching pass found 1,902 candidates. Multiple creators, non-person creators, attribution qualifications, multi-object groups and unresolved object identity remain held. New painters require an exact closed lifespan; circa/active/open biographies do not become exact birth/death years. Artwork `post`/`ante` wording remains an unknown date pending editorial review; supported `ca` ranges preserve circa precision. Accession numbers absent from the source remain empty.

Before applying, an additional cross-scheme object audit identified **50 source IDs already owned by other catalogue artworks**. Those candidates were removed from the plan and retained for duplicate review, with their existing counterpart recorded. No records were deleted or merged. The unapplied initial draft is preserved under `draft-before-object-audit/`. The final production identity audit checked all 2,398 existing Lombardia/SIRBeC object identifiers and found zero remaining conflicts.

## Backups, application and verification

Fresh backups are under `/Users/vadimdulub/Library/Application Support/Artline/backups/expanded-round4-20260913/`. Local dump: 348,218,179 bytes, SHA-256 `7bd696e04996d6885fca091d94bb4bdf804c1da0b09baf20ea051e44a25c05c7`; its archive directory was checked. Managed production backup `1789302414554` completed successfully.

Private evidence archive: `gs://artline-508319-images/research/expanded-round4-20260913/plan-and-sources-v1.tar.gz`, SHA-256 `4c2a383d7cda873a7a0e265db06263adc817ffe47b3264026e39653434dbc0f3`, 10,368,890 bytes. Cloud object size and MD5 were verified against the local archive.

The existing guarded serializable writer and migration-0018 enrichment ledger are reused with 100-row batches. Historical citation field names retain their `round2_` prefix; full evidence and plan hash distinguish this round. Before applying, all selected local/production rows had identical verification hashes. After checks cover exact links, metadata, review status, provenance and unchanged unrelated fields, excluding independently managed image pointers and audit timestamps. No real-catalogue fixtures or test databases were created. Offline policy tests cover uncertain lifespans, qualified chronology, circa ranges and institution matching. This is not a 10-million-row load test.

Final database/live verification receipts are stored alongside this report.

Completed and verified in both databases: 1,102 additional painter links and metadata enrichments, with 398 new painters. Remaining unlinked review artworks: **81,627**. The selected-row verification SHA-256 is identical locally and in production: `feecf7b6369d88c2986aa9e37d50d901ffd95267b3b57301b2ca61617c0a4c9b`. Live artwork-list checks passed for exact, unknown and circa-range dates, with all metadata matching the plan.
