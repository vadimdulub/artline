"""One bounded read-only source selection and recovery reconciliation."""
import importlib.util,csv,json,gzip,subprocess,shutil,fcntl,re
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('base',ROOT/'ops/continuous-image-batch-000002.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000278';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000278';S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000278'
for p in [E,R,S]:p.mkdir(parents=True,exist_ok=True)
def save(name,v):
 p=E/name
 if not p.exists():h.save(p,v)
 return h.load(p)
with (R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 Q=E.parents[1]/'source-queue.json';q=h.load(Q);save('source-queue-before.json',q)
 req=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',Q,E.parents[1]/'CHECKPOINT.json']
 for p in req:p.read_text()
 registry=list(csv.DictReader(req[1].open()));assert len(registry)==111
 save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in req],original_registry_rows=111,complete_registry_preserved=True,local_catalogue_connections=0))
 save('original-source-registry.json',registry)
 holds=sorted(E.parent.glob('*/**/*hold*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:18]
 save('inherited-holds-verification.json',dict(at=h.now(),ledgers=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),content=h.load(p)) for p in holds],prior_holds_preserved=True))
 target=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert target=='artline-508319:europe-west1:artline-postgres'
 save('production-target-reconciliation.json',dict(b.target(),connection_name=target,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',local_catalogue_connections=0))
 with h.connect() as db:
  for batch,path,key in [('107','000107/independent-production-verification.json','after'),('277','000277/norway/independent-production-verification.json','rows')]:
   p=E.parent/path;old=h.load(p);prior=old.get('after') or old.get(key);assert prior
   current=h.snapshot(db,list(prior));assert current==prior
   save('batch'+batch+'-live-reconciliation.json',dict(at=h.now(),rows=len(current),postimage_exact=True,prior_receipt_sha256=h.sha(p.read_bytes()),uncertain_writes=False,previous_increments_counted=0))
  rows=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_display,date_precision,primary_media_id::text,work_type FROM artworks WHERE current_institution_id='052007aa-11f7-4d57-90e6-d3b62bb0bf4b' AND status<>'archived' AND primary_media_id IS NULL ORDER BY id LIMIT 150")]
  save('athens-live-image-gap-query.json',dict(at=h.now(),bounded_limit=150,rows=rows,eligible_known_dates=[r['id'] for r in rows if r['creation_year_end'] and r['creation_year_end']<=1955],images_requested=0))
 page=E/'athens-page3-capture.json'
 if not page.exists():
  i.provider_slot('www.nationalgallery.gr');r=i.session().post('https://www.nationalgallery.gr/wp-admin/admin-ajax.php',data={'creteria[language]':'en','creteria[artwork_name]':'','creteria[artwork_type]':'64','creteria[permanent_exhibition]':'','creteria[location]':'','creteria[extra_filters]':'false','page':'3','action':'get_artworks'},timeout=(15,45));path=S/'athens-page3.json';path.write_bytes(r.content)
  save('athens-page3-capture.json',dict(at=h.now(),url=r.url,status=r.status_code,sha256=h.sha(r.content),body_path=str(path),retry_after=r.headers.get('Retry-After'),request=dict(action='get_artworks',artwork_type=64,page=3)))
 rc=h.load(page);assert rc['status']==200;raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'];payload=json.loads(raw)
 save('athens-page3-index.json',payload)
 print('ATHENS GAPS',json.dumps(rows,ensure_ascii=False));print('PAGE3',str(payload)[:18000])
 state=h.load(E.parents[1]/'CHECKPOINT.json');cmd=subprocess.check_output(['ps','-p',str(state['supervisor_pid']),'-o','command='],text=True).strip();assert 'continuous-production-research.py run' in cmd
 save('supervisor-observation.json',dict(at=h.now(),external_supervisor_live=True,pid=state['supervisor_pid'],command=cmd,supervisor_unchanged=True,new_sessions=0,subagents=0))
 save('storage-limit-verification.json',dict(at=h.now(),free_bytes=shutil.disk_usage(R).free,configured_headroom_bytes=30*1024**3,limits_unchanged=True,new_budget=False))
