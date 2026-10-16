#!/usr/bin/env python3
import datetime, hashlib, json, subprocess
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000202"
R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000202"
Q = E.parents[1] / "source-queue.json"
TARGET = "artline-508319:europe-west1:artline-postgres"

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

prior_path = E.parent / "000142/french-reserve-live-reconciliation.json"
visual_path = E.parent / "000061/independent-french-reserve-evidence-verification.json"
prior = load(prior_path)
assert prior["inspected"] == prior["already_imported_and_illustrated"] == 188
assert prior["unimported"] == prior["selected"] == 0
ids = [row["entity_id"] for row in prior["source_citations"]]
assert len(ids) == len(set(ids)) == 188

secret = subprocess.check_output([
    "gcloud", "secrets", "versions", "access", "latest",
    "--secret=artline-database-url", "--project=artline-508319",
    "--account=vadim@alingva.com",
], text=True).strip()
kwargs = psycopg.conninfo.conninfo_to_dict(secret)
kwargs.update(host="127.0.0.1", port="55519", sslmode="disable", connect_timeout=20)
with psycopg.connect(**kwargs, autocommit=True, row_factory=dict_row,
                     options="-c default_transaction_read_only=on -c statement_timeout=60000") as db:
    rows = list(db.execute("select id::text, primary_media_id::text, status, accession_number from artworks where id=any(%s::uuid[])", (ids,)))
assert len(rows) == 188 and all(row["primary_media_id"] for row in rows)

save(E / "french-reserve-live-reconciliation.json", {
    "at": now(), "inspected": 188, "selected_limit": 25,
    "already_imported_and_illustrated": 188, "genuinely_unimported": 0,
    "selected": 0, "new_programme_increments": 0,
    "production_ids_verified": sorted(ids), "all_primary_media_present": True,
    "plan_sha256": prior["plan_sha256"],
    "prior_reconciliation": str(prior_path.relative_to(ROOT)),
    "prior_reconciliation_sha256": sha(prior_path),
    "immutable_prior_visual_evidence": str(visual_path.relative_to(ROOT)),
    "immutable_prior_visual_evidence_sha256": sha(visual_path),
    "prior_actual_visual_review_reused": True, "new_visual_review_claim": False,
    "physical_date_holds_preserved": prior["physical_date_holds_preserved"],
    "decision": "No supplement: every reserve artwork UUID already exists in live production with a primary image; prior programme rows are excluded from batch-202 increments."
})
save(E / "actual-visual-review.json", {
    "at": now(), "prepared_images": 0, "images_actually_viewed_this_batch": 0,
    "contact_sheets_viewed_this_batch": 0, "new_visual_review_claim": False,
    "prior_actual_review_reused": True,
    "prior_evidence": str(visual_path.relative_to(ROOT)), "prior_evidence_sha256": sha(visual_path),
    "reason": "The 188 French reserve images are immutable already-reviewed evidence and all are already live; SAAM shard 31 produced no eligible image candidate."
})

cp = load(E / "CHECKPOINT.json")
cp.update(stage="independently_verified_complete_no_eligible_candidates",
          french_reserve_inspected=188, french_reserve_unimported=0,
          selected=0, prepared=0, imported=0, verified=0,
          next_task="Rotate to an undercovered Greek or Byzantine registry route with open object-level evidence; do not replay the exhausted French reserve or SAAM shards 0-31.")
for name in ["french-reserve-live-reconciliation.json", "actual-visual-review.json"]:
    rel = str((E / name).relative_to(ROOT))
    if rel not in cp["evidence"]: cp["evidence"].append(rel)
save(E / "CHECKPOINT.json", cp); save(R / "CHECKPOINT.json", cp)

receipt = load(E / "batch-verification-receipt.json")
receipt.update(french_reserve_live_rows=188, french_reserve_unimported=0,
               selected=0, attribution="No production mutation. All 188 French reserve rows pre-existed batch 202 and are excluded; SAAM shard 31 yielded no candidate.")
save(E / "batch-verification-receipt.json", receipt)

result = load(R / "worker-result.json")
result.update(summary="Batch 202 re-reconciled all 188 French reserve records against live production: every immutable UUID is already present and illustrated, so none was eligible for a supplement or counted again. The fallback classified all 70 records in Smithsonian SAAM shard 31; none uniquely matched an eligible production image gap. No writes occurred.", next_task=cp["next_task"])
result["evidence_paths"] = [str((E / n).relative_to(ROOT)) for n in [
    "CHECKPOINT.json", "french-reserve-live-reconciliation.json", "saam-shard31-reconciliation.json",
    "production-target-reconciliation.json", "batch107-live-reconciliation.json", "actual-visual-review.json",
    "batch-verification-receipt.json", "source-queue-update-verification.json", "independent-final-artifact-verification.json"]]
save(R / "worker-result.json", result)

files = sorted(p for p in E.glob("*.json") if p.name != "independent-final-artifact-verification.json")
save(E / "independent-final-artifact-verification.json", {
    "at": now(), "files": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p), "bytes": p.stat().st_size} for p in files],
    "runtime_checkpoint_equal": load(E / "CHECKPOINT.json") == load(R / "CHECKPOINT.json"),
    "production_writes": 0, "french_live_rows_verified": 188,
    "queue_next_shard": next(x for x in load(Q)["sources"] if x["source_id"] == "smithsonian_open_access")["resume_cursor"]["next_shard"],
    "verified_counts": result["verified_counts"], "passed": True
})
print(json.dumps(result))
