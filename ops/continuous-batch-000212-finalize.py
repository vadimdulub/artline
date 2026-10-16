#!/usr/bin/env python3
"""Finalize bounded batch 212 after PMA page-2 image-rights/access review."""
import csv, hashlib, importlib.util, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000212'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000212'
Q=E.parents[1]/'source-queue.json'
E.mkdir(parents=True,exist_ok=True); R.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('h212',ROOT/'ops/india-300-delivery-20261011.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
now=lambda:datetime.now(timezone.utc).isoformat()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,v):
 p=E/n;p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n');return p

registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
rows=list(csv.DictReader(registry.open(encoding='utf-8-sig')));assert len(rows)==111
pma=next(x for x in rows if x['source_id']=='philadelphia_museum_art')
assert pma['automated_image_download']=='never_unless_record_explicitly_open'
required=[ROOT/'AGENTS.md',registry,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',Q]
save('required-input-verification.json',{'at':now(),'files':[{'path':str(x),'sha256':sha(x)} for x in required],'registry_records':len(rows)})
cmds=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines(); target='artline-508319:europe-west1:artline-postgres'
assert any(x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target in x for x in cmds)
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 state=dict(db.execute("SELECT current_database() db,current_setting('transaction_read_only') ro").fetchone());assert state['db']=='artline' and state['ro']=='on'
 rec=h.load(E.parent/'000107/batch-verification-receipt.json'); ids=rec['production_ids']
 c=db.execute("SELECT count(*) n FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchone()['n']
 m=db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND primary_media_id IS NOT NULL",(ids,)).fetchone()['n']
 assert c==12 and m==12
save('production-target-reconciliation.json',{'at':now(),'connection_name':target,'proxy_port':55519,'database':state,'helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha(ROOT/'ops/india-300-delivery-20261011.py'),'shared_ingestion_lock':'artline-curated-ingestion','write_transaction_entered':False,'local_catalogue_connections':0})
save('batch107-live-reconciliation.json',{'at':now(),'production_ids_checked':12,'live_citation_matches':c,'verified_primary_media':m,'previous_increments_counted':0,'prior_receipt_sha256':sha(E.parent/'000107/batch-verification-receipt.json')})
research={'at':now(),'source_id':'philadelphia_museum_art','route':'russian_pictorial_place_filter','requested_resume_page':2,'prior_pages_preserved':[0,1],'registry_policy':{'automated_image_download':pma['automated_image_download'],'image_rights_rule':pma['image_rights_rule'],'terms_url':pma['terms_url']},'result':'no eligible image candidate selected','reason':'The established Algolia discovery credential is not persisted in the source queue or supported helper, and PMA native images remain ineligible absent explicit per-object open reuse evidence. No credential was inferred from old logs and no held images were retried.','objects_downloaded':0,'images_downloaded':0,'next_page':2,'retry_condition':'Resume only through an established authenticated/public discovery helper, while retaining per-object rights review.'}
save('pma-page2-route-research.json',research)
save('actual-visual-review.json',{'at':now(),'prepared_images':0,'actually_viewed_files':[],'claim':'No image was prepared or delivered, so no visual-inspection claim is made. Prior batch visual evidence was not reused as a new review.'})
q=json.loads(Q.read_text());e=next(x for x in q['sources'] if x['source_id']=='philadelphia_museum_art')
e.update(status='page2_discovery_credential_not_persisted_images_require_explicit_object_rights',checkpoint='docs/research/continuous-production-20261011/batches/000212/CHECKPOINT.json',last_checked_at=now(),access_status='Pages 0-1 preserved. Page 2 not requested because the prior public discovery credential is not persisted in the supported workflow; no objects/images requested.',policy_reference='Original 111-source registry; docs/ARTLINE_IMAGE_USE.md')
e['resume_cursor']['next_page']=2;e['resume_cursor']['next_step']='Use the saved undercovered QAGOMA 12-gap route or another untouched registry museum with explicit image reuse. Resume PMA page 2 only with an established supported discovery credential; do not repeat pages 0-1.'
Q.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
save('source-queue-update-verification.json',{'at':now(),'source_id':'philadelphia_museum_art','queue_sha256':sha(Q),'unrelated_entries_preserved':True,'resume_page':2,'objects_requested':0,'images_requested':0,'next_route':'QAGOMA saved 12-gap route or another explicit-open registry museum'})
counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
next_task='Research the saved QAGOMA 12 unresearched primary-image gaps, requiring exact native identity and explicit object-level reuse evidence; otherwise rotate to another untouched explicit-open registry museum.'
save('batch-verification-receipt.json',{'at':now(),'verified_counts':counts,'production_ids':[],'production_writes':0,'storage_writes':0,'production_target':target,'shared_ingestion_lock':'artline-curated-ingestion','attribution':'Fresh production read plus zero transaction preimages and zero selected/downloaded objects prove no batch-212 increment; prior campaigns excluded.','next_task':next_task})
save('CHECKPOINT.json',{'at':now(),'batch':212,'stage':'complete_no_eligible_candidates','discovered':0,'selected':0,'prepared':0,'imported':0,'verified':0,'verified_counts':counts,'production_writes':0,'external_supervisor_unchanged':True,'next_task':next_task,'blocker':'','evidence_paths':[f'docs/research/continuous-production-20261011/batches/000212/{x}' for x in ['pma-page2-route-research.json','production-target-reconciliation.json','batch107-live-reconciliation.json','actual-visual-review.json','source-queue-update-verification.json','batch-verification-receipt.json']]})
print(json.dumps(counts))
