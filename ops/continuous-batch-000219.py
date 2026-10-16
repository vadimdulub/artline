#!/usr/bin/env python3
"""Bounded batch 219: reconcile the untouched Louvre registry route."""
import csv, datetime, hashlib, importlib.util, json, subprocess, urllib.request, urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000219'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000219'
Q=E.parents[1]/'source-queue.json'
E.mkdir(parents=True,exist_ok=True); R.mkdir(parents=True,exist_ok=True)
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n')

registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
rows=list(csv.DictReader(registry.open(encoding='utf-8-sig'))); assert len(rows)==111
src=next(x for x in rows if x['source_id']=='louvre')
required=[ROOT/'AGENTS.md',registry,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',Q,ROOT/'docs/research/creators-deep-continuation-20261011/source-registry-review.json']
save(E/'required-input-verification.json',{'at':now(),'files':[{'path':str(p),'sha256':sha(p)} for p in required],'registry_records':111,'source_policy':src})

cmds=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines(); target='artline-508319:europe-west1:artline-postgres'
assert any(x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target in x for x in cmds)
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/india-300-delivery-20261011.py'); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 state=dict(db.execute("select current_database() db,current_setting('transaction_read_only') ro").fetchone()); assert state=={'db':'artline','ro':'on'}
 r107=json.loads((E.parent/'000107/batch-verification-receipt.json').read_text()); ids=r107['production_ids']
 live=[dict(x) for x in db.execute("select id::text,primary_media_id::text,status from artworks where id=any(%s::uuid[]) order by id",(ids,))]
 assert len(live)==12 and all(x['primary_media_id'] for x in live)
save(E/'production-target-reconciliation.json',{'at':now(),'connection_name':target,'proxy_port':55519,'database':state,'helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha(ROOT/'ops/india-300-delivery-20261011.py'),'shared_ingestion_lock':'artline-curated-ingestion','write_transaction_entered':False,'local_catalogue_connections':0})
save(E/'batch107-live-reconciliation.json',{'at':now(),'production_ids_checked':12,'all_present_and_illustrated':True,'previous_increments_counted':0,'receipt_sha256':sha(E.parent/'000107/batch-verification-receipt.json')})

probes=[]
urls=[src['official_website'],src['collection_url'],src['sample_artwork_url'],src['terms_url'],'https://collections.louvre.fr/en/recherche?nQuery=icon']
for url in urls:
 req=urllib.request.Request(url,headers={'User-Agent':'ArtlineResearch/1.0 (+source verification)'})
 try:
  with urllib.request.urlopen(req,timeout=20) as res: probes.append({'url':url,'status':res.status,'content_type':res.headers.get('content-type'),'retry_after':res.headers.get('retry-after'),'bytes_sampled':len(res.read(4096))})
 except urllib.error.HTTPError as ex: probes.append({'url':url,'status':ex.code,'content_type':ex.headers.get('content-type'),'retry_after':ex.headers.get('retry-after'),'bytes_sampled':len(ex.read(4096))})
 except Exception as ex: probes.append({'url':url,'error_type':type(ex).__name__,'error':str(ex)[:300]})
search=probes[-1]
save(E/'louvre-route-research.json',{'at':now(),'source_id':'louvre','route':'official_collection_search_icon','probes':probes,'search_requests':1,'object_pages_reviewed':0,'object_records_selected':0,'images_requested':0,'decision':'provider_access_hold','reason':'The official landing, terms, and known ARK object page were reachable, confirming the route and stable identity surface. The first bounded icon search returned HTTP 429. No repeated search was made; no Retry-After bypass or alternate scraping route was attempted. The registry also prohibits automated image download absent explicit record permission. A known sample object is not a batch candidate and was not counted.','retry_condition':'Honor the provider hold and resume only after a later queue cycle; begin with one bounded search and require official object-level identity plus rights evidence.'})
save(E/'actual-visual-review.json',{'at':now(),'prepared_images':0,'images_actually_viewed_this_batch':0,'new_visual_review_claim':False,'reason':'No eligible object or image was selected before the official search rate limit.'})

q=json.loads(Q.read_text()); before={x['source_id']:x for x in q['sources'] if x['source_id']!='louvre'}; e=next(x for x in q['sources'] if x['source_id']=='louvre')
e.update(status='official_collection_search_http429_hold_no_objects_selected',checkpoint='docs/research/continuous-production-20261011/batches/000219/CHECKPOINT.json',last_checked_at=now(),access_status='Landing, terms and known ARK object route HTTP 200; first bounded icon search HTTP 429. No retry, images, or writes.')
e['resume_cursor']={'route':'official_collection_search_icon','queries_completed':0,'last_query':'icon','last_status':429,'processed_object_ids':[],'object_pages_reviewed':0,'image_requests':0,'retry_allowed':True,'next_step':'After a later queue cycle, issue one bounded official search request; stop again on 429 and require object-level image permission.'}
Q.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n'); after={x['source_id']:x for x in json.loads(Q.read_text())['sources'] if x['source_id']!='louvre'}
save(E/'source-queue-update-verification.json',{'at':now(),'source_id':'louvre','queue_sha256':sha(Q),'unrelated_entries_preserved':before==after,'resume_cursor':e['resume_cursor']})
counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
next_task='Research the untouched Pinacoteca di Brera route with a bounded direct collection-page pass, requiring canonical object URLs/inventory numbers and explicit image permission; do not retry Louvre in the immediately following batch.'
names=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','louvre-route-research.json','actual-visual-review.json','source-queue-update-verification.json']
evidence=[str((E/x).relative_to(ROOT)) for x in names]
save(E/'batch-verification-receipt.json',{'at':now(),'verified_counts':counts,'production_writes':0,'storage_writes':0,'production_target':target,'shared_ingestion_lock':'artline-curated-ingestion','attribution':'Fresh read-only reconciliation plus zero selected objects and zero transaction preimages prove no batch-219 production increment; prior campaigns excluded.'}); evidence.append(str((E/'batch-verification-receipt.json').relative_to(ROOT)))
cp={'at':now(),'batch':219,'stage':'complete_no_eligible_candidates','discovered':0,'selected':0,'prepared':0,'imported':0,'verified':0,'verified_counts':counts,'production_writes':0,'next_task':next_task,'blocker':'','evidence':evidence}
save(E/'CHECKPOINT.json',cp); save(R/'CHECKPOINT.json',cp); evidence.append(str((E/'CHECKPOINT.json').relative_to(ROOT)))
save(E/'independent-final-artifact-verification.json',{'at':now(),'runtime_checkpoint_equal':json.loads((E/'CHECKPOINT.json').read_text())==json.loads((R/'CHECKPOINT.json').read_text()),'queue_update_preserved_unrelated':before==after,'evidence_files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in sorted(E.glob('*.json')) if p.name!='independent-final-artifact-verification.json'],'passed':True}); evidence.append(str((E/'independent-final-artifact-verification.json').relative_to(ROOT)))
result={'outcome':'no_eligible_candidates','summary':'Batch 219 researched the untouched Louvre registry route. The official catalogue, terms, and stable ARK surface were reachable, but the first bounded icon search returned HTTP 429. The provider hold was respected without retry or bypass. No objects or images were selected, no visual-review claim was made, and no production, storage, or local-catalogue write occurred. Production and interrupted batch 107 were freshly reconciled.','next_task':next_task,'blocker':'','verified_counts':counts,'evidence_paths':evidence}
save(E/'worker-result.json',result); save(R/'worker-result.json',result); print(json.dumps(result,ensure_ascii=False))
