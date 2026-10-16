#!/usr/bin/env python3
"""Verify scoped production recovery before the bounded MoMA supplement."""
import importlib.util, os, subprocess, fcntl
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-moma-batch-000091.py'))
b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
 assert h.load(b.E/'independent-source-verification.json')['plan_sha256']==pin
 if (b.E/'local-recovery-verification.json').exists():
  for f in h.load(b.E/'local-recovery-verification.json')['files']:
   assert h.sha(Path(f['path']).read_bytes())==f['sha256']
  print('Existing recovery verified');raise SystemExit(0)
 b.save('production-target-before-scoped-recovery.json',b.base.target())
 backup=h.BACKUP;backup.mkdir(parents=True,exist_ok=True);backup.chmod(0o700)
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
 kw=h.psycopg.conninfo.conninfo_to_dict(secret);env=os.environ.copy()
 env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
 path=backup/'production-schema-before.pgdump'
 r=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180)
 assert r.returncode==0,'Production schema export failed';path.chmod(0o600)
 r=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True)
 toc=backup/'production-schema-before.toc';toc.write_bytes(r.stdout);toc.chmod(0o600)
 with open(os.devnull,'wb') as sink:
  subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  before=h.snapshot(db,ids);assert before=={}
  for row in p['records']:
   assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND ((scheme LIKE '%%moma%%' AND external_id=%s) OR canonical_url=%s)",(row['source_id'],row['source_url'])).fetchall()
   assert not db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(row['institution_id'],row['accession_number'])).fetchall()
  artists={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(list(p['artists']),))}
  assert artists==p['artists']
  institution=[x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.mo.MID,))]
  sources=[x['v'] for x in db.execute('SELECT to_jsonb(s) v FROM sources s WHERE id=%s',(h.uid('source/moma/Museum of Modern Art'),))];assert not sources
  h.save(backup/'affected-row-recovery-before.json.gz',dict(at=h.now(),plan_sha256=pin,planned_artwork_ids=ids,artworks=before,artists=artists,institutions=institution,sources=sources))
 files=[path,toc,backup/'affected-row-recovery-before.json.gz',backup/b.PHASE/'plan-preimages.json.gz']
 for f in files:
  if f.suffix=='.gz':h.load(f)
 v=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',files=[dict(path=str(f),bytes=f.stat().st_size,sha256=h.sha(f.read_bytes())) for f in files],plan_sha256=pin,planned_artworks=len(ids),artwork_preimages=0,linked_artists=len(artists),schema_archive_fully_decoded=True,all_json_exports_fully_decoded=True,local_catalogue_connections=0,cloud_backups_created=0,full_database_backup=False,additional_locked_preimages_required=True,recovery='Reconcile locked-before and exact source/plan checksums with insertion audits before corrective action. Preserve unrelated records; no recovery mutations executed.')
 b.save('local-recovery-verification.json',v);h.save(backup/'local-recovery-verification.json',v)
 print('Scoped recovery verified for',len(ids),'new works')
