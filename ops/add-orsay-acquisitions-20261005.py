#!/usr/bin/env python3
"""Retain two verified Orsay acquisitions as review records, without images."""
import argparse,hashlib,importlib.util,uuid
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit-museum-gaps-20261005.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);r=a.r
RUN=r.RUN/'orsay-acquisitions';BACKUP=Path.home()/'Library/Application Support/Artline/backups/orsay-acquisitions-20261005';OP='orsay-acquisitions-20261005';EDITOR='local-european-research'
def uid(k):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+k))
def insert(db,table,row):db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,row)),sql.SQL(',').join(sql.Placeholder()for _ in row)),tuple(row.values()))
def duplicate(db,w,artist,institution):
 urls=[w['source_url'],w['object_url']]
 assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork'AND(canonical_url=ANY(%s)OR(scheme='orsay-object'AND external_id=%s))",(urls,w['object_id'])).fetchone()
 assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork'AND source_url=ANY(%s)",(urls,)).fetchone()
 assert not db.execute('SELECT 1 FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND (lower(a.title)=lower(%s)OR lower(a.alternate_title)=lower(%s))',(artist,w['title'],w['title'])).fetchone()
 if w['accession']:assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(institution,w['accession'])).fetchone()
def plan():
 facts=r.load(r.RUN/'orsay-selected-acquisition-facts.json');targets={}
 for target in ['local','production']:
  with r.connect(target)as db:
   institution=db.execute("SELECT to_jsonb(i)row FROM institutions i WHERE slug='musee-orsay'").fetchone()['row'];artists={}
   for w in facts['records']:
    ar=db.execute('SELECT to_jsonb(a)row FROM artists a WHERE slug=%s',(w['artist_slug'],)).fetchone()['row'];assert ar['status']!='archived';artists[w['artist_slug']]=ar;duplicate(db,w,ar['id'],institution['id'])
   targets[target]=dict(institution=institution,artists=artists)
 r.save_gz(RUN/'plan.json.gz',dict(facts=facts,targets=targets));print('Two acquisitions selected; existing authorities; review only')
def apply(target):
 path=RUN/'plan.json.gz';p=r.load(path);old=p['targets'][target];works=p['facts']['records'];digest=hashlib.sha256(path.read_bytes()).hexdigest();ids=[uid('work/'+w['object_id'])for w in works];sid=uid('source')
 with r.connect(target,readonly=False)as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='3s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  if db.execute('SELECT count(*)n FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==len(ids):print(target,'already added');return
  for w in works:
   ar=old['artists'][w['artist_slug']];assert db.execute('SELECT to_jsonb(a)row FROM artists a WHERE id=%s FOR SHARE',(ar['id'],)).fetchone()['row']==ar;duplicate(db,w,ar['id'],old['institution']['id'])
  r.save_gz(BACKUP/(target+'-before.json.gz'),dict(plan_sha256=digest,**old,new_artwork_ids=ids))
  insert(db,'sources',dict(id=sid,slug=OP,name='Musée d’Orsay: selected acquisition notices, 5 October 2026',source_type='collection_page',base_url='https://www.musee-orsay.fr/'))
  for w,aid in zip(works,ids):
   insert(db,'artworks',dict(id=aid,slug='orsay-selected-'+w['object_id'],title=w['title'],normalized_title=r.norm(w['title']),creation_year_start=w['start'],creation_year_end=w['end'],date_precision=w['precision'],date_display=w['date_display'],work_type=w['work_type'],medium_text=w['medium'],accession_number=w['accession'],status='review',research_candidate=True,created_by=EDITOR,updated_by=EDITOR))
   insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=old['artists'][w['artist_slug']]['id'],attribution_role='primary',attribution_note='Named by the official museum acquisition/object notice.'))
   insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme='orsay-object',external_id=w['object_id'],canonical_url=w['object_url'],source_id=sid,retrieved_at=p['facts']['reviewed_at']))
   insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='museum_source_metadata',source_id=sid,source_record_id=w['object_id'],source_url=w['source_url'],evidence_note=w['note']+' Plan SHA-256 '+digest+'.',retrieved_at=p['facts']['reviewed_at'],created_by=EDITOR))
   insert(db,'artwork_location_assertions',dict(id=uid('holding/'+w['object_id']),artwork_id=aid,claim_type='holding',institution_id=old['institution']['id'],context='collection',source_id=sid,source_url=w['source_url'],evidence_note='Official Musée d’Orsay acquisition/object notice confirms collection membership. No assertion of current display.',checked_at=p['facts']['reviewed_at'],review_state='accepted'))
  rows=[x['row']for x in db.execute('SELECT to_jsonb(a)row FROM artworks a WHERE id=ANY(%s::uuid[])ORDER BY id',(ids,)).fetchall()];assert len(rows)==2 and all(x['status']=='review'and x['primary_media_id']is None and x['current_institution_id']==old['institution']['id']for x in rows)
 r.save_gz(BACKUP/(target+'-after.json.gz'),dict(plan_sha256=digest,artworks=rows));print(target,'added two Orsay acquisition records in review')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['plan','apply']);p.add_argument('--target',choices=['local','production']);args=p.parse_args()
 if args.command=='plan':plan()
 else:assert args.target;apply(args.target)
