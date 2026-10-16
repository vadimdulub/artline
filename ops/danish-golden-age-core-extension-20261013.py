#!/usr/bin/env python3
"""Add two exact existing academy authorities omitted from the first closed roster."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/danish-golden-age-20261013'
s=importlib.util.spec_from_file_location('d',ROOT/'ops/danish-golden-age-20261013.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
PEOPLE={'696_person':'primary','693_person':'primary'}
def main():
 assert json.loads((RUN/'cloud-backup.json').read_text())['status']=='SUCCESSFUL'
 with d.c.connect() as db:
  before=[dict(x) for x in db.execute("""SELECT e.external_id,a.id::text,a.slug,a.display_name,a.status,count(DISTINCT aa.artwork_id) works,
   EXISTS(SELECT 1 FROM artist_movements am WHERE am.artist_id=a.id AND am.movement_id=%s) linked
   FROM external_identifiers e JOIN artists a ON a.id=e.entity_id LEFT JOIN artwork_artists aa ON aa.artist_id=a.id
   WHERE e.entity_type='artist' AND e.scheme='smk-person' AND e.external_id=ANY(%s) GROUP BY e.external_id,a.id ORDER BY e.external_id""",(d.MOVEMENT,list(PEOPLE)))]
 assert len(before)==2 and not any(x['linked'] for x in before)
 d.save(RUN/'core-extension-before.json',before)
 with d.c.connect(True) as db,db.transaction():
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(d.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  for x in before:
   current=db.execute('SELECT id::text,display_name,status FROM artists WHERE id=%s FOR SHARE',(x['id'],)).fetchone();assert current['display_name']==x['display_name'] and current['status']!='archived'
   db.execute("INSERT INTO artist_movements(artist_id,movement_id,role) VALUES(%s,%s,'primary')",(x['id'],d.MOVEMENT))
   note={'smk_person_id':x['external_id'],'display_name':x['display_name'],'classification':'core','interpretation':'Academy professor/precursor explicitly named by the Hirschsprung Collection Golden Age account; exact existing SMK authority. Association does not classify every work by date.'}
   db.execute("""INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
    VALUES(%s,'artist',%s,%s,'danish_golden_age_association',%s,%s,%s,now(),%s)""",(d.uid('core-extension/'+x['external_id']),x['id'],d.source_id('hirschsprung'),x['external_id'],d.SOURCES['hirschsprung'][3],json.dumps(note,ensure_ascii=False),d.ACTOR))
 with d.c.connect() as db:
  after=[dict(x) for x in db.execute("SELECT a.id::text,a.slug,a.display_name,am.role,(SELECT count(*) FROM artwork_artists aa WHERE aa.artist_id=a.id) works FROM artist_movements am JOIN artists a ON a.id=am.artist_id WHERE am.movement_id=%s ORDER BY a.display_name",(d.MOVEMENT,))]
 assert len(after)==34;d.save(RUN/'core-extension-applied.json',{'artists':after,'works':sum(x['works'] for x in after)});print(len(after),sum(x['works'] for x in after))
if __name__=='__main__':main()
