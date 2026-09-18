# Artline: verified research handoff

Start with [REPORT.md](REPORT.md), then paste [RESEARCH_PROMPT.md](RESEARCH_PROMPT.md) into ChatGPT and attach the relevant CSVs. The archive contains metadata and image-source links; artwork binaries and database backups remain in their dedicated local/GCS locations.

- `artworks_added_active.csv`: 2,767 active additions, including reconciled replacement identities.
- `artworks_added_this_session.csv`: gross inserted rows, including later archived duplicates.
- `artwork_identity_index_*.csv`: complete local catalogue identity baseline, split into bounded files.
- `artworks_NL_*.csv` and other country files: country-focused research; multiple affiliations can overlap.
- `painters_country_inventory.csv`, `painters_country_gaps.csv`, `country_source_evidence.csv`: creator identities and documented cultural affiliations.
- `verified_selected_images.csv`: selected authentic reproductions, rights, credits, local paths and production URLs.
- `confirmed_duplicate_consolidations.csv`, `same_title_primary_pair_review.csv`, `unresolved_duplicate_leads.csv`: confirmed decisions versus unresolved research leads.
- `portugal_research_delivery.csv`: actual import/image outcomes and retained holds.
- `unresolved_creators_top_500.csv`: manageable starting queue for creator reconciliation.
- `research_round_ledger.csv`, `local_and_production_delivery.csv`, audit JSONs: completion evidence.

CSV files use UTF-8 with BOM, RFC4180 quoting and JSON for multivalue cells. Formula-leading literal text is prefixed with an apostrophe; that escape is not part of the source wording. Match by stable slug and exact source identity, not a cross-environment UUID. Use canonical redirects before proposing duplicates. The two Walraven historical-attribution works intentionally do not inherit his country. All active additions remain In review.
