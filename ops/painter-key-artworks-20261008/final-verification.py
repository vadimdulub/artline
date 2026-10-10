import importlib.util,collections,json,hashlib,concurrent.futures,requests,time
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
for target in ['local','production']:
 with m.base.connect(target) as db:
  totals=db.execute('''SELECT count(*) active_painters,count(k.artist_id) saved_choices,
    count(k.artist_id) FILTER(WHERE w.status<>'archived' AND artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision)='eligible') eligible_choices,
    count(k.artist_id) FILTER(WHERE ma.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\\.(jpg|jpeg|png|webp|avif)$') illustrated_choices,
    count(*) FILTER(WHERE k.artist_id IS NULL) unresolved_painters
    FROM artists a LEFT JOIN artist_key_artworks k ON k.artist_id=a.id LEFT JOIN artworks w ON w.id=k.artwork_id
    LEFT JOIN media_assets ma ON ma.id=w.primary_media_id WHERE a.status<>'archived' ''').fetchone()
  missing=db.execute('''SELECT a.id,a.slug,a.display_name,
    CASE WHEN EXISTS(SELECT 1 FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=a.id AND w.status<>'archived')
      THEN 'Existing works require date/identity review or eligible key-work research'
      ELSE 'No verified linked artwork yet' END reason
    FROM artists a LEFT JOIN artist_key_artworks k ON k.artist_id=a.id WHERE a.status<>'archived' AND k.artist_id IS NULL ORDER BY a.sort_name,a.id''').fetchall()
  m.save(target+'-final-unresolved-v4.json.gz',missing)
  basis=db.execute('SELECT selection_basis,count(*) FROM artist_key_artworks GROUP BY selection_basis').fetchall();totals['bases']=basis
  missingimages=db.execute('''SELECT a.slug,a.display_name,w.slug artwork_slug,w.title FROM artist_key_artworks k
    JOIN artists a ON a.id=k.artist_id JOIN artworks w ON w.id=k.artwork_id LEFT JOIN media_assets ma ON ma.id=w.primary_media_id
    WHERE ma.storage_path IS NULL ORDER BY a.sort_name''').fetchall();m.save(target+'-selected-without-images-v4.json.gz',missingimages)
  m.save(target+'-final-verification-v4.json',totals);print(target,totals,flush=True)
