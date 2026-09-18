#!/usr/bin/env python3
"""Correct two conventional master identities; preserve every artwork and date."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;RUN=m.x.BASE/'creator-quality-followup/anonymous-masters';SOURCE='overnight-anonymous-master-review-20260913'
CASES={'wikimedia-painter-q1246986':('altenberg-museum','https://stories.staedelmuseum.de/de/altenberger-madonna-erwerbung','Conventional identity for the unnamed Rhenish maker associated with the Altenberg altarpiece. The museum describes a Rhenish master, circa 1330; this is an anonymous master, not a documented personal name.'),'wikimedia-painter-q1364366':('sierentz-museum','https://kunstmuseumbasel.ch/de/ausstellungen/2025/verso','Conventional identity Master of Sierentz, associated with the surviving Saint George/Lamentation altarpiece wing. This is an anonymous master, not a documented personal name.')}
def run(target,apply=False):
 dest=RUN/(target+'-classification-verified.json')
 if dest.exists():return
 evidence={}
 for slug,(stem,url,note) in CASES.items():
  p=RUN/(stem+'.html');evidence[slug]=dict(url=url,capture_path=str(p),sha256=CORE.sha(p.read_bytes()),review=note)
 with m.m.r.base.connect(target=='production') as db:
  with db.transaction():
   db.execute('SET TRANSACTION READ ONLY');rows={r['row']['slug']:r['row'] for r in db.execute('SELECT to_jsonb(a) row FROM artists a WHERE slug=ANY(%s)',(list(CASES),))};assert rows.keys()==CASES.keys()
   for row in rows.values():assert row['status']=='review' and row['published_at'] is None and row['entity_type']=='person' and row['birth_year'] is None and row['death_year'] is None
   ids=[r['id'] for r in rows.values()];links=db.execute('SELECT to_jsonb(aa) row FROM artwork_artists aa WHERE artist_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id,attribution_role',(ids,)).fetchall();countries=db.execute('SELECT to_jsonb(c) row FROM artist_countries c WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,country_code,relationship_type',(ids,)).fetchall()
  backup=m.BACKUPS/'anonymous-master-classification'/(target+'-preimages.json')
  data=dict(at=CORE.now(),artists=rows,artwork_artists=links,countries=countries,evidence=evidence)
  if backup.exists():assert json.loads(backup.read_text())['artists']==rows
  else:CORE.save_new(backup,data)
  if not apply:print(target,'classification plan ready',len(rows));return
  pin=CORE.sha(backup.read_bytes())
  with db.transaction():
   db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'Museum review of conventional anonymous-master identities','collection_page','https://www.staedelmuseum.de/')
   for slug,old in rows.items():
    current=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=%s FOR UPDATE',(old['id'],)).fetchone()['row'];assert current==old
    db.execute("UPDATE artists SET entity_type='anonymous_master',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.m.ACTOR,old['id']))
    m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=old['id'],source_id=sid,field_name='identity',source_url=evidence[slug]['url'],retrieved_at=data['at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(preimage_sha256=pin,evidence=evidence[slug],classification_only=True,publication_status='review'),ensure_ascii=False)))
  with db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   for slug,old in rows.items():
    actual=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=%s',(old['id'],)).fetchone()['row'];ignore={'revision','updated_at','updated_by'};expected={**old,'entity_type':'anonymous_master'};assert {k:v for k,v in actual.items() if k not in ignore}=={k:v for k,v in expected.items() if k not in ignore}
   assert links==db.execute('SELECT to_jsonb(aa) row FROM artwork_artists aa WHERE artist_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id,attribution_role',(ids,)).fetchall()
   assert countries==db.execute('SELECT to_jsonb(c) row FROM artist_countries c WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,country_code,relationship_type',(ids,)).fetchall()
 CORE.save_new(dest,dict(at=CORE.now(),target=target,corrected=len(rows),preimage_sha256=pin,artwork_links_unchanged=True,countries_unchanged=True,dates_unchanged=True,status='review'));print(target,'two anonymous masters corrected and verified',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--target',choices=['local','production'],required=True);p.add_argument('--apply',action='store_true');a=p.parse_args();run(a.target,a.apply)
