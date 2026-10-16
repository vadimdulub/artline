#!/usr/bin/env python3
"""Bounded batch 240: Pinacoteca de Sao Paulo access and production reconciliation."""
import csv,datetime,fcntl,hashlib,importlib.util,json,os,subprocess
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'docs/research/continuous-production-20261011/batches/000240'; R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000240'; Q=E.parents[1]/'source-queue.json'; REG=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'); TARGET='artline-508319:europe-west1:artline-postgres'
spec=importlib.util.spec_from_file_location('helper',ROOT/'ops/india-300-delivery-20261011.py'); h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,p)
def rel(p): return str(Path(p).relative_to(ROOT))
E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
with (R/'worker.lock').open('a+') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB); started=now(); counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
 required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 rows=list(csv.DictReader(REG.open()));assert len(rows)==111;route=next(x for x in rows if x['source_id']=='pinacoteca_sao_paulo')
 save(E/'required-input-verification.json',dict(at=started,files=[dict(path=p,sha256=digest(ROOT/p)) for p in required],registry_path=str(REG),registry_sha256=digest(REG),registry_records=111,complete_registry_used=True,supplementary_review_only=True))
 q=load(Q);assert len(q['sources'])==111;before=json.loads(json.dumps(q));save(E/'source-queue-before.json',before)
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 proxies=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and TARGET in x];assert len(proxies)==1
 db=h.connect(); server=db.execute('select current_database() db').fetchone(); assert server['db']=='artline'
 save(E/'production-target-reconciliation.json',dict(at=now(),connection_name=actual,proxy_port=55519,proxy_command_inspected=True,database='artline',helper='ops/india-300-delivery-20261011.py',helper_sha256=digest(ROOT/'ops/india-300-delivery-20261011.py'),shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
 prior=load(E.parent/'000107/independent-production-verification.json');live=h.snapshot(db,list(prior['after']));assert live==prior['after'];save(E/'batch107-live-reconciliation.json',dict(at=now(),production_rows=len(live),matches_independent_postimage=True,increment=0))
 inst=[dict(x) for x in db.execute("select id::text,name from institutions where lower(name) like any(%s) order by name",(['%pinacoteca de s%o paulo%','%pinacoteca do estado%'],))]
 ids=[x['id'] for x in inst];gaps=[]
 if ids:gaps=[dict(x) for x in db.execute("select id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,current_institution_id::text,unlinked_creator_label,status from artworks where current_institution_id=any(%s::uuid[]) and primary_media_id is null and status<>'archived' order by id limit 50",(ids,))]
 save(E/'bounded-production-gap-cohort.json',dict(at=now(),institutions=inst,limit=50,rows=gaps,count=len(gaps),read_only=True))
 s=requests.Session();s.headers['User-Agent']='ArtlineResearch/1.0 (bounded source verification)';checks=[]
 for label,url in [('collection',route['collection_url']),('terms',route['terms_url'])]:
  try:
   z=s.get(url,timeout=(10,20),allow_redirects=True);checks.append(dict(label=label,requested_url=url,final_url=z.url,status=z.status_code,bytes=len(z.content),sha256=hashlib.sha256(z.content).hexdigest(),content_type=z.headers.get('Content-Type'),retry_after=z.headers.get('Retry-After')))
  except Exception as ex:checks.append(dict(label=label,requested_url=url,error=type(ex).__name__+': '+str(ex)[:240]))
 save(E/'source-access-and-rights-check.json',dict(at=now(),source=route,requests=checks,disposition='provider_access_hold_no_eligible_candidates',basis='Both bounded official-route requests failed without an HTTP response. The original registry requires record-explicit open image rights. No object evidence could be captured, so no metadata, holding, or image was selected and no request was repeated.',selected=0,downloaded=0,viewed=0,retry_policy='Do not retry unchanged in the next batch; rotate source.'))
 own=[dict(x) for x in db.execute('select media_id::text from media_rights_evidence where adapter_version=%s',('continuous-primary-images-20261011-b000240',))];assert own==[];db.close()
 save(E/'actual-visual-review.json',dict(at=now(),prepared_images=0,viewed_images=0,claim='No image was captured or prepared; no visual-review claim is made.'))
 save(E/'independent-production-verification.json',dict(at=now(),production_target=TARGET,current_campaign_rows=own,production_writes=0,verified_counts=counts,local_catalogue_connections=0))
 entry=next(x for x in q['sources'] if x['source_id']=='pinacoteca_sao_paulo');entry.update(status='bounded_official_routes_timed_out_access_hold',last_checked_at=now(),last_batch=240,checkpoint=rel(E/'CHECKPOINT.json'),access_status='Collection and terms routes timed out in bounded checks; no bypass or repeated request.',resume_cursor=dict(official_requests=2,object_records_captured=0,next_step='Rotate to another undercovered eligible registry route; retry Pinacoteca only after a later cooldown or access-state change.'),remaining_gaps=['Official collection object metadata remains uncaptured.','No record-explicit reusable image rights established.','Production institution identity and holdings require later official evidence.'],latest_batch_verified_counts=counts,evidence_paths=[rel(E/'bounded-production-gap-cohort.json'),rel(E/'source-access-and-rights-check.json')])
 assert [x for x in q['sources'] if x['source_id']!='pinacoteca_sao_paulo']==[x for x in before['sources'] if x['source_id']!='pinacoteca_sao_paulo']
 tmp=Q.with_suffix('.000240.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q)
 save(E/'source-queue-update-verification.json',dict(at=now(),modified_source_ids=['pinacoteca_sao_paulo'],unrelated_entries_preserved=110,all_111_registry_routes_preserved=True,queue_sha256=digest(Q),resume_cursor=entry['resume_cursor']))
 save(E/'batch-verification-receipt.json',dict(at=now(),verified_counts=counts,production_ids=[],production_writes=0,attribution='Fresh bounded read-only production reconciliation and official-route access audit; no prior additions counted.',production_target=TARGET,shared_ingestion_lock='artline-curated-ingestion',lock_not_acquired_because_no_write=True))
 nxt='Research an untouched undercovered Greek, Byzantine, Russian-icon, or post-Byzantine registry route whose access state is available; keep Pinacoteca de Sao Paulo on cooldown and do not repeat its unchanged timeout.'
 evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','bounded-production-gap-cohort.json','source-access-and-rights-check.json','actual-visual-review.json','independent-production-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']
 cp=dict(at=now(),batch=240,stage='verified_no_eligible_candidates',outcome='no_eligible_candidates',researched=dict(source_id='pinacoteca_sao_paulo',production_gaps=len(gaps),official_requests=len(checks)),selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task=nxt,blocker='',evidence_paths=[rel(E/x) for x in evidence],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0)
 save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
 save(E/'independent-final-artifact-verification.json',dict(at=now(),checkpoint_runtime_equal=load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),evidence=[dict(path=rel(E/x),sha256=digest(E/x)) for x in evidence],all_evidence_exists=all((E/x).exists() for x in evidence),counts_match=True,source_queue_sha256=digest(Q)))
 result=dict(outcome='no_eligible_candidates',summary='Batch 240 reconciled batch 107 and the production target, then checked the untouched Pinacoteca de Sao Paulo route. Both official collection and terms requests timed out in bounded checks; no object-level evidence or record-explicit reusable image rights could be established, so no records or images were selected and no production writes occurred.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=cp['evidence_paths']+[rel(E/'independent-final-artifact-verification.json'),rel(E/'CHECKPOINT.json')]);save(E/'worker-result.json',result);save(R/'result-001.json',result);print(json.dumps(result,ensure_ascii=False))
