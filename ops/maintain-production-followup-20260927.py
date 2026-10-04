#!/usr/bin/env python3
"""Post-ingestion nonblocking VACUUM/ANALYZE for the indexed discovery tables."""
import importlib.util,json,time
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('audit-production-release.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
out=r.ROOT/'docs/research/production-followup-20260927'
tables=['artworks','media_assets','artwork_artists','artwork_location_assertions','artist_countries','curated_collection_items']
query="""SELECT c.relname,c.relpages,c.relallvisible,s.n_live_tup,s.n_dead_tup,s.last_vacuum,s.last_autovacuum,s.last_analyze FROM pg_class c JOIN pg_stat_user_tables s ON s.relid=c.oid WHERE c.relname=ANY(%s) ORDER BY c.relname"""
results={}
for target in ['cloud','local']:
 with r.connect(target,readonly=False) as db:
  db.autocommit=True
  before=db.execute(query,(tables,)).fetchall();print(target,'before',json.dumps(before,default=str),flush=True)
  results[target]={'before':before,'maintenance':[]}
  for t in tables:
   start=time.monotonic();db.execute(sql.SQL('VACUUM (ANALYZE) {}').format(sql.Identifier(t)));duration=time.monotonic()-start
   results[target]['maintenance'].append({'table':t,'seconds':duration});print(target,'VACUUM ANALYZE',t,round(duration,2),flush=True)
   (out/'maintenance.json').write_text(json.dumps(results,indent=2,default=str))
  results[target]['after']=db.execute(query,(tables,)).fetchall()
  (out/'maintenance.json').write_text(json.dumps(results,indent=2,default=str))
