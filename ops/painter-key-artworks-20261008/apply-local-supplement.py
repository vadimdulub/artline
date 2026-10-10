import importlib.util,collections,hashlib,json,uuid,shutil
from pathlib import Path
from psycopg import sql
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
pkg=m.base.load(m.RUN/'local-supplement-source.json.gz');rows=m.base.load(m.RUN/'local-supplement-plan.json.gz');assert all(r['new'] for r in rows);media={r['id']:r for r in pkg['media']};actor='local-european-research';counts=collections.Counter()
def insert(db,table,data):
 fields=list(data);db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,fields)),sql.SQL(',').join(sql.Placeholder() for _ in fields)),[data[k] for k in fields])
for r in rows:
 ma=media.get(r['source']['primary_media_id'])
 if not ma:continue
 src=Path('/tmp/artline-key-artwork-20261008/local-supplement-assets')/(ma['id']+'.jpg');data=src.read_bytes();assert hashlib.sha256(data).hexdigest()==ma['checksum_sha256'].strip();dest=Path.cwd()/'apps/web/public'/ma['storage_path'].lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert dest.read_bytes()==data
 else:dest.write_bytes(data)
with m.base.connect('local',readonly=False) as db:
 db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
 ids=[r['source']['id'] for r in rows];assert not db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s)',(ids,[r['source']['slug'] for r in rows])).fetchall()
 source_map={}
 for source in pkg['sources']:
  match=db.execute('SELECT id FROM sources WHERE slug=%s',(source['slug'],)).fetchone()
  if match:source_map[source['id']]=str(match['id'])
  else:insert(db,'sources',source);source_map[source['id']]=source['id'];counts['sources_added']+=1
 for r in rows:
  w=dict(r['source']);artist=r['artist'];assert not db.execute('SELECT 1 FROM artist_key_artworks WHERE artist_id=%s',(artist['id'],)).fetchone()
  ma=media.get(w['primary_media_id'])
  if ma and not db.execute('SELECT id FROM media_assets WHERE id=%s',(ma['id'],)).fetchone():
   ma=dict(ma);ma['verified_by']=actor;insert(db,'media_assets',ma);counts['media_added']+=1
  # This selected local copy carries source metadata, not an unreviewed local
  # holding/display assertion. Production's full source state remains captured.
  w.update(status='review',revision=1,created_by=actor,updated_by=actor,published_at=None,research_candidate=True,current_institution_id=None,current_location_text=None,location_checked_at=None)
  insert(db,'artworks',w);counts['new_review_artworks']+=1
  db.execute('INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES (%s,%s,%s,%s)',(w['id'],artist['id'],r['candidate']['attribution_role'],'Exact existing painter identity matched by Wikidata authority or canonical slug to the source-backed production catalogue; selected opening work.'))
  if ma:db.execute("INSERT INTO artwork_media(artwork_id,media_id,view_label) VALUES (%s,%s,'Selected reproduction')",(w['id'],ma['id']));counts['illustrated']+=1
  for source in [x for x in pkg['citations'] if x['entity_id']==w['id']]:
   c=dict(source);c['source_id']=source_map[c['source_id']];c['created_by']=actor;insert(db,'citations',c)
  for source in [x for x in pkg['identifiers'] if x['entity_id']==w['id']]:
   e=dict(source)
   if e['source_id']:e['source_id']=source_map[e['source_id']]
   insert(db,'external_identifiers',e)
  evidence=dict(operation='painter-key-artworks-20261008-local-supplement',artist_slug=artist['slug'],artist_name=artist['display_name'],artwork_slug=w['slug'],artwork_title=w['title'],recorded_date=w['date_display'],creation_scope='eligible',image_available=bool(ma),selection_policy='Source-backed representative; exact production catalogue object copied into local review',source_production_artist=r['candidate']['artist_id'],source_sha256=m.base.digest(m.RUN/'local-supplement-source.json.gz'),holding_not_reconciled=True,display_not_claimed=True)
  db.execute("INSERT INTO artist_key_artworks(artist_id,artwork_id,attribution_role,selection_basis,source_urls,evidence_json,selection_batch) VALUES (%s,%s,%s,'editorial_representative',%s,%s,'painter-key-artworks-20261008-local-supplement')",(artist['id'],w['id'],r['candidate']['attribution_role'],r['candidate']['sources'],Jsonb(evidence)))
 after=db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall();assert len(after)==len(rows) and all(r['status']=='review' for r in after);m.base.save(m.BACKUP/'local-supplement-after.json.gz',after)
m.save('local-supplement-receipt.json',dict(counts=dict(counts),publication_changes=0,plan_sha256=m.base.digest(m.RUN/'local-supplement-plan.json.gz'),images_visually_reviewed=True));print(dict(counts))
