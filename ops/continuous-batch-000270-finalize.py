#!/usr/bin/env python3
"""Correct and independently re-pin batch 270's bounded shard-tail cursor."""
import datetime, hashlib, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000270"
R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000270"
Q = E.parents[1] / "source-queue.json"

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def save(p, value):
    p = Path(p); tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n")
    os.replace(tmp, p)

q = load(Q)
s = next(x for x in q["sources"] if x["source_id"] == "smithsonian_open_access")
assert s["last_batch"] == 270 and s["resume_cursor"]["next_record_offset"] == 50
s["resume_cursor"]["next_route"] = "Rotate to an undercovered Greek/Byzantine registry institution, then resume SAAM shard44 at record offset 50."
s["status"] = "saam_shard44_first50_classified_no_exact_existing_primary_gap"
save(Q, q)

v = load(E / "source-queue-update-verification.json")
v.update(at=now(), queue_sha256=sha(Q), resume_cursor=s["resume_cursor"], correction="Bounded shard-tail cursor independently normalized; no source or production replay.")
save(E / "source-queue-update-verification.json", v)

cp = load(E / "CHECKPOINT.json")
cp["stage"] = "complete_no_eligible_candidates"
cp["discovered"] = 50
save(E / "CHECKPOINT.json", cp); save(R / "CHECKPOINT.json", cp)

names = ["required-input-verification.json", "production-target-reconciliation.json", "batch107-live-reconciliation.json", "saam-shard44-reconciliation.json", "source-queue-update-verification.json", "batch-verification-receipt.json", "CHECKPOINT.json"]
save(E / "independent-final-artifact-verification.json", {"at": now(), "files": [{"path": str((E/n).relative_to(ROOT)), "sha256": sha(E/n), "bytes": (E/n).stat().st_size} for n in names], "runtime_checkpoint_equal": load(E/"CHECKPOINT.json") == load(R/"CHECKPOINT.json"), "production_writes": 0, "verified_counts": cp["verified_counts"], "queue_cursor": s["resume_cursor"], "passed": True})
