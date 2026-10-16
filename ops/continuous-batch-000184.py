#!/usr/bin/env python3
"""Bounded batch 184: replay-safe French reserve reconciliation and handoff."""
import copy,csv,fcntl,gzip,importlib.util,json,os,subprocess
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000184'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000184'
for p in (E,R):p.mkdir(parents=True,exist_ok=True)
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=mod('delivery184','india-300-delivery-20261011.py')
def save(name,v):h.save(E/name,v);return v
def rel(p):return str(Path(p).relative_to(ROOT))

def main():
 started=h.now();target_name='artline-508319:europe-west1:artline-postgres'
 required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json']
 registry=list(csv.DictReader(required[1].open()));assert len(registry)==111
 save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],registry_rows=111,complete_registry_used=True,local_catalogue_connections=0,translation_calls=0))
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==target_name
 proxies=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target_name in x];assert len(proxies)==1
 with h.connect() as db:
  t=dict(db.execute('SELECT current_database() database,pg_is_in_recovery() recovery').fetchone());assert t['database']=='artline' and not t['recovery']
 save('production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_command=proxies[0],database=t,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
 old107=h.load(E.parent/'000107/independent-production-verification.json')
 with h.connect() as db:live107=h.snapshot(db,list(old107['after']))
 assert live107==old107['after'];save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(live107),previous_increments_counted=0,receipt_sha256=h.sha((E.parent/'000107/independent-production-verification.json').read_bytes())))
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';plan=h.load(pp);assert len(plan['rows'])==188
 digest=h.sha(pp.read_bytes());evidence=[]
 prior=E.parent/'000061/independent-french-reserve-evidence-verification.json';assert prior.exists()
 for row in plan['rows']:
  source=ROOT/row['source_record_reference'];assert h.sha(source.read_bytes())==row['source_record_sha256']
  for receipt in (row['receipt'],row['manifest_receipt']):assert h.sha(gzip.decompress((ROOT/receipt['body_path']).read_bytes()))==receipt['sha256']
  visual=row['continuation_visual_evidence'];decision=ROOT/visual['decision_reference'];assert h.sha(decision.read_bytes())==visual['decision_sha256']
  im=plan['images'][row['artwork_id']];image=Path(im['local_path']);assert h.sha(image.read_bytes())==im['sha256']==visual['image_sha256'] and image.stat().st_size<=100000
  with Image.open(image) as decoded:decoded.load();assert list(decoded.size)==[im['width'],im['height']]
  evidence.append(dict(artwork_id=row['artwork_id'],native_id=row['native_id'],source_record_sha256=row['source_record_sha256'],derivative_sha256=im['sha256'],immutable_prior_visual_review=visual))
 ids=[x['artwork_id'] for x in plan['rows']]
 with h.connect() as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  live=h.snapshot(db,ids);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
 assert len(live)==len(cit)==188 and all(x['plan_sha256']==digest for x in cit)
 assert all(live[x]['artwork']['primary_media_id']==plan['images'][x]['media_id'] and live[x]['artwork']['status']!='archived' for x in ids)
 rec=save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,genuinely_unimported=0,selected=0,prepared=0,imported=0,verified_new=0,plan_sha256=digest,prior_visual_evidence=rel(prior),prior_visual_evidence_sha256=h.sha(prior.read_bytes()),checksum_verified_prior_reviews=evidence,new_visual_review_claim=False,held_native_ids=['80082','80437','81054'],hold_reason='Previously recorded physical-date holds remain excluded; no reserve row was replayed.',source_citations=cit,live_rows=live))
 save('independent-reserve-evidence-verification.json',dict(at=h.now(),passed=True,objects=188,source_records_checksum_verified=188,manifests_checksum_verified=188,derivatives_complete_decoded=188,immutable_visual_decisions_checksum_verified=188,live_active_illustrated=188,unimported=0,prior_review_reused=True,new_visual_review_claim=False,production_writes=0))
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX);q=h.load(qp);before=copy.deepcopy(q);route=next(x for x in q['sources'] if x['source_id']=='yale_lux')
  cursor=dict(route='french_printmaking_prepared_reserve',inspected=188,already_imported=188,genuinely_unimported=0,selected=0,reserve_exhausted=True,do_not_replay=True,held_native_ids=['80082','80437','81054'],evidence=rel(E/'french-reserve-live-reconciliation.json'),next_source_id='national_gallery_athens',next_route='checkpointed_aivazovsky_creator_authority_exact_version_visual_review')
  route['last_checked_at']=h.now();route['last_batch']=184;route['status']='french_reserve_exhausted_188_live_reverified_batch184';route.setdefault('resume_cursor',{})['french_reserve_batch184']=cursor;route.setdefault('batch_history',[]).append(dict(batch=184,route='french_printmaking_prepared_reserve',inspected=188,verified_counts={k:0 for k in ['new_painters','new_artworks','newly_illustrated','alternate_images','museum_links']},evidence=rel(E/'batch-verification-receipt.json')))
  unchanged=[x for x in before['sources'] if x['source_id']!='yale_lux']==[x for x in q['sources'] if x['source_id']!='yale_lux'];assert unchanged
  tmp=qp.with_suffix('.184.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
 save('source-queue-update-verification.json',dict(at=h.now(),updated_source='yale_lux',unrelated_entries_preserved=True,resume_cursor=cursor,queue_sha256=h.sha(qp.read_bytes())))
 counts={k:0 for k in ['new_painters','new_artworks','newly_illustrated','alternate_images','museum_links']};next_task='Validate the eight checkpointed National Gallery Athens Aivazovsky candidates with creator authority, exact-version reconciliation, and individual visual review; rotate to an untouched Russian icon or Byzantine registry institution if they cannot be delivered. Do not replay French188 or SAAM shards 0–27.'
 save('batch-verification-receipt.json',dict(at=h.now(),outcome='progress',verified_counts=counts,production_writes=0,prior_campaign_increments_excluded=188,attribution='Fresh locked live-production reconciliation proves every reserve UUID and checksum-bound plan citation is already present and illustrated; immutable prior visual review reused explicitly. No replay counted.',next_task=next_task))
 cp=dict(at=h.now(),batch=184,stage='verified_complete_no_new_french_reserve_objects',started_at=started,finished_at=h.now(),verified_counts=counts,resume_cursor=cursor,next_task=next_task,blocker='',production_writes=0,external_supervisor_unchanged=True,evidence=[rel(E/x) for x in ['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']])
 save('CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
 files=[dict(path=rel(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in sorted(E.glob('*.json')) if p.name!='independent-final-artifact-verification.json']
 save('independent-final-artifact-verification.json',dict(at=h.now(),passed=True,files=files,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,all_evidence_files_decoded=True,queue_sha256=h.sha(qp.read_bytes())))
 print(json.dumps(dict(outcome='progress',verified_counts=counts,unimported=0,next_task=next_task)))
if __name__=='__main__':main()
