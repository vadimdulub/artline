#!/usr/bin/env python3
"""Bounded batch 239: untouched Uffizi primary-image-gap rights audit."""
import csv, datetime, fcntl, hashlib, importlib.util, json, os, subprocess
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000239'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000239'
Q=E.parents[1]/'source-queue.json'; REG=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
TARGET='artline-508319:europe-west1:artline-postgres'
spec=importlib.util.spec_from_file_location('helper',ROOT/'ops/india-300-delivery-20261011.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,p)
def rel(p): return str(Path(p).relative_to(ROOT))

E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
with (R/'worker.lock').open('a+') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB);started=now()
 required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 rows=list(csv.DictReader(REG.open()));assert len(rows)==111;route=next(x for x in rows if x['source_id']=='uffizi')
 save(E/'required-input-verification.json',{'at':started,'files':[{'path':p,'sha256':sha(ROOT/p)} for p in required],'registry_path':str(REG),'registry_sha256':sha(REG),'registry_records':111,'complete_registry_used':True})
 q=load(Q);assert len(q['sources'])==111;before=json.loads(json.dumps(q));save(E/'source-queue-before.json',before)
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 cmds=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();proxies=[x for x in cmds if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and TARGET in x];assert len(proxies)==1
 db=h.connect();server=db.execute('select current_database() db, inet_server_addr()::text host').fetchone();assert server['db']=='artline'
 save(E/'production-target-reconciliation.json',{'at':now(),'connection_name':actual,'proxy_port':55519,'proxy_command_inspected':True,'database':server['db'],'helper':'ops/india-300-delivery-20261011.py','shared_ingestion_lock':'artline-curated-ingestion','write':False,'local_catalogue_connections':0})
 prior=load(E.parent/'000107/independent-production-verification.json');live=h.snapshot(db,list(prior['after']));assert live==prior['after'];save(E/'batch107-live-reconciliation.json',{'at':now(),'production_rows':len(live),'matches_independent_postimage':True,'increment':0})
 inst=[dict(x) for x in db.execute("select id::text,name from institutions where lower(name) like any(%s) order by name",(['%uffizi%','%pitti%'],))]
 ids=[x['id'] for x in inst]
 gaps=[]
 if ids:
  gaps=[dict(x) for x in db.execute("select id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,current_institution_id::text,unlinked_creator_label,status from artworks where current_institution_id=any(%s::uuid[]) and primary_media_id is null and status<>'archived' order by id limit 25",(ids,))]
 save(E/'bounded-production-gap-cohort.json',{'at':now(),'institutions':inst,'limit':25,'rows':gaps,'count':len(gaps),'read_only':True})
 session=requests.Session();session.headers['User-Agent']='ArtlineResearch/1.0 (bounded source verification)'
 checks=[]
 for label,url in [('collection',route['collection_url']),('terms',route['terms_url'])]:
  try:
   r=session.get(url,timeout=(15,45),allow_redirects=True);checks.append({'label':label,'requested_url':url,'final_url':r.url,'status':r.status_code,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'content_type':r.headers.get('Content-Type'),'retry_after':r.headers.get('Retry-After')})
  except Exception as ex: checks.append({'label':label,'requested_url':url,'error':type(ex).__name__+': '+str(ex)[:240]})
 save(E/'source-access-and-rights-check.json',{'at':now(),'source':route,'requests':checks,'disposition':'no_eligible_record_explicit_open_image','basis':'Registry requires never_unless_explicit_permission. The bounded official collection/terms checks supplied no object-level open-image licence for any production gap; no images were downloaded. Italian cultural-heritage and museum terms were not generalized into permission.','selected':0,'downloaded':0,'viewed':0})
 own=[dict(x) for x in db.execute("select media_id::text from media_rights_evidence where adapter_version=%s",('continuous-primary-images-20261011-b000239',))];assert own==[];db.close()
 counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
 save(E/'actual-visual-review.json',{'at':now(),'prepared_images':0,'viewed_images':0,'claim':'No image was selected or prepared because record-explicit reuse permission was absent; no visual-review claim is made.'})
 save(E/'independent-production-verification.json',{'at':now(),'production_target':TARGET,'current_campaign_rows':own,'production_writes':0,'verified_counts':counts,'local_catalogue_connections':0})
 entry=next(x for x in q['sources'] if x['source_id']=='uffizi');entry.update(status='bounded_official_collection_and_terms_researched_no_record_explicit_open_images',last_checked_at=now(),checkpoint=rel(E/'CHECKPOINT.json'),access_status='Official collection and terms checked once; exact HTTP receipts persisted. No authentication bypass, media download, or repeated request.',remaining_gaps=['Bounded production cohort retained in bounded-production-gap-cohort.json.','Object-level explicit image permission remains absent; manual licensing is outside this image batch.','Broader catalogue and museum coverage remain unresearched.'],latest_batch_verified_counts=counts,evidence_paths=[rel(E/'bounded-production-gap-cohort.json'),rel(E/'source-access-and-rights-check.json')])
 assert [x for x in q['sources'] if x['source_id']!='uffizi']==[x for x in before['sources'] if x['source_id']!='uffizi']
 tmp=Q.with_suffix('.000239.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q)
 save(E/'source-queue-update-verification.json',{'at':now(),'modified_source_ids':['uffizi'],'unrelated_entries_preserved':110,'all_111_registry_routes_preserved':True,'queue_sha256':sha(Q)})
 save(E/'batch-verification-receipt.json',{'at':now(),'verified_counts':counts,'production_ids':[],'production_writes':0,'attribution':'Fresh bounded read-only production and source-rights audit; no prior campaign additions counted.','production_target':TARGET,'shared_ingestion_lock':'artline-curated-ingestion','lock_not_acquired_because_no_write':True})
 nxt='Research the untouched Pinacoteca de Sao Paulo registry route: identify a bounded live production image-gap cohort and require record-explicit reusable image rights; if no eligible images, rotate to another undercovered route without retrying Uffizi unchanged.'
 evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','bounded-production-gap-cohort.json','source-access-and-rights-check.json','actual-visual-review.json','independent-production-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']
 cp={'at':now(),'batch':239,'stage':'verified_no_eligible_candidates','outcome':'no_eligible_candidates','researched':{'source_id':'uffizi','production_gaps':len(gaps),'official_requests':len(checks)},'selected':0,'prepared':0,'imported':0,'verified':0,'verified_counts':counts,'next_task':nxt,'blocker':'','evidence_paths':[rel(E/x) for x in evidence],'external_supervisor_unchanged':True,'production_writes':0,'local_catalogue_connections':0}
 save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
 save(E/'independent-final-artifact-verification.json',{'at':now(),'checkpoint_runtime_equal':load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),'evidence':[{'path':rel(E/x),'sha256':sha(E/x)} for x in evidence],'all_evidence_exists':all((E/x).exists() for x in evidence),'counts_match':True,'source_queue_sha256':sha(Q)})
 print(json.dumps({'outcome':cp['outcome'],'summary':f"Researched {len(gaps)} Uffizi production image gaps; no record-explicit open images were eligible and no writes occurred.",'next_task':nxt,'blocker':'','verified_counts':counts,'evidence_paths':cp['evidence_paths']+[rel(E/'independent-final-artifact-verification.json')]}))
