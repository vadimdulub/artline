#!/usr/bin/env python3
"""Country-level browsing links for source-backed, nonempty Polish collections."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-poland-collections-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=m.pinned('poland')[0];extra={x['id']:x for x in m.load(m.RUN/'poland/additional-geography-evidence.json')};assert not(m.RUN/'institution-country-applied.json').exists()
with m.connect(True) as db,db.transaction():
 db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
 rows=list(db.execute("SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE",([i['id'] for i in p['institutions'].values()]+list(extra),)));m.save(m.BACKUP/'institution-country-before.json.gz',rows)
 place=db.execute("SELECT id::text FROM places WHERE country_code='PL' AND name='Poland' AND latitude IS NULL AND longitude IS NULL").fetchall();assert len(place)<=1
 pid=place[0]['id'] if place else m.uid('place/poland-country')
 if not place:m.batch_insert(db,'places',[dict(id=pid,name='Poland',normalized_name='poland',country_code='PL')])
 records=[]
 extra_sid=m.uid('source/extra-geography');m.batch_insert(db,'sources',[dict(id=extra_sid,slug=m.OP+'-additional-geography',name='Official Polish institution websites',source_type='collection_page',base_url='https://wawel.krakow.pl/',adapter_key=m.OP)])
 for x in rows:
  i=x['v'];assert db.execute("SELECT EXISTS(SELECT 1 FROM artworks WHERE current_institution_id=%s AND status<>'archived') yes",(i['id'],)).fetchone()['yes']
  if i['place_id']:
   assert db.execute('SELECT country_code FROM places WHERE id=%s',(i['place_id'],)).fetchone()['country_code']=='PL';continue
  r=next((r for r in p['records'] if r['institution_id']==i['id']),None)
  if r is None:r=dict(source_url=extra[i['id']]['url'],evidence=extra[i['id']]['evidence'],provider='extra-geography',museum=i['name'])
  evidence=dict(basis='Country-level placement of the identified Polish institution, supported by its official collection catalogue and named city. No coordinates, address or current display asserted.',institution=i['name'],source_url=r['source_url'],source_sha256=r['evidence']['sha256'],editorial_confidence=.99)
  db.execute('UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s AND place_id IS NULL',(pid,i['id']))
  m.batch_insert(db,'citations',[dict(id=m.uid('institution-country/'+i['id']),entity_type='institution',entity_id=i['id'],field_name='country_location',source_id=extra_sid if i['id'] in extra else m.uid('source/'+r['provider']+'/'+r['museum']),source_url=r['source_url'],evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=r['evidence']['retrieved_at'],created_by=m.ACTOR)])
  records.append(dict(institution_id=i['id'],name=i['name'],country_code='PL',place_id=pid,evidence=evidence))
m.save(m.RUN/'institution-country-applied.json',dict(at=m.now(),records=records,local_database_changes=0));print('Country links applied',len(records),flush=True)
