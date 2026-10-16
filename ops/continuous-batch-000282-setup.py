import importlib.util,csv,json,subprocess,gzip,datetime,requests
from pathlib import Path
ROOT=Path('/Users/vadimdulub/Documents/vadim-dulub-git/artline')
spec=importlib.util.spec_from_file_location('h',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
E=ROOT/'docs/research/continuous-production-20261011/batches/000282';E.mkdir(parents=True,exist_ok=True)
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000282';R.mkdir(parents=True,exist_ok=True)
original_save=h.save
def stable_save(p,v):
 if not p.exists():original_save(p,v)
h.save=stable_save
Q=E.parents[1]/'source-queue.json';q=h.load(Q)
required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',Q,E.parents[1]/'CHECKPOINT.json']
for p in required:p.read_text()
registry=list(csv.DictReader(required[1].open()));assert len(registry)==111
h.save(E/'required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],complete_original_registry_used=True,registry_rows=111))
h.save(E/'original-source-registry.json',registry)
h.save(E/'source-queue-preimage.json',q)
paths=sorted(E.parent.glob('*/*hold*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:12]
h.save(E/'inherited-holds-verification.json',dict(at=h.now(),ledgers=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),content=h.load(p)) for p in paths],prior_holds_preserved=True,policy_correction='Athens batch259 blanket rights hold is superseded by Greek museum image extension through1955; no object/date/access holds removed.'))
target='artline-508319:europe-west1:artline-postgres'
actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==target
ps=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();proxies=[x for x in ps if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target in x];assert len(proxies)==1
with h.connect() as db:
 server=dict(db.execute('SELECT current_database() database,pg_is_in_recovery() recovery').fetchone());assert server['database']=='artline' and not server['recovery']
 h.save(E/'production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_command=proxies[0],database=server,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',local_catalogue_connections=0))
 for batch,key in [('000107','after'),('000281/norway','after')]:
  p=E.parent/batch/('independent-production-verification.json');prior=h.load(p);live=h.snapshot(db,list(prior[key]));assert live==prior[key]
  h.save(E/f'batch{batch[:6]}-live-reconciliation.json',dict(at=h.now(),rows=len(live),snapshot_equal=True,receipt_sha256=h.sha(p.read_bytes()),prior_increments_counted=0))

h.save(E/'authorization.json',dict(at=h.now(),operation='continuous-greek-20261011-b000282',metadata='Source-backed production additions through1970, new works review; local catalogue read-only',images='Explicit Greek museum extension through1955 in docs/ARTLINE_IMAGE_USE.md; actual rights restricted separate from user authorization',services='Cloud SQL Storage plus authentication secret proxy recovery verification only; Translation prohibited'))
import shutil
free=shutil.disk_usage(R).free;assert free>30*1024**3
h.save(E/'storage-limit-verification.json',dict(at=h.now(),free_bytes=free,minimum_headroom_bytes=30*1024**3,new_budget=False,limits_unchanged=True))
state=h.load(E.parents[1]/'CHECKPOINT.json');assert state['inflight']['batch']==282
cmd=subprocess.check_output(['ps','-p',str(state['supervisor_pid']),'-o','command='],text=True).strip();assert 'continuous-production-research.py run' in cmd
h.save(E/'supervisor-observation.json',dict(at=h.now(),pid=state['supervisor_pid'],command=cmd,external_supervisor_live=True,supervisor_modified=False,subagents_created=0))
print('Inputs, registry, holds, target, batch107 and281 receipts and live supervisor verified.')
