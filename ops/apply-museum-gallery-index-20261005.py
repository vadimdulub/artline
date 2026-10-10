#!/usr/bin/env python3
"""Build the museum gallery index concurrently; preserve data and index evidence."""
import importlib.util,hashlib
from pathlib import Path
s=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit-museum-gaps-20261005.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);r=a.r
path=r.ROOT/'apps/server/db/migrations/0034_museum_gallery_covering_index.sql'
statement=path.read_text().split('CREATE INDEX',1)[1]
backup=Path.home()/'Library/Application Support/Artline/backups/museum-gallery-index-20261005'
for target in ['local','production']:
 with r.connect(target,readonly=False)as db:
  db.execute("SET lock_timeout='3s'");db.execute('SELECT pg_advisory_lock(20250907001)')
  try:
   if db.execute('SELECT 1 FROM schema_migrations WHERE filename=%s',(path.name,)).fetchone():print(target,'already indexed');continue
   before=db.execute("SELECT indexname,indexdef FROM pg_indexes WHERE tablename='artworks' ORDER BY indexname").fetchall()
   assert not any(x['indexname']=='artworks_museum_gallery_covering_idx'for x in before),'Existing unrecorded index needs validation'
   r.save_gz(backup/(target+'-before.json.gz'),before)
   db.execute('CREATE INDEX CONCURRENTLY'+statement)
   row=db.execute("SELECT i.indisvalid,i.indisready,pg_get_indexdef(i.indexrelid)definition,pg_relation_size(i.indexrelid)bytes FROM pg_index i WHERE i.indexrelid='artworks_museum_gallery_covering_idx'::regclass").fetchone()
   assert row['indisvalid']and row['indisready']
   db.execute('INSERT INTO schema_migrations(filename)VALUES(%s)',(path.name,))
   r.save(backup/(target+'-after.json'),{'migration':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**row})
   print(target,'index ready',row['bytes'],'bytes',flush=True)
  finally:db.execute('SELECT pg_advisory_unlock(20250907001)')
