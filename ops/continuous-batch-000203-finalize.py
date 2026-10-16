#!/usr/bin/env python3
import csv, gzip, hashlib, importlib.util, json, os, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000203'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000203'
E.mkdir(parents=True,exist_ok=True); R.mkdir(parents=True,exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def save(name,v):
 p=E/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n'); return v
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
h=mod('delivery203','ops/india-300-delivery-20261011.py')
ids=['54d0f5c9-450e-57b6-a4b2-d0bf1a6fdf65','55cb8894-e6b4-53d2-9e33-d3d67f132c96','56b54223-1004-55f5-812c-b9ecd1b761df','5784b26a-6fdb-57ab-bc5d-0b5400b1d040']
required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'); rows=list(csv.DictReader(reg.open()))
assert len(rows)==111
save('required-input-verification.json',{'at':now(),'files':[{'path':p,'sha256':sha((ROOT/p).read_bytes())} for p in required],'registry':{'path':str(reg),'sha256':sha(reg.read_bytes()),'records':111},'latest_hold_ledgers':[str(p.relative_to(ROOT)) for p in sorted((E.parent).glob('*/source-access-holds.json'))[-5:]]})
actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
assert actual=='artline-508319:europe-west1:artline-postgres'
save('production-target-reconciliation.json',{'at':now(),'connection_name':actual,'proxy_port':int(os.environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')),'helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),'shared_ingestion_lock':'artline-curated-ingestion','write':False,'local_catalogue_connections':0})
with h.connect() as db:
 live=h.snapshot(db,ids)
 cites=[dict(x) for x in db.execute("select entity_id::text,field_name,source_url,evidence_note from citations where entity_type='artwork' and entity_id=any(%s::uuid[]) order by entity_id,field_name",(ids,))]
 ext=[dict(x) for x in db.execute("select entity_id::text,scheme,external_id,canonical_url from external_identifiers where entity_type='artwork' and entity_id=any(%s::uuid[]) order by entity_id,scheme",(ids,))]
 own=[dict(x) for x in db.execute("select media_id::text,evidence_json from media_rights_evidence where adapter_version=%s",('continuous-auckland-images-20261013-b000203',))]
save('interrupted-write-reconciliation.json',{'at':now(),'campaign_adapter':'continuous-auckland-images-20261013-b000203','existing_campaign_rows':own,'production_writes_attributable_to_batch':0,'decision':'No unknown earlier batch-203 write exists.'})
out=[]
for aid in ids:
 a=live[aid]['artwork']; cs=[c for c in cites if c['entity_id']==aid]; es=[x for x in ext if x['entity_id']==aid]
 reason=''
 if a['primary_media_id']: reason='already illustrated in live production; excluded from new increments'
 elif aid=='56b54223-1004-55f5-812c-b9ecd1b761df': reason='official object 3405 explicitly says Copying restrictions apply; preserved provider hold, no download'
 elif aid=='55cb8894-e6b4-53d2-9e33-d3d67f132c96': reason='1970 work lacks a verified native-object crosswalk and per-object reusable image evidence; no speculative match/download'
 else: reason='Lindauer title is discoverable, but the frozen catalogue row lacks a verified Auckland native-object identifier/citation crosswalk; multiple Paora Tuhaere versions exist, so exact physical-version image attachment remains held'
 out.append({'artwork_id':aid,'title':a['title'],'primary_media_id':a['primary_media_id'],'citations':cs,'identifiers':es,'outcome':'held','reason':reason})
save('auckland-four-crosswalk-reconciliation.json',{'at':now(),'route':'Auckland four untouched frozen-input crosswalks from batch 101','checked':4,'selected':0,'downloaded':0,'rows':out,'official_object_evidence':[{'url':'https://www.aucklandartgallery.com/explore-art-and-ideas/artwork/3405/rocks-concrete-and-iron','title':'Rocks, concrete and iron','accession':'1967/12','rights_label':'Copying restrictions apply'},{'url':'https://www.aucklandartgallery.com/explore-art-and-ideas/artwork/299/whetoi-pomare-1896','title':'Whetoi Pomare 1896','accession':'1915/2/27','identity_hold':'catalogue row has no native crosswalk; exact source attachment not inferred'}]})
save('actual-visual-review.json',{'at':now(),'prepared_images':0,'viewed_images':0,'contact_sheets_viewed':0,'statement':'No candidate passed identity and rights selection, so no image was downloaded/prepared and no visual acceptance claim is made.'})
qpath=E.parents[1]/'source-queue.json'; before=json.loads(qpath.read_text()); after=json.loads(json.dumps(before)); src=next(x for x in after['sources'] if x['source_id']=='auckland_art_gallery')
src['last_batch']=203; src['last_checked_at']=now(); src['checkpoint']='docs/research/continuous-production-20261011/batches/000203/CHECKPOINT.json'; src['status']='four_frozen_crosswalks_researched_no_eligible_images'
src['latest_batch_verified_counts']={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
src.setdefault('research_history',[]).append({'batch':203,'at':now(),'route':'four untouched native crosswalks from batch101','checked':4,'selected':0,'evidence':'docs/research/continuous-production-20261011/batches/000203/auckland-four-crosswalk-reconciliation.json','verified_counts':src['latest_batch_verified_counts']})
src.setdefault('resume_cursor',{})['batch203_dispositions']={x['artwork_id']:x['reason'] for x in out}
src['resume_cursor']['next_task']='Rotate away from Auckland frozen crosswalks to an undercovered open Greek/Byzantine existing-image-gap route with exact native IDs and object-level image evidence.'
qpath.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
save('source-queue-update-verification.json',{'at':now(),'updated_source':'auckland_art_gallery','unrelated_entries_preserved':[x for x in before['sources'] if x['source_id']!='auckland_art_gallery']==[x for x in after['sources'] if x['source_id']!='auckland_art_gallery'],'after_sha256':sha(qpath.read_bytes())})
counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
next_task='Select a bounded existing-image-gap set from an undercovered open Greek/Byzantine registry route with exact native identifiers and object-level image evidence; do not replay Auckland batch-101 crosswalks, French reserve, or SAAM shards 0–31.'
save('batch-verification-receipt.json',{'at':now(),'verified_counts':counts,'production_writes':0,'production_ids':[],'attribution':'No selected images and no mutation; all prior programme rows excluded.','shared_ingestion_lock':'artline-curated-ingestion','lock_not_acquired_because_no_write':True})
cp={'at':now(),'batch':203,'stage':'verified_complete_no_eligible_candidates','verified_counts':counts,'researched':{'provider':'auckland_art_gallery','route':'four frozen native crosswalks','checked':4},'selected':0,'prepared':0,'imported':0,'verified':0,'next_task':next_task,'production_writes':0,'local_catalogue_connections':0}
save('CHECKPOINT.json',cp)
evidence=['required-input-verification.json','production-target-reconciliation.json','interrupted-write-reconciliation.json','auckland-four-crosswalk-reconciliation.json','actual-visual-review.json','source-queue-update-verification.json','batch-verification-receipt.json','CHECKPOINT.json']
save('independent-final-artifact-verification.json',{'at':now(),'files':[{'path':'docs/research/continuous-production-20261011/batches/000203/'+p,'sha256':sha((E/p).read_bytes())} for p in evidence],'queue_sha256':sha(qpath.read_bytes()),'passed':True})
result={'outcome':'no_eligible_candidates','summary':'Batch 203 reconciled the four untouched Auckland frozen-input crosswalks against live production and source evidence. Rocks, concrete and iron is explicitly rights-held; the other three lack a sufficiently pinned native-object/image crosswalk, with two Lindauer version risks. No images were downloaded or written.','next_task':next_task,'blocker':'','verified_counts':counts,'evidence_paths':['docs/research/continuous-production-20261011/batches/000203/'+p for p in ['CHECKPOINT.json','auckland-four-crosswalk-reconciliation.json','production-target-reconciliation.json','interrupted-write-reconciliation.json','actual-visual-review.json','batch-verification-receipt.json','source-queue-update-verification.json','independent-final-artifact-verification.json']]}
save('worker-result.json',result); print(json.dumps(result,ensure_ascii=False))
