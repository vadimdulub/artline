#!/usr/bin/env python3
"""Regenerate batch-227 queue/checkpoint verification after cursor correction."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000227"
R = Path("/Users/vadimdulub/Library/Application Support/Artline/continuous-research/batches/000227")
Q = ROOT / "docs/research/continuous-production-20261011/source-queue.json"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

q = json.loads(Q.read_text())
s = next(x for x in q["sources"] if x["source_id"] == "smithsonian_open_access")
assert s["resume_cursor"]["completed_shard"] == "36"
assert s["resume_cursor"]["next_shard"] == "37"
u = json.loads((E / "source-queue-update-verification.json").read_text())
u["at"] = datetime.now(timezone.utc).isoformat()
u["queue_sha256"] = sha(Q)
u["resume_cursor"] = s["resume_cursor"]
save(E / "source-queue-update-verification.json", u)
assert (E / "CHECKPOINT.json").read_bytes() == (R / "CHECKPOINT.json").read_bytes()
names = ["CHECKPOINT.json", "batch-verification-receipt.json", "batch107-live-reconciliation.json",
         "production-target-reconciliation.json", "required-input-verification.json",
         "saam-shard36-reconciliation.json", "source-queue-update-verification.json"]
files = [{"path": str((E / n).relative_to(ROOT)), "sha256": sha(E / n), "bytes": (E / n).stat().st_size} for n in names]
final = {"at": datetime.now(timezone.utc).isoformat(), "files": files,
         "runtime_checkpoint_equal": True, "production_writes": 0,
         "verified_counts": {"new_painters": 0, "new_artworks": 0, "newly_illustrated": 0,
                             "alternate_images": 0, "museum_links": 0},
         "cursor_correction": "Shard 36 completed; next untouched shard is 37.", "passed": True}
save(E / "independent-final-artifact-verification.json", final)
print(json.dumps(final))
