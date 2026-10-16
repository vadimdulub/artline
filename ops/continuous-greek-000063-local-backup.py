import importlib.util,subprocess,os,json,hashlib
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000063.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
assert not (b.E/'full-export-interruption.json').exists(),'Full export strategy superseded: use continuous-greek-000063-recovery.py'
b.save('production-target-before-local-export.json',b.target())
p=b.h.BACKUP/'production-before.pgdump';p.parent.mkdir(parents=True,exist_ok=True);p.parent.chmod(0o700)
secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
kw=b.h.psycopg.conninfo.conninfo_to_dict(secret);env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
assert not p.exists()
part=p.with_suffix('.part')
r=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--format=custom','--compress=3','--no-owner','--no-acl','--file',str(part)],env=env,capture_output=True,timeout=1200)
assert r.returncode==0,'Production read-only export failed: '+r.stderr.decode()[:500]
part.chmod(0o600);part.rename(p)
r=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(p)],capture_output=True,check=True);toc=p.with_suffix('.toc');toc.write_bytes(r.stdout);toc.chmod(0o600)
# Full archive decode, without a database restore or local catalogue connection.
with open(os.devnull,'wb') as sink: subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(p)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=600)
digest=hashlib.sha256()
with p.open('rb') as f:
 for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
v=dict(at=b.h.now(),status='VERIFIED',kind='local_full_production_pg_dump',path=str(p),sha256=digest.hexdigest(),bytes=p.stat().st_size,toc_path=str(toc),toc_sha256=b.h.sha(r.stdout),archive_fully_decoded_without_restore=True,production_target='artline-508319:europe-west1:artline-postgres',local_catalogue_connections=0,cloud_backups_created=0)
b.save('local-recovery-verification.json',v);b.h.save(b.h.BACKUP/'local-recovery-verification.json',v);print(json.dumps(v))
