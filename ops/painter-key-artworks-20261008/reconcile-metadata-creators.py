import importlib.util, json, re, uuid
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OP='painter-key-artworks-20261008-metadata-creators'
assert not (m.RUN/'production-metadata-creator-receipt.json').exists()
local={r['work_qid']:r for r in m.base.load(m.RUN/'local-metadata-gap-plan.json.gz')}
conflicts=m.base.load(m.RUN/'production-metadata-gap-conflicts.json');assert len(conflicts)==2
norm=lambda s:re.sub(r'\W','',s.casefold())
with m.base.connect('production',readonly=False) as db:
 db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
 source=db.execute("SELECT id FROM sources WHERE slug='wikidata'").fetchone()['id'];actor='local-european-research'
 ids=[r['id'] for r in conflicts];before=db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
 m.base.save(m.BACKUP/'production-metadata-creators-before.json.gz',before)
 for c in conflicts:
  r=local[c['external_id']];aw=c['id'];row=next(x for x in before if str(x['id'])==aw)
  assert row['status']=='review' and row['primary_media_id'] is None
  assert row['creation_year_start']==r['year'] and row['creation_year_end'] in (None,r['year']) and row['date_precision']=='exact'
  assert norm(row['unlinked_creator_label'])==norm(r['artist_name'])
  assert not db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=%s',(aw,)).fetchone()
  assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(aw,r['work_qid'])).fetchone()
  artists=db.execute("SELECT a.id,a.display_name FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme='wikidata' AND e.external_id=%s AND a.status<>'archived'",(r['artist_qid'],)).fetchall();assert len(artists)==1
  artist=artists[0];assert norm(artist['display_name'])==norm(r['artist_name'])
  assert not db.execute('SELECT 1 FROM artist_key_artworks WHERE artist_id=%s',(artist['id'],)).fetchone()
  evidence=dict(operation=OP,artist_qid=r['artist_qid'],artwork_qid=r['work_qid'],original_creator_label=row['unlinked_creator_label'],source_revision=r['entity_revision'],source_url=r['source_url'],image_available=False,image_status='Source download unavailable',recorded_year=r['year'],creator_life_evidence=r['creator_life_evidence'],publication_preserved=True,display_not_claimed=True,selection_policy='Source-backed editorial representative; no museum-highlight designation claimed')
  db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES (%s,%s,'primary',%s)",(aw,artist['id'],'Exact original creator label and unqualified P170 statement verified against '+r['source_url']+' / '+r['artist_qid']+'; original label retained'))
  db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at,created_by) VALUES (%s,'artwork',%s,'key_artwork_creator',%s,%s,%s,now(),%s)",(str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+r['work_qid'])),aw,source,r['source_url'],json.dumps(evidence),actor))
  db.execute("INSERT INTO artist_key_artworks(artist_id,artwork_id,attribution_role,selection_basis,source_urls,evidence_json,selection_batch) VALUES (%s,%s,'primary','editorial_representative',%s,%s,%s)",(artist['id'],aw,[r['source_url']],Jsonb(evidence),OP))
 after=db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall();assert before==after
 m.base.save(m.BACKUP/'production-metadata-creators-after.json.gz',dict(artworks=after,links=db.execute('SELECT * FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id',(ids,)).fetchall(),keys=db.execute('SELECT * FROM artist_key_artworks WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id',(ids,)).fetchall()))
m.save('production-metadata-creator-receipt.json',dict(at=m.base.now(),creator_links=2,key_selections=2,new_artworks=0,existing_metadata_changes=0,image_changes=0,publication_changes=0));print('Two existing production objects reconciled; source labels, dates and review status preserved')
