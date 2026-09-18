# Russian image pass — completion receipt

213 new images verified in local and production; 0 selected images still await preparation. No prepared attachments remain pending.

Read [RESEARCH.md](RESEARCH.md) for the cited findings and [IMAGE-INVENTORY.md](IMAGE-INVENTORY.md) for every selected artwork.

Providers: {'russian-deep-nga': 3, 'russian-deep-met': 2, 'russian-deep-cleveland': 2, 'russian-deep-commons': 206}. Types: {'drawing': 14, 'print': 1, 'painting': 198}. Licenses: {'NGA Open Access — public domain': 3, 'CC0 1.0': 4, 'Public domain': 195, 'CC BY-SA 4.0': 3, 'CC0': 6, 'CC BY-SA 3.0': 2}.

Recovery: local custom-format dump `/Users/vadimdulub/Library/Application Support/Artline/backups/russian-images-deep-20260913/local-before.dump` (381,968,954 bytes, SHA-256 `a637b28bd3de26e32d22919ae8cc82620db4cd7794d20d0c6146ac8829676395`); managed Cloud SQL backup `1789324487279`, verified SUCCESSFUL. pg_restore --list passed; no full restore rehearsal was performed.

Scripts: ops/research-russian-deep-images.py (read-only baseline and metadata research), ops/select-russian-deep-images.py (pin identity and rights), ops/apply-russian-deep-images.py (prepare/apply/evidence), ops/verify-russian-deep-images.py (read-only verification), ops/report-russian-deep-images.py (report/archive). Use `/tmp/artline-images-venv/bin/python` and `PYTHONPYCACHEPREFIX=/tmp/artline-deep-pycache`. Completed selections and receipts are immutable; create a new research run to change them. Preparation and application skip existing receipts. Check provider cooldown evidence before resuming a pending download.

No new artworks, biographies, creation years or current-display claims were manufactured. Existing review/publication states are unchanged. No commits or deployment.
