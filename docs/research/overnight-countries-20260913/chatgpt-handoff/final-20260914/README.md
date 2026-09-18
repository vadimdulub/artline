# Artline research handoff — 14 September 2026

Start with **RESEARCH_PROMPT.md**. This package contains real catalogue data, source evidence and the remaining research queues. The main CSV snapshot was taken at 04:02 UTC; supporting audits were completed afterward. All active additions remain **In review**.

The first 20 rounds for each of ten countries were imported into both databases. Later local updates are pending Google Cloud reauthentication. Portugal has 20 completed research scopes and 74 prepared candidates, including eight explicit identity/source holds; it has **not** been imported into either database. See [the report](REPORT.md) and [delivery ledger](local_and_production_delivery.csv).

To continue in ChatGPT:

1. Paste **RESEARCH_PROMPT.md** into a new research conversation.
2. For a Dutch pass, attach **artworks_NL_001.csv**, **painters_country_inventory.csv**, **institutions_inventory.csv** and **canonical_redirects.json**. Add the country-evidence file when checking existing affiliations.
3. For creator reconciliation, attach **painters_country_gaps.csv** and **unresolved_creators_top_500.csv**. The complete creator queue is also included.
4. For another country, attach its country file(s). Upload the identity-index chunks when a cross-country duplicate search is needed. Ask ChatGPT to inspect the files with its data tools and retrieve relevant rows rather than reproduce whole files in the conversation.
5. Request the proposed artwork, painter-country and duplicate-review CSVs specified in the prompt. Review those proposals before importing them.

| File | Contents |
|---|---|
| artworks_added_active.csv | 2,707 active rows added in this session; includes enriched replacements of older records |
| artworks_added_this_session.csv | All 2,718 inserted rows, including 11 later archived duplicates |
| new_row_identity_review.csv | Identifies 212 active additions reconciled to earlier/other catalogue records; 2,495 active rows had no prior identity found in this audit |
| artworks_NL_001.csv | 5,806 active Dutch-affiliated catalogue works, including the pre-existing baseline |
| artworks_GR/RU/FR/IT/ES/DE/AT/BE/FI/PT_*.csv | Other country inventories; French data spans three files |
| painters_country_inventory.csv | All 12,015 local creator profiles, including archived identities, aliases, authorities and country relationships |
| painters_country_gaps.csv | 3,589 active profiles without a cultural-affiliation assignment |
| country_source_evidence.csv | 13,652 dated country-review citations, including primary museum facts and uncertainty notes |
| institutions_inventory.csv | 587 existing museum/collection profiles; museum country is separate from creator country |
| artwork_identity_index_001–010.csv | All 231,630 artwork rows, including 443 archived records; bounded chunks of at most 25,000 rows |
| canonical_redirects.json | Follow these canonical identities before proposing records or interpreting archived rows |
| verified_selected_images.csv | 1,535 verified image assets with sources, licences, credits, hashes and delivery flags |
| research_round_ledger.csv | 240 distinct country-research scopes: 220 verified in both databases, 20 Portuguese scopes pending import |
| confirmed_duplicate_consolidations.csv | 60 painter and 438 artwork consolidations locally; production status is recorded separately |
| same_title_primary_pair_review.csv | 170 individually reviewed pairs: 166 kept separate, two recto/verso pairs retained, two confirmed Pavia duplicates |
| unresolved_duplicate_leads.csv | 8,475 candidate groups, **not** a deletion list |
| unresolved_creator_labels.csv | 27,252 creator labels covering 69,441 currently unlinked artworks; sample artwork slugs are provided |
| unresolved_creators_top_500.csv | A smaller starting queue, ordered by the number of affected artworks |
| portugal_local_identity_preview.csv | Read-only local checks: 66 potential additions and eight holds; fresh two-database plans are still required |
| institution_identity_review.csv | Three shared-website groups retained as distinct institutions/collection scopes |
| portugal_pending_research.csv | All 74 prepared Portuguese candidates with primary-source corrections and explicit holds |
| LOCAL_AUDIT_SUMMARY.json / ACTIVE_IMAGE_DELIVERY.json | Final local status, country, date and image checks |
| RESUME_PRODUCTION.md | Exact remaining work and the guarded resume command |

Counts in country files overlap when an artist has several documented affiliations. Country research rosters are discovery scopes; roster membership alone is not a verified nationality. Rows in the full identity index can include older, out-of-scope records retained for duplicate checking.

**An inserted row is not necessarily a newly discovered physical artwork.** The identity review found 212 active added rows representing objects already present under another catalogue identity. Eleven added rows were archived after consolidation. The remaining 2,495 are candidates with no prior identity found by this audit; this is not a guarantee of exhaustive uniqueness.

The image ledger includes ten retained assets from duplicate records that are no longer active primary images. There are **1,525 active local primary images** from this session and **1,496 observed on active public production records**. Another **29 active images are local only**, awaiting Cloud sign-in. The 1,506 production-upload count includes the ten retained assets. An archived artwork or retained image is not an instruction to delete its provenance or original file.

CSV files use UTF-8 with BOM and standard CSV quoting. Multivalue cells contain JSON arrays or documented semicolon-separated codes. Blank means unknown or unverified. Formula-leading literal values have an initial apostrophe; remove that escape only when interpreting the original literal text, never execute it as a formula. Preserve Unicode and accession punctuation.

Database IDs can differ between local and production. Use stable slugs and exact source identifiers to match objects. Production UUIDs were observed through public, bounded API pages; this was not a transactionally consistent production database audit. A missing production UUID does **not** prove that the object is absent remotely. The public crosswalk covered 11,954 active painters and 161,944 artwork identities, with no failed queried scopes after retry; 150 painters without locally linked works were not queried for work pages.

`image_delivery_state=local_only_production_pending_cloud_login` means the local file exists but the CSV intentionally leaves its public URL blank. Other pre-existing image rows in country inventories are not all newly audited images; use **verified_selected_images.csv** for this session's checked files. `review` in the database corresponds to the requested `in_review` proposal status. Do not publish records or infer current display from a holding institution.

`manifest.json` describes the original main CSV snapshot; `support-manifest.json` describes supplementary queues. The final package manifest and checksum receipt cover the complete delivered package. Raw museum/Wikimedia captures and mutation preimages remain in the workspace and dedicated Artline backup folders; full museum metadata dumps and original artwork images are intentionally not bundled into this upload package.

Two added works, Q26997957 and Q27000045, intentionally have blank artwork-country cells: their only link to the Dutch painter Isaac Walraven is a museum-rejected historical attribution. The painter has country evidence, but his country is not projected onto those works. See QUALIFIED_CREATOR_COUNTRY_AUDIT.json. Stored institution website fields can contain a shared official catalogue portal; verify an institution-specific website before proposing replacements.
