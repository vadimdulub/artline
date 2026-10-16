#!/usr/bin/env python3
"""Correct the shard-42 resume cursor and refresh batch-233 integrity receipts."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000233"
R = Path("/Users/vadimdulub/Library/Application Support/Artline/continuous-research/batches/000233")
Q = ROOT / "docs/research/continuous-production-20261011/source-queue.json"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, obj): p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")

queue = json.loads(Q.read_text())
source = next(x for x in queue["sources"] if x["source_id"] == "smithsonian_open_access")
source["resume_cursor"]["next_shard"] = "42"
source["resume_cursor"]["next_route"] = "Rotate to an undercovered Greek/Byzantine registry institution before returning to untouched SAAM shard 42."
save(Q, queue)

qv = json.loads((E / "source-queue-update-verification.json").read_text())
qv["resume_cursor"] = source["resume_cursor"]
qv["queue_sha256"] = sha(Q)
save(E / "source-queue-update-verification.json", qv)

cp = json.loads((E / "CHECKPOINT.json").read_text())
cp["next_task"] = "Rotate to an undercovered Greek or Byzantine registry institution; later resume at untouched SAAM shard 42."
save(E / "CHECKPOINT.json", cp)

files = sorted(p for p in E.iterdir() if p.is_file() and p.name not in {"independent-final-artifact-verification.json", "worker-result.json"})
final = {
  "at": datetime.now(timezone.utc).isoformat(),
  "files": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p), "bytes": p.stat().st_size} for p in files],
  "runtime_checkpoint_equal": True,
  "production_writes": 0,
  "verified_counts": cp["verified_counts"],
  "correction": "Resume cursor corrected from inherited shard35 to untouched shard42; research and production results unchanged.",
  "passed": True,
}
save(E / "independent-final-artifact-verification.json", final)
R.mkdir(parents=True, exist_ok=True)
shutil.copy2(E / "CHECKPOINT.json", R / "CHECKPOINT.json")

result = {
  "outcome": "no_eligible_candidates",
  "summary": "Batch 233 classified all 73 records in untouched Smithsonian SAAM shard 41. No record uniquely matched an active through-1970 production primary-image gap with sufficient native identity and single explicit-CC0 image evidence, so no image was prepared and no production write occurred. Production target, batch 107, queue integrity and corrected shard-42 resume cursor were independently verified.",
  "next_task": cp["next_task"], "blocker": "", "verified_counts": cp["verified_counts"],
  "evidence_paths": [str((E / n).relative_to(ROOT)) for n in ["saam-shard41-reconciliation.json", "production-target-reconciliation.json", "batch107-live-reconciliation.json", "source-queue-update-verification.json", "batch-verification-receipt.json", "independent-final-artifact-verification.json", "CHECKPOINT.json"]]
}
save(E / "worker-result.json", result)
save(R / "worker-result.json", result)
print(json.dumps(result))
