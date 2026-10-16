from pathlib import Path
import sys,json,collections
import exhibitions_common as c
from psycopg import sql
OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012'
TABLES=['artist_key_artworks','exhibition_entries','curated_collection_items','artwork_location_assertions','research_artwork_enrichments','research_artwork_links','research_resolutions','artwork_artists','artwork_media','artwork_places','member_artwork_bookmarks','artwork_search_documents']

def plan():
 selected=c.load(OUT/'selected-main-removal-review.json')['selected'];ids=[r['id']for r in selected]
 with c.connect()as db:
  rows=db.execute('SELECT id,title,work_type,created_at,revision,current_institution_id,primary_media_id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall();assert len(rows)==546
  counts={}
  for table in TABLES:
   column='id'if table=='artwork_search_documents'else'artwork_id'
   counts[table]=db.execute(sql.SQL('SELECT count(*) n FROM {} WHERE {}=ANY(%s::uuid[])').format(sql.Identifier(table),sql.Identifier(column)),(ids,)).fetchone()['n']
  artists=db.execute("""SELECT a.id,a.display_name,a.birth_year,a.created_at FROM artists a WHERE a.created_at>='2026-10-10' AND a.birth_year>=1750 AND EXISTS(SELECT 1 FROM artwork_artists x WHERE x.artist_id=a.id AND x.artwork_id=ANY(%s::uuid[])) AND NOT EXISTS(SELECT 1 FROM artwork_artists x WHERE x.artist_id=a.id AND NOT(x.artwork_id=ANY(%s::uuid[]))) ORDER BY a.id""",(ids,ids)).fetchall()
  protected=[dict(t=db.execute('SELECT count(*) n FROM '+t).fetchone()['n'],table=t)for t in ['artists','artworks','institutions']]
  sources=db.execute("SELECT entity_id,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme,external_id",(ids,)).fetchall()
 c.save(OUT/'main-removal-plan.json',dict(at=c.now(),rule=c.load(OUT/'selected-main-removal-review.json')['rule'],artworks=rows,sourceIdentities=sources,dependentCounts=counts,newlyOrphanedModernArtists=artists,beforeCounts=protected))
 print(json.dumps(dict(artworks=len(rows),types=dict(collections.Counter(r['work_type']for r in rows)),dependentCounts=counts,newlyOrphanedModernArtists=artists),default=str,indent=2),flush=True)

def apply():
 p=c.load(OUT/'main-removal-plan.json');ids=[r['id']for r in p['artworks']]
 with c.connect(write=True)as db:
  db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  now=db.execute('SELECT id,title,work_type,created_at,revision,current_institution_id,primary_media_id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall();assert json.loads(json.dumps(now,default=str))==p['artworks'],'Selected works changed during preparation'
  counts={}
  for table in TABLES:
   column='id'if table=='artwork_search_documents'else'artwork_id'
   counts[table]=db.execute(sql.SQL('DELETE FROM {} WHERE {}=ANY(%s::uuid[])').format(sql.Identifier(table),sql.Identifier(column)),(ids,)).rowcount
   assert counts[table]==p['dependentCounts'][table],table
  for table in ['external_identifiers','citations','slug_redirects']:
   counts[table]=db.execute(sql.SQL("DELETE FROM {} WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])").format(sql.Identifier(table)),(ids,)).rowcount
  counts['artworks']=db.execute('DELETE FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).rowcount;assert counts['artworks']==546
  # Audit triggers and catalogue invalidation remain enabled. Retain unrelated
  # artists and media until their complete ownership/references are reviewed.
  assert db.execute('SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==0
 c.save(OUT/'main-removal-delivered.json',dict(at=c.now(),counts=counts,planSHA256=c.sha((OUT/'main-removal-plan.json').read_bytes()),realLocalDatabaseWrites=False));print(json.dumps(counts),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
