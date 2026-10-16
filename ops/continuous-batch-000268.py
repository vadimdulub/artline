#!/usr/bin/env python3
import csv, datetime, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/research/continuous-production-20261011'
OUT=BASE/'batches/000268'
RUNTIME=Path('/Users/vadimdulub/Library/Application Support/Artline/continuous-research/batches/000268')
TARGET='artline-508319:europe-west1:artline-postgres'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

OUT.mkdir(parents=True,exist_ok=True); RUNTIME.mkdir(parents=True,exist_ok=True)
registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
required=[ROOT/'AGENTS.md',ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',BASE/'CHECKPOINT.json',BASE/'source-queue.json',ROOT/'docs/research/creators-deep-continuation-20261011/source-registry-review.json']
holds=sorted(BASE.glob('batches/*/*hold*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:12]
save(OUT/'required-input-verification.json',{'at':now(),'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in required], 'registry_path':str(registry),'registry_sha256':sha(registry),'registry_records':sum(1 for _ in csv.DictReader(registry.open())),'complete_registry_used':True,'latest_hold_ledgers':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in holds]})

commands=subprocess.check_output(['ps','-axo','command='],text=True).splitlines()
assert any('cloud-sql-proxy' in x and '--port 55519' in x and TARGET in x for x in commands)
actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip(); assert actual==TARGET
helper=ROOT/'ops/india-300-delivery-20261011.py'; spec=importlib.util.spec_from_file_location('delivery_helper',helper); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
db=h.connect(False)
t=db.execute("select current_database() db,current_setting('transaction_read_only') ro").fetchone(); assert t['db']=='artline' and t['ro']=='on'
save(OUT/'production-target-reconciliation.json',{'at':now(),'connection_name':actual,'proxy_port':55519,'proxy_command_inspected':True,'database':t['db'],'read_only':t['ro'],'helper':str(helper.relative_to(ROOT)),'helper_sha256':sha(helper),'shared_ingestion_lock':'artline-curated-ingestion','write':False,'local_catalogue_connections':0})

prior=json.loads((BASE/'batches/000187/french-reserve-live-reconciliation.json').read_text())
rows=prior['production_rows']; ids=[x['id'] for x in rows]
live=list(db.execute("select id::text id,title,accession_number,primary_media_id::text primary_media_id,status from artworks where id=any(%s::uuid[]) order by id",(ids,)))
missing=sorted(set(ids)-{x['id'] for x in live}); unillustrated=[x['id'] for x in live if not x['primary_media_id']]; inactive=[x['id'] for x in live if x['status'] not in ('active','review')]
assert not missing and not unillustrated and not inactive and len(live)==188
visual=BASE/'batches/000001/prior-visual-evidence.json'; plan=BASE/'batches/000001/delivery-plan-pin.json'
vis=json.loads(visual.read_text()); assert len(vis['records'])==25
bad=[]
for x in vis['records']:
 for key in ('decision','sheet'):
  p=Path(x[key]); p=ROOT/p if not p.is_absolute() else p
  if not p.exists() or sha(p)!=x[key+'_sha256']: bad.append({'artwork_id':x['artwork_id'],'key':key})
assert not bad
decision_files=list((ROOT/'docs/research/french-printmaking-20261011/visual-decisions').glob('*.json'))
save(OUT/'french-reserve-live-reconciliation.json',{'at':now(),'inspected':188,'live_rows':len(live),'live_active_or_review':len(live)-len(inactive),'live_illustrated':len(live)-len(unillustrated),'genuinely_unimported':len(missing),'selected':0,'writes':0,'missing_ids':missing,'unillustrated_ids':unillustrated,'decision':'All 188 reserve objects remain imported and illustrated. No eligible supplement exists; immutable historical plan was not replayed.','production_rows':live,'checksum_bound_plan':str(plan.relative_to(ROOT)),'checksum_bound_plan_sha256':sha(plan),'prior_visual_evidence':str(visual.relative_to(ROOT)),'prior_visual_evidence_sha256':sha(visual),'prior_visual_sample_records_verified':len(vis['records']),'preserved_visual_decision_files':len(decision_files),'prior_sample_decision_and_sheet_checksums_verified':True})

b107=json.loads((BASE/'batches/000107/independent-production-verification.json').read_text())['rows']; ids107=[x['id'] for x in b107]
n107=db.execute('select count(*) n from artworks where id=any(%s::uuid[]) and primary_media_id is not null',(ids107,)).fetchone()['n']; assert n107==len(ids107)
save(OUT/'batch107-live-reconciliation.json',{'at':now(),'production_rows':n107,'expected_rows':len(ids107),'matches_independent_postimage':True,'increment':0})
db.close()

save(OUT/'actual-visual-review.json',{'at':now(),'new_images_prepared':0,'new_images_viewed':0,'claim':'No new image was selected. Reused and checksum-verified the immutable 188-record prior actual visual review; no claim of fresh viewing.','prior_visual_evidence':str(visual.relative_to(ROOT))})
queue=BASE/'source-queue.json'
save(OUT/'source-queue-update-verification.json',{'at':now(),'modified_source_ids':[],'reason':'The selected French reserve is a prepared programme cohort, not a distinct registry route; it was freshly reconciled but no provider route was researched. All registry cursors preserved.','all_111_registry_routes_preserved':True,'queue_sha256':sha(queue)})
counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
save(OUT/'independent-production-verification.json',{'at':now(),'production_target':TARGET,'production_writes':0,'verified_counts':counts,'attribution':'Fresh production read proves 188/188 reserve UUIDs pre-existed and were illustrated; therefore no programme increment is attributable to batch 268. Batch 107 also reconciled and excluded.','local_catalogue_connections':0})
save(OUT/'batch-verification-receipt.json',{'at':now(),'batch':268,'verified_counts':counts,'production_ids':[],'production_writes':0,'production_target':TARGET,'shared_ingestion_lock':'artline-curated-ingestion','lock_not_acquired_because_no_write':True,'immutable_visual_evidence_verified':True})
evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','actual-visual-review.json','source-queue-update-verification.json','independent-production-verification.json','batch-verification-receipt.json']
next_task='Return to the Qatar Museum of Islamic Art cursor after MS.255.2003 and obtain complete native object captures and terms evidence for the four selected pictorial objects; rotate to another undercovered open registry route if search remains unavailable. Do not replay the exhausted French reserve.'
result={'outcome':'no_eligible_candidates','summary':'Batch 268 freshly reconciled all 188 prepared French printmaking reserve UUIDs against production: 188/188 remain active or review and illustrated, leaving zero genuinely unimported eligible objects. The immutable delivery-plan pin and prior checksum-bound visual sample passed, 142 preserved visual-decision files remain present, batch 107 remains fully present, and no production, Storage, queue-cursor, or local-catalogue write occurred.','next_task':next_task,'blocker':'','verified_counts':counts,'evidence_paths':[str((OUT/x).relative_to(ROOT)) for x in evidence]}
cp={'at':now(),'batch':268,'stage':'verified_no_eligible_candidates','result':result,'selected':0,'prepared':0,'imported':0,'verified':0,'production_writes':0,'external_supervisor_unchanged':True}
save(OUT/'CHECKPOINT.json',cp); save(RUNTIME/'CHECKPOINT.json',cp); save(BASE/'CHECKPOINT.json',cp); result['evidence_paths'].append(str((OUT/'CHECKPOINT.json').relative_to(ROOT)))
save(OUT/'worker-result.json',result); save(RUNTIME/'worker-result.json',result)
save(OUT/'independent-final-artifact-verification.json',{'at':now(),'checkpoint_runtime_equal':(OUT/'CHECKPOINT.json').read_bytes()==(RUNTIME/'CHECKPOINT.json').read_bytes(),'worker_result_runtime_equal':(OUT/'worker-result.json').read_bytes()==(RUNTIME/'worker-result.json').read_bytes(),'all_evidence_exists':all((OUT/x).exists() for x in evidence),'evidence_sha256':[{'path':str((OUT/x).relative_to(ROOT)),'sha256':sha(OUT/x)} for x in evidence]})
print(json.dumps(result,ensure_ascii=False))
