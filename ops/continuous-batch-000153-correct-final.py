#!/usr/bin/env python3
"""Correct inherited shard-02 labels after independently verified batch 153."""
import hashlib, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000153"
R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000153"
Q = E.parents[1] / "source-queue.json"

def load(path):
    return json.loads(path.read_text())

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.replace(temp, path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

next_task = (
    "Process bounded Smithsonian SAAM shard 10 or rotate to another undercovered "
    "permitted registry museum if shard 10 is unavailable; do not replay shards "
    "01–09 or the exhausted French reserve."
)
summary = (
    "Batch 153 fully classified all 68 Smithsonian SAAM shard-09 records and "
    "independently verified two new primary images for exact existing artworks: "
    "Somali Man and Reclining Nude. Both CC0 derivatives were individually viewed, "
    "checksum-bound, transactionally attached under the shared ingestion lock, and "
    "publicly verified. Metadata, creators, holdings, and the read-only local "
    "catalogue remained unchanged; the exhausted French reserve was excluded."
)

queue = load(Q)
entry = next(x for x in queue["sources"] if x["source_id"] == "smithsonian_open_access")
entry["status"] = "saam_shard09_two_exact_legacy_primary_images_verified"
entry["last_batch"] = 153
entry["resume_cursor"].update({
    "completed_shard": "09", "next_shard": "10", "records_classified": 68,
    "eligible_exact_missing_image_matches": 2,
    "scope": "All 68 shard records classified; two exact existing SAAM legacy works were eligible and illustrated. Other records were nonmatches, already identified, already illustrated, out of scope, or lacked required exact identity evidence."
})
save(Q, queue)

qv = load(E / "source-queue-update-verification.json")
qv["queue_sha256"] = sha(Q)
qv["resume_cursor"] = entry["resume_cursor"]
save(E / "source-queue-update-verification.json", qv)

cp = load(E / "CHECKPOINT.json")
cp["batch"] = 153
cp["researched"]["saam_shard09_records"] = cp["researched"].pop("saam_shard02_records", 68)
cp["researched"]["saam_shard09_records"] = 68
cp["next_task"] = next_task
save(E / "CHECKPOINT.json", cp)
save(R / "CHECKPOINT.json", cp)

result = load(E / "worker-result.json")
result["summary"] = summary
result["next_task"] = next_task
save(E / "worker-result.json", result)
save(R / "worker-result.json", result)

final = load(E / "independent-final-artifact-verification.json")
final["artifacts"] = [
    {"path": x["path"],
     "sha256": sha(ROOT / x["path"]),
     "bytes": (ROOT / x["path"]).stat().st_size}
    for x in final["artifacts"]
]
final["runtime_checkpoint_equal"] = load(R / "CHECKPOINT.json") == cp
final["passed"] = True
save(E / "independent-final-artifact-verification.json", final)
print(json.dumps(result))
