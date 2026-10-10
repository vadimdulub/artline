import importlib.util,collections,json,re
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
plans=m.base.load(m.RUN/'gap-reviewed-plan.json.gz')
for target in ['local','production']:
 with m.base.connect(target) as db:
  rows=[]
  for offset in range(0,len(plans),100):
   ids=[p['artist_id'] for p in plans[offset:offset+100]]
   rows+=db.execute('''SELECT w.id,w.slug,w.title,w.creation_year_start,w.creation_year_end,w.date_precision,w.status,w.primary_media_id,w.accession_number,w.current_institution_id,aa.artist_id,aa.attribution_role,
    e.external_id wikidata,i.external_id institution_wikidata
    FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id
    LEFT JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=w.id AND e.scheme='wikidata'
    LEFT JOIN external_identifiers i ON i.entity_type='institution' AND i.entity_id=w.current_institution_id AND i.scheme='wikidata'
    WHERE aa.artist_id=ANY(%s::uuid[]) AND w.status<>'archived' ''',(ids,)).fetchall()
   db.commit()
  m.base.save(m.BACKUP/(target+'-gap-artwork-identities.json.gz'),rows)
  print(target,'gap identity candidates',len(rows),flush=True)
