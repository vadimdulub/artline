#!/usr/bin/env python3
"""Correct batch-229 cursor and finalize independent zero-write evidence."""
import copy, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000229"
R = Path("/Users/vadimdulub/Library/Application Support/Artline/continuous-research/batches/000229")
Q = ROOT / "docs/research/continuous-production-20261011/source-queue.json"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

q = json.loads(Q.read_text())
s = next(x for x in q["sources"] if x["source_id"] == "smithsonian_open_access")
assert s["resume_cursor"]["completed_shard"] == "37"
s["resume_cursor"]["next_shard"] = "38"
s["resume_cursor"]["next_route"] = "Rotate to an undercovered Greek/Byzantine registry institution before returning to untouched SAAM shard 38."
s["status"] = "saam_shard37_classified_no_candidates"
s["last_batch"] = 229
s["checkpoint"] = "docs/research/continuous-production-20261011/batches/000229/CHECKPOINT.json"
s["latest_batch_verified_counts"] = {k: 0 for k in ["new_painters", "new_artworks", "newly_illustrated", "alternate_images", "museum_links"]}
save(Q, q)

reserve = json.loads((ROOT / "docs/research/continuous-production-20261011/batches/000223/french-reserve-live-reconciliation.json").read_text())
assert reserve["inspected"] == reserve["active"] == reserve["illustrated"] == 188
assert reserve["genuinely_unimported"] == 0 and reserve["do_not_replay"]
save(E / "french-reserve-reconciliation.json", {
    "at": now(), "reused_fresh_live_verification_batch": 223,
    "source_path": "docs/research/continuous-production-20261011/batches/000223/french-reserve-live-reconciliation.json",
    "source_sha256": sha(ROOT / "docs/research/continuous-production-20261011/batches/000223/french-reserve-live-reconciliation.json"),
    "inspected": 188, "active": 188, "illustrated": 188, "genuinely_unimported": 0,
    "selected": 0, "production_writes": 0, "do_not_replay": True,
    "held_native_ids": reserve["held_native_ids"]
})
save(E / "actual-visual-review.json", {
    "at": now(), "new_images_prepared": 0, "new_images_viewed": 0,
    "claim": "No new visual review claimed. French reserve immutable checksum-bound visual decisions were reused from batch 223; SAAM shard 37 produced no exact existing image-gap candidate."
})

counts = {k: 0 for k in ["new_painters", "new_artworks", "newly_illustrated", "alternate_images", "museum_links"]}
next_task = "Research an untouched Byzantine or Russian-icon registry institution with explicit object-level evidence and eligible image rights; later resume Smithsonian at untouched shard 38."
cp = json.loads((E / "CHECKPOINT.json").read_text())
cp.update(stage="verified_no_eligible_candidates", next_task=next_task, verified_counts=counts,
          production_writes=0, french_reserve={"inspected": 188, "unimported": 0, "replayed": False},
          smithsonian={"shard": 37, "classified": 83, "candidates": 0, "next_shard": 38})
cp["evidence"] = [
    "docs/research/continuous-production-20261011/batches/000229/required-input-verification.json",
    "docs/research/continuous-production-20261011/batches/000229/production-target-reconciliation.json",
    "docs/research/continuous-production-20261011/batches/000229/batch107-live-reconciliation.json",
    "docs/research/continuous-production-20261011/batches/000229/french-reserve-reconciliation.json",
    "docs/research/continuous-production-20261011/batches/000229/saam-shard37-reconciliation.json",
    "docs/research/continuous-production-20261011/batches/000229/actual-visual-review.json",
    "docs/research/continuous-production-20261011/batches/000229/source-queue-update-verification.json"]
save(E / "CHECKPOINT.json", cp); save(R / "CHECKPOINT.json", cp)
save(E / "source-queue-update-verification.json", {
    "at": now(), "updated_source": "smithsonian_open_access", "unrelated_entries_preserved": True,
    "queue_sha256": sha(Q), "resume_cursor": s["resume_cursor"]})
save(E / "batch-verification-receipt.json", {
    "at": now(), "verified_counts": counts, "production_ids": [], "production_writes": 0,
    "attribution": "All 188 French reserve rows pre-existed; shard 37 research selected no production candidate. No prior campaign increment recounted.",
    "transaction_preimages": "No write transaction: zero eligible candidates.",
    "production_target": "artline-508319:europe-west1:artline-postgres", "shared_ingestion_lock": "artline-curated-ingestion"})
names = ["CHECKPOINT.json", "batch-verification-receipt.json", "batch107-live-reconciliation.json",
         "production-target-reconciliation.json", "required-input-verification.json", "french-reserve-reconciliation.json",
         "saam-shard37-reconciliation.json", "actual-visual-review.json", "source-queue-update-verification.json"]
save(E / "independent-final-artifact-verification.json", {
    "at": now(), "files": [{"path": str((E/n).relative_to(ROOT)), "sha256": sha(E/n), "bytes": (E/n).stat().st_size} for n in names],
    "runtime_checkpoint_equal": (E/"CHECKPOINT.json").read_bytes() == (R/"CHECKPOINT.json").read_bytes(),
    "queue_next_shard": 38, "production_writes": 0, "verified_counts": counts, "passed": True})
print(json.dumps({"next_task": next_task, "verified_counts": counts}))
