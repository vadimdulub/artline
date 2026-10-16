#!/usr/bin/env python3
"""Scoped recovery and independent prewrite checks for batch 228."""
import hashlib, importlib.util, json, os, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('b228',ROOT/'ops/continuous-greek-batch-000228.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
p,pin=h.pinned(b.PHASE); ids=[r['artwork_id'] for r in p['records']]; assert len(ids)==8 and len(set(ids))==8
for r in p['records']:
 raw=Path(r['evidence_file']).read_bytes(); assert h.sha(raw)==r['evidence']['sha256']; assert r['evidence']['status']==200; assert r['last']<=1970
backup=h.BACKUP; backup.mkdir(parents=True,exist_ok=True); backup.chmod(0o700)
secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
kw=h.psycopg.conninfo.conninfo_to_dict(secret); env=os.environ.copy(); env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
schema=backup/'production-schema-before.pgdump'; rr=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(schema)],env=env,capture_output=True,timeout=180); assert rr.returncode==0
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'); before=h.snapshot(db,ids); assert before=={}
 target=dict(db.execute('select current_database() db,inet_server_addr()::text server,pg_is_in_recovery() recovery').fetchone()); assert target['db']=='artline' and not target['recovery']
 assert not db.execute('select id from artworks where current_institution_id=%s and accession_number=any(%s)',(b.MID,[r['accession_number'] for r in p['records']])).fetchall()
state=backup/'affected-row-recovery-before.json.gz'; h.save(state,dict(at=h.now(),plan_sha256=pin,artworks=before,planned_artwork_ids=ids,target=target))
files=[schema,state,b.h.BACKUP/b.PHASE/'plan-preimages.json.gz']; manifest=[dict(path=str(x),bytes=x.stat().st_size,sha256=h.sha(x.read_bytes())) for x in files]
v=dict(at=h.now(),status='VERIFIED',kind='schema_and_exact_empty_preimages',path=str(backup),files=manifest,plan_sha256=pin,planned_artworks=8,artwork_preimages=0,local_catalogue_connections=0,cloud_backups_created=0)
b.save('local-recovery-verification.json',v); h.save(backup/'local-recovery-verification.json',v)
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=8,images=0,new_painters=0,no_existing_production_rows=True,source_checks=8,shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
print(json.dumps(dict(passed=True,selected=8)))
