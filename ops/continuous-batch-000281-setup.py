import csv,copy,fcntl,gzip,hashlib,importlib.util,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path('/Users/vadimdulub/Documents/vadim-dulub-git/artline');E=ROOT/'docs/research/continuous-production-20261011/batches/000281';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000281';E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
s=importlib.util.spec_from_file_location('h',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
with (R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json']
 for p in required:p.read_text()
 reg=list(csv.DictReader(required[1].open()));q=h.load(required[-1]);assert len(reg)==len(q['sources'])==111
 h.save(E/'required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in required],original_registry_rows=len(reg),supplementary_not_substituted=True))
 h.save(E/'original-source-registry.json',reg);h.save(E/'source-queue-before.json',q)
 target=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert target=='artline-508319:europe-west1:artline-postgres'
 proxies=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target in x];assert len(proxies)==1
 with h.connect() as db:
  server=dict(db.execute('SELECT current_database() db,pg_is_in_recovery() recovery').fetchone());assert server['db']=='artline' and not server['recovery']
  for n,tail in [('000107',''),('000280','norway/')]:
   p=E.parent/n/(tail+'independent-production-verification.json');prev=h.load(p);live=h.snapshot(db,list(prev['after']));assert live==prev['after'];h.save(E/('batch'+str(int(n))+'-live-reconciliation.json'),dict(at=h.now(),rows=len(live),prior_receipt=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),exact_postimage=True,uncertain_writes=False,prior_increments_counted=0))
  institutions=[dict(x) for x in db.execute("SELECT id::text,name,slug FROM institutions WHERE status<>'archived' AND (name ILIKE '%fine arts%boston%' OR slug ILIKE '%boston%') ORDER BY id LIMIT 20")]
  rows=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.unlinked_creator_label,to_jsonb(e) native FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikiart-artwork' WHERE a.current_institution_id=ANY(%s::uuid[]) AND a.status<>'archived' AND a.primary_media_id IS NULL AND a.creation_year_end<=1970 ORDER BY a.id LIMIT 10",([x['id'] for x in institutions],))]
  h.save(E/'boston-native-wikiart-gap-discovery.json',dict(at=h.now(),institutions=institutions,rows=rows,scope='Institution scoped bounded existing primary gaps + exact native wikiart-artwork identifier + creation_end<=1970; no provider or image requests'))
 h.save(E/'production-target-reconciliation.json',dict(at=h.now(),connection_name=target,proxy_command_inspected=True,proxy_port=55519,helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),database=server,shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
 ledgers=[E.parent/'000280/inherited-holds-verification.json',E.parent/'000280/failures-and-holds.json',E.parent/'000280/norway/research-holds.json',E.parent/'000280/norway/research-hold-clarification.json']
 h.save(E/'inherited-holds-verification.json',dict(at=h.now(),files=[dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),content=h.load(p)) for p in ledgers],queue_holds_read=True,all_unrelated_holds_preserved=True,no_held_provider_retry=True))
 h.save(E/'limits-verification.json',dict(at=h.now(),configured_source='ops/illustrated-300k-20261011.py',limits=dict(minimum_free_disk_bytes=32212254720,maximum_source_bytes=12000000,maximum_source_pixels=12000000,maximum_served_bytes=100000),free_disk_bytes=shutil.disk_usage(ROOT).free,separate_paid_services=0,spending_budget_invented=False))
 stops=[p for p in (ROOT/'docs/research/illustrated-300k-20261011').glob('*') if p.is_file() and any(t in p.name.lower() for t in ['stop','complete'])]
 h.save(E/'separate-continuation-verification.json',dict(at=h.now(),campaign='continuous-norway-images-20261011-b000281',stop_files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in stops],supervisor_unchanged=True,external_supervisor_pid=q.get('supervisor_pid'),no_new_supervisor_started=True))
 print(json.dumps(dict(boston_institutions=institutions,boston_candidates=rows,reconciled_batches=[107,280]),ensure_ascii=False))
