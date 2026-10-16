# Continuous production research

Authorized on 11 October 2026. The original 111-source registry is
`/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv`.
Current AGENTS.md and ARTLINE_IMAGE_USE.md supersede older local-write instructions.
The real local catalogue remains read-only. No application deployment is involved.

The supervisor runs serial bounded Codex CLI batches using existing ChatGPT
CLI authentication and the configured model (gpt-6.1-sol at initial launch).
The source prompt is `docs/INFINITE_RESEARCH_PROMPT.txt`.
Worker instructions constrain each invocation to one batch; only the supervisor
starts subsequent sessions. Prepared files and worker starts are not deliveries.
Consult batch verification files before attributing production additions.

Runtime state, per-attempt prompts, JSONL logs and structured outputs:
`/Users/vadimdulub/Library/Application Support/Artline/continuous-research/`

LaunchAgent: `~/Library/LaunchAgents/com.artline.continuous-research.plist`.
It starts at GUI login and restarts the supervisor after abnormal exits.
An exclusive process lock prevents concurrent supervisors. Atomic checkpoints
and per-batch result journals preserve progress. Interrupted writes must be
reconciled against production by the next worker, not blindly replayed.
Three consecutive infrastructure/blocked failures pause execution for inspection.
Temporary failures have bounded backoff; provider holds must not be retried.

The Mac must remain powered on and logged in with network and working credentials.
Caffeinate prevents idle sleep while the supervisor runs; it cannot guarantee
operation through shutdown, closed-lid sleep, network loss or account limits.
The existing Cloud SQL proxy is a dependency, not owned or stopped by this job.

Status:

    python3 ops/continuous-production-research.py status

Graceful stop (finishes the current bounded batch before stopping):

    python3 ops/continuous-production-research.py stop

Resume after inspecting blockers:

    python3 ops/continuous-production-research.py resume
    launchctl kickstart gui/501/com.artline.continuous-research

`CHECKPOINT.json` mirrors cumulative worker-reported verified increments.
Batch evidence lives in `batches/`; the actual production receipts referenced
there provide the evidence. Prior completed campaigns are excluded from totals.
Hourly reports and the 100-hour milestone are emitted during future supervisor
runs; completing 100 hours does not end the programme. Individual sessions
can finish or fail while the supervisor continues.

Offline supervisor checks exercise atomic checkpoint updates, recovery data,
the evidence requirement, task rotation and bounded worker instructions without
creating database fixtures:

    python3 ops/continuous-production-research.py self-test
