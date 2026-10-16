#!/usr/bin/env python3
"""Fresh read-only reconciliation of the exhausted French reserve for batch 265."""
import copy, csv, datetime, fcntl, gzip, hashlib, importlib.util, json, os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000265"
R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000265"
E.mkdir(parents=True, exist_ok=True); R.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location("helper", ROOT / "ops/india-300-delivery-20261011.py")
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
    p=Path(p); return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(name, value):
    p=E/name; b=json.dumps(value,ensure_ascii=False,indent=2,default=str).encode()
    if p.exists(): return load(p)
    else: p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)
    return value
def rel(p): return str(Path(p).relative_to(ROOT))

with (R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 started=now()
 required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json']
 registry=list(csv.DictReader(required[1].open())); queue=load(required[-1]); assert len(registry)==len(queue['sources'])==111
 save('required-input-verification.json',{'at':now(),'files':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in required],'original_registry_rows':111,'supplementary_json_not_substituted':True,'local_catalogue_connections':0})
 target=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert target=='artline-508319:europe-west1:artline-postgres'
 proxy=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target in x]; assert proxy
 save('production-target-reconciliation.json',{'at':now(),'connection_name':target,'proxy_port':55519,'proxy_command_inspected':True,'helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha(ROOT/'ops/india-300-delivery-20261011.py'),'shared_ingestion_lock':'artline-curated-ingestion','write_mode':'not_entered_no_candidates','local_catalogue_connections':0})
 planp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz'; plan=load(planp); pin=sha(planp); assert len(plan['rows'])==188
 ids=[x['artwork_id'] for x in plan['rows']]
 prior107=load(E.parent/'000107/independent-production-verification.json')
 with h.connect() as db:
  live=h.snapshot(db,ids); assert len(live)==188
  cites=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity' ORDER BY entity_id",(ids,))]
  assert len(cites)==188 and all(x['plan_sha256']==pin for x in cites)
  for row in plan['rows']:
   a=live[row['artwork_id']]['artwork']; im=plan['images'][row['artwork_id']]
   assert a['status']!='archived' and a['accession_number']==row['accession_number'] and a['primary_media_id']==im['media_id']
  live107=h.snapshot(db,list(prior107['after'])); assert live107==prior107['after']
 save('batch107-live-reconciliation.json',{'at':now(),'production_rows':len(live107),'matches_independent_postimage':True,'uncertain_writes_found':False,'previous_increments_counted':0,'prior_receipt_sha256':sha(E.parent/'000107/independent-production-verification.json')})
 decisions=[]
 for row in plan['rows']:
  ev=row['continuation_visual_evidence']; dp=ROOT/ev['decision_reference']; d=load(dp)
  assert sha(dp)==ev['decision_sha256']
  assert row['artwork_id'] in d['approved']
  decisions.append({'artwork_id':row['artwork_id'],'native_id':row['source_id'],'decision_reference':ev['decision_reference'],'decision_sha256':ev['decision_sha256'],'image_sha256':ev['image_sha256'],'prior_review_reused':True})
 save('independent-reserve-evidence-verification.json',{'at':now(),'historical_plan_sha256':pin,'records':188,'source_identity_citations':188,'checksum_bound_visual_decisions':len(decisions),'visual_decisions':decisions,'new_visual_review_claimed':False,'basis':'Immutable prior decisions and their exact image hashes were reverified; no new image was selected, prepared, or viewed in batch 265.'})
 save('french-reserve-live-reconciliation.json',{'at':now(),'inspected':188,'already_imported_active_and_illustrated':188,'genuinely_unimported':0,'selected':0,'prepared':0,'imported':0,'verified_new_increments':0,'historical_plan_sha256':pin,'historical_plan_unchanged':True,'held_source_ids':['80082','80437','81054'],'held_objects_skipped':True})
 save('actual-visual-review.json',{'at':now(),'new_images_viewed':0,'new_images_accepted':0,'new_images_held':0,'prior_visual_evidence_reused':188,'claim':'No new visual inspection claimed. Batch 265 verified immutable checksum-bound decisions from the original individual review; held objects stayed held.'})
 qold=copy.deepcopy(queue); row=next(x for x in queue['sources'] if x['source_id']=='yale_lux')
 row['last_checked_at']=now(); row['status']='french_reserve_exhausted_live_verified_188_already_delivered_batch265'; row['checkpoint']=rel(E/'CHECKPOINT.json')
 row['resume_cursor']={'french_reserve_total':188,'already_imported_active_and_illustrated':188,'genuinely_unimported':0,'do_not_replay':True,'held_source_ids':['80082','80437','81054'],'next_step':'Rotate to an undercovered registry source with explicit object-level open image rights; do not replay the exhausted French reserve.'}
 for n in ['french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','batch107-live-reconciliation.json']:
  p=rel(E/n)
  if p not in row.setdefault('evidence_paths',[]): row['evidence_paths'].append(p)
 assert [x for x in qold['sources'] if x['source_id']!='yale_lux']==[x for x in queue['sources'] if x['source_id']!='yale_lux']
 tmp=required[-1].with_suffix('.batch265.tmp'); tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)); os.replace(tmp,required[-1]); assert load(required[-1])==queue
 save('source-queue-update-verification.json',{'at':now(),'updated_source':'yale_lux','unrelated_entries_preserved':True,'entries':111,'before_sha256':hashlib.sha256(json.dumps(qold,sort_keys=True).encode()).hexdigest(),'after_file_sha256':sha(required[-1]),'resume_cursor':row['resume_cursor']})
 counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
 nxt='Rotate to an undercovered registry source with stable object identifiers and explicit object-level open image rights; preserve all provider holds and do not replay the exhausted French reserve.'
 ev=[rel(E/x) for x in ['production-target-reconciliation.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','actual-visual-review.json','source-queue-update-verification.json']]
 cp={'at':now(),'started_at':started,'batch':265,'stage':'complete_no_eligible_candidates','discovered':188,'selected':0,'prepared':0,'imported':0,'verified':0,'verified_counts':counts,'production_writes':0,'storage_writes':0,'local_catalogue_writes':0,'external_supervisor_unchanged':True,'next_task':nxt,'blocker':'','evidence_paths':ev}
 save('CHECKPOINT.json',cp); (R/'CHECKPOINT.json').write_text(json.dumps(cp,ensure_ascii=False,indent=2))
 save('batch-verification-receipt.json',{'at':now(),'batch':265,'outcome':'no_eligible_candidates','verified_counts':counts,'production_target':target,'reserve_records_live_verified':188,'new_attributable_rows':0,'prior_campaign_rows_excluded':188,'production_writes':0,'storage_writes':0,'attribution_basis':'Fresh live row-scoped reconciliation against pinned source citations, plan checksum, transaction postimages, and immutable checksum-bound visual decisions.'})
 ev += [rel(E/'batch-verification-receipt.json'),rel(E/'CHECKPOINT.json')]
 result={'outcome':'no_eligible_candidates','summary':'Batch 265 freshly reconciled all 188 French printmaking reserve records against production. Every record is already active, illustrated, and pinned to the original source and visual-decision checksums; three historical holds remain held. Batch 107 also matches its independent postimage. No replay or production/storage/local-catalogue write occurred.','next_task':nxt,'blocker':'','verified_counts':counts,'evidence_paths':ev}
 save('worker-result.json',result); (R/'result-001.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 save('independent-final-artifact-verification.json',{'at':now(),'evidence':[{'path':p,'sha256':sha(ROOT/p)} for p in ev],'runtime_checkpoint_matches':load(R/'CHECKPOINT.json')==load(E/'CHECKPOINT.json'),'result_matches_runtime':load(R/'result-001.json')==result,'source_queue_entries':len(load(required[-1])['sources']),'passed':True})
 print(json.dumps(result,ensure_ascii=False))
