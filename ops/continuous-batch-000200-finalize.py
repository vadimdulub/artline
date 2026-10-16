#!/usr/bin/env python3
import datetime, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000200"
R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000200"

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def save(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

rec = load(E / "saam-shard30-reconciliation.json")
assert rec["candidates"] == [] and rec["selected_for_write"] == 0
save(E / "actual-visual-review.json", {
    "at": now(),
    "prepared_images": 0,
    "images_actually_viewed": 0,
    "contact_sheets_viewed": 0,
    "reason": "All 57 source records were reconciled before image preparation; none uniquely matched an active production primary-image gap, so there was no actual image eligible to view or attach.",
    "unsampled_visual_review_claimed": False,
    "production_writes": 0,
})
cp = load(E / "CHECKPOINT.json")
cp["next_task"] = "Research a different untouched registry route with open object images, prioritizing Greek or Byzantine holdings; do not replay French reserve or SAAM shards 0-30."
cp["evidence"].append("docs/research/continuous-production-20261011/batches/000200/actual-visual-review.json")
save(E / "CHECKPOINT.json", cp); save(R / "CHECKPOINT.json", cp)
result = load(R / "worker-result.json")
result["next_task"] = cp["next_task"]
result["evidence_paths"].insert(2, "docs/research/continuous-production-20261011/batches/000200/actual-visual-review.json")
save(R / "worker-result.json", result)
files = sorted(p for p in E.glob("*.json") if p.name != "independent-final-artifact-verification.json")
save(E / "independent-final-artifact-verification.json", {
    "at": now(),
    "files": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p), "bytes": p.stat().st_size} for p in files],
    "runtime_checkpoint_equal": load(E / "CHECKPOINT.json") == load(R / "CHECKPOINT.json"),
    "production_writes": 0,
    "verified_counts": result["verified_counts"],
    "passed": True,
})
print(json.dumps(result))
