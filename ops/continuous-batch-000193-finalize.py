#!/usr/bin/env python3
import base64,copy,fcntl,gzip,hashlib,importlib.util,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'docs/research/continuous-production-20261011/batches/000193';BASE=E.parents[1];R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000193'
s=importlib.util.spec_from_file_location('b',ROOT/'ops/continuous-rijks-images-000193.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
def load(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(name,v): return b.save(E/name,v)
def rel(p): return str(Path(p).relative_to(ROOT))
images,_,_=i.accepted(b.B);assert len(images)==1;im=images[0];aid=im['artwork_id'];mid=im['media_id'];at=h.now();counts=dict(new_painters=0,new_artworks=0,newly_illustrated=1,alternate_images=0,museum_links=0)
with b.connect() as db:
 before=load(i.BACKUP/b.B/'before-000.json.gz');after=h.snapshot(db,[aid]);assert before[aid]['artwork']['primary_media_id'] is None and after[aid]['artwork']['primary_media_id']==mid
 events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=%s AND action='update' AND after_json->>'primary_media_id'=%s",(aid,mid))];assert len(events)==1 and events[0]['before_json']==before[aid]['artwork'] and events[0]['after_json']==after[aid]['artwork']
 fp=load(ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz');fids=[x['artwork_id'] for x in fp['rows']];assert len(fids)==188;flive=h.snapshot(db,fids);assert len(flive)==188 and all(x['artwork']['primary_media_id'] for x in flive.values())
 prior=load(E.parent/'000107/independent-production-verification.json');live107=h.snapshot(db,list(prior['after']));assert live107==prior['after']
save('independent-audit-history-verification.json',dict(at=at,events=events,locked_preimages_equal_audit_before=True,newly_illustrated=1))
save('french-reserve-live-reconciliation.json',dict(at=at,inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,plan_sha256=h.sha((ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz').read_bytes()),immutable_prior_visual_review_reused=True,new_visual_review_claim=False))
save('batch107-live-reconciliation.json',dict(at=at,production_rows=len(live107),matches_independent_postimage=True,evidence=rel(E.parent/'000107/independent-production-verification.json')))
credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);blob=client.bucket(i.d.core.BUCKET).blob(im['storage_path'].lstrip('/'));blob.reload();raw=blob.download_as_bytes();assert blob.size==im['bytes'] and h.sha(raw)==im['sha256'] and blob.metadata['operation']==i.OP and blob.metadata['sha256']==im['sha256'] and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
save('independent-storage-verification.json',dict(at=at,rows=[dict(artwork_id=aid,object_key=blob.name,generation=blob.generation,bytes=blob.size,sha256=h.sha(raw),metadata=blob.metadata,md5_verified=True)]))
qpath=BASE/'source-queue.json';beforeq=load(E/'source-queue-before.json');q=json.loads(qpath.read_text());assert len(q['sources'])==111 and [x for x in q['sources'] if x['source_id']!='rijksmuseum']==[x for x in beforeq['sources'] if x['source_id']!='rijksmuseum'];route=next(x for x in q['sources'] if x['source_id']=='rijksmuseum');assert route['resume_cursor']['position']==600
save('source-queue-update-verification.json',dict(at=at,modified_source_ids=['rijksmuseum'],unrelated_entries_preserved=110,all_111_registry_routes_preserved=True,new_position=600,checkpoint=route['checkpoint']))
receipt=load(E/'batch-verification-receipt.json');assert receipt['verified_counts']==counts and receipt['production_ids']==[aid]
evidence=['batch-verification-receipt.json','independent-production-verification.json','independent-audit-history-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-prewrite-verification.json','local-recovery-verification.json','actual-visual-review.json','french-reserve-live-reconciliation.json','batch107-live-reconciliation.json','source-queue-update-verification.json']
cp=dict(at=at,batch=193,stage='independently_verified_complete',researched=dict(french_reserve=188,rijks_positions=25),selected=1,prepared=1,imported=1,verified=1,verified_counts=counts,next_task='Research Rijksmuseum reserve positions 600–624, or rotate to another undercovered open-image registry route; do not revisit the exhausted French reserve.',blocker='',evidence_paths=[rel(E/x) for x in evidence],external_supervisor_unchanged=True,production_writes=1,local_catalogue_connections=0)
tmp=E/'CHECKPOINT.tmp';tmp.write_text(json.dumps(cp,indent=2)+'\n');os.replace(tmp,E/'CHECKPOINT.json');R.mkdir(parents=True,exist_ok=True);(R/'CHECKPOINT.json').write_text(json.dumps(cp,indent=2)+'\n')
save('independent-final-artifact-verification.json',dict(at=at,checkpoint_runtime_equal=load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),evidence=[dict(path=rel(E/x),sha256=h.sha((E/x).read_bytes())) for x in evidence],all_evidence_exists=True,counts_match=True))
print(json.dumps(dict(outcome='progress',verified_counts=counts,next_task=cp['next_task'])))
