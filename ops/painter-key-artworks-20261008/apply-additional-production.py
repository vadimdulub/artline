import importlib.util,collections
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=m.base.load(m.RUN/'additional-production-candidates.json.gz');artists={a['id']:a for a in m.base.load(m.RUN/'additional-production-artists.json.gz')};changes=[]
with m.base.connect('production',readonly=False) as db:
 db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
 before=db.execute('SELECT * FROM artist_key_artworks WHERE artist_id=ANY(%s::uuid[])',([r['artist_id'] for r in rows],)).fetchall();m.base.save(m.BACKUP/'production-additional-keys-before.json.gz',before)
 for r in rows:
  a=artists[r['artist_id']];evidence=dict(artist_slug=a['slug'],artist_name=a['display_name'],artwork_slug=r['slug'],artwork_title=r['title'],recorded_date=r['date_display'],creation_scope='eligible',image_available=bool(r['storage_path']),publication_preserved=r['status'],selection_policy='Source-backed representative opening work; scoped production gap pass, preserving existing saved choices',operation='painter-key-artworks-20261008-additional')
  result=db.execute('''INSERT INTO artist_key_artworks(artist_id,artwork_id,attribution_role,selection_basis,source_urls,evidence_json,selection_batch)
   SELECT %s,w.id,%s,%s,%s,%s,'painter-key-artworks-20261008-additional' FROM artworks w JOIN artists a ON a.id=%s
   JOIN artwork_artists aa ON aa.artwork_id=w.id AND aa.artist_id=a.id AND aa.attribution_role=%s
   WHERE w.id=%s AND w.status<>'archived' AND a.status<>'archived' AND artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision)='eligible'
   ON CONFLICT(artist_id) DO NOTHING RETURNING artist_id''',(r['artist_id'],r['attribution_role'],'curated_representative' if r['representative_order'] else 'editorial_representative',r['sources'],Jsonb(evidence),r['artist_id'],r['attribution_role'],r['id'])).fetchone()
  if result:changes.append(str(result['artist_id']))
 after=db.execute('SELECT * FROM artist_key_artworks WHERE artist_id=ANY(%s::uuid[])',([r['artist_id'] for r in rows],)).fetchall();m.base.save(m.BACKUP/'production-additional-keys-after.json.gz',after)
m.save('production-additional-receipt.json',dict(count=len(changes),artist_ids=changes,publication_changes=0));print('Additional production choices applied',len(changes))
