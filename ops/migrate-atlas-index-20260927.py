#!/usr/bin/env python3
"""Install the atlas covering index without blocking catalogue reads."""
import importlib.util,json,hashlib,subprocess
from pathlib import Path
s=importlib.util.spec_from_file_location('release',Path(__file__).with_name('audit-production-release.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
RUN=r.ROOT/'docs/research/production-followup-20260927';NAME='0030_atlas_illustrated_native_index.sql';INDEX='artworks_atlas_illustrated_native_idx'
body=(r.ROOT/'apps/server/db/migrations'/NAME).read_text()
backup=json.loads(subprocess.check_output(['/Users/vadimdulub/Documents/google-cloud-sdk/bin/gcloud','sql','backups','describe','1790533520479','--instance=artline-postgres','--project=artline-508319','--format=json']))
assert backup['status']=='SUCCESSFUL'
assert (Path('/Users/vadimdulub/Library/Application Support/Artline/backups/production-followup-20260927')/'local-before.dump').stat().st_size>600000000
out={'at':r.core.now(),'backup_id':backup['id'],'migration_sha256':hashlib.sha256(body.encode()).hexdigest(),'targets':{}}
for target in ['local','cloud']:
 with r.connect(target,readonly=False) as db:
  db.autocommit=True;db.execute('SELECT pg_advisory_lock(20250907001)')
  try:
   db.execute("SET lock_timeout='5s'");db.execute("SET statement_timeout='10min'")
   existing=db.execute('SELECT indisvalid,pg_get_indexdef(indexrelid) FROM pg_index WHERE indexrelid=to_regclass(%s)',(INDEX,)).fetchone()
   if not existing:db.execute(body.replace('CREATE INDEX ','CREATE INDEX CONCURRENTLY ',1))
   row=db.execute('SELECT indisvalid,pg_get_indexdef(indexrelid),pg_relation_size(indexrelid) FROM pg_index WHERE indexrelid=to_regclass(%s)',(INDEX,)).fetchone();assert row and row[0]
   db.execute('INSERT INTO schema_migrations(filename) VALUES(%s) ON CONFLICT DO NOTHING',(NAME,))
   out['targets'][target]={'valid':row[0],'definition':row[1],'bytes':row[2]}
   print(target,'index valid',row[2],'bytes',flush=True)
  finally:db.execute('SELECT pg_advisory_unlock(20250907001)')
RUN.joinpath('atlas-index-delivery.json').write_text(json.dumps(out,indent=2)+'\n')
