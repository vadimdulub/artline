#!/usr/bin/env python3
"""Verified local schema export and exact affected-row preimages, production read only."""
import importlib.util,subprocess,os
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-shuzo-000076.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
assert not (b.E/'local-recovery-verification.json').exists()
b.save('production-target-before-scoped-recovery.json',b.target());backup=h.BACKUP;backup.chmod(0o700)
secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip();kw=h.psycopg.conninfo.conninfo_to_dict(secret)
env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
path=backup/'production-schema-before.pgdump'
r=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180);assert r.returncode==0,'Schema export failed';path.chmod(0o600)
r=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True);toc=backup/'production-schema-before.toc';toc.write_bytes(r.stdout);toc.chmod(0o600)
with open(os.devnull,'wb') as sink:subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');before=h.snapshot(db,ids);assert before=={}
 arts=db.execute('SELECT to_jsonb(t) v FROM artists t WHERE id=%s',(b.NEW_ARTIST,)).fetchall();institutions=db.execute('SELECT to_jsonb(t) v FROM institutions t WHERE id=%s',(b.MID,)).fetchall();source=db.execute('SELECT to_jsonb(t) v FROM sources t WHERE id=%s',(h.uid('source/aichi/'+b.MUSEUM),)).fetchall();assert not arts and not institutions and not source
 out=dict(at=h.now(),scope='Only six new artworks, one new artist, one new institution and one new source; not a full catalogue export',plan_sha256=pin,artwork_preimages=before,new_artist_preimages=arts,new_institution_preimages=institutions,new_source_preimages=source,planned_ids=ids)
 h.save(backup/'affected-row-recovery-before.json.gz',out)
files=[path,toc,backup/'affected-row-recovery-before.json.gz',backup/b.PHASE/'plan-preimages.json.gz'];manifest=[]
for f in files:
 if f.suffix=='.gz':h.load(f)
 manifest.append(b.b.ref(f))
v=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',path=str(backup),files=manifest,plan_sha256=pin,planned_artworks=6,new_artists=1,new_institutions=1,schema_archive_fully_decoded=True,all_json_exports_fully_decoded=True,local_catalogue_connections=0,cloud_backups_created=0,full_database_backup=False,additional_locked_preimages_required=True,recovery='Before any corrective action reconcile immutable batch plan and image rights pins with insert audit IDs. Locked metadata and image preimages govern only these entities. No recovery/deletion mutations executed; preserve unrelated records and historical statuses.')
b.save('local-recovery-verification.json',v);h.save(backup/'local-recovery-verification.json',v);print('Scoped local recovery verified',len(files),'files')
