#!/usr/bin/env python3
"""Record explicit American creator labels from native museum objects; no birth inference."""
import importlib.util,re,json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-random-country-collections-20261009.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=m.load(m.RUN/'US/artists-plan.json.gz');records={r['provider']+'/'+r['source_id']:r for r in m.source_records('US')};candidates=[]
for a in p['matches']:
 for w in a['works']:
  r=records[w['provider']+'/'+w['source_id']];raw=r['raw'];labels=[raw.get('artist_display') or '']+[v.get('description','') for v in raw.get('creators',[])]
  if r.get('creator_link_hold'):continue
  selected=next((s for s in labels if re.search(r'(?:^|\(|\n|;)\s*American\b',s)),None)
  if selected:candidates.append(dict(artist_id=a['artist_id'],name=a['name'],label=selected,record=r));break
with m.connect() as db:
 before=list(db.execute('SELECT artist_id::text,country_code,relationship_type,is_primary,note FROM artist_countries WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,country_code,relationship_type',([x['artist_id'] for x in candidates],)))
known={(x['artist_id'],x['country_code'],x['relationship_type']) for x in before};selected=[x for x in candidates if (x['artist_id'],'US','cultural_affiliation') not in known];plan=dict(at=m.now(),candidates=candidates,selected=selected,before=before)
m.save(m.RUN/'US/artist-country-supplement-plan.json.gz',plan);m.save(m.BACKUP/'US/artist-country-supplement-before.json.gz',plan)
with m.connect(True) as db,db.transaction():
 db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
 actual=list(db.execute('SELECT artist_id::text,country_code,relationship_type,is_primary,note FROM artist_countries WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,country_code,relationship_type',([x['artist_id'] for x in candidates],)));assert actual==before
 rows=[];cites=[]
 for x in selected:
  r=x['record'];rows.append(dict(artist_id=x['artist_id'],country_code='US',relationship_type='cultural_affiliation',is_primary=False,note='Explicit American label in native museum creator metadata: '+x['label']+'. '+r['source_url']))
  cites.append(dict(id=m.uid('artist-country-native-US/'+x['artist_id']),entity_type='artist',entity_id=x['artist_id'],field_name='country_cultural_affiliation',source_id=m.uid('source/'+r['provider']+'/'+r['museum']),source_url=r['source_url'],evidence_note=json.dumps(dict(label=x['label'],source_evidence=r['evidence'],country_code='US',basis='Explicit American creator label; not inferred from museum location or place of birth.'),ensure_ascii=False),retrieved_at=r['evidence']['retrieved_at'],created_by=m.ACTOR))
 m.batch_insert(db,'artist_countries',rows);m.batch_insert(db,'citations',cites)
 for x in selected:assert db.execute("SELECT EXISTS(SELECT 1 FROM artist_countries WHERE artist_id=%s AND country_code='US' AND relationship_type='cultural_affiliation') yes",(x['artist_id'],)).fetchone()['yes']
m.save(m.RUN/'US/artist-country-supplement-applied.json',dict(at=m.now(),source_labels_verified=len(candidates),country_links_added=len(selected),artist_ids=[x['artist_id'] for x in selected],artist_metadata_unchanged=True,local_database_changes=0));print('Explicit American affiliations added',len(selected),flush=True)
