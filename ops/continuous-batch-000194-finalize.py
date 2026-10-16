#!/usr/bin/env python3
"""Finalize an exhausted bounded Rijks reserve window without production writes."""
import fcntl, gzip, hashlib, importlib.util, json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000194'
BASE=E.parents[1]
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000194'
s=importlib.util.spec_from_file_location('b194',ROOT/'ops/continuous-rijks-images-000194.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h

def load(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(name,value):
 h.save(E/name,value);return value
def rel(p): return str(Path(p).relative_to(ROOT))

R.mkdir(parents=True,exist_ok=True)
with (R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 at=h.now();counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
 rr=load(E/'reserve-reconciliation.json')
 assert rr['start_position']==600 and rr['resume_position']==625 and rr['selected']==0
 assert len(rr['rows'])==25 and all(x['reason']=='New creator reconciliation required' for x in rr['rows'])
 # Fresh read-only production checks: no selected row changed and batch 107 remains reconciled.
 ids=[x['artwork_id'] for x in rr['rows']]
 before=load(E/'preparation-production-snapshot.json.gz')['before']
 assert before=={}
 with b.connect() as db:
  live=h.snapshot(db,ids)
  assert len(live)==25 and all(x['artwork']['primary_media_id'] is None for x in live.values())
  prior=load(E.parent/'000107/independent-production-verification.json')
  live107=h.snapshot(db,list(prior['after']))
  assert live107==prior['after']
  own=[dict(x) for x in db.execute('SELECT media_id::text FROM media_rights_evidence WHERE adapter_version=%s',(b.i.OP,))]
  assert own==[]
 target=b.target()
 save('batch107-live-reconciliation.json',dict(at=at,production_rows=len(live107),matches_independent_postimage=True,evidence=rel(E.parent/'000107/independent-production-verification.json')))
 save('independent-production-verification.json',dict(at=at,production_target=target,inspected_artwork_ids=ids,all_remain_primary_image_gaps=True,current_campaign_rows=[],production_writes=0,local_catalogue_connections=0))
 save('actual-visual-review.json',dict(at=at,prepared_images=0,viewed_images=0,claim='No image was prepared or attached; the 25 records were held at identity reconciliation, so no visual-review claim is made.'))
 save('batch-verification-receipt.json',dict(at=at,verified_counts=counts,production_ids=[],production_target=target,shared_ingestion_lock='artline-curated-ingestion',attribution='Fresh production read found no batch-194 adapter rows and no writes. All 25 bounded positions remained primary-image gaps but require creator reconciliation before image attachment.',limitations=['All 25 rows have unresolved unlinked creator labels; image-only delivery may not invent or bypass canonical creator reconciliation.']))
 # Advance only the actually researched Rijksmuseum route and preserve all other registry entries byte-for-value.
 qpath=BASE/'source-queue.json';beforeq=load(E/'source-queue-before.json');q=load(qpath)
 assert len(q['sources'])==111
 assert [x for x in q['sources'] if x['source_id']!='rijksmuseum']==[x for x in beforeq['sources'] if x['source_id']!='rijksmuseum']
 route=next(x for x in q['sources'] if x['source_id']=='rijksmuseum')
 assert route['resume_cursor']['position']==600
 route['resume_cursor']['position']=625
 route['status']='bounded_primary_image_window_held_creator_reconciliation'
 route['checkpoint']=rel(E/'CHECKPOINT.json')
 route['last_checked_at']=at
 route['last_batch_evidence']=rel(E/'reserve-reconciliation.json')
 tmp=qpath.with_suffix('.tmp');tmp.write_text(json.dumps(q,indent=2)+'\n');os.replace(tmp,qpath)
 save('source-queue-update-verification.json',dict(at=at,modified_source_ids=['rijksmuseum'],unrelated_entries_preserved=110,all_111_registry_routes_preserved=True,new_position=625,checkpoint=route['checkpoint']))
 evidence=['reserve-reconciliation.json','global-identity-reconciliation.json','production-target-reconciliation.json','prior-batch-live-reconciliation.json','source-access-holds.json','batch107-live-reconciliation.json','independent-production-verification.json','actual-visual-review.json','batch-verification-receipt.json','source-queue-update-verification.json']
 cp=dict(at=at,batch=194,stage='verified_no_eligible_candidates',researched=dict(rijks_positions=25,start=600,end=624),selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task='Rotate to a different undercovered permitted open-image registry route; Rijksmuseum positions 600–624 require separate canonical creator reconciliation, and the French reserve is exhausted.',blocker='',evidence_paths=[rel(E/x) for x in evidence],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0)
 tmp=E/'CHECKPOINT.tmp';tmp.write_text(json.dumps(cp,indent=2)+'\n');os.replace(tmp,E/'CHECKPOINT.json')
 (R/'CHECKPOINT.json').write_text(json.dumps(cp,indent=2)+'\n')
 save('independent-final-artifact-verification.json',dict(at=at,checkpoint_runtime_equal=load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),evidence=[dict(path=rel(E/x),sha256=h.sha((E/x).read_bytes())) for x in evidence],all_evidence_exists=True,counts_match=True,source_queue_sha256=hashlib.sha256(qpath.read_bytes()).hexdigest()))
 print(json.dumps(dict(outcome='no_eligible_candidates',verified_counts=counts,next_task=cp['next_task'])))
