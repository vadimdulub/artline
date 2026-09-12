# Continuation prompt — popular-painter research, all-artwork images and visible delivery

> Superseded task ordering,11 September2026 at20:16UTC: the user redirected work to cleanup and a collection-first iteration. Execute [DATA_AND_IMAGE_COLLECTION_PROMPT.md](DATA_AND_IMAGE_COLLECTION_PROMPT.md). The prior four-to-five-hour window was interrupted before completion; do not claim it was fulfilled. Backups have moved: see [LOCAL_DATA_LOCATIONS.md](LOCAL_DATA_LOCATIONS.md). The historical instructions/checkpoints below remain for provenance.

Continue work in `/Users/vadimdulub/Documents/vadim-dulub-git/artline`. Read `AGENTS.md`, `docs/POPULAR_RESEARCH_CYCLE.md`, and `docs/research/popular-resume-20260911-1852/{CONTINUATION,PROGRESS,FINDINGS}.md` first. Inspect the latest receipts rather than repeating completed imports. Preserve all existing work. Do not commit, push, publish, deploy or apply Terraform.

## Current task: finish the active research window

Continue the user's requested four-to-five-hour **active-work** research window across all 100 currently popular painters. Count useful work, not approval waits, idle time or repeated unchanged searches. Do not claim exhaustive coverage or mark painters complete from inventory checks. Prioritize European and smaller regional museums; include Greek, Russian and Byzantine traditions. Use documented alternate artist names, official object notices and permitted open datasets.

Keep ingestion in bounded, resumable Go commands. Back up the local PostgreSQL database before mutations. Verify exact artwork identity, creator, date no later than 1970, museum holding and global deduplication. Preserve uncertain source assertions in research notes; defer conflicts. Collection, ownership and current display are different claims. Never infer masterpiece status. Download only authentic rights-cleared full-composition images, each at most 100,000 bytes. Record per-painter additions, source evidence, image outcomes and unresolved gaps. Verify database preservation and actual image delivery after changes.

Read the latest [continuation checkpoint](research/popular-resume-20260911-1852/CONTINUATION.md) and newer receipts/progress entries. This run began 11 September2026 at18:52:48UTC with106,330 artworks and621 media. Earlier-session additions are already included in that baseline. At19:34UTC this run had added6 Nivaagaard artworks across6 painters and3 SMK Matisse images; the Nivaagaard image batch was staged, not yet applied. Reconcile subsequent receipts and live totals before counting or retrying anything. Do not replay completed imports, use superseded manifests or mistake elapsed time for active work. Exclude service-error interruptions.

## Safe failure handling and retries

The user repeatedly sees `■ {"detail":"Bad Request"}`. Its origin is unresolved: sampled local Artline routes succeeded; no failing request URL/method/status was supplied. Do not claim the error is fixed or belongs to a particular service without evidence.

- Capture the failed operation, sanitized URL, method, actual HTTP status, bounded error body, request ID if available and timestamp. Never log authorization headers, cookies or secret query parameters.
- For an identified read-only GET/HEAD failure, one diagnostic retry is allowed if source policy permits. If the same HTTP400 returns, stop repeating that unchanged request: validate URL encoding, parameter names/types/ranges, cursor and payload against the service contract. Retry only after a justified correction. Record unresolved failures and continue other sources.
- Retry transient transport errors/408/502/503/504 only in bounded attempts with backoff and jitter. Respect Retry-After and per-source budgets. A429 pauses that source; do not immediately loop or change hosts to evade it. Do not retry401/403 or bypass access restrictions. Do not change an unavailable source's rights rules.
- Never automatically replay a database mutation, image attachment or import after an ambiguous result. First inspect the receipt and current database; resume idempotently from the last verified item. Coding-chat/tool-service failures are separate from Artline HTTP failures and may require a new turn; save a checkpoint when possible.

## Additional requested task: research images for EVERY artwork

After the active popular-painter research task, systematically cover the entire eligible artwork inventory, not only popular painters or selected masterpieces. Start the real visibility audit with Monet as below, then work through missing-image queues across all painters. Finding every picture is the objective, not a guarantee: some reproductions are unavailable or restricted.

1. Export a bounded, resumable Go/PostgreSQL inventory grouped by painter and holding institution. Include artwork UUID, exact title, creator/attribution, date, accession, canonical object URL, current media and previous research outcomes. Use keyset pagination and persistent cursors, not a multi-million-record browser payload or one enormous Markdown file. Link a master Markdown index to manageable per-painter/per-batch checklists.
2. Review existing media first for correct identity, file presence, full composition, rights evidence and actual delivery. Preserve valid existing assets and editorial associations; flag suspected wrong images for review instead of silently replacing them.
3. For each genuine gap, consult the exact official catalogue object, an independently permitted open dataset, or a file-specific rights-cleared reproduction. Verify the same physical artwork and version using accession, attribution, date, dimensions and provenance where necessary. Museum identity does not imply ownership or current display. Never copy an image merely because it appears in search results.
4. Download authentic permitted images to local assets in small resumable Go batches, full composition and at most100,000 bytes per new image. Keep source URL, per-image licence, credit, retrieval timestamp, source/derivative hashes and transformation record. Do not substitute AI imagery, similar compositions, detail crops, merchandise or another museum's version.
5. Record distinct outcomes: attached-and-verified; existing-valid; source-has-no-image; rights-deferred; identity-conflict; access-blocked; temporary-error; not-yet-reviewed. Query success, an empty result or one download does not finish a painter. Keep deferred items visible and don't repeatedly revisit unchanged blocked sources.
6. Back up before mutations, deduplicate across the whole database and preserve editorial/media evidence. Verify decoded dimensions, file size, source association, database changes, HTTP delivery and rendered UI. Continue through the next bounded queue immediately, with concise updates and exact checkpoints.

## Required follow-up after the current task: image visibility audit

The user reports: **“For Claude Monet I don't see any pictures.”** Treat this as an unresolved user-visible issue even if database image counts are nonzero. Start with Monet, then review other popular painters systematically.

1. Read the browser skill before interacting with the local app. Reproduce the real painter timeline/right panel, catalogue and museum views, including default popular-painter filtering and relevant preview/public states. Capture evidence at desktop and mobile sizes.
2. Trace each missing-image state from the UI through the bounded Go API, artwork-to-media association, rights/visibility rules, asset URL, HTTP response and local file. Check filtering, pagination, ordering, lazy loading and fallbacks. A successful database count or direct asset request alone is not a passing UI test.
3. Distinguish genuinely absent images from attached images hidden by incorrect API/UI behavior or unavailable files. Fix in-scope implementation defects and add regression tests. Do not publish review records, weaken access control, invent image rights, or silently change editorial selections to make pictures appear.
4. Make available images discoverable without loading a painter's entire collection in the browser; backend owns bounded filtering, counts and ordering. Preserve factual chronological ordering where required. Clearly distinguish missing images, deferred rights and loading failures.
5. For genuine gaps, research the exact work and permitted reproduction. Keep full composition and the 100,000-byte limit. Do not substitute a visually similar painting, AI-generated artwork, cropped merchandise photo or another museum's version.
6. Re-test the user journey and record screenshots, verified image counts, repaired causes and remaining rights/source gaps in the painter's Markdown checklist and the session checkpoint.

Send concise progress updates while executing. If an unavoidable execution limit is reached, save an exact continuation checkpoint with completed receipts, active processes, remaining commands and measured—not inferred—work duration.
