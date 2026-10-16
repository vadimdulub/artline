# Museum image recovery — 13 October 2026

Target: 1,000 serial iterations, each checking up to 10 distinct existing museum-held artworks without images. Repeated IDs and infrastructure failures do not count. Museum pages provide identity and image evidence; only independently verified production attachments count as newly illustrated. Other programmes remain unchanged.

Supervisor: `ops/museum-image-recovery-20261013.py`. Runtime and logs: `runtime/`. Progress: `CHECKPOINT.json`; evidence: `batches/`; reports: `hourly/`. Singleton lock inherited by each worker prevents overlap after supervisor crash. Existing production ingestion lock coordinates writes. Three consecutive infrastructure failures create a checkpointed PAUSE; provider-specific holds switch to other sources. Run again to recover after a process interruption. This process depends on the Mac remaining available, account limits and valid credentials.
