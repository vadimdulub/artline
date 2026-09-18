#!/usr/bin/env python3
"""Preserve museum-rejected attributions as historical links, in both DBs."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('research-country-primary.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
m=p.m;RUN=m.x.BASE/'attribution-followup';QIDS=['Q26997957','Q27000045']
def main():
 evidence={q:json.loads((RUN/(q+'.json')).read_text()) for q in QIDS}
 for q,e in evidence.items():
  assert any('rejected attribution' in str(n) for n in p.values(e['official']['produced_by'],'content'))
 snapshots={}
 for target in ['local','production']:
  dest=m.BACKUPS/('rejected-attributions-'+target+'-preimages.json')
  if dest.exists():snapshots[target]=json.loads(dest.read_text());continue
  rows={}
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   for q in QIDS:
    row=db.execute("SELECT to_jsonb(a) work,to_jsonb(ma) media FROM artworks a LEFT JOIN media_assets ma ON ma.id=a.primary_media_id WHERE a.slug=%s",('wikimedia-artwork-'+q.lower(),)).fetchone();assert row['work']['status']=='review'
    row['links']=db.execute('SELECT to_jsonb(aa) link FROM artwork_artists aa WHERE artwork_id=%s',(row['work']['id'],)).fetchall();assert len(row['links'])==1 and row['links'][0]['link']['attribution_role']=='primary';rows[q]=row
  m.m.core.save_new(dest,rows);snapshots[target]=rows
 for target in ['local','production']:
  dest=RUN/('rejected-attributions-'+target+'.json')
  if dest.exists():continue
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SELECT pg_advisory_xact_lock(559220260914)')
   sid=m.m.source(db,'overnight-rijksmuseum-primary-20260913','Rijksmuseum official object and creator authority cross-checks','museum_api','https://data.rijksmuseum.nl/')
   for q in QIDS:
    old=snapshots[target][q];e=evidence[q];aid=old['work']['id'];artist=old['links'][0]['link']['artist_id']
    now=db.execute('SELECT to_jsonb(a) work FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['work'];assert now==old['work']
    note='Rijksmuseum explicitly marks the Isaac Walraven attribution as rejected. The historical association is retained; a current named creator is not asserted. Official object: '+e['official']['id']
    assert db.execute("UPDATE artwork_artists SET attribution_role='formerly_attributed_to',attribution_note=%s WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'",(note,aid,artist)).rowcount==1
    db.execute("UPDATE artworks SET unlinked_creator_label='Unidentified painter (formerly attributed to Isaac Walraven)',description_md=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(old['work']['title']+'. '+note+' Metadata remains in review.',m.m.ACTOR,aid))
    if old['media']:db.execute('UPDATE media_assets SET alt_text=%s WHERE id=%s',(old['work']['title']+' — formerly attributed to Isaac Walraven',old['media']['id']))
    m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='attribution_review',source_record_id=e['official']['id'].rsplit('/',1)[-1],source_url=e['official']['id'],retrieved_at=e['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps({'decision':'formerly_attributed_to','current_creator':'unknown','official_source_receipt':e['receipt'],'source_production_evidence':e['official']['produced_by'],'previous_wikidata_attribution_preserved_as_historical':True},ensure_ascii=False)))
  checked=[]
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   for q in QIDS:
    old=snapshots[target][q];aid=old['work']['id'];now=db.execute('SELECT to_jsonb(a) work FROM artworks a WHERE id=%s',(aid,)).fetchone()['work'];ignored={'unlinked_creator_label','description_md','revision','updated_at','updated_by'}
    assert {k:v for k,v in now.items() if k not in ignored}=={k:v for k,v in old['work'].items() if k not in ignored}
    links=db.execute('SELECT attribution_role FROM artwork_artists WHERE artwork_id=%s',(aid,)).fetchall();assert links==[{'attribution_role':'formerly_attributed_to'}];checked.append({'qid':q,'artwork_id':aid,'status':'review','attribution':'formerly_attributed_to','image_preserved':now['primary_media_id']==old['work']['primary_media_id']})
  m.m.core.save_new(dest,{'at':m.m.core.now(),'verified':checked});print(target,'corrected and verified rejected attributions',len(checked),flush=True)
if __name__=='__main__':main()
