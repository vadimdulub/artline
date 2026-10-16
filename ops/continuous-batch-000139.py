#!/usr/bin/env python3
"""Batch 139: independently prove the French reserve is exhausted; no writes."""
import copy,csv,fcntl,gzip,importlib.util,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'docs/research/continuous-production-20261011/batches/000139'; R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000139'
E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
sp=importlib.util.spec_from_file_location('h139',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
fp=importlib.util.spec_from_file_location('fp139',ROOT/'ops/french-printmaking-delivery-20261011.py');d=importlib.util.module_from_spec(fp);fp.loader.exec_module(d)
def save(n,v):
 p=E/n
 if p.exists(): return h.load(p)
 h.save(p,v);return v
def rel(p): return str(Path(p).relative_to(ROOT))
with (R/'worker.lock').open('a+') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB)
 req=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json']
 registry=list(csv.DictReader(req[1].open()));q=h.load(req[-1]);assert len(registry)==111 and len(q['sources'])==111
 save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in req],registry_rows=111,local_catalogue_connections=0))
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 proxy=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if 'cloud-sql-proxy' in x and '--port 55519' in x and actual in x];assert proxy
 save('production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_verified=True,proxy_port=55519,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
 with h.connect() as db:
  prev=h.load(E.parent/'000107/independent-production-verification.json');assert h.snapshot(db,list(prev['after']))==prev['after']
 save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(prev['after']),previous_increments_counted=0))
 original,pin=d.final_plan();top=h.load(d.RUN/'scope-topup/delivery-plan.json.gz');reserve=set(original['eligible_reserve'])-{x['artwork_id'] for x in top['rows']};assert len(reserve)==188
 identities={x['artwork_id']:x for x in d.identity_rows() if x['artwork_id'] in reserve};assert len(identities)==188
 prior=E.parent/'000103/khm/independent-reserve-evidence-verification.json';prior_data=h.load(prior);assert len(prior_data['records'])==188
 source_checks=[]
 for aid,row in identities.items():
  p=ROOT/row['source_record_reference'];assert h.sha(p.read_bytes())==row['source_record_sha256'];obj=h.load(p);assert obj['native_id']==row['native_id']
  im=h.load(d.RUN/'prepared-images'/(aid+'.json'));raw=Path(im['local_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
  source_checks.append(dict(artwork_id=aid,native_id=row['native_id'],source_record_sha256=row['source_record_sha256'],derivative_sha256=im['sha256']))
 with h.connect() as db:
  live=h.snapshot(db,sorted(reserve));assert set(live)==reserve
  rows=[dict(x) for x in db.execute("SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256,c.evidence_note FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN citations c ON c.entity_type='artwork' AND c.entity_id=a.id AND c.field_name='french_printmaking_source_identity' WHERE a.id=ANY(%s::uuid[])",(list(reserve),))]
  assert len(rows)==188 and all(x['primary_media_id'] and x['checksum_sha256'] for x in rows)
  plan_shas=[]
  for x in rows:
   ev=x['evidence_note'];ev=json.loads(ev) if isinstance(ev,str) else ev;plan_shas.append(ev.get('plan_sha256'))
  prior_plan=prior_data['prior_campaign_plan_sha256'];assert set(plan_shas)=={prior_plan}
 save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,source_and_derivative_checks=source_checks,live_artwork_ids=sorted(reserve),original_catalogue_plan_sha256=pin,citation_delivery_plan_sha256=prior_plan,production_target=actual,new_programme_increments=0))
 visual=h.load(E.parent/'000103/khm/reserve-actual-visual-sample.json');assert visual['viewed'] is True and h.sha(Path(visual['path']).read_bytes())==visual['sha256']
 save('visual-evidence-reuse-verification.json',dict(at=h.now(),immutable_prior_review=rel(prior),prior_review_sha256=h.sha(prior.read_bytes()),prior_records=188,actual_sample=visual,policy='No new candidate exists. Reused checksum-bound visual decisions and explicitly cited the prior actual sample; no claim of new visual inspection.'))
 save('independent-production-verification.json',dict(at=h.now(),production_target=actual,writes=0,all_188_live=True,all_188_illustrated=True,all_188_attributed_to_prior_plan=True,verified_counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)))
 before=q;after=copy.deepcopy(q);row=next(x for x in after['sources'] if x['source_id']=='yale_lux');now=h.now();row.update(last_batch=139,last_checked_at=now,checkpoint=rel(E/'CHECKPOINT.json'),status='french_reserve_exhausted_188_already_imported_illustrated_live_reverified_batch139',latest_batch_verified_counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0));row['resume_cursor']=dict(route='french_printmaking_prepared_reserve',prepared=188,live_imported_and_illustrated=188,unimported=0,retry_allowed=False,next_step='Do not revisit without new contradictory evidence; rotate to an undercovered Byzantine or Greek registry route.',exact_evidence=rel(E/'french-reserve-live-reconciliation.json'));row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+[rel(E/'french-reserve-live-reconciliation.json'),rel(E/'visual-evidence-reuse-verification.json')]))
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as ql:
  fcntl.flock(ql,fcntl.LOCK_EX);tmp=qp.with_suffix('.139.tmp');tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
 save('source-queue-update-verification.json',dict(at=h.now(),updated_source='yale_lux',unrelated_entries_preserved=[x for x in before['sources'] if x['source_id']!='yale_lux']==[x for x in after['sources'] if x['source_id']!='yale_lux'],unrelated_count=110,queue_sha256=h.sha(qp.read_bytes())))
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0);nxt='Rotate to a new undercovered registry-backed Byzantine or Greek pictorial route; do not revisit the exhausted French reserve without new contradictory evidence.'
 save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=[],production_writes=0,attribution='All 188 reserve UUIDs already have live images and prior-plan checksum citations; none is attributable to batch139.',production_target=actual))
 names=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','visual-evidence-reuse-verification.json','independent-production-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']
 cp=save('CHECKPOINT.json',dict(at=h.now(),batch=139,outcome='no_eligible_candidates',stage='french_reserve_exhaustion_live_reverified',verified_counts=counts,inspected=188,selected=0,prepared=0,imported=0,verified=0,production_writes=0,next_task=nxt,blocker='',evidence=[rel(E/x) for x in names],external_supervisor_unchanged=True,local_catalogue_connections=0));h.save(R/'CHECKPOINT.json',cp)
 checked=[]
 for n in names+['CHECKPOINT.json']:
  p=E/n;h.load(p);checked.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
 save('independent-final-artifact-verification.json',dict(at=h.now(),artifacts=checked,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,queue_yale_unimported=0,passed=True))
 print(json.dumps(dict(outcome='no_eligible_candidates',summary='Batch 139 re-inspected all 188 prepared French printmaking reserve UUIDs. Every object is already present and illustrated in live production with checksum-bound source evidence and the prior delivery-plan citation, so no genuinely unimported candidate exists and no write was made.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in names+['CHECKPOINT.json','independent-final-artifact-verification.json']])))
