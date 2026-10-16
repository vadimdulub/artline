#!/usr/bin/env python3
"""Finalize bounded batch 159 when SAAM shard 15 has no eligible delivery."""
import copy, csv, fcntl, gzip, importlib.util, json, os, subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000159"
R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000159"
SRC = Path.home() / "Library/Application Support/Artline/source-metadata/continuous-production-20261011/000159/saam-15.txt"
MID = "259d7efe-d565-56bf-bdc0-b467d3b2f69b"
for p in (E, R, E / "source-captures"):
    p.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location("delivery159", ROOT / "ops/india-300-delivery-20261011.py")
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
def save(name, value): h.save(E / name, value); return value

raw = SRC.read_bytes(); objects = [json.loads(x) for x in raw.splitlines()]
body = E / "source-captures/saam-15.body.gz"; body.write_bytes(gzip.compress(raw, mtime=0))
receipt_path=E/"source-captures/saam-15.receipt.json"
receipt = h.load(receipt_path) if receipt_path.exists() else save("source-captures/saam-15.receipt.json", dict(
    url="https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/saam/15.txt",
    status=200, retrieved_at=h.now(), sha256=h.sha(raw), bytes=len(raw), body_path=str(body.relative_to(ROOT))))
assert receipt["sha256"]==h.sha(raw) and receipt["bytes"]==len(raw)

classified=[]
with h.connect() as db:
    for o in objects:
        c=o.get("content",{}); d=c.get("descriptiveNonRepeating") or {}; ft=c.get("freetext") or {}
        link=d.get("record_link",""); oid=link.rsplit("=",1)[-1] if "?id=" in link else None
        def vals(k,label=None): return [x["content"] for x in ft.get(k,[]) if label is None or x.get("label")==label]
        title=(d.get("title") or {}).get("content"); dates=vals("date","Date"); media=((d.get("online_media") or {}).get("media") or [])
        row=dict(native_id=oid,title=title)
        if not oid or not title or not dates or len(media)!=1:
            row["decision"]="missing_required_identity_date_or_single_image"; classified.append(row); continue
        matches=[dict(x) for x in db.execute("SELECT id::text,title,primary_media_id::text,creation_year_start,creation_year_end,date_display,status FROM artworks WHERE normalized_title=%s AND current_institution_id=%s AND status<>'archived'",(h.norm(title),MID))]
        native=[dict(x) for x in db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='saam-object' AND external_id=%s",(oid,))]
        eligible=[a for a in matches if a["primary_media_id"] is None and a["creation_year_end"] is not None and a["creation_year_end"]<=1970 and str(a["creation_year_start"]) in dates[0]]
        if native: decision="native_identity_already_present"
        elif len(eligible)==1: decision="eligible_unexpected"
        elif not matches: decision="no_exact_catalogue_title_in_institution"
        elif any(a["primary_media_id"] for a in matches): decision="exact_title_already_illustrated_or_ambiguous"
        else: decision="identity_date_or_scope_not_exact"
        row.update(decision=decision,date=dates[0],title_match_count=len(matches),eligible_count=len(eligible),native_match_count=len(native))
        classified.append(row)
assert len(classified)==len(objects) and not any(x["decision"]=="eligible_unexpected" for x in classified)
decisions=dict(Counter(x["decision"] for x in classified))
save("saam-shard15-identity-reconciliation.json",dict(at=h.now(),captured_records=len(objects),selected=0,decisions=decisions,classified=classified,source_sha256=receipt["sha256"],production_writes=0))

registry=Path("/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv")
required=[ROOT/"AGENTS.md",registry,ROOT/"docs/ARTLINE_IMAGE_USE.md",ROOT/"docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md",ROOT/"docs/LOCAL_DATA_LOCATIONS.md",E.parents[1]/"CHECKPOINT.json",E.parents[1]/"source-queue.json"]
assert len(list(csv.DictReader(registry.open())))==111
save("required-input-verification.json",dict(at=h.now(),registry_rows=111,complete_original_registry_used=True,files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],local_catalogue_connections=0))
actual=subprocess.check_output(["gcloud","sql","instances","describe","artline-postgres","--project=artline-508319","--account=vadim@alingva.com","--format=value(connectionName)"],text=True).strip()
assert actual=="artline-508319:europe-west1:artline-postgres"
proxy=subprocess.check_output(["ps","ax","-o","command="],text=True); assert "--port 55519" in proxy and actual in proxy
save("production-target-reconciliation.json",dict(at=h.now(),connection_name=actual,proxy_port=55519,proxy_command_verified=True,helper="ops/india-300-delivery-20261011.py",shared_ingestion_lock="artline-curated-ingestion",write=False,backup_required=False,local_catalogue_connections=0))
prev=h.load(E.parent/"000107/independent-production-verification.json")
with h.connect() as db: assert h.snapshot(db,list(prev["after"]))==prev["after"]
save("batch107-live-reconciliation.json",dict(at=h.now(),snapshot_equal=True,rows=len(prev["after"]),previous_increments_counted=0))
fr=h.load(E.parent/"000142/french-reserve-live-reconciliation.json"); assert fr["unimported"]==0
save("french-reserve-live-reconciliation.json",dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,prior_verified_evidence=str((E.parent/"000142/french-reserve-live-reconciliation.json").relative_to(ROOT)),plan_sha256=fr["plan_sha256"],prior_actual_visual_review_reused=True,new_visual_review_claim=False))

