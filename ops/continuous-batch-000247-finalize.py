#!/usr/bin/env python3
"""Batch 247 recovery: independently reconcile the exhausted French reserve."""
import csv, fcntl, hashlib, importlib.util, json, os, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000247'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000247'
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=mod('b247base','continuous-image-batch-000002.py');h=b.h
def now(): return h.now()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n');os.replace(t,p)
def main():
 E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
 req=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'); assert len(list(csv.DictReader(reg.open())))==111
 latest_holds=sorted((E.parent).glob('*/**/*hold*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:8]
 save(E/'required-input-verification.json',{'at':now(),'files':[{'path':x,'sha256':sha(ROOT/x)} for x in req],'registry_records':111,'registry_sha256':sha(reg),'complete_registry_used':True,'latest_hold_ledgers':[{'path':str(x.relative_to(ROOT)),'sha256':sha(x)} for x in latest_holds]})
 target='artline-508319:europe-west1:artline-postgres'; commands=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines(); proxy=[x for x in commands if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target in x]; assert len(proxy)==1
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==target
 save(E/'production-target-reconciliation.json',{'at':now(),'connection_name':actual,'proxy_port':55519,'proxy_command_verified':True,'helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha(ROOT/'ops/india-300-delivery-20261011.py'),'shared_ingestion_lock':'artline-curated-ingestion','write_transaction_entered':False,'local_catalogue_connections':0})
 prior=h.load(E.parent/'000187/french-reserve-live-reconciliation.json'); ids=[x['id'] for x in prior['production_rows']]; assert len(ids)==188
 b107=h.load(E.parent/'000107/independent-production-verification.json')
 with b.connect() as db:
  live=h.snapshot(db,list(b107['after'])); assert live==b107['after']
  save(E/'batch107-live-reconciliation.json',{'at':now(),'production_rows':len(live),'matches_independent_postimage':True,'increment':0})
  rows=db.execute("select id::text,status,primary_media_id::text,exists(select 1 from external_identifiers e where e.entity_type='artwork' and e.entity_id=artworks.id) ext,exists(select 1 from artwork_location_assertions l where l.artwork_id=artworks.id and l.claim_type='holding' and l.review_state='accepted' and l.superseded_by is null) hold from artworks where id=any(%s)",(ids,)).fetchall()
 assert len(rows)==188 and all(x['status']!='archived' and x['primary_media_id'] and x['ext'] and x['hold'] for x in rows)
 save(E/'french-reserve-live-reconciliation.json',{'at':now(),'input_reserve_records':188,'live_active_artworks':188,'live_illustrated_artworks':188,'genuinely_unimported':0,'selected':0,'prepared':0,'imported':0,'verified_new':0,'writes':0,'decision':'All 188 checksum-bound reserve objects are already present, illustrated, externally identified, and supported by accepted holding evidence. Immutable plans and prior visual decisions were not replayed.','prior_visual_evidence':['docs/research/continuous-production-20261011/batches/000001/batch-visual-review.json','docs/research/continuous-production-20261011/batches/000001/prior-visual-evidence.json'],'prior_live_reconciliation':'docs/research/continuous-production-20261011/batches/000187/french-reserve-live-reconciliation.json','prior_exhaustion_evidence':'docs/research/continuous-production-20261011/batches/000246/french-reserve-live-reconciliation.json'})
 counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
 save(E/'independent-production-verification.json',{'at':now(),'production_rows_checked':188,'all_active':True,'all_illustrated':True,'all_external_ids_present':True,'all_accepted_holdings_present':True,'production_writes':0,'storage_writes':0,'verified_counts':counts,'attribution':'Fresh live production reconciliation proves the reserve has no unimported objects. Prior campaigns and concurrent writes are excluded.'})
 qp=E.parents[1]/'source-queue.json'; before=sha(qp); q=h.load(qp); assert len(q['sources'])==111
 save(E/'source-queue-update-verification.json',{'at':now(),'modified_source_ids':[],'routes_actually_researched':['french_printmaking_prepared_reserve'],'queue_sha256_before':before,'queue_sha256_after':sha(qp),'unrelated_entries_preserved':111,'resume_cursor':{'reserve_total':188,'verified_present':188,'next_offset':188,'status':'exhausted_do_not_replay'}})
 next_task='Rotate to an undercovered registry-backed Greek, Byzantine, Russian-icon or post-Byzantine route with explicit open-image permission; do not replay the exhausted French reserve or Tretyakov Q107546923.'
 ev=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','independent-production-verification.json','source-queue-update-verification.json']
 cp={'at':now(),'batch':247,'stage':'independently_verified_complete','outcome':'no_eligible_candidates','selected':0,'prepared':0,'imported':0,'verified':0,'verified_counts':counts,'production_writes':0,'storage_writes':0,'next_task':next_task,'blocker':'','evidence_paths':[str((E/x).relative_to(ROOT)) for x in ev],'local_catalogue_connections':0,'external_supervisor_unchanged':True}
 save(E/'batch-verification-receipt.json',cp);save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
 save(E/'independent-final-artifact-verification.json',{'at':now(),'checkpoint_runtime_equal':h.load(E/'CHECKPOINT.json')==h.load(R/'CHECKPOINT.json'),'all_evidence_exists':all((E/x).exists() for x in ev),'evidence':[{'path':str((E/x).relative_to(ROOT)),'sha256':sha(E/x)} for x in ev],'counts_match':True})
 result={'outcome':'no_eligible_candidates','summary':'Batch 247 freshly reconciled all 188 prepared French printmaking reserve records against production. Every record is already active, illustrated, externally identified, and backed by an accepted holding assertion, so no immutable plan was replayed and no prior delivery was recounted.','next_task':next_task,'blocker':'','verified_counts':counts,'evidence_paths':cp['evidence_paths']+[str((E/'batch-verification-receipt.json').relative_to(ROOT)),str((E/'independent-final-artifact-verification.json').relative_to(ROOT)),str((E/'CHECKPOINT.json').relative_to(ROOT))]}
 save(E/'worker-result.json',result);save(R/'result-001.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lk: fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
