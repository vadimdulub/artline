#!/usr/bin/env python3
"""Source-backed country placement for researched institutions, preserving existing places."""
import importlib.util,json,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-random-country-collections-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-random-country-collections-20261010.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
COUNTRIES={'CH':'Switzerland','US':'United States','CA':'Canada'}
TARGETS={
'CH': [('kunsthaus-zurich','https://www.kunsthaus.ch/'),('wikimedia-museum-q194626','https://kunstmuseumbasel.ch/'),('wikimedia-museum-q194622','https://www.kunstmuseumbern.ch/en/collection-research'),('wikimedia-museum-q3329523','https://www.mcba.ch/en/collection/'),('museum-source-24c90cc17d9c10fd3fb7','https://www.kmw.ch/en/collection/'),('wikimedia-museum-q301250','https://aargauerkunsthaus.ch/en/exhibitions/collection/'),('fondation-beyeler','https://www.fondationbeyeler.ch/en/collection'),('sammlung-oskar-reinhart-am-roemerholz','https://www.bundessammlungen.ch/en/collection/'),('spain-research-museum-q679075','https://www.mahmah.ch/collection')],
'US':[('cleveland-museum-of-art','https://www.clevelandart.org/'),('art-institute-of-chicago','https://www.artic.edu/'),('minneapolis-institute-of-art','https://new.artsmia.org/'),('national-gallery-of-art','https://www.nga.gov/'),('the-met','https://www.metmuseum.org/'),('spain-research-museum-q731126','https://www.getty.edu/'),('smithsonian-american-art-museum','https://americanart.si.edu/'),('wikimedia-museum-q639791','https://whitney.org/'),('museum-authority-q1201549','https://dia.org/'),('wikimedia-museum-q510324','https://philamuseum.org/'),('wikimedia-museum-q1129820','https://www.cooperhewitt.org/')],
'CA':[('wikimedia-museum-q1068063','https://www.gallery.ca/'),('museum-authority-q670250','https://ago.ca/'),('wikimedia-museum-q860812','https://www.mbam.qc.ca/fr/collections/'),('museum-authority-q2338135','https://www.mnbaq.org/'),('museum-authority-q3700321','https://mcmichael.com/collection/'),('museum-authority-q1032442','https://www.warmuseum.ca/'),('museum-authority-q649250','https://www.rom.on.ca/'),('musee-art-contemporain-montreal','https://macm.org/')]}
def research():
 out=[]
 for code,targets in TARGETS.items():
  r.phase(code)
  for slug,url in targets:
   try:
    sp,rc=r.page(url);out.append(dict(country=code,slug=slug,url=url,evidence=rc,text=sp.get_text(' ',strip=True),title=sp.title.get_text() if sp.title else None))
   except Exception as e:out.append(dict(country=code,slug=slug,url=url,error=str(e)[:220]))
  print('Directory researched',code,flush=True)
 m.save(m.RUN/'institution-research.json.gz',out)
def apply():
 records=m.load(m.RUN/'geography-reviewed.json');assert not(m.RUN/'institution-country-applied.json').exists()
 with m.connect(True) as db,db.transaction():
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  rows={x['v']['slug']:x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE slug=ANY(%s) ORDER BY id FOR UPDATE',([x['slug'] for x in records],))};m.save(m.BACKUP/'institution-country-before.json.gz',rows);applied=[]
  sid=m.uid('source/geography');m.batch_insert(db,'sources',[dict(id=sid,slug=m.OP+'-institution-geography',name='Official Swiss, US and Canadian institution websites',source_type='collection_page',base_url='https://www.mbam.qc.ca/',adapter_key=m.OP)])
  for rec in records:
   i=rows[rec['slug']];assert i['status']!='archived'
   if i['place_id']:continue
   assert db.execute("SELECT EXISTS(SELECT 1 FROM artworks WHERE current_institution_id=%s AND status<>'archived') yes",(i['id'],)).fetchone()['yes']
   code=rec['country'];places=db.execute('SELECT id::text FROM places WHERE country_code=%s AND name=%s AND latitude IS NULL AND longitude IS NULL',(code,COUNTRIES[code])).fetchall();assert len(places)<=1
   pid=places[0]['id'] if places else m.uid('place/country/'+code)
   if not places:m.batch_insert(db,'places',[dict(id=pid,name=COUNTRIES[code],normalized_name=m.norm(COUNTRIES[code]),country_code=code)])
   db.execute('UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s AND place_id IS NULL',(pid,i['id']))
   m.batch_insert(db,'citations',[dict(id=m.uid('institution-country/'+i['id']),entity_type='institution',entity_id=i['id'],field_name='country_location',source_id=sid,source_url=rec['url'],evidence_note=json.dumps(dict(**rec,basis='Official institution identity and named city/country. Country-level placement only; no coordinates or current display asserted.',confidence=.99),ensure_ascii=False),retrieved_at=rec['evidence']['retrieved_at'],created_by=m.ACTOR)])
   applied.append(dict(id=i['id'],name=i['name'],country=code))
 m.save(m.RUN/'institution-country-applied.json',dict(at=m.now(),records=applied,local_database_changes=0));print('Institution countries linked',len(applied),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
