#!/usr/bin/env python3
"""Place delivered Indian museums using the captured national directory."""
import importlib.util,json,sys
from pathlib import Path

s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('india-300-delivery-20261011.py'))
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)

def run(phase):
 folder=d.RUN/phase
 assert not (folder/'geography-applied.json').exists()
 delivered=d.load(folder/'applied.json');plan,digest=d.pinned(phase)
 assert delivered['plan_sha256']==digest
 assert d.load(d.RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'
 registry=d.load(d.RUN/'institution-registry.json')
 directory={x['code']:x for x in d.load(d.RUN/'portal-directory-crosswalk.json')}
 rows=[]
 for name,i in plan['institutions'].items():
  r=registry[name];entry=directory[r['portal_museum_code']]
  assert d.norm(entry['record']['city'])==d.norm(r['city'])
  assert entry['evidence']['status']==200
  rows.append(dict(name=name,institution_id=i['id'],city=r['city'],country='IN',source_url=entry['evidence']['url'],evidence=entry['evidence'],directory_id=entry['record']['id'],source_name=entry['record']['name'],source_address=entry['record']['address']))
 d.save(folder/'geography-reviewed.json',rows)
 ids=[r['institution_id'] for r in rows]
 with d.connect(True) as db,db.transaction():
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(d.ACTOR,))
  db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  before={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,))}
  assert len(before)==len(ids)
  d.save(d.BACKUP/phase/'geography-before.json.gz',before)
  sid=d.uid('source/india-national-directory')
  if not db.execute('SELECT 1 FROM sources WHERE id=%s',(sid,)).fetchone():
   d.batch_insert(db,'sources',[dict(id=sid,slug=d.OP+'-national-directory',name='Museums of India — national museum directory',source_type='collection_page',base_url='https://museumsofindia.gov.in',adapter_key=d.OP)])
  applied=[];preserved=[]
  for r in rows:
   i=before[r['institution_id']];assert i['status']!='archived'
   if i['place_id']:
    place=db.execute('SELECT country_code,name FROM places WHERE id=%s',(i['place_id'],)).fetchone()
    assert place['country_code']=='IN',('Conflicting existing geography',i['id'])
    preserved.append(dict(id=i['id'],place_id=i['place_id'],**place));continue
   assert db.execute("SELECT EXISTS(SELECT 1 FROM artworks WHERE current_institution_id=%s AND status<>'archived') yes",(i['id'],)).fetchone()['yes']
   places=list(db.execute('SELECT id::text FROM places WHERE country_code=%s AND name=%s',('IN',r['city'])))
   assert len(places)<=1,('Ambiguous city identity',r['city'])
   pid=places[0]['id'] if places else d.uid('place/IN/'+d.norm(r['city']))
   if not places:d.batch_insert(db,'places',[dict(id=pid,name=r['city'],normalized_name=d.norm(r['city']),country_code='IN')])
   db.execute('UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s AND place_id IS NULL',(pid,i['id']))
   d.batch_insert(db,'citations',[dict(id=d.uid('institution-geography/'+i['id']),entity_type='institution',entity_id=i['id'],field_name='country_city_location',source_id=sid,source_url=r['source_url'],evidence_note=json.dumps(dict(**r,basis='Official directory museum and postal locality, cross-referenced to the native collection code; no inferred coordinates or current-display claim',confidence=.99),ensure_ascii=False),retrieved_at=r['evidence']['retrieved_at'],created_by=d.ACTOR)])
   applied.append(dict(id=i['id'],name=i['name'],city=r['city'],country='IN',place_id=pid))
  after=list(db.execute('SELECT i.id::text,i.name,p.name city,p.country_code FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.id=ANY(%s::uuid[])',(ids,)))
  assert len(after)==len(ids) and all(x['country_code']=='IN' for x in after)
 d.save(folder/'geography-applied.json',dict(at=d.now(),applied=applied,preserved=preserved,after=after,local_database_changes=0))
 print(json.dumps(dict(phase=phase,cities_linked=len(applied),existing_places_preserved=len(preserved))),flush=True)

if __name__=='__main__':run(sys.argv[1])
