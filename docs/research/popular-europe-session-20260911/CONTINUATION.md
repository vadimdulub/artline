# Exact continuation checkpoint — 11 September 2026, 18:49 UTC

The user repeatedly reports `■ {"detail":"Bad Request"}` in the coding conversation. Root cause is **not established**. Artline's recent browser requests returned HTTP 200; a deliberately invalid Artline timeline query returned its own `{ "error": { "code": ..., "message": ... } }` shape, not the reported `detail` shape. No current-date Codex diagnostic files were found at the documented default macOS app/session log locations. Do not claim the platform error was fixed, caused by context size, or caused by permissions. A fresh chat is a recovery option, not a guaranteed repair.

## Verified state

- Database `artline`, local PostgreSQL: **106,330 artworks; 621 media assets; 5,328 artists; 100 popular painters**.
- Session baseline: 106,195 artworks and 608 media. Measured additions: **135 artworks across 43 popular painters, 13 authentic images, four new museum records**. No artist popularity changes, no new inferred masterpieces, no publication or deployment.
- All 135 added artwork detail responses passed API checks. Every metadata batch passed existing-row/editorial-preservation checks. All 13 added images passed file decoding, ≤100,000-byte limits and served-hash checks. Image metadata preserved full composition; selected images were not generated.
- All 100 popular painters have inventory/source-screening checklists. These are **not** 100 completed art-historical reviews. Unresolved research remains unchecked. The latest full inventory `inventory-v1` predates the eleven Athens/Repin additions; generate a new exclusive version when resuming.
- Session began 12:48:18 UTC; this checkpoint is 18:49 UTC. Elapsed time is about six hours, but substantial approval waits and user interruptions occurred. There is no sufficiently precise active-time ledger to claim an exact four-to-five-hour active-work total.

## Applied batches — never reimport a superseded version

| Source | Applied selection directory | Artworks | Receipt directory under `output/popular-europe-session/` |
|---|---|---:|---|
| National Gallery | `ng-v2` | 102 | `ng-apply` |
| Caen | `caen-v3` | 3 | `caen-apply` |
| National Gallery Claude alias | `ng-aliases-v1` | 11 | `ng-aliases-apply` |
| Dürer / Bavaria and loans | `durer-v1` | 8 | `durer-apply` |
| Goulandris Athens | `goulandris-v2` | 5 | `goulandris-apply` |
| National Gallery Athens | `athens-national-v3` | 1 | `athens-national-apply` |
| Russian Museum / Repin | `repin-v1` | 5 | `repin-apply` |

Selection directories are under this checkpoint's directory. Each metadata receipt has corresponding `*-before.json`, `*-after.json`, `*-api.json` verification files in the output directory. Exact SHA pins are in `apps/server/internal/ingest/continuation.go`. Original National Gallery batch has a verified zero-addition replay; later batches still have an optional explicit idempotency verification queued.

Images: `pinakothek-selection.json` / `pinakothek-apply.json` (five), `durer-image-selection.json` / `durer-images-apply.json` (eight). Their after/API receipts passed. All individually licensed CC BY-SA 4.0; full credit and evidence retained.

Backups are in `/Users/vadimdulub/Documents/artline-popular-europe-session-backup-20260911.l1B9ac/`. `before-repin.dump` is the last pre-mutation backup. Take a **new** backup before any further database mutations. Do not restore or overwrite the user's work.

## Remaining research

Read `FINDINGS.md`, `PROGRESS.md` and `review-v1/painters/` for source-specific decisions. All newly reviewed painters have supplements; Repin's five images remain deferred for written permission. Chagall branch/rights, Malevich 1878/1879 birth discrepancy, Crete Baptism 1567/1569 conflict, and El Greco early-1580s interval/fragment relationships remain unresolved. No source bypasses or repeated requests to blocked image hosts.

Next candidates: Athens El Greco *Entombment* Π.9979; Crete *View of Mt Sinai*; explicit Dürer multipart/loan-accession reconciliation; other low-coverage popular painters and regional European museums. Do not focus only on Monet or the easiest source.

## Required next phase: actual picture visibility

Read `docs/POPULAR_RESEARCH_CONTINUATION_PROMPT.md`. The user reports that **Monet has no visible pictures**. This is not yet reproduced or fixed. Database counts show existing images, but that does not establish UI visibility. After finishing/checkpointing the current research cycle, use the browser skill to inspect the real timeline/right-panel, catalogue and museum views. Trace pagination/default ordering, API media fields, visibility/rights and asset delivery. Preserve chronological semantics and backend-owned bounded filtering. Do not publish review records or weaken authorization to make images appear.

Local development processes were left running: Go API port 8080, Next.js port 3000. The old terminal session IDs were 60975 and 40240; a new chat may not be able to reuse them, so check ports before starting duplicate servers. No source collector, importer or image batch is intentionally left running. Editor credentials are in local env files; never print or copy them into reports.

## Useful verification / export commands

From `apps/server`, after inspecting existing outputs:

```sh
go test ./cmd/research-coverage ./cmd/review-masterpieces ./internal/ingest
env 'DATABASE_URL=postgres://localhost/artline?sslmode=disable' go run ./cmd/review-painters -mode export-popular -root ../.. -out ../../docs/research/popular-europe-session-20260911/inventory-v2
```

Tests with an isolated DB fixture require the project's dedicated test setup; do not point destructive integration fixtures at the user's catalogue. No commits, pushes, publication, deployments or Terraform apply.
