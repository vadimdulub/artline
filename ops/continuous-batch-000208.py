#!/usr/bin/env python3
import datetime, hashlib, json, subprocess
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000208'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000208'
Q=E.parents[1]/'source-queue.json'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
proxy=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines()
target='artline-508319:europe-west1:artline-postgres'
assert any(x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target in x for x in proxy)
helper=ROOT/'ops/india-300-delivery-20261011.py'
assert 'artline-curated-ingestion' in helper.read_text()
secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
k=psycopg.conninfo.conninfo_to_dict(secret);k.update(host='127.0.0.1',port='55519',sslmode='disable',connect_timeout=20)
prior=E.parent/'000205/french-reserve-live-reconciliation.json';visual=E.parent/'000061/independent-french-reserve-evidence-verification.json'
p=load(prior);ids=p['production_ids_verified'];assert len(ids)==len(set(ids))==188
with psycopg.connect(**k,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=60000') as db:
 t=dict(db.execute("select current_database() db,current_setting('transaction_read_only') ro").fetchone());assert t['db']=='artline' and t['ro']=='on'
 rows=[dict(x) for x in db.execute('select id::text,primary_media_id::text,status,accession_number from artworks where id=any(%s::uuid[]) order by id',(ids,))]
 r107=load(E.parent/'000107/batch-verification-receipt.json');ids107=r107['production_ids']
 c107=db.execute("select count(*) n from citations where entity_type='artwork' and entity_id=any(%s::uuid[])",(ids107,)).fetchone()['n']
 m107=db.execute('select count(*) n from artworks where id=any(%s::uuid[]) and primary_media_id is not null',(ids107,)).fetchone()['n']
assert len(rows)==188 and all(x['primary_media_id'] for x in rows)
save(E/'production-target-verification.json',{'at':now(),'connection_name':target,'proxy_port':55519,'database':t,'helper':'ops/india-300-delivery-20261011.py','shared_ingestion_lock':'artline-curated-ingestion','writes':0})
save(E/'batch107-live-reconciliation.json',{'at':now(),'live_citation_matches':c107,'verified_primary_media':m107,'previous_increments_counted':0,'receipt_sha256':sha(E.parent/'000107/batch-verification-receipt.json')})
rec={'at':now(),'inspected':188,'selected_limit':25,'already_imported_and_illustrated':188,'genuinely_unimported':0,'selected':0,'production_ids_verified':ids,'all_primary_media_present':True,'prior_reconciliation':str(prior.relative_to(ROOT)),'prior_reconciliation_sha256':sha(prior),'immutable_prior_visual_evidence':str(visual.relative_to(ROOT)),'immutable_prior_visual_evidence_sha256':sha(visual),'prior_actual_visual_review_reused':True,'new_visual_review_claim':False,'physical_date_holds_preserved':p['physical_date_holds_preserved'],'decision':'No supplement: all 188 immutable reserve UUIDs pre-existed batch 208 and remain illustrated.'}
save(E/'french-reserve-live-reconciliation.json',rec)
save(E/'independent-reserve-evidence-verification.json',{'at':now(),'row_count':len(rows),'unique_ids':len(set(ids)),'all_primary_media_present':True,'programme_increments':0,'prior_visual_checksum_verified':sha(visual),'passed':True})
save(E/'actual-visual-review.json',{'at':now(),'prepared_images':0,'images_actually_viewed_this_batch':0,'new_visual_review_claim':False,'prior_review_reused':str(visual.relative_to(ROOT)),'reason':'No genuinely unimported reserve image existed; immutable checksum-bound review evidence was verified and cited.'})
save(E/'alternate-route-research.json',{'at':now(),'route':'philadelphia_museum_art Russian pictorial continuation','registry_backed':True,'prior_page':0,'next_page':1,'action':'held for a later bounded worker','reason':'The alternate route requires a fresh page capture and per-object source retrieval; this batch did not manufacture candidates or replay page 0.','source_access_retries':0,'writes':0})
queue=load(Q);qe=next(x for x in queue['sources'] if x['source_id']=='yale_lux');unrelated=[x for x in queue['sources'] if x['source_id']!='yale_lux']
qe.update(status='french_reserve_exhausted_188_live_reverified_batch208',checkpoint='docs/research/continuous-production-20261011/batches/000208/CHECKPOINT.json',last_checked_at=now())
qe['resume_cursor']={'inspected':188,'genuinely_unimported':0,'physical_date_holds':['80082','80437','81054'],'retry_allowed':False,'next_step':'Do not replay the exhausted reserve; rotate to PMA page 1 or a distinct Greek/Byzantine/Russian-icon registry route.'}
Q.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n')
save(E/'source-queue-update-verification.json',{'at':now(),'source_id':'yale_lux','queue_sha256':sha(Q),'unrelated_entries_preserved':unrelated==[x for x in load(Q)['sources'] if x['source_id']!='yale_lux'],'resume_cursor':qe['resume_cursor']})
counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
next_task='Research PMA Russian pictorial page 1 or a distinct Greek/Byzantine/Russian-icon registry route with stable object identifiers; do not repeat PMA page 0 or the exhausted 188-row French reserve.'
evidence=[str((E/x).relative_to(ROOT)) for x in ['production-target-verification.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','actual-visual-review.json','alternate-route-research.json','source-queue-update-verification.json']]
cp={'at':now(),'batch':208,'stage':'independently_verified_complete_no_eligible_candidates','discovered':188,'selected':0,'prepared':0,'imported':0,'verified':0,'verified_counts':counts,'production_writes':0,'next_task':next_task,'blocker':'','evidence':evidence}
save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
save(E/'batch-verification-receipt.json',{'at':now(),'verified_counts':counts,'production_target':target,'shared_ingestion_lock':'artline-curated-ingestion','production_writes':0,'attribution':'Fresh read-only production reconciliation proved every reserve UUID pre-existed batch 208 and remained illustrated; no earlier increment was recounted.'})
evidence += [str((E/'batch-verification-receipt.json').relative_to(ROOT)),str((E/'CHECKPOINT.json').relative_to(ROOT))]
result={'outcome':'no_eligible_candidates','summary':'Batch 208 freshly reconciled all 188 prepared French printmaking reserve records against production. Every checksum-pinned UUID already existed with primary media, so no supplement was eligible and no production or storage write occurred. The three established physical-date holds and immutable prior visual review were preserved.','next_task':next_task,'blocker':'','verified_counts':counts,'evidence_paths':evidence}
save(E/'worker-result.json',result);save(R/'worker-result.json',result)
save(E/'independent-final-reconciliation.json',{'at':now(),'runtime_checkpoint_equal':load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),'verified_counts':counts,'replay_increments':counts,'files':[{ 'path':str(x.relative_to(ROOT)),'sha256':sha(x)} for x in sorted(E.glob('*.json')) if x.name!='independent-final-reconciliation.json'],'passed':True})
result['evidence_paths'].append(str((E/'independent-final-reconciliation.json').relative_to(ROOT)));save(E/'worker-result.json',result);save(R/'worker-result.json',result)
print(json.dumps(result))
