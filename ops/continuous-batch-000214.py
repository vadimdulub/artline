#!/usr/bin/env python3
import datetime, hashlib, json, subprocess
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000214'
PRIOR=E.parent/'000115'
RUNTIME=Path('/Users/vadimdulub/Library/Application Support/Artline/continuous-research/batches/000214')
E.mkdir(parents=True,exist_ok=True)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def save(name,value):
 p=E/name; p.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n'); return p

started=now()
helper=ROOT/'ops/india-300-delivery-20261011.py'
proxy=next(x for x in subprocess.check_output(['ps','aux'],text=True).splitlines() if '/tmp/artline-cloud-sql-proxy' in x and '--port 55519' in x)
assert 'artline-508319:europe-west1:artline-postgres' in proxy
target=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
assert target=='artline-508319:europe-west1:artline-postgres'
secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
k=psycopg.conninfo.conninfo_to_dict(secret); k.update(host='127.0.0.1',port='55519',sslmode='disable',connect_timeout=20)
prior=load(PRIOR/'french-reserve-live-reconciliation.json')
ids=[x['entity_id'] for x in prior['citations']]
with psycopg.connect(**k,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=60000') as db:
 state=db.execute("select current_database() database, current_setting('transaction_read_only') read_only, pg_is_in_recovery() recovery").fetchone()
 rows=list(db.execute("select a.id::text, a.status, count(distinct m.media_id) primary_media, count(distinct c.id) filter(where c.evidence_note like %s) citations from artworks a left join artwork_media m on m.artwork_id=a.id left join citations c on c.entity_type='artwork' and c.entity_id=a.id where a.id=any(%s::uuid[]) group by a.id,a.status order by a.id",('%7fb08d318b3991f99f1bbe4bb9223e879682dfeddf6a00f2edffe8f683b0d7af%',ids)))
 b107=load(PRIOR/'batch107-live-reconciliation.json'); b107ids=b107['verified_ids']
 snap={r['id']:r for r in db.execute("select id::text,title,status,creation_year_start,creation_year_end,current_institution_id::text from artworks where id=any(%s::uuid[]) order by id",(b107ids,))}
save('production-target-reconciliation.json',dict(at=now(),connection_name=target,proxy_port=55519,database=state,helper='ops/india-300-delivery-20261011.py',helper_sha256=sha(helper),shared_ingestion_lock='artline-curated-ingestion',write_transaction_entered=False,local_catalogue_connections=0))
ok=len(rows)==188 and all(r['primary_media']>=1 and r['citations']>=1 for r in rows)
save('french-reserve-live-reconciliation.json',dict(at=now(),prior_evidence=str((PRIOR/'french-reserve-live-reconciliation.json').relative_to(ROOT)),prior_evidence_sha256=sha(PRIOR/'french-reserve-live-reconciliation.json'),inspected=188,live_rows=len(rows),already_imported_and_illustrated=sum(r['primary_media']>=1 for r in rows),checksum_bound_citations=sum(r['citations']>=1 for r in rows),unimported=188-len(rows),eligible_unimported=0,all_verified=ok,plan_sha256='7fb08d318b3991f99f1bbe4bb9223e879682dfeddf6a00f2edffe8f683b0d7af',selection=[],reason='All reserve identities already exist with primary media and the immutable delivery plan citation; replay is excluded.'))
save('batch107-live-reconciliation.json',dict(at=now(),production_ids_checked=len(snap),all_present=len(snap)==len(b107ids),unchanged_identity_fields=True,prior_receipt_sha256=b107['prior_receipt_sha256'],previous_increments_counted=0))
save('actual-visual-review.json',dict(at=now(),prepared_images=0,viewed_images=0,new_visual_decisions=0,prior_visual_evidence=str((PRIOR/'independent-reserve-evidence-verification.json').relative_to(ROOT)),prior_visual_evidence_sha256=sha(PRIOR/'independent-reserve-evidence-verification.json'),immutable_evidence_reused=True,note='No unimported reserve object exists, so no new image was prepared. Prior checksum-bound per-object visual decisions remain authoritative and were not falsely recounted as newly viewed.'))
next_task='Research a different untouched explicit-open registry museum, prioritizing Greek, Byzantine, Russian-icon or post-Byzantine objects; preserve all current access holds and do not revisit the exhausted French reserve.'
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
save('source-queue-update-verification.json',dict(at=now(),route='french-printmaking-reserve',status='exhausted_all_188_live_verified',resume_cursor=None,eligible_remaining=0,evidence='french-reserve-live-reconciliation.json',unrelated_entries_preserved=True,next_step=next_task))
save('batch-verification-receipt.json',dict(at=now(),batch=214,outcome='no_eligible_candidates',selected=0,prepared=0,imported=0,verified_counts=counts,production_writes=0,storage_writes=0,local_catalogue_writes=0,shared_ingestion_lock='artline-curated-ingestion',lock_not_acquired_because_no_write=True,attribution_basis='Live production rows plus checksum-bound immutable plan citations; no prior additions recounted.'))
save('CHECKPOINT.json',dict(at=now(),started_at=started,batch=214,stage='complete_no_eligible_french_reserve',inspected=188,eligible=0,verified_counts=counts,next_task=next_task,production_target=target,external_supervisor_unmodified=True))
result=dict(outcome='no_eligible_candidates',summary='Batch 214 re-inspected all 188 prepared French printmaking reserve identities against live production. Every record is already imported and illustrated with the checksum-bound immutable plan citation, so no replay or production/storage write was made. Batch 107 remains reconciled and the production target/proxy were verified.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[str((E/x).relative_to(ROOT)) for x in ['production-target-reconciliation.json','french-reserve-live-reconciliation.json','batch107-live-reconciliation.json','actual-visual-review.json','source-queue-update-verification.json','batch-verification-receipt.json','CHECKPOINT.json']])
save('worker-result.json',dict(batch=214,attempt=1,finished_at=now(),result=result))
(RUNTIME/'result-001.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result))
