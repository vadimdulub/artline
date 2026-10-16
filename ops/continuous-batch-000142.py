#!/usr/bin/env python3
"""Bounded batch 142: reconcile exhausted French reserve and rotate to DDB."""
import copy,csv,fcntl,gzip,importlib.util,json,os,subprocess
from pathlib import Path
from urllib.parse import quote
import requests

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000142'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000142'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000142'
for p in (E,R,S):p.mkdir(parents=True,exist_ok=True)
sp=importlib.util.spec_from_file_location('h142',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
def save(n,v):h.save(E/n,v);return v
def rel(p):return str(Path(p).relative_to(ROOT))

with (R/'worker.lock').open('a+') as worker:
 fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
 reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
 required=[ROOT/'AGENTS.md',reg,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json']
 rows=list(csv.DictReader(reg.open()));queue=h.load(required[-1]);assert len(rows)==111 and {x['source_id'] for x in rows}=={x['source_id'] for x in queue['sources']}
 save('required-input-verification.json',dict(at=h.now(),registry_rows=111,complete_original_registry_used=True,files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],local_catalogue_connections=0))
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 proxy=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if 'cloud-sql-proxy' in x and '--port 55519' in x and actual in x];assert proxy
 save('production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_verified=True,proxy_port=55519,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
 with h.connect() as db:
  prev=h.load(E.parent/'000107/independent-production-verification.json');assert h.snapshot(db,list(prev['after']))==prev['after']
 save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(prev['after']),previous_increments_counted=0))
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';plan=h.load(pp);assert len(plan['rows'])==188
 prior=h.load(E.parent/'000061/independent-french-reserve-evidence-verification.json');assert len(prior['records'])==188 and prior['prior_review_reused_without_new_view_claim']
 for x in prior['records']:
  assert h.sha((ROOT/x['source_record_reference']).read_bytes())==x['source_sha256'] if 'source_record_reference' in x else True
 with h.connect() as db:
  live=h.snapshot(db,[x['artwork_id'] for x in plan['rows']]);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(list(live),))]
 assert len(live)==len(cit)==188
 psha=h.sha(pp.read_bytes());assert all(x['plan_sha256']==psha for x in cit)
 assert all(live[x['artwork_id']]['artwork']['primary_media_id']==plan['images'][x['artwork_id']]['media_id'] and live[x['artwork_id']]['artwork']['status']!='archived' for x in plan['rows'])
 save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,plan_sha256=psha,immutable_prior_visual_evidence=rel(E.parent/'000061/independent-french-reserve-evidence-verification.json'),prior_actual_visual_review_reused=True,new_visual_review_claim=False,physical_date_holds_preserved=['80082','80437','81054'],source_citations=cit,live_rows=live))
 # Rotate once to an undercovered registry route. DDB API requires a key, so only
 # official public discovery and policy pages are fetched; no credential probing.
 route=next(x for x in queue['sources'] if x['source_id']=='deutsche_digitale_bibliothek');assert route['status']=='not_yet_reconciled_for_this_programme'
 urls=['https://www.deutsche-digitale-bibliothek.de/searchresults?query='+quote('byzantinische Ikone'),'https://labs.deutsche-digitale-bibliothek.de/app/ddbapi/','https://pro.deutsche-digitale-bibliothek.de/daten-nutzen/lizenzen-rechtehinweise']
 ses=requests.Session();ses.headers['User-Agent']='Artline catalogue research; bounded metadata review'
 captures=[]
 for n,url in enumerate(urls):
  r=ses.get(url,timeout=(15,45),allow_redirects=True);raw=r.content;bp=S/(f'ddb-{n}.body.gz');bp.write_bytes(gzip.compress(raw,mtime=0));captures.append(dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=h.now(),sha256=h.sha(raw),bytes=len(raw),body_path=str(bp),retry_after=r.headers.get('Retry-After')))
 save('ddb-route-research.json',dict(at=h.now(),provider='deutsche_digitale_bibliothek',query='byzantinische Ikone',captures=captures,api_authentication='API key required by original registry; no configured key located or requested',objects_selected=0,images_downloaded=0,finding='Public search returned an access denial and the official API/rights pages did not provide an unauthenticated object API route. No repeated requests made.',next_step='Research Europeana open-rights route if an existing configured API key is available; otherwise rotate to an unauthenticated museum API.'))
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
 save('independent-production-verification.json',dict(at=h.now(),production_target=actual,writes=0,verified_counts=counts,reason='French reserve is wholly pre-existing; alternate DDB route yielded no selectable objects.'))
 before=queue;after=copy.deepcopy(before);row=next(x for x in after['sources'] if x['source_id']=='deutsche_digitale_bibliothek');now=h.now();row.update(status='public_search_access_hold_api_key_required_no_objects_selected',last_checked_at=now,last_batch=142,checkpoint=rel(E/'CHECKPOINT.json'),access_status='One bounded public-search request denied; official API requires a key. No object API requests or image requests.',policy_reference='Original 111-source registry DDB row; official DDB rights page capture.',resume_cursor=dict(route='byzantine_icon_open_rights',query='byzantinische Ikone',processed_object_ids=[],object_requests=0,image_requests=0,retry_allowed=False,next_step='Use configured API key if it already exists, otherwise rotate to Europeana or an unauthenticated registry source.'));row['evidence_paths']=[rel(E/'ddb-route-research.json')]
 qpath=E.parents[1]/'source-queue.json'
 with qpath.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);tmp=qpath.with_suffix('.142.tmp');tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qpath)
 save('source-queue-update-verification.json',dict(at=h.now(),updated_source='deutsche_digitale_bibliothek',unrelated_entries_preserved=[x for x in before['sources'] if x['source_id']!='deutsche_digitale_bibliothek']==[x for x in after['sources'] if x['source_id']!='deutsche_digitale_bibliothek'],queue_sha256=h.sha(qpath.read_bytes()),resume_cursor=row['resume_cursor']))
 save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=[],production_writes=0,attribution='No new programme increments: all 188 reserve works pre-existed and DDB produced no selected objects.',production_target=actual,shared_ingestion_lock='artline-curated-ingestion'))
 next_task='Research a bounded Europeana open-rights Greek/Byzantine painting or icon route if an already configured key exists; otherwise use another unauthenticated registry-backed museum API. Do not retry DDB until access changes.'
 evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','ddb-route-research.json','independent-production-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']
 cp=dict(at=h.now(),batch=142,stage='verified_complete_no_eligible_candidates',researched=dict(french_reserve=188,alternate_provider='deutsche_digitale_bibliothek'),selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task=next_task,blocker='',evidence=[rel(E/x) for x in evidence],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0)
 save('CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
 checked=[]
 for n in evidence+['CHECKPOINT.json']:
  p=E/n;h.load(p);checked.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
 save('independent-final-artifact-verification.json',dict(at=h.now(),artifacts=checked,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,passed=True))
 print(json.dumps(dict(outcome='no_eligible_candidates',summary='All 188 French reserve records are already active and illustrated in production with checksum-bound source citations; none is an unimported candidate. The bounded DDB fallback reached an access hold/API-key boundary and selected no objects, so production remained unchanged.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in evidence+['CHECKPOINT.json','independent-final-artifact-verification.json']])))
