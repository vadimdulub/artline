#!/usr/bin/env python3
"""Verified Swiss city placement for delivered museum records; local DB untouched."""
import importlib.util
import json
import sys
from pathlib import Path

s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('switzerland-india-delivery-20261011.py'))
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)


def run(phase):
 folder=d.RUN/phase
 assert not (folder/'geography-applied.json').exists()
 delivered=d.load(folder/'applied.json');plan=d.load(folder/'plan.json.gz')
 assert delivered['plan_sha256']==d.sha((folder/'plan.json.gz').read_bytes())
 assert d.load(d.RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'
 registry=d.load(d.RUN/'institution-registry.json')
 for path in d.RUN.glob('institution-registry-wave*.json'):registry.update(d.load(path))
 directory={x['directory_id']:x for x in d.load(d.RUN/'CH/directory.json.gz')['records']}
 source_rows=[]
 for name,i in plan['institutions'].items():
  r=registry[name];entry=directory[r['directory_id']]
  assert d.norm(entry['locality'])==d.norm(r['city']),(name,entry['locality'],r['city'])
  detail=d.load(d.RUN/'CH/directory-details'/(r['directory_id']+'.json.gz'))
  assert detail['evidence']['status']==200
  source_rows.append(dict(name=name,institution_id=i['id'],city=r['city'],country='CH',
                         source_url=entry['directory_url'],evidence=detail['evidence'],
                         source_name=entry['name'],source_locality=entry['locality']))
 d.save(folder/'geography-reviewed.json',source_rows)
 ids=[r['institution_id'] for r in source_rows]
 with d.connect(True) as db,db.transaction():
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(d.ACTOR,))
  db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  before={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,))}
  assert len(before)==len(ids)
  d.save(d.BACKUP/phase/'geography-before.json.gz',before)
  sid=d.uid('source/swiss-museums-directory')
  if not db.execute('SELECT 1 FROM sources WHERE id=%s',(sid,)).fetchone():
   d.batch_insert(db,'sources',[dict(id=sid,slug=d.OP+'-vms-directory',name='Association of Swiss Museums / ICOM Switzerland — museum directory',source_type='collection_page',base_url='https://www.museums.ch',adapter_key=d.OP)])
  applied=[];preserved=[]
  for r in source_rows:
   i=before[r['institution_id']]
   assert i['status']!='archived'
   if i['place_id']:
    preserved.append(dict(id=i['id'],place_id=i['place_id']));continue
   assert db.execute("SELECT EXISTS(SELECT 1 FROM artworks WHERE current_institution_id=%s AND status<>'archived') yes",(i['id'],)).fetchone()['yes']
   places=list(db.execute('SELECT id::text FROM places WHERE country_code=%s AND name=%s',('CH',r['city'])))
   assert len(places)<=1,('Ambiguous city identity',r['city'])
   pid=places[0]['id'] if places else d.uid('place/CH/'+d.norm(r['city']))
   if not places:d.batch_insert(db,'places',[dict(id=pid,name=r['city'],normalized_name=d.norm(r['city']),country_code='CH')])
   db.execute('UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s AND place_id IS NULL',(pid,i['id']))
   d.batch_insert(db,'citations',[dict(id=d.uid('institution-geography/'+i['id']),entity_type='institution',entity_id=i['id'],field_name='country_city_location',source_id=sid,source_url=r['source_url'],evidence_note=json.dumps(dict(**r,basis='Exact named Swiss museum and directory locality, corroborated by native collection website. No coordinates or display claim.',confidence=.99),ensure_ascii=False),retrieved_at=r['evidence']['retrieved_at'],created_by=d.ACTOR)])
   applied.append(dict(id=i['id'],name=i['name'],city=r['city'],country='CH',place_id=pid))
  after=list(db.execute('SELECT i.id::text,i.name,p.name city,p.country_code FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.id=ANY(%s::uuid[])',(ids,)))
  assert all(x['country_code']=='CH' for x in after) and len(after)==len(ids)
 d.save(folder/'geography-applied.json',dict(at=d.now(),applied=applied,preserved=preserved,after=after,local_database_changes=0))
 print(json.dumps(dict(phase=phase,cities_linked=len(applied),existing_places_preserved=len(preserved))),flush=True)


if __name__=='__main__':run(sys.argv[1])
