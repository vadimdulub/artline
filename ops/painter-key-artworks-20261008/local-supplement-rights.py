import importlib.util
from pathlib import Path
from psycopg import sql
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
pkg=m.base.load(m.RUN/'local-supplement-source.json.gz');ids=[r['id'] for r in pkg['media']]
with m.base.connect('production') as db:
 rights=db.execute('SELECT * FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',(ids,)).fetchall();sources=db.execute('SELECT * FROM sources WHERE id=ANY(%s::uuid[])',([r['source_id'] for r in rights],)).fetchall();m.save('local-supplement-rights-source.json.gz',dict(rights=rights,sources=sources))
with m.base.connect('local',readonly=False) as db:
 source_map={}
 for source in sources:
  current=db.execute('SELECT id FROM sources WHERE slug=%s',(source['slug'],)).fetchone()
  if not current:
   fields=list(source);db.execute(sql.SQL('INSERT INTO sources ({}) VALUES ({})').format(sql.SQL(',').join(map(sql.Identifier,fields)),sql.SQL(',').join(sql.Placeholder() for _ in fields)),[source[k] for k in fields]);source_map[str(source['id'])]=source['id']
  else:source_map[str(source['id'])]=current['id']
 for row in rights:
  if db.execute('SELECT 1 FROM media_rights_evidence WHERE media_id=%s',(row['media_id'],)).fetchone():continue
  fields=list(row);row['source_id']=source_map[str(row['source_id'])];row['evidence_json']=Jsonb(row['evidence_json']);db.execute(sql.SQL('INSERT INTO media_rights_evidence ({}) VALUES ({})').format(sql.SQL(',').join(map(sql.Identifier,fields)),sql.SQL(',').join(sql.Placeholder() for _ in fields)),[row[k] for k in fields])
m.save('local-supplement-rights-receipt.json',dict(rights_records_preserved=len(rights)));print('Rights records preserved',len(rights))
