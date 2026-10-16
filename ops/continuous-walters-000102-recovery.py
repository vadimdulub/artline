#!/usr/bin/env python3
"""Bounded production recovery: full schema plus exact impacted-row snapshots."""
import importlib.util,subprocess,os,json,hashlib
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-walters-batch-000102.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
assert not (b.E/'local-recovery-verification.json').exists()
b.MID=h.load(b.E/'institution-before.json')['id']
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
b.save('production-target-before-scoped-recovery.json',b.target())
backup=h.BACKUP;backup.mkdir(parents=True,exist_ok=True);backup.chmod(0o700)
secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
kw=h.psycopg.conninfo.conninfo_to_dict(secret);env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
path=backup/'production-schema-before.pgdump'
r=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180);assert r.returncode==0,'Schema export failed'
path.chmod(0o600)
r=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True);toc=backup/'production-schema-before.toc';toc.write_bytes(r.stdout);toc.chmod(0o600)
with open(os.devnull,'wb') as sink:subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);before=h.snapshot(db,ids);assert before=={}
 artists=[r['v'] for r in db.execute('SELECT to_jsonb(t) v FROM artists t WHERE id=ANY(%s::uuid[])',(list(p['artists']),))]
 institution=[r['v'] for r in db.execute('SELECT to_jsonb(t) v FROM institutions t WHERE id=%s',(b.MID,))]
 source_ids=[h.uid('source/walters/'+b.MUSEUM)];sources=[r['v'] for r in db.execute('SELECT to_jsonb(t) v FROM sources t WHERE id=ANY(%s::uuid[])',(source_ids,))];assert not sources
 original=h.load(b.E/'preserved-existing-before.json.gz')['artworks'];existing_ids=list(original)
 preserved=h.snapshot(db,existing_ids);assert preserved==original
 out=dict(at=h.now(),scope='Exact planned objects, sources, institution, linked creator and existing creator works; not a full catalogue export.',plan_sha256=pin,planned_artwork_ids=ids,artworks=before,artists=artists,institutions=institution,sources=sources,preserved=preserved)
 h.save(backup/'affected-row-recovery-before.json.gz',out)
files=[path,toc,backup/'affected-row-recovery-before.json.gz',backup/b.PHASE/'plan-preimages.json.gz']
for f in files:
 if f.suffix=='.gz': h.load(f)
manifest=[dict(path=str(f),bytes=f.stat().st_size,sha256=h.sha(f.read_bytes())) for f in files]
v=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',path=str(backup),files=manifest,plan_sha256=pin,planned_artworks=len(ids),artwork_preimages=0,linked_artists=len(artists),preserved_existing_artworks=len(preserved),schema_archive_fully_decoded=True,all_json_exports_fully_decoded=True,local_catalogue_connections=0,cloud_backups_created=0,full_database_backup=False,additional_locked_preimages_required=True,recovery='Reconcile batch-specific plan/source/rights checksums and insert audit IDs before any corrective action; locked-before and image before-000 snapshots govern affected rows. Preserve unrelated records and audit history. No recovery mutations executed.')
b.save('local-recovery-verification.json',v);h.save(backup/'local-recovery-verification.json',v);print('Scoped production recovery verified',len(files),'files')
