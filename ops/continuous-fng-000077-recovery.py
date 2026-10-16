#!/usr/bin/env python3
"""Scoped production schema and exact affected-row backup outside Documents."""
import importlib.util,subprocess,os,json,shutil,fcntl
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-fng-images-000077.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,_,_=i.accepted(b.B);ids=[im['artwork_id'] for im in images]
assert not (b.E/'local-recovery-verification.json').exists()
b.save(b.E/'production-target-before-scoped-recovery.json',b.target())
backup=i.BACKUP;backup.mkdir(parents=True,exist_ok=True);backup.chmod(0o700)
secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
kw=h.psycopg.conninfo.conninfo_to_dict(secret);env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
path=backup/'production-schema-before.pgdump'
r=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180);assert r.returncode==0,'Schema export failed'
path.chmod(0o600)
r=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True);toc=backup/'production-schema-before.toc';toc.write_bytes(r.stdout);toc.chmod(0o600)
with open(os.devnull,'wb') as sink:subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
with b.connect() as db:
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 states=h.snapshot(db,ids);prior=b.load(b.E/'preparation-production-snapshot.json.gz')['before'];assert all(states[aid]==prior[aid] for aid in ids)
 out=dict(at=h.now(),artworks=states)
 for table,where,args in [
 ('citations',"entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)),
 ('external_identifiers',"entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)),
 ('artwork_search_documents','id=ANY(%s::uuid[])',(ids,)),
 ('sources','id=%s',(b.b.SID,)),
 ('institutions','id=%s',(b.b.MID,))]:
  out[table]=[r['v'] for r in db.execute('SELECT to_jsonb(t) v FROM '+table+' t WHERE '+where,args)]
 assert out['sources'] and out['institutions']
 h.save(backup/'affected-row-recovery-before.json.gz',out)
 plan=backup/'image-selection.json.gz';shutil.copyfile(i.folder(b.B)/'selection.json.gz',plan)
files=[path,toc,backup/'affected-row-recovery-before.json.gz',plan]
for f in files:
 if f.suffix=='.gz':h.load(f)
manifest=[dict(path=str(f),bytes=f.stat().st_size,sha256=h.sha(f.read_bytes())) for f in files]
v=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',path=str(backup),files=manifest,selected_images=len(ids),schema_archive_fully_decoded=True,all_json_exports_fully_decoded=True,full_database_backup=False,cloud_backups_created=0,additional_locked_preimages_required=True,local_catalogue_connections=0,recovery='Use exact transaction preimages, selection/source/visual checksums and audit history before corrective action. Immutable storage writes use generation-zero preconditions. No recovery mutations executed.')
b.save(b.E/'local-recovery-verification.json',v);h.save(backup/'local-recovery-verification.json',v)
print('Scoped local production recovery verified:',len(ids),'image-gap records')
