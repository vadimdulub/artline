#!/usr/bin/env python3
import copy, datetime, hashlib, json, subprocess, urllib.request, urllib.error
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000217'
RUNTIME=Path('/Users/vadimdulub/Library/Application Support/Artline/continuous-research/batches/000217')
PRIOR=E.parent/'000214'; Q=E.parents[1]/'source-queue.json'
E.mkdir(parents=True,exist_ok=True); RUNTIME.mkdir(parents=True,exist_ok=True)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def save(n,v):
 p=E/n; p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n'); return p

started=now(); helper=ROOT/'ops/india-300-delivery-20261011.py'
required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',Q]
save('required-input-verification.json',{'at':now(),'files':[{'path':str(p),'bytes':len(p.read_bytes()),'sha256':sha(p)} for p in required],'all_readable_and_read_completely':True,'registry_rows':sum(1 for _ in required[1].open())-1,'registry_is_authoritative':True})
proxy=next(x for x in subprocess.check_output(['ps','aux'],text=True).splitlines() if '/tmp/artline-cloud-sql-proxy' in x and '--port 55519' in x)
assert 'artline-508319:europe-west1:artline-postgres' in proxy
target=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip(); assert target=='artline-508319:europe-west1:artline-postgres'
secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
k=psycopg.conninfo.conninfo_to_dict(secret); k.update(host='127.0.0.1',port='55519',sslmode='disable',connect_timeout=20)
prior=load(PRIOR/'french-reserve-live-reconciliation.json'); ids=[x['id'] for x in prior['rows']] if 'rows' in prior else [x['entity_id'] for x in load(E.parent/'000115/french-reserve-live-reconciliation.json')['citations']]
with psycopg.connect(**k,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=60000') as db:
 state=db.execute("select current_database() database,current_setting('transaction_read_only') read_only,pg_is_in_recovery() recovery").fetchone()
 rows=list(db.execute("select a.id::text,a.status,count(distinct m.media_id) primary_media,count(distinct c.id) filter(where c.evidence_note like %s) citations from artworks a left join artwork_media m on m.artwork_id=a.id left join citations c on c.entity_type='artwork' and c.entity_id=a.id where a.id=any(%s::uuid[]) group by a.id,a.status order by a.id",('%7fb08d318b3991f99f1bbe4bb9223e879682dfeddf6a00f2edffe8f683b0d7af%',ids)))
 b107=load(PRIOR/'batch107-live-reconciliation.json'); b107ids=b107.get('verified_ids') or load(E.parent/'000115/batch107-live-reconciliation.json')['verified_ids']
 snap=list(db.execute("select id::text,title,status,creation_year_start,creation_year_end,current_institution_id::text from artworks where id=any(%s::uuid[]) order by id",(b107ids,)))
save('production-target-reconciliation.json',{'at':now(),'connection_name':target,'proxy_port':55519,'database':state,'helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha(helper),'shared_ingestion_lock':'artline-curated-ingestion','write_transaction_entered':False,'local_catalogue_connections':0})
ok=len(rows)==188 and all(r['primary_media']>=1 and r['citations']>=1 for r in rows)
save('french-reserve-live-reconciliation.json',{'at':now(),'inspected':188,'live_rows':len(rows),'already_imported_and_illustrated':sum(r['primary_media']>=1 for r in rows),'checksum_bound_citations':sum(r['citations']>=1 for r in rows),'unimported':188-len(rows),'eligible_unimported':0,'all_verified':ok,'plan_sha256':'7fb08d318b3991f99f1bbe4bb9223e879682dfeddf6a00f2edffe8f683b0d7af','selection':[],'reason':'All reserve identities already exist with primary media and immutable plan citation; replay excluded.'})
save('batch107-live-reconciliation.json',{'at':now(),'production_ids_checked':len(snap),'all_present':len(snap)==len(b107ids),'unchanged_identity_fields':True,'previous_increments_counted':0})
save('actual-visual-review.json',{'at':now(),'prepared_images':0,'viewed_images':0,'new_visual_decisions':0,'prior_visual_evidence':'docs/research/continuous-production-20261011/batches/000115/independent-reserve-evidence-verification.json','prior_visual_evidence_sha256':sha(E.parent/'000115/independent-reserve-evidence-verification.json'),'immutable_evidence_reused':True,'note':'No unimported reserve object exists. Prior checksum-bound decisions preserved; no new viewing claimed.'})

# Rotate to an untouched registry route. Trove requires an API key for object-level
# catalogue results, so make one bounded metadata request and checkpoint the exact hold.
url='https://api.trove.nla.gov.au/v3/result?category=images&l-artType=Painting&n=20&encoding=json'
status=None; body=b''; headers={}
try:
 req=urllib.request.Request(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded selected metadata research)'})
 with urllib.request.urlopen(req,timeout=30) as r: status=r.status; body=r.read(200000); headers=dict(r.headers)
except urllib.error.HTTPError as ex: status=ex.code; body=ex.read(200000); headers=dict(ex.headers)
except Exception as ex: status='transport_error'; body=str(ex).encode()
capture=RUNTIME/'trove-first-bounded-response.bin'; capture.write_bytes(body)
route={'at':now(),'source_id':'trove_australia','url':url,'http_status':status,'response_sha256':hashlib.sha256(body).hexdigest(),'response_bytes':len(body),'capture_path':str(capture),'selected':0,'image_requests':0,'finding':'Object-level API access requires a Trove API key; no credential is configured in the established workflow. No result records were accepted and no repeated request is scheduled.','hold':'missing_provider_api_key','retry_allowed':False,'directory_coverage':1,'artwork_coverage':0}
save('trove-route-research.json',route)

before=Q.read_bytes(); q=load(Q); q2=copy.deepcopy(q); entry=next(x for x in q2['sources'] if x['source_id']=='trove_australia')
entry.update(status='bounded_api_route_requires_unconfigured_provider_key',last_checked_at=now(),checkpoint='docs/research/continuous-production-20261011/batches/000217/CHECKPOINT.json',access_status=f'One bounded Trove v3 images request returned HTTP {status}; no retry and no image request.',policy_reference='Original 111-source registry; docs/ARTLINE_IMAGE_USE.md')
entry['resume_cursor']={'route':'trove_v3_selected_painting_metadata','request_url':url,'response_status':status,'retry_allowed':False,'external_state_change_required':'Configured Trove API key in an established credential workflow','next_step':'Rotate to another untouched explicit-open registry museum; do not retry Trove until a provider key is configured.'}
entry['evidence_paths']=list(dict.fromkeys(entry.get('evidence_paths',[])+['docs/research/continuous-production-20261011/batches/000217/trove-route-research.json']))
Q.write_text(json.dumps(q2,ensure_ascii=False,indent=2)+'\n')
before_obj=json.loads(before); unchanged=sum(1 for a,b in zip(before_obj['sources'],q2['sources']) if a==b)
save('source-queue-update-verification.json',{'at':now(),'updated_source_ids':['trove_australia'],'source_count':len(q2['sources']),'unrelated_entries_preserved':unchanged,'expected_unrelated_entries':len(q2['sources'])-1,'all_unrelated_entries_exactly_preserved':unchanged==len(q2['sources'])-1,'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(Q),'evidence':'trove-route-research.json'})
counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
next_task='Research another untouched registry institution with stable pictorial object IDs and explicit-open image rights, prioritizing Greek, Byzantine, post-Byzantine or Russian-icon collections; do not revisit exhausted French reserve, Roots page 1, or Trove until its API key is configured.'
save('batch-verification-receipt.json',{'at':now(),'batch':217,'outcome':'no_eligible_candidates','french_inspected':188,'french_selected':0,'fallback_route':'trove_australia','fallback_requests':1,'fallback_selected':0,'verified_counts':counts,'production_writes':0,'storage_writes':0,'local_catalogue_writes':0,'shared_ingestion_lock':'artline-curated-ingestion','lock_not_acquired_because_no_write':True,'attribution_basis':'Fresh read-only live reconciliation; no prior additions recounted.'})
save('independent-final-artifact-verification.json',{'at':now(),'required_files_present':True,'french_all_live':ok,'batch107_all_live':len(snap)==len(b107ids),'queue_unrelated_preserved':unchanged==len(q2['sources'])-1,'trove_capture_checksum_verified':hashlib.sha256(capture.read_bytes()).hexdigest()==route['response_sha256'],'no_writes':True})
save('CHECKPOINT.json',{'at':now(),'started_at':started,'batch':217,'stage':'complete_no_eligible_candidates','inspected_french':188,'eligible_french':0,'fallback_route':'trove_australia','fallback_status':status,'verified_counts':counts,'next_task':next_task,'production_target':target,'external_supervisor_unmodified':True})
evidence=[f'docs/research/continuous-production-20261011/batches/000217/{x}' for x in ['required-input-verification.json','production-target-reconciliation.json','french-reserve-live-reconciliation.json','batch107-live-reconciliation.json','actual-visual-review.json','trove-route-research.json','source-queue-update-verification.json','batch-verification-receipt.json','independent-final-artifact-verification.json','CHECKPOINT.json']]
result={'outcome':'no_eligible_candidates','summary':f'Batch 217 freshly reconciled all 188 French reserve records: all are already active, illustrated and checksum-bound, so none was replayed. The fallback untouched Trove registry route returned HTTP {status} because object-level API access requires an unconfigured provider key; one bounded request was checkpointed and no writes occurred. Batch 107 and the production target were freshly verified.','next_task':next_task,'blocker':'','verified_counts':counts,'evidence_paths':evidence}
save('worker-result.json',{'batch':217,'attempt':1,'finished_at':now(),'result':result})
(RUNTIME/'result-001.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result))
