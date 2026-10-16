#!/usr/bin/env python3
"""Finalize bounded batch 213 after the NGI page-40 transient access hold."""
import csv, copy, datetime, fcntl, importlib.util, json, os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000213"
R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000213"
E.mkdir(parents=True, exist_ok=True); R.mkdir(parents=True, exist_ok=True)

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value

h = module("delivery213", "ops/india-300-delivery-20261011.py")
now = datetime.datetime.now(datetime.timezone.utc)
counts = dict(new_painters=0, new_artworks=0, newly_illustrated=0, alternate_images=0, museum_links=0)
required = [ROOT/"AGENTS.md", Path("/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv"), ROOT/"docs/ARTLINE_IMAGE_USE.md", ROOT/"docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md", ROOT/"docs/LOCAL_DATA_LOCATIONS.md", E.parents[1]/"CHECKPOINT.json", E.parents[1]/"source-queue.json"]
registry = list(csv.DictReader(required[1].open()))
assert len(registry) == 111
h.save(E/"required-input-verification.json", dict(at=now.isoformat(), files=[dict(path=str(p), sha256=h.sha(p.read_bytes()), read_complete=True) for p in required], registry_rows=111, supplementary_review_not_replacement=True))

connection = subprocess.check_output(["gcloud","sql","instances","describe","artline-postgres","--project=artline-508319","--account=vadim@alingva.com","--format=value(connectionName)"], text=True).strip()
assert connection == "artline-508319:europe-west1:artline-postgres"
commands = subprocess.check_output(["ps","ax","-o","command="], text=True).splitlines()
proxy = [x for x in commands if x.startswith("/tmp/artline-cloud-sql-proxy ") and "--port 55519 " in x and connection in x]
assert len(proxy) == 1
with h.connect() as db:
    state = dict(db.execute("SELECT current_database() database, pg_is_in_recovery() recovery, current_setting('default_transaction_read_only') read_only").fetchone())
    assert state == {'database':'artline','recovery':False,'read_only':'on'}
h.save(E/"production-target-reconciliation.json", dict(at=now.isoformat(), connection_name=connection, proxy_port=55519, database=state, helper="ops/india-300-delivery-20261011.py", helper_sha256=h.sha((ROOT/"ops/india-300-delivery-20261011.py").read_bytes()), shared_ingestion_lock="artline-curated-ingestion", write_transaction_entered=False, local_catalogue_connections=0))

prior = h.load(E.parent/"000107/independent-production-verification.json")
with h.connect() as db: live = h.snapshot(db, list(prior['after']))
assert live == prior['after']
h.save(E/"batch107-live-reconciliation.json", dict(at=now.isoformat(), production_ids_checked=len(live), snapshot_equal=True, prior_receipt_sha256=h.sha((E.parent/"000107/independent-production-verification.json").read_bytes()), previous_increments_counted=0))

research = h.load(E/"ireland-page40-pending-research.json")
assert len(research['rows']) == 5 and all(x.get('error_type') == 'ReadTimeout' for x in research['rows'])
hold_until = (now + datetime.timedelta(hours=1)).isoformat()
h.save(E/"source-access-hold.json", dict(at=now.isoformat(), provider="onlinecollection.nationalgallery.ie", route="page40 pending native objects", affected_native_ids=[x['index']['source_id'] for x in research['rows']], outcome="transient_read_timeout", attempts_per_object=1, automatic_retries=0, retry_allowed_after=hold_until, image_host_requested=False, next_action="Rotate to another eligible source; resume these exact IDs only after hold expiry."))
h.save(E/"actual-visual-review.json", dict(at=now.isoformat(), prepared_images=0, actually_viewed_files=[], claim="No image was prepared or visually reviewed."))

Q = E.parents[1]/"source-queue.json"
with (Q.parent/"source-queue.worker.lock").open('a+') as a, (Q.parent/"source-queue.lock").open('a+') as b:
    fcntl.flock(a, fcntl.LOCK_EX); fcntl.flock(b, fcntl.LOCK_EX)
    before = h.load(Q); after = copy.deepcopy(before)
    row = next(x for x in after['sources'] if x['source_id'] == 'national_gallery_ireland')
    row.update(status="page40_pending_native_objects_transient_read_timeout_hold", last_batch=213, last_checked_at=now.isoformat(), checkpoint="docs/research/continuous-production-20261011/batches/000213/CHECKPOINT.json")
    row['resume_cursor'].update(pending_page40_object_ids=["8956","8957","8958","8959","8960"], metadata_hold_until=hold_until, pending_page40_evidence="docs/research/continuous-production-20261011/batches/000213/ireland-page40-pending-research.json", next_step="After the recorded hold expires, resume only native IDs 8956-8960 with one bounded attempt; meanwhile rotate to an untouched explicit-open registry institution, preferably Greek/Byzantine/Russian icon.")
    refs=["docs/research/continuous-production-20261011/batches/000213/ireland-page40-pending-research.json","docs/research/continuous-production-20261011/batches/000213/source-access-hold.json"]
    row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+refs)); row.setdefault('research_history',[]).append(dict(batch=213,at=now.isoformat(),route="page40 pending native objects",researched=5,selected=0,verified_counts=counts,evidence=refs))
    assert [x for x in before['sources'] if x['source_id']!='national_gallery_ireland'] == [x for x in after['sources'] if x['source_id']!='national_gallery_ireland'] and len(after['sources'])==111
    tmp=Q.with_suffix('.batch213.tmp'); tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)); os.replace(tmp,Q)
h.save(E/"source-queue-update-verification.json", dict(at=now.isoformat(), updated_source="national_gallery_ireland", unrelated_entries_preserved=110, original_registry_routes=111, queue_sha256=h.sha(Q.read_bytes()), resume_ids=["8956","8957","8958","8959","8960"], hold_until=hold_until))

next_task="Research a different untouched explicit-open registry museum, prioritizing Greek/Byzantine/Russian icon objects; do not retry NGI IDs 8956-8960 before the recorded hold expires."
evidence=["required-input-verification.json","production-target-reconciliation.json","batch107-live-reconciliation.json","ireland-page40-pending-research.json","source-access-hold.json","actual-visual-review.json","source-queue-update-verification.json"]
checkpoint=dict(at=now.isoformat(),batch=213,status="complete",outcome="no_eligible_candidates",verified_counts=counts,researched=5,selected=0,prepared=0,imported=0,verified=0,next_task=next_task,blocker="",evidence_paths=[f"docs/research/continuous-production-20261011/batches/000213/{x}" for x in evidence],local_catalogue_connections=0,production_writes=0,storage_writes=0,external_supervisor_unchanged=True)
h.save(E/"batch-verification-receipt.json",checkpoint); h.save(E/"CHECKPOINT.json",checkpoint); h.save(R/"CHECKPOINT.json",checkpoint)
assert h.load(E/"CHECKPOINT.json") == h.load(R/"CHECKPOINT.json")
print(json.dumps(checkpoint))
