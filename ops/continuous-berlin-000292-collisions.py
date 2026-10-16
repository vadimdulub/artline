import importlib.util,json
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000292.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
initial=h.load(b.E/'global-identity-initial.json');ids=list({x['id'] for r in initial['records'] for x in r['title_collisions']+r['accession_collisions']})
with h.connect() as db:
 rows=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.date_display,a.dimensions_text,a.medium_text,a.current_institution_id::text,a.primary_media_id::text,m.storage_path,ar.display_name creator FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id LEFT JOIN artwork_artists aa ON aa.artwork_id=a.id LEFT JOIN artists ar ON ar.id=aa.artist_id WHERE a.id=ANY(%s::uuid[])",(ids,))]
 b.save('collision-catalogue-context.json',dict(at=h.now(),rows=rows))
 for x in rows:print(json.dumps(x,ensure_ascii=False))
