# Execution prompt — Artline collection first

Work in `/Users/vadimdulub/Documents/vadim-dulub-git/artline`. Execute this task yourself; do not return only another plan or spawn a replacement session. Read `AGENTS.md`, `docs/LOCAL_DATA_LOCATIONS.md`, and the latest data-collection checkpoint first. Preserve existing editorial work. Do not commit, push, publish, deploy or apply Terraform.

## First iteration: collect and verify data and authentic pictures

Use the **real local PostgreSQL `artline` database** as the source of truth. Query it directly with read-only transactions for audits. Do not create temporary/test databases, seed fixtures into the real database, or run destructive integration tests against it. Back up before import/image mutations, using `/Users/vadimdulub/Library/Application Support/Artline/backups/`; do not scatter dump folders in Documents.

1. Reconcile existing reviewed import manifests, successful application receipts and live database records. Distinguish captured leads, staged candidates, applied records and deferred records. Never say all collected data is imported merely because a file or preview exists. Check exact source identities globally before resuming an interrupted batch; preserve duplicates/conflicts for reconciliation rather than importing them twice.
2. Build a bounded, resumable backend queue for **every eligible painting**, not only popular painters. Include other museum artworks already in scope, including icons and qualified/anonymous creators. Use keyset pages and stable artwork UUIDs, with painter, attribution, dates, holding, accession, source URL, existing media and previous research outcome. Keep anonymous Greek/Russian/Byzantine works visible. Do not place the full collection in the browser or one enormous Markdown document.
3. For each queued work, check whether a valid authentic image is already attached and present on disk. Verify path containment, file existence, byte size, SHA256, complete image decoding, database association, provenance and rights evidence. Flag suspected wrong pictures and legacy oversized files without deleting or silently replacing them. File verification is not art-historical identity verification.
4. Research each actual image gap using the exact official museum catalogue notice and permitted open sources. Match the same physical artwork/version using accession, creator/attribution, title, creation date, dimensions and provenance where needed. Search documented alternate artist names. Prioritize European/regional museums and low-coverage painters; do not concentrate only on Monet or one convenient source.
5. Download only authentic, explicitly reusable reproductions through small resumable **Go** batches. Preserve the full composition; resize/compress each new local image to **at most100,000 bytes**. Save under `apps/web/public/assets/artworks/imported/`, attach it to the correct real database record, and retain exact source/image URLs, licence, credit, retrieval time, source/derivative hashes and transformations. Never use generated images, similar paintings, detail crops, merchandise or another version as substitutes.
6. In parallel with the image queue, add further verified museum artwork metadata when found: creation ends no later than1970; exact attribution and holding supported; global dedup completed. Unknown dates or ranges crossing1970 are deferred. Do not infer ownership, current display or masterpiece status from a museum association, exhibition, or attractive image. Keep new records in review; do not change popularity/editorial selections to improve counts.
7. Record per-item outcomes separately: existing-file-valid; attached-and-verified; captured-not-imported; no-image-at-checked-source; rights-deferred; attribution/identity-conflict; access-blocked; transient-error; not-yet-researched. None of these alone means the painter is fully researched. Use a compact master Markdown index with per-painter/batch checklists, machine-readable receipts and resumable cursors.
8. After each mutation batch, reconcile live rows and files, preserve prior editorial state, fully decode new files and check actual local HTTP delivery. Count new artworks, new images, existing verified files and unresolved gaps separately. A successful download is not proof of a successful attachment, and a successful attachment is not proof of browser visibility.

## Failures and persistence

For a reported `Bad Request`, record sanitized URL, method, HTTP status, bounded body and timestamp. One permitted diagnostic GET/HEAD retry is acceptable; do not repeatedly retry unchanged400s. Validate parameters and encoding before correcting a request. Use bounded backoff for transient failures, honor Retry-After, pause429 sources, and never bypass401/403, robots restrictions, licences or API account requirements. Never blindly replay ambiguous database mutations; reconcile receipts and live state first.

Continue into the next bounded batch after each verification, with concise progress updates. Do useful source-backed work, not repeated unchanged searches or sleeping. Save an exact checkpoint if interrupted. Do not promise that every painting has an obtainable reusable picture or claim exhaustive museum coverage.

This iteration is **data and pictures first**. Defer new design/features. Keep the user's Monet image-visibility complaint queued for a separate real-UI audit after the collection work; do not claim it fixed from database counts alone.

Use the latest checkpoint at `docs/research/data-collection-20260911-2016/CONTINUATION.md`.
Do not mistake legacy catalogue migrations for test data. For icons, a Commons
accession is not sufficient by itself: cross-check subject, attribution, date,
dimensions and the physical side/version against the museum. A conflicting
Commons BXM01544 record has already been found. Keep artwork creation dates
separate from modern photograph dates. Preserve photographer credit and
share-alike licensing where applicable; do not label every old-art image CC0.
Named-painter-only image selectors must not silently exclude documented workshop
or anonymous works. Never invent a painter to make an image importer accept one.

At handoff, report measured live totals, batch additions, actual disk checks, unimported selections, missing/restricted images, verification limits and the next precise queue. Include the prompt and checkpoint paths. Never claim time worked without a recorded interval.
