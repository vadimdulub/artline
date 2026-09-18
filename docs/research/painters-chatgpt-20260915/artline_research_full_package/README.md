# Artline ChatGPT research handoff

Start with `START_HERE_package.zip`. Extract it, attach `START_HERE_images_100.csv`, `START_HERE_painters.csv`, `country_taxonomy.csv`, and paste the text from `RESEARCH_PROMPT.md` into a research conversation. The first assignment contains 100 image gaps across 88 painter identities. Each artwork has its existing Artline page, identifiers, museum/source context and blank fields for verified details and image URLs. Some authoritative object links are missing: finding them is part of the research.

For new-artwork discovery during that job, also attach `START_HERE_existing_artworks.csv` (24,958 existing records associated with those painters), `canonical_redirects.csv` and `new_artworks_template.csv`. This subset cannot exclude matches under unrelated painter identities; the full existing-artwork index is required before a candidate is finally accepted as new.

To focus on painter countries instead, attach `START_HERE_countries_100.csv` with the same prompt and country taxonomy. The full package contains all 3,561 country-gap painters split into 100-profile assignments in `painter_batches/`.

After the first image job, use another file from `batches/`: 473 assignments of up to 250 artworks cover the complete 118,137-row queue. Batches retain priority columns; start with priority 1 within each file. They are partitioned by stable artwork ID, not sorted into priority order. The first 100-image file overlaps these batches; skip task IDs you have already completed. Do not send the entire queue as one research assignment.

## Files

| File | Purpose |
|---|---|
| `STATISTICS.md` | Readable local/production comparison, painter countries and image gaps |
| `statistics.csv`, `statistics.json`, `statistics_by_country.csv` | Machine-readable statistics and definitions |
| `painters_research.csv` | Every active painter with aliases, authority links, artwork/image counts and blank research columns |
| `painters_country_gaps.csv` | Profiles lacking a cultural-affiliation country |
| `painters_existing_countries_to_verify.csv` | 652 profiles with existing country claims still marked not reviewed |
| `artwork_research_queue.csv` | Existing painted/unknown-type artwork gaps, with proposed metadata and licensed-image fields |
| `existing_artworks_index.csv` | Complete production identity context, including archived records; use to detect duplicates |
| `START_HERE_images_100.csv` | First 100 missing-image tasks for popular painters with recorded selection evidence and eligible dates |
| `START_HERE_painters.csv` | Painter context for those 100 tasks |
| `START_HERE_existing_artworks.csv` | Existing-object subset for the starting painter identities |
| `START_HERE_countries_100.csv` | First 100 country-gap profiles, prioritizing existing artwork coverage |
| `new_artworks_template.csv` | Empty header-only template for independently verified new-object proposals |
| `canonical_redirects.csv`, `country_taxonomy.csv` | Existing identity redirects and country vocabulary |
| `field_dictionary.csv` | Column instructions |
| `RESEARCH_PROMPT.md` | Complete copy-and-paste research instructions |
| `validation.json`, `link_checks.json`, `manifest.json` | Export checks, sampled link checks and file checksums |

The CSVs use UTF-8 with a BOM and standard quoting. Unknown values are empty. Some multivalue cells contain JSON arrays; country and artist-slug lists use semicolons. Formula-like text is escaped with an apostrophe. IDs and current fields are immutable input; ChatGPT fills proposed values and evidence columns. These are research worksheets, not files to import blindly into Artline.

Production and local were queried read-only. Local UUIDs are a separately captured slug-based crosswalk, not a guarantee of full parity. Review/publication states remain unchanged. No private reference dataset, descriptions from one, image files, credentials, or private filesystem paths are included in the data handoff. Existing public sources and titles are context to reverify, not a new research result.

All artwork-country context is aggregated from linked artist affiliations and can include qualified/historical attribution roles. Read `current_creator_relationships` and verify the actual maker before proposing countries or images. Empty death years can be appropriate for a living or poorly documented person; never invent one to fill a cell.

Return the completed CSV files for a separately reviewed import. Prefer sourced metadata without a picture when rights are unresolved. Do not publish records merely because one field was verified.

## Regenerating the snapshot

From the Artline repository, run `python ops/export-chatgpt-research.py --output <new-output-directory>`. Use an environment with psycopg and the existing image-research helper's dependencies, authenticated GCP access, and the configured local production database proxy. The exporter creates a new directory, opens both databases read-only, never prints credentials, and fails instead of overwriting an existing snapshot. It produces the raw CSVs and statistics; this dated handoff also adds the prompt, summaries and convenient starting packages.
