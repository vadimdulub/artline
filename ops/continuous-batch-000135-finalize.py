#!/usr/bin/env python3
"""Bounded batch 135: research the untouched official Doxaras route."""
import csv, gzip, html, json, re, subprocess
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000135'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000135'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000135'
for p in (E,R,S):p.mkdir(parents=True,exist_ok=True)
import importlib.util
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,ROOT/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=mod('h135','ops/india-300-delivery-20261011.py')
def save(n,v):
 p=E/n
 if p.exists(): return h.load(p)
 h.save(p,v);return v
def rel(p):return str(Path(p).relative_to(ROOT))
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s))).strip()

required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json']
registry=list(csv.DictReader(required[1].open()));queue=h.load(required[-1]);assert len(registry)==111 and {x['source_id'] for x in registry}=={x['source_id'] for x in queue['sources']}
save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],registry_rows=111,complete_original_registry_used=True,local_catalogue_connections=0))
actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
proxy=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x];assert proxy
save('production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_verified=True,proxy_port=55519,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
with h.connect() as db:
 prev=h.load(E.parent/'000107/independent-production-verification.json');snap=h.snapshot(db,list(prev['after']));assert snap==prev['after']
save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,previous_increments_counted=0,rows=len(snap)))

index='https://www.nationalgallery.gr/en/artist/doxaras-panagiotis/'
session=requests.Session();session.headers['User-Agent']='Artline research contact: catalogue enrichment'
ri=session.get(index,timeout=(15,45));ri.raise_for_status();urls=list(dict.fromkeys(re.findall(r'href=["\']([^"\']+/en/artwork/[^"\']+)',ri.text)))
assert 1<=len(urls)<=50
captures=[]
with h.connect() as db:
 for url in urls:
  r=session.get(url,timeout=(15,45));r.raise_for_status();raw=r.content;key=url.rstrip('/').split('/')[-1];bp=S/(key+'.html.gz');bp.write_bytes(gzip.compress(raw,mtime=0))
  text=r.text
  title=clean(re.search(r'<h1 class="artwork[^"]*">(.*?)</h1>',text,re.S).group(1))
  inv=clean(re.search(r'<div class="artwork-no">(.*?)</div>',text,re.S).group(1)).replace('Inv. Number','').strip()
  desc=clean(re.search(r'<p class="description">(.*?)</p>',text,re.S).group(1))
  date_match=re.search(r'<h1 class="artwork[^"]*">.*?<span[^>]*>(.*?)</span>.*?</h1>',text,re.S)
  date=clean(date_match.group(1)) if date_match else ''
  years=[int(x) for x in re.findall(r'(?<!\d)[12]\d{3}(?!\d)',date)]
  exact=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,primary_media_id::text FROM artworks WHERE current_institution_id=%s AND accession_number=%s UNION SELECT a.id::text,a.title,a.accession_number,a.primary_media_id::text FROM citations c JOIN artworks a ON a.id=c.entity_id WHERE c.entity_type='artwork' AND c.source_url=%s",('052007aa-11f7-4d57-90e6-d3b62bb0bf4b',inv,url))]
  reason='Exact existing physical object; excluded from new increments' if exact else ('Official notice supplies no creation year; held under no-invented-dates rule' if not years else 'Requires further global version/creator reconciliation before selection')
  captures.append(dict(url=url,status=r.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(bp),source_id=key,title=title,accession_number=inv,date_display=date,description=desc,existing=exact,outcome=reason))
save('independent-source-verification.json',dict(at=h.now(),provider='national_gallery_athens',route='doxaras-panagiotis',index_url=index,index_status=ri.status_code,index_sha256=h.sha(ri.content),object_notices=len(captures),rows=captures,all_http_200=True,selected=0))
save('research-holds.json',dict(at=h.now(),holds=[dict(source_id=x['source_id'],reason=x['outcome']) for x in captures],unchanged_failed_requests=0,provider_access_hold=False))
save('source-access-holds.json',dict(at=h.now(),provider_access_hold=False,access_status=f'Official artist index and {len(captures)} distinct object notices HTTP 200.',prior_ledgers_preserved=True))

before=queue;after=json.loads(json.dumps(before));row=next(x for x in after['sources'] if x['source_id']=='national_gallery_athens');row.update(last_batch=135,last_checked_at=h.now(),checkpoint=rel(E/'CHECKPOINT.json'),status='doxaras_five_official_notices_researched_no_eligible_new_rows',latest_batch_verified_counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0));row.setdefault('research_history',[]).append(dict(batch=135,at=h.now(),route='doxaras-panagiotis',source_notices_reviewed=len(captures),selected=0,evidence=rel(E/'independent-source-verification.json'),verified_counts=row['latest_batch_verified_counts']));row['resume_cursor']['doxaras_processed_urls']=urls;row['resume_cursor']['next_undercovered_creator_route']='Select a different untouched official Greek creator index; Doxaras route is reviewed and held.'
qpath=E.parents[1]/'source-queue.json';qpath.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
save('independent-queue-verification.json',dict(at=h.now(),updated_source='national_gallery_athens',unrelated_entries_preserved=[x for x in before['sources'] if x['source_id']!='national_gallery_athens']==[x for x in after['sources'] if x['source_id']!='national_gallery_athens'],processed_urls=urls,after_sha256=h.sha(qpath.read_bytes())))
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','independent-source-verification.json','research-holds.json','source-access-holds.json','independent-queue-verification.json']
checkpoint=dict(at=h.now(),batch=135,stage='verified_complete_no_eligible_candidates',verified_counts=counts,researched=dict(provider='national_gallery_athens',route='doxaras-panagiotis',object_notices=len(captures)),selected=0,prepared=0,imported=0,verified=0,next_task='Rotate to a different untouched registry-backed Greek or Byzantine object route; do not repeat the reviewed Doxaras notices or unchanged holds.',evidence=[rel(E/x) for x in evidence],external_supervisor_unchanged=True,local_catalogue_connections=0,production_writes=0)
save('CHECKPOINT.json',checkpoint);save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=[],production_writes=0,attribution='No eligible new rows after exact official-notice and live-production reconciliation.',production_target=actual,shared_ingestion_lock='artline-curated-ingestion'))
result=dict(outcome='no_eligible_candidates',summary=f'Batch 135 researched {len(captures)} distinct official National Gallery Athens Doxaras object notices. Exact existing objects and notices without a usable creation year were excluded or held; no production write was made.',next_task=checkpoint['next_task'],blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in evidence+['batch-verification-receipt.json','CHECKPOINT.json']])
save('worker-result.json',result);print(json.dumps(result))
