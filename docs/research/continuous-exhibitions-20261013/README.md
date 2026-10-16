# Continuous exhibition research — 13 October 2026

The user explicitly invoked `docs/INFINITE_EXHIBITION_RESEARCH_PROMPT.md`.
A dedicated macOS LaunchAgent runs `ops/continuous-exhibition-research.py`, which
starts one bounded Codex research worker at a time and owns continuation.
The separate artwork research supervisor and its configuration are unchanged.

## Scope and delivery

Exhibitions remain within the documented historical scope, 1600–1989, excluding
photography and sculpture. Artwork creation is a separate test: through 1970,
with only documented exceptions. The completed through-1979 linking batch is
not a general scope extension. New records retain appropriate review states;
active catalogue visibility is independent of legacy publication status.
Qualified attributions, unknown dates, partial checklists, historical venue
labels and touring-stop distinctions must remain explicit.

Cloud SQL and Storage, including necessary authentication, secret/proxy access,
backups and public-delivery verification, are authorized. Translation, deletion,
commits, pushes, deployment and infrastructure changes are excluded. The real
local database stays read-only. Each production batch must inspect its target,
use checksum-pinned plans, transaction preimages and audit evidence, coordinate
on `artline-curated-ingestion` and `2026101201` advisory locks, and independently
verify attributable additions before reporting them.

`source-queue.json` records the original 111 registry sources and its checksum.
Arthive is a separately identified additional source; the original CSV remains
unchanged. Existing historical research is a recovery/discovery lead, not new
programme output. Source-specific access holds and image policies still apply.
Images require authentic exact-object identity, actual visual review, rights
and credits, full-frame proportional derivatives at most 100,000 bytes, original
archives and checksum-verified public delivery.

## Persistence and recovery

- LaunchAgent: `~/Library/LaunchAgents/org.artline.continuous-exhibition-research.plist`.
- Runtime: `~/Library/Application Support/Artline/continuous-exhibition-research/`.
- Supervisor lock: runtime `supervisor.lock`, inherited by the worker so a
  supervisor crash cannot start a concurrent replacement worker.
- Current state: runtime `state.json` and this directory's `CHECKPOINT.json`.
- Worker prompts/logs/results: runtime `batches/NNNNNN/`.
- Evidence and finalized result journals: `batches/NNNNNN/` in this directory.
- Hourly summaries: `hourly/`, including source queue, holds, next task and totals.
- Source originals and backups: the existing Application Support source-image,
  source-metadata and backup locations; no large originals in Documents.

Results are journaled before state advances. Interrupted attempts carry recovery
context into the next invocation and must reconcile live writes before retrying.
Three consecutive infrastructure/account failures create a checkpointed `PAUSE`;
retries use backoff, and exhausted providers must give way to eligible routes.
The 100-hour milestone is reported without stopping. No spending budget is
invented. Execution depends on this Mac being available and its user session,
network, authentication, storage and configured account limits.

Commands from the repository:

```sh
python3 ops/continuous-exhibition-research.py status
python3 ops/continuous-exhibition-research.py stop
# After an explicit user resume, clear the hold and restart the LaunchAgent:
python3 ops/continuous-exhibition-research.py resume
launchctl kickstart gui/$(id -u)/org.artline.continuous-exhibition-research
```

Stop is graceful after the current bounded batch. An active inherited lock
prevents another worker from starting. The worker does not control its own
supervisor, prompt, schema, schedules or other programmes.

## Verification and results

Five isolated tests cover directory separation, atomic checkpoints, the delivery
evidence gate, inherited-lock exclusion and bounded worker instructions. No
catalogue fixtures or test databases are used. Initial launch verification found
both the supervisor and worker alive, the worker holding the singleton lock,
and the separate artwork supervisor still running.

Only independently verified changes in finalized batch journals count toward
programme totals. The earlier 10,406-exhibition reconciliation and concurrent
Danish/SMK work are excluded. Discovered, prepared and held candidates are not
production additions. Consult `CHECKPOINT.json` for current verified totals and
the current batch. Batch 1 independently verified **two new artist participation
links** (Pancrace Bessa and Georg Dionysius Ehret) in the existing 1976
“Gardener’s Pride” exhibition. One existing event was enriched; no new events,
main artworks or images were added. Arthive returned HTTP 429 and is held.
Batch 2 started automatically, with its inherited singleton lock verified.
See `continuation-verification.json` and `batches/000001/verification.json`.
