#!/usr/bin/env python3
import copy, datetime, fcntl, hashlib, json, os, subprocess, urllib.request
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000186'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000186'
Q=ROOT/'docs/research/continuous-production-20261011/source-queue.json'
URL='https://www.getty.edu/art/collection/api/search?q=Byzantine&size=50&from=200&include_deaccessioned=false'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n')
def connect():
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
 kw=psycopg.conninfo.conninfo_to_dict(secret);kw.update(host='127.0.0.1',port='55519',sslmode='disable',connect_timeout=20)
 return psycopg.connect(**kw,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=60000')

E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
save(E/'required-input-verification.json',{'at':now(),'files':[{'path':p,'sha256':sha((ROOT/p).read_bytes())} for p in required],'registry':{'path':'/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv','sha256':sha(Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv').read_bytes())}})
proxy=subprocess.check_output(['ps','aux'],text=True)
pline=next(x for x in proxy.splitlines() if '/tmp/artline-cloud-sql-proxy' in x and '--port 55519' in x)
assert 'artline-508319:europe-west1:artline-postgres' in pline
with connect() as db:
 target=db.execute("select current_database() db, current_setting('transaction_read_only') ro").fetchone()
 live=db.execute("select count(*) artworks, count(*) filter(where primary_media_id is not null) illustrated from artworks where status<>'archived'").fetchone()
 b107=db.execute("select count(*) n from citations where source_url like '%%000107%%'").fetchone()['n']
save(E/'production-target-reconciliation.json',{'at':now(),'proxy':{'port':55519,'target':'artline-508319:europe-west1:artline-postgres','verified':True},'database':target,'live':live,'batch107_citation_matches':b107,'writes':0,'read_only':True})
req=urllib.request.Request(URL,headers={'User-Agent':'ArtlineResearch/1.0'})
with urllib.request.urlopen(req,timeout=30) as res: body=res.read(); status=res.status
cap=R/'getty-byzantine-offset-200.json';cap.write_bytes(body)
data=json.loads(body);pool=data.get('data',[])
def labels(x): return ' '.join(str(x.get(k,'')) for k in ('title','name','type','classification','medium','description')).lower()
nonpic=('coin','medal','vessel','jewelry','jewellery','statuette','sculpture','textile','glass','bowl','cup','plate','spoon','cross','reliquary','manuscript binding')
pict=('painting','illumination','drawing','print','icon','fresco','mosaic','panel')
rows=[]
for x in pool:
 t=labels(x); rows.append({'id':x.get('id'),'slug':x.get('slug'),'title':x.get('title') or x.get('name'),'classification_text':t,'decision':'pictorial_lead_requires_detail_review' if any(k in t for k in pict) and not any(k in t for k in nonpic) else 'excluded_nonpictorial_or_unresolved_index_lead'})
selected=[x for x in rows if x['decision'].startswith('pictorial')]
receipt={'at':now(),'url':URL,'status':status,'sha256':sha(body),'offset':200,'returned':len(pool),'search_total':data.get('total'),'classified':rows,'pictorial_leads':selected,'images_requested':0,'production_writes':0}
save(E/'independent-source-verification.json',receipt)
with open(str(Q)+'.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);q=json.loads(Q.read_text());before=copy.deepcopy(q);route=next(r for r in q['sources'] if r['source_id']=='getty_museum')
 route['status']='byzantine_offset200_researched_no_selected_pictorial_objects' if not selected else 'byzantine_offset200_pictorial_leads_held_for_detail_review'
 route['checkpoint']='docs/research/continuous-production-20261011/batches/000186/CHECKPOINT.json'
 route['resume_cursor']['last_offset']=200;route['resume_cursor']['next_offset']=250;route['resume_cursor']['size']=50
 route['resume_cursor']['last_page_evidence']='docs/research/continuous-production-20261011/batches/000186/independent-source-verification.json'
 route['resume_cursor']['next_step']='Resume Getty Byzantine at offset250 only after choosing a verified pictorial filter; offset200 yielded '+str(len(selected))+' unresolved pictorial leads. Prefer an untouched Russian icon registry route.'
 Q.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');save(E/'source-queue-update-verification.json',{'at':now(),'source_id':'getty_museum','unrelated_entries_preserved':len(before['sources'])==len(q['sources']),'before_sha256':sha(json.dumps(before,sort_keys=True).encode()),'after_sha256':sha(json.dumps(q,sort_keys=True).encode()),'resume_cursor':route['resume_cursor']})
counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
next_task='Research an untouched Russian icon registry institution with object-level metadata and permitted images; Getty broad Byzantine offset250 is deferred pending a pictorial filter.'
checkpoint={'at':now(),'batch':186,'stage':'complete_no_eligible_candidates','discovered':len(pool),'selected':0,'prepared':0,'imported':0,'verified_counts':counts,'holds':{'pictorial_index_leads_requiring_detail_review':len(selected),'nonpictorial_or_unresolved_index_leads':len(pool)-len(selected)},'next_task':next_task,'blocker':'','evidence':['docs/research/continuous-production-20261011/batches/000186/required-input-verification.json','docs/research/continuous-production-20261011/batches/000186/production-target-reconciliation.json','docs/research/continuous-production-20261011/batches/000186/independent-source-verification.json','docs/research/continuous-production-20261011/batches/000186/source-queue-update-verification.json']}
save(E/'CHECKPOINT.json',checkpoint);save(E/'batch-verification-receipt.json',checkpoint)
save(E/'independent-final-artifact-verification.json',{'at':now(),'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())} for p in sorted(E.glob('*.json')) if p.name!='independent-final-artifact-verification.json'],'verified_counts':counts,'production_writes':0})
save(R/'worker-result.json',{'outcome':'no_eligible_candidates','summary':f'Getty Byzantine offset 200 researched: {len(pool)} index leads, {len(selected)} pictorial leads held for detail review, no selected production-safe objects or writes.','next_task':next_task,'blocker':'','verified_counts':counts,'evidence_paths':checkpoint['evidence']+['docs/research/continuous-production-20261011/batches/000186/batch-verification-receipt.json','docs/research/continuous-production-20261011/batches/000186/independent-final-artifact-verification.json','docs/research/continuous-production-20261011/batches/000186/CHECKPOINT.json']})
print(json.dumps(json.loads((R/'worker-result.json').read_text())))
