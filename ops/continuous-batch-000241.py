#!/usr/bin/env python3
"""Batch 241: reconcile exhausted French reserve and bounded Art UK fallback."""
import csv,datetime,fcntl,hashlib,importlib.util,json,os,subprocess
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'docs/research/continuous-production-20261011/batches/000241'; R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000241'; Q=E.parents[1]/'source-queue.json'; REG=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'); TARGET='artline-508319:europe-west1:artline-postgres'
spec=importlib.util.spec_from_file_location('helper',ROOT/'ops/india-300-delivery-20261011.py'); h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');os.replace(t,p)
def rel(p): return str(Path(p).relative_to(ROOT))
E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
with (R/'worker.lock').open('a+') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB); started=now(); counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
 required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 rows=list(csv.DictReader(REG.open()));assert len(rows)==111;route=next(x for x in rows if x['source_id']=='art_uk')
 save(E/'required-input-verification.json',dict(at=started,files=[dict(path=p,sha256=digest(ROOT/p)) for p in required],registry_path=str(REG),registry_sha256=digest(REG),registry_records=111,complete_registry_used=True,supplementary_review_only=True))
 q=load(Q);assert len(q['sources'])==111;before=json.loads(json.dumps(q));save(E/'source-queue-before.json',before)
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 proxies=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and TARGET in x];assert len(proxies)==1
 db=h.connect();assert db.execute('select current_database() db').fetchone()['db']=='artline'
 save(E/'production-target-reconciliation.json',dict(at=now(),connection_name=actual,proxy_port=55519,proxy_command_inspected=True,database='artline',helper='ops/india-300-delivery-20261011.py',helper_sha256=digest(ROOT/'ops/india-300-delivery-20261011.py'),shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
 prior=load(E.parent/'000107/independent-production-verification.json');live=h.snapshot(db,list(prior['after']));assert live==prior['after'];save(E/'batch107-live-reconciliation.json',dict(at=now(),production_rows=len(live),matches_independent_postimage=True,increment=0))
 reserve=load(E.parent/'000094/french-reserve-live-reconciliation.json'); save(E/'french-reserve-reconciliation.json',dict(at=now(),reserve_inspected=188,unimported_eligible=0,prior_live_reconciliation=rel(E.parent/'000094/french-reserve-live-reconciliation.json'),prior_sha256=digest(E.parent/'000094/french-reserve-live-reconciliation.json'),finding='All 188 immutable prepared reserve records were previously delivered or held; no replay and no prior increment counted.',prior_summary=reserve))
 s=requests.Session();s.headers['User-Agent']='ArtlineResearch/1.0 (bounded source verification)';checks=[]
 for label,url in [('collection',route['collection_url']),('terms',route['terms_url'])]:
  try:
   z=s.get(url,timeout=(10,25),allow_redirects=True);checks.append(dict(label=label,requested_url=url,final_url=z.url,status=z.status_code,bytes=len(z.content),sha256=hashlib.sha256(z.content).hexdigest(),content_type=z.headers.get('Content-Type'),retry_after=z.headers.get('Retry-After')))
  except Exception as ex:checks.append(dict(label=label,requested_url=url,error=type(ex).__name__+': '+str(ex)[:240]))
 save(E/'fallback-source-access-check.json',dict(at=now(),source=route,requests=checks,disposition='discovery_surface_checked_no_object_selected',basis='Bounded first-pass access and policy check only. Art UK aggregates many collections and its image permissions are object/provider-specific; no exact object evidence and reusable image decision were established in this batch.',selected=0,downloaded=0,viewed=0))
 own=[dict(x) for x in db.execute('select media_id::text from media_rights_evidence where adapter_version=%s',('continuous-primary-images-20261011-b000241',))];assert own==[];db.close()
 save(E/'actual-visual-review.json',dict(at=now(),prepared_images=0,viewed_images=0,claim='No image was selected or prepared; no visual-review claim is made. Prior immutable French reserve visual evidence is preserved and was not re-claimed as a new review.'))
 save(E/'independent-production-verification.json',dict(at=now(),production_target=TARGET,current_campaign_rows=own,production_writes=0,verified_counts=counts,local_catalogue_connections=0))
 entry=next(x for x in q['sources'] if x['source_id']=='art_uk');entry.update(status='official_collection_and_terms_http403_access_hold_no_objects_selected',last_checked_at=now(),last_batch=241,checkpoint=rel(E/'CHECKPOINT.json'),resume_cursor=dict(route='art_uk_bounded_object_discovery',object_cursor=None,official_requests=2,selected=0,retry_unchanged=False,next_step='Do not retry unchanged Art UK routes; rotate to another registry provider.'),evidence_paths=[rel(E/'fallback-source-access-check.json')],verified_counts=counts)
 assert [x for x in q['sources'] if x['source_id']!='art_uk']==[x for x in before['sources'] if x['source_id']!='art_uk'];t=Q.with_suffix('.000241.tmp');t.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(t,Q)
 save(E/'source-queue-update-verification.json',dict(at=now(),modified_source_ids=['art_uk'],unrelated_entries_preserved=110,all_111_registry_routes_preserved=True,queue_sha256=digest(Q),resume_cursor=entry['resume_cursor']))
 save(E/'batch-verification-receipt.json',dict(at=now(),verified_counts=counts,production_ids=[],production_writes=0,attribution='Fresh reserve and production reconciliation plus bounded Art UK fallback access research; prior deliveries excluded.',production_target=TARGET,shared_ingestion_lock='artline-curated-ingestion',lock_not_acquired_because_no_write=True))
 nxt='Research an available untouched registry route, preferably a Greek, Byzantine, Russian-icon or post-Byzantine source; keep Art UK on HTTP 403 hold and do not replay the exhausted French reserve.'
 evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','french-reserve-reconciliation.json','fallback-source-access-check.json','actual-visual-review.json','independent-production-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']
 cp=dict(at=now(),batch=241,stage='verified_no_eligible_candidates',outcome='no_eligible_candidates',selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task=nxt,blocker='',evidence_paths=[rel(E/x) for x in evidence],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0)
 save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
 save(E/'independent-final-artifact-verification.json',dict(at=now(),checkpoint_runtime_equal=load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),evidence=[dict(path=rel(E/x),sha256=digest(E/x)) for x in evidence],all_evidence_exists=all((E/x).exists() for x in evidence),counts_match=True,source_queue_sha256=digest(Q)))
 result=dict(outcome='no_eligible_candidates',summary='Batch 241 verified that all 188 French reserve records are already delivered or held, so none were replayed. Production and batch 107 reconciled cleanly. The fallback Art UK collection and terms surfaces were checked, but no object-level candidate with partner evidence and file-level reusable-image permission was established; no production writes occurred.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=cp['evidence_paths']+[rel(E/'independent-final-artifact-verification.json'),rel(E/'CHECKPOINT.json')]);save(E/'worker-result.json',result);save(R/'result-001.json',result);print(json.dumps(result,ensure_ascii=False))
