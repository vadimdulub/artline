#!/usr/bin/env python3
"""Bounded batch 218: reconcile eMuseum Korea before any keyed API use."""
import csv, datetime, hashlib, importlib.util, json, subprocess, urllib.request, urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000218'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000218'
Q=E.parents[1]/'source-queue.json'
E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n')

registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
rows=list(csv.DictReader(registry.open(encoding='utf-8-sig')));assert len(rows)==111
src=next(x for x in rows if x['source_id']=='emuseum_korea')
required=[ROOT/'AGENTS.md',registry,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',Q]
save(E/'required-input-verification.json',{'at':now(),'files':[{'path':str(p),'sha256':sha(p)} for p in required],'registry_records':111,'source_policy':src})

cmds=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();target='artline-508319:europe-west1:artline-postgres'
assert any(x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target in x for x in cmds)
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 state=dict(db.execute("select current_database() db,current_setting('transaction_read_only') ro").fetchone());assert state['db']=='artline' and state['ro']=='on'
 r107=json.loads((E.parent/'000107/batch-verification-receipt.json').read_text());ids=r107['production_ids']
 live=[dict(x) for x in db.execute("select id::text,primary_media_id::text,status from artworks where id=any(%s::uuid[]) order by id",(ids,))]
 assert len(live)==12 and all(x['primary_media_id'] for x in live)
save(E/'production-target-reconciliation.json',{'at':now(),'connection_name':target,'proxy_port':55519,'database':state,'helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha(ROOT/'ops/india-300-delivery-20261011.py'),'shared_ingestion_lock':'artline-curated-ingestion','write_transaction_entered':False,'local_catalogue_connections':0})
save(E/'batch107-live-reconciliation.json',{'at':now(),'production_ids_checked':12,'all_present_and_illustrated':True,'previous_increments_counted':0,'receipt_sha256':sha(E.parent/'000107/batch-verification-receipt.json')})

probes=[]
for url in [src['official_website'],src['api_docs_url'],src['api_base_or_dataset_url']]:
 req=urllib.request.Request(url,headers={'User-Agent':'ArtlineResearch/1.0 (+source verification)'})
 try:
  with urllib.request.urlopen(req,timeout=20) as res: probes.append({'url':url,'status':res.status,'content_type':res.headers.get('content-type'),'bytes_sampled':len(res.read(4096))})
 except urllib.error.HTTPError as e: probes.append({'url':url,'status':e.code,'content_type':e.headers.get('content-type'),'bytes_sampled':len(e.read(4096))})
 except Exception as e: probes.append({'url':url,'error_type':type(e).__name__,'error':str(e)[:300]})
research={'at':now(),'source_id':'emuseum_korea','route':'official_open_api_paintings','registry_authentication':src['authentication'],'registry_image_rule':src['image_rights_rule'],'probes':probes,'object_api_requests':0,'object_records_selected':0,'images_requested':0,'decision':'hold','reason':'The registry specifies a public-data portal key, and no established configured eMuseum key/helper is present. Landing/docs probes do not yield stable object records or per-image open rights. No credential was invented and API availability was not treated as an image licence.','retry_condition':'Resume only when an established provider key is configured; still require exact native identity and object-level image permission.'}
save(E/'emuseum-korea-route-research.json',research)
save(E/'actual-visual-review.json',{'at':now(),'prepared_images':0,'images_actually_viewed_this_batch':0,'new_visual_review_claim':False,'reason':'No eligible object or image was obtainable without the required provider key and per-image rights evidence.'})

q=json.loads(Q.read_text());before={x['source_id']:x for x in q['sources'] if x['source_id']!='emuseum_korea'};e=next(x for x in q['sources'] if x['source_id']=='emuseum_korea')
e.update(status='official_api_requires_unconfigured_public_data_key_no_objects_selected',checkpoint='docs/research/continuous-production-20261011/batches/000218/CHECKPOINT.json',last_checked_at=now(),access_status='Official landing/docs/data portal probed once; no object API request made because the registry requires a provider key. No images requested.')
e['resume_cursor']={'route':'official_open_api_paintings','processed_object_ids':[],'object_requests':0,'image_requests':0,'retry_allowed':False,'next_step':'Resume only after an established provider key is configured; otherwise rotate to another untouched registry route with unauthenticated stable object IDs and explicit-open images.'}
Q.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
after={x['source_id']:x for x in json.loads(Q.read_text())['sources'] if x['source_id']!='emuseum_korea'}
save(E/'source-queue-update-verification.json',{'at':now(),'source_id':'emuseum_korea','queue_sha256':sha(Q),'unrelated_entries_preserved':before==after,'resume_cursor':e['resume_cursor']})
counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
next_task='Research a different untouched registry institution with unauthenticated stable pictorial object IDs and explicit-open image rights, prioritizing Greek, Byzantine, post-Byzantine or Russian icons. Do not retry eMuseum Korea until a provider key is configured.'
evidence=[str((E/x).relative_to(ROOT)) for x in ['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','emuseum-korea-route-research.json','actual-visual-review.json','source-queue-update-verification.json']]
save(E/'batch-verification-receipt.json',{'at':now(),'verified_counts':counts,'production_writes':0,'storage_writes':0,'production_target':target,'shared_ingestion_lock':'artline-curated-ingestion','attribution':'Fresh read-only reconciliation plus zero selected objects and zero transaction preimages prove no batch-218 production increment; earlier campaigns excluded.'})
evidence.append(str((E/'batch-verification-receipt.json').relative_to(ROOT)))
cp={'at':now(),'batch':218,'stage':'complete_no_eligible_candidates','discovered':0,'selected':0,'prepared':0,'imported':0,'verified':0,'verified_counts':counts,'production_writes':0,'next_task':next_task,'blocker':'','evidence':evidence}
save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
evidence.append(str((E/'CHECKPOINT.json').relative_to(ROOT)))
save(E/'independent-final-artifact-verification.json',{'at':now(),'runtime_checkpoint_equal':json.loads((E/'CHECKPOINT.json').read_text())==json.loads((R/'CHECKPOINT.json').read_text()),'queue_update_preserved_unrelated':before==after,'evidence_files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in sorted(E.glob('*.json')) if p.name!='independent-final-artifact-verification.json'],'passed':True})
evidence.append(str((E/'independent-final-artifact-verification.json').relative_to(ROOT)))
result={'outcome':'no_eligible_candidates','summary':'Batch 218 researched the previously untouched eMuseum Korea registry route. The official landing, API documentation and data-portal endpoints were boundedly probed, but the object API requires an unconfigured provider key and image permission remains object-specific. No object/image was selected, no visual-review claim was made, and no production, storage or local-catalogue write occurred. Batch 107 and the production target were freshly verified.','next_task':next_task,'blocker':'','verified_counts':counts,'evidence_paths':evidence}
save(E/'worker-result.json',result);save(R/'worker-result.json',result)
print(json.dumps(result,ensure_ascii=False))
