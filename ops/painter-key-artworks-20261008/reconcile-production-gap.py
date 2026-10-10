import importlib.util,collections,json
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=m.base.load(m.RUN/'gap-final-plan-v2.json.gz');qids=[r['work_qid'] for r in rows]
with m.base.connect('production') as db:
 records=db.execute('''SELECT e.external_id,w.id,w.slug,w.title,w.creation_year_start,w.creation_year_end,w.date_precision,w.status,w.primary_media_id,w.unlinked_creator_label,
  ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=w.id AND aa.attribution_role='primary') creator_ids,
  ARRAY(SELECT a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=w.id) creator_names
  FROM external_identifiers e JOIN artworks w ON w.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme='wikidata' AND e.external_id=ANY(%s)''',(qids,)).fetchall()
 m.base.save(m.BACKUP/'production-gap-global-authorities.json.gz',records)
 by={r['external_id']:r for r in records}
 mismatches=[dict(q=r['work_qid'],artist=r['artist_name'],expected=r['targets']['production'],actual=by[r['work_qid']]) for r in rows if r['work_qid'] in by and str(by[r['work_qid']]['id'])!=r['targets']['production']['artwork_id']]
 m.save('production-gap-identity-conflicts.json.gz',mismatches);print('Global authority conflicts',len(mismatches));print(json.dumps(mismatches,default=str,ensure_ascii=False)[:16000])