qp=E.parents[1]/"source-queue.json"; queue=h.load(qp); before=copy.deepcopy(queue)
q=next(x for x in queue["sources"] if x["source_id"]=="smithsonian_open_access")
q.update(status="saam_shard15_classified_no_eligible_exact_missing_image_matches",last_checked_at=h.now(),last_batch=159,checkpoint=str((E/"CHECKPOINT.json").relative_to(ROOT)),resume_cursor=dict(unit="saam",completed_shard="15",next_shard="16",source_sha256=receipt["sha256"],records_classified=len(objects),eligible_exact_missing_image_matches=0,newly_illustrated_native_ids=[],scope="All 59 shard records classified; none met the exact existing-work, missing-primary-image, through-1970, native-identity and single-CC0-image criteria."))
q["evidence_paths"]=[str((E/x).relative_to(ROOT)) for x in ["saam-shard15-identity-reconciliation.json","production-target-reconciliation.json","batch107-live-reconciliation.json","CHECKPOINT.json"]]
with qp.with_suffix(".lock").open("a+") as lock:
    fcntl.flock(lock,fcntl.LOCK_EX); tmp=qp.with_suffix(".159.tmp"); tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+"\n"); os.replace(tmp,qp)
save("source-queue-update-verification.json",dict(at=h.now(),updated_source="smithsonian_open_access",unrelated_entries_preserved=[x for x in before["sources"] if x["source_id"]!="smithsonian_open_access"]==[x for x in queue["sources"] if x["source_id"]!="smithsonian_open_access"],queue_sha256=h.sha(qp.read_bytes()),resume_cursor=q["resume_cursor"]))
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
save("independent-production-verification.json",dict(at=h.now(),verified_counts=counts,production_writes=0,production_ids=[],classification_source_sha256=receipt["sha256"],live_target=actual,batch107_snapshot_equal=True,local_catalogue_connections=0))
save("batch-verification-receipt.json",dict(at=h.now(),verified_counts=counts,production_writes=0,production_ids=[],attribution="No eligible selection and no production mutation; prior programme rows excluded.",shared_ingestion_lock="artline-curated-ingestion",lock_not_acquired_because_no_write=True))
nxt="Process bounded Smithsonian SAAM shard 16 or rotate to another undercovered permitted registry museum; do not replay shards 01–15 or the exhausted French reserve."
evidence=["required-input-verification.json","production-target-reconciliation.json","batch107-live-reconciliation.json","french-reserve-live-reconciliation.json","saam-shard15-identity-reconciliation.json","independent-production-verification.json","source-queue-update-verification.json","batch-verification-receipt.json"]
cp=dict(at=h.now(),batch=159,stage="independently_verified_complete_no_eligible_candidates",researched=dict(french_reserve=188,saam_shard15_records=len(objects)),selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task=nxt,blocker="",evidence=[str((E/x).relative_to(ROOT)) for x in evidence],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0)
save("CHECKPOINT.json",cp); h.save(R/"CHECKPOINT.json",cp)
checked=[]
for n in evidence+["CHECKPOINT.json"]:
    p=E/n; h.load(p); checked.append(dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
save("independent-final-artifact-verification.json",dict(at=h.now(),artifacts=checked,runtime_checkpoint_equal=h.load(R/"CHECKPOINT.json")==cp,passed=True))
result=dict(outcome="no_eligible_candidates",summary="Batch 159 classified all 59 Smithsonian SAAM shard-15 records; none met the established exact missing-image delivery criteria. No production or local-catalogue writes occurred. Live target configuration and interrupted batch 107 were independently reconciled, and the source cursor advanced to shard 16.",next_task=nxt,blocker="",verified_counts=counts,evidence_paths=[str((E/x).relative_to(ROOT)) for x in evidence+["CHECKPOINT.json","independent-final-artifact-verification.json"]])
save("worker-result.json",result); h.save(R/"worker-result.json",result); print(json.dumps(result))
