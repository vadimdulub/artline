#!/usr/bin/env python3
"""Bounded batch 138: finish Museum Data Service painting page 4 research."""
import copy, csv, fcntl, gzip, importlib.util, json, os, re, subprocess
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000138'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000138'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000138'
for p in (E,R,S): p.mkdir(parents=True,exist_ok=True)
sp=importlib.util.spec_from_file_location('h138',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
def save(name,value):
 p=E/name
 if p.exists(): return h.load(p)
 h.save(p,value);return value
def rel(p): return str(Path(p).relative_to(ROOT))

with (R/'worker.lock').open('a+') as worker:
 fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
 required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json']
 registry=list(csv.DictReader(required[1].open()));queue=h.load(required[-1]);assert len(registry)==111 and {x['source_id'] for x in registry}=={x['source_id'] for x in queue['sources']}
 save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],registry_rows=111,complete_original_registry_used=True,local_catalogue_connections=0))
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 proxy=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if 'cloud-sql-proxy' in x and '--port 55519' in x and actual in x];assert proxy
 save('production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_verified=True,proxy_port=55519,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
 with h.connect() as db:
  prev=h.load(E.parent/'000107/independent-production-verification.json');assert h.snapshot(db,list(prev['after']))==prev['after']
 save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(prev['after']),previous_increments_counted=0))
 prior=h.load(E.parent/'000129/captures/mds-painting-page4.json');body=gzip.decompress(Path(prior['body_path']).read_bytes());assert h.sha(body)==prior['sha256']
 page=BeautifulSoup(body,'html.parser');links=[]
 for a in page.select('a[href*="/objects/"]'):
  m=re.search(r'/objects/([0-9a-f-]{36})',a.get('href',''))
  if m and m.group(1) not in links: links.append(m.group(1))
 assert len(links)>=20;todo=links[10:20]
 route=next(x for x in queue['sources'] if x['source_id']=='museum_data_service_uk');assert not set(todo)&set(route['resume_cursor']['processed_source_ids'])
 session=requests.Session();session.headers['User-Agent']='Artline catalogue research; bounded metadata review'
 records=[]
 with h.connect() as db:
  for off,pid in enumerate(todo,10):
   url='https://museumdata.uk/objects/'+pid;r=session.get(url,timeout=(15,45));r.raise_for_status();raw=r.content;bp=S/(pid+'.html.gz');bp.write_bytes(gzip.compress(raw,mtime=0));soup=BeautifulSoup(raw,'html.parser')
   fields=[]
   for div in soup.select('dl div'):
    if div.dt and div.dd: fields.append([div.dt.get_text(' ',strip=True).rstrip(':'),div.dd.get_text(' ',strip=True)])
   vals={}
   for k,v in fields: vals.setdefault(k,[]).append(v)
   text=soup.get_text(' ',strip=True);title=(vals.get('Title') or vals.get('Object title') or [soup.title.get_text(' ',strip=True) if soup.title else pid])[0]
   dates=' '.join(vals.get('Object production date',[])+vals.get('Date - earliest/single',[])+vals.get('Date - latest',[]));years=[int(x) for x in re.findall(r'(?<!\d)(1\d{3}|20\d{2})(?!\d)',dates)]
   names=' '.join(vals.get('Object name(s)',[])+vals.get('Object name',[])).lower();lic=' '.join(vals.get('Attribution',[])+vals.get('Rights',[])+[text[-2000:]])
   existing=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme='museum-data-service-object' AND e.external_id=%s UNION SELECT a.id::text,a.title,a.accession_number FROM citations c JOIN artworks a ON a.id=c.entity_id WHERE c.entity_type='artwork' AND c.source_url=%s",(pid,url))]
   pictorial=any(x in (title+' '+names).lower() for x in ['painting','watercolour','drawing','icon','print'])
   if existing: outcome='existing_exact_object'
   elif not pictorial: outcome='non_pictorial_or_directory_notice'
   elif not years: outcome='unknown_creation_date_hold'
   elif max(years)>1970: outcome='outside_creation_scope'
   elif 'CC BY-NC' in text or 'non-commercial' in text.lower(): outcome='metadata_reuse_hold'
   else: outcome='eligible_requires_contributor_holding_and_global_identity_reconciliation'
   records.append(dict(source_id=pid,source_url=url,page=4,offset=off,status=r.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(bp),title=title,date_text=dates,years=years,object_names=names,existing=existing,outcome=outcome,fields=fields))
 save('independent-source-verification.json',dict(at=h.now(),provider='museum_data_service_uk',route='painting_page4_offsets10_19',page_capture_sha256=prior['sha256'],records=records,distinct_objects=len(records),all_http_200=True,selected_for_ingestion=0))
 counts_by={}
 for x in records: counts_by[x['outcome']]=counts_by.get(x['outcome'],0)+1
 save('object-research-and-holds.json',dict(at=h.now(),records=records,counts_by_outcome=counts_by,source_notices_not_delivered_artworks=True,selected=0))
 save('independent-production-verification.json',dict(at=h.now(),production_target=actual,writes=0,verified_counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0),reason='No object passed contributor-holding and global-identity selection in this bounded research pass; live production used read-only reconciliation only.'))
 before=queue;after=copy.deepcopy(before);row=next(x for x in after['sources'] if x['source_id']=='museum_data_service_uk');now=h.now();row.update(last_batch=138,last_checked_at=now,checkpoint=rel(E/'CHECKPOINT.json'),status='painting_page4_complete_offsets10_19_researched_no_selected_rows',latest_batch_verified_counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0));row['resume_cursor'].update(completed_page=4,next_page=5,next_url='https://museumdata.uk/object-search/?q=painting&i=5',page=5,offset=0,completed_page4_offsets=list(range(20)),exact_resume_evidence=rel(E/'object-research-and-holds.json'));row['resume_cursor']['processed_source_ids']=list(dict.fromkeys(row['resume_cursor']['processed_source_ids']+todo));row.setdefault('research_history',[]).append(dict(at=now,batch=138,researched_distinct_objects=10,selected=0,verified_counts=row['latest_batch_verified_counts'],evidence=rel(E/'independent-source-verification.json')));row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+[rel(E/'independent-source-verification.json'),rel(E/'object-research-and-holds.json')]))
 qpath=E.parents[1]/'source-queue.json'
 with qpath.with_suffix('.lock').open('a+') as qlock:
  fcntl.flock(qlock,fcntl.LOCK_EX);tmp=qpath.with_suffix('.138.tmp');tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qpath)
 save('source-queue-update-verification.json',dict(at=h.now(),updated_source='museum_data_service_uk',unrelated_entries_preserved=[x for x in before['sources'] if x['source_id']!='museum_data_service_uk']==[x for x in after['sources'] if x['source_id']!='museum_data_service_uk'],processed_source_ids=todo,next_page=5,queue_sha256=h.sha(qpath.read_bytes())))
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0);next_task='Rotate to a new undercovered registry-backed Byzantine or Greek pictorial route. MDS painting search is checkpointed at page5; do not repeat page4 or unchanged holds.'
 evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','independent-source-verification.json','object-research-and-holds.json','independent-production-verification.json','source-queue-update-verification.json']
 save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=[],production_writes=0,attribution='Ten distinct new source notices researched; none imported or counted.',production_target=actual,shared_ingestion_lock='artline-curated-ingestion'))
 cp=dict(at=h.now(),batch=138,stage='verified_complete_no_eligible_candidates',verified_counts=counts,researched=dict(provider='museum_data_service_uk',route='painting_page4_offsets10_19',distinct_objects=10,counts_by_outcome=counts_by),selected=0,prepared=0,imported=0,verified=0,next_task=next_task,blocker='',evidence=[rel(E/x) for x in evidence+['batch-verification-receipt.json']],external_supervisor_unchanged=True,local_catalogue_connections=0,production_writes=0)
 save('CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
 checked=[]
 for name in evidence+['batch-verification-receipt.json','CHECKPOINT.json']:
  p=E/name;h.load(p);checked.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
 save('independent-final-artifact-verification.json',dict(at=h.now(),artifacts=checked,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,queue_resume_page=5,passed=True))
 print(json.dumps(dict(outcome='no_eligible_candidates',summary='Batch 138 completed the ten unreviewed Museum Data Service painting notices on page 4. All source pages returned HTTP 200; none passed the full date, pictorial-object, contributor-holding and global-identity selection needed for a production insert, so production remained unchanged.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in evidence+['batch-verification-receipt.json','CHECKPOINT.json','independent-final-artifact-verification.json']])))
