import importlib.util,collections,copy
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with m.base.connect('production') as db:
 artists=db.execute("SELECT a.id,a.slug,a.display_name,a.status FROM artists a WHERE a.status<>'archived' AND NOT EXISTS(SELECT 1 FROM artist_key_artworks k WHERE k.artist_id=a.id) ORDER BY a.id").fetchall();rows=[]
 for offset in range(0,len(artists),300):
  ids=[a['id'] for a in artists[offset:offset+300]]
  chosen=db.execute('''SELECT DISTINCT ON (aa.artist_id) aa.artist_id,aa.attribution_role,aa.representative_order,w.id,w.slug,w.title,w.date_display,w.creation_year_start,w.creation_year_end,w.date_precision,w.status,m.storage_path,m.source_page_url
   FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id JOIN artists a ON a.id=aa.artist_id LEFT JOIN media_assets m ON m.id=w.primary_media_id
   WHERE aa.artist_id=ANY(%s::uuid[]) AND aa.attribution_role<>'formerly_attributed_to' AND w.status<>'archived'
    AND artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision)='eligible'
   ORDER BY aa.artist_id,(a.status='published' AND w.status<>'published'),(m.storage_path IS NOT NULL) DESC,(aa.attribution_role='primary') DESC,aa.representative_order NULLS LAST,(w.work_type IN ('painting','fresco')) DESC,w.normalized_title,w.id''',(ids,)).fetchall()
  for w in chosen:
   sources=[r['url'] for r in db.execute("SELECT canonical_url url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND canonical_url IS NOT NULL UNION SELECT source_url FROM citations WHERE entity_type='artwork' AND entity_id=%s",(w['id'],w['id']))]
   if w['source_page_url']:sources.append(w['source_page_url'])
   if sources:w['sources']=sorted(set(sources));rows.append(w)
  db.commit()
  if offset%1500==0:print('Additional production artists checked',offset+len(ids),'supported choices',len(rows),flush=True)
 m.save('additional-production-artists.json.gz',artists);m.save('additional-production-candidates.json.gz',rows);print('Additional source-backed choices',len(rows),flush=True)
