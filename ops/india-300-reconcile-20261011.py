#!/usr/bin/env python3
"""Read-only, creator-scoped identity audit and explicit source corrections."""
import collections, importlib.util, re
from pathlib import Path

s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('india-300-delivery-20261011.py'))
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)

def run():
 folder=d.RUN/'IN-wave1';rows=d.load(folder/'source-records.json.gz')
 artists=d.load(d.RUN/'creator-identity-baseline.json.gz')
 names=collections.defaultdict(set)
 for a in artists:
  for name in [a['display_name']]+(a.get('aliases') or []):names[d.norm(name)].add(a['id'])
 corrections={};links={};scope=set()
 for r in rows:
  key=r['provider']+'/'+r['source_id'];c={}
  if r['provider']=='jatan-avm_pun':
   c['editorial_hold']='Historical event/subject dates do not establish the date of the physical photographic print; original/reproduction identity unresolved'
  if r['provider']=='jatan-ngma_mum' and re.search(r'\b(?:1981|1982|1984)\b',r['title'] or '') and r['date_decision']!='after_cutoff':
   c['editorial_hold']='Explicit post-1970 year in source artwork title; absent Period field does not make this eligible'
  if r['source_id']=='im_kol-AT-73-192-6575':
   c.update(date_display='Date unknown',year_start=None,year_end=None,date_decision='date_review',date_basis='The source Period field 1875–1962 coincides with Sunayani Devi’s lifespan, confirmed in the official NGMA biography; not treated as artwork creation years',date_correction_source_url='https://museumsofindia.gov.in/repository/record/ngma_blr-acc-no-00355-466')
  if r['date_display']=='May 1944':c.update(year_start=1944,year_end=1944,date_decision='eligible',date_basis='Explicit month and creation year in native Period / Year of Work field')
  if c:corrections[key]=c
  simple=re.sub(r'\s*\([^)]*\)\s*$','',r.get('creator_label') or '').strip()
  hits=names[d.norm(simple)]
  scope.update(hits)
  link=dict(creator_link_hold=True,creator_identity_basis='No unique exact existing creator name/alias; native label preserved')
  if len(hits)==1 and not r['creator_link_hold']:
   link.update(verified_artist_id=next(iter(hits)),creator_identity_basis='Unique exact existing creator name or documented alias; native label retained in citation')
  links[key]=link
 # Orthographic variants are included in duplicate search, without silently
 # assigning a qualified or ambiguous creator to a primary artist record.
 for name in ['Raja Ravi Varma','Abanindranath Tagore','Vasily Vereshchagin']:
  scope.update(names[d.norm(name)])
 d.save(folder/'source-field-corrections.json.gz',corrections)
 d.save(folder/'creator-links.json.gz',links)
 dest=folder/'creator-scoped-existing.json.gz'
 if not dest.exists():
  with d.connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
   records=[x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id IN (SELECT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]))',(sorted(scope),))]
   ids=[a['id'] for a in records]
   creators=list(db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(ids,)))
   identifiers=[x['v'] for x in db.execute("SELECT to_jsonb(e) v FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
   d.save(dest,dict(at=d.now(),artist_ids=sorted(scope),artworks=records,creators=creators,identifiers=identifiers))
 records=d.load(dest);print('Scoped existing artworks',len(records['artworks']),flush=True)
 existing={a['id']:a for a in records['artworks']}
 existing.update({a['record']['id']:a['record'] for a in d.load(d.RUN/'existing-museum-artworks.json.gz')['artworks']})
 bytitle=collections.defaultdict(list)
 for a in existing.values():
  for title in [a['title'],a.get('alternate_title')]:
   if title:bytitle[d.norm(title)].append(a)
 matches=[]
 for r in rows:
  if r['date_decision']=='after_cutoff' or r.get('editorial_hold') or corrections.get(r['provider']+'/'+r['source_id'],{}).get('editorial_hold'):continue
  hits=bytitle[d.norm(r['title'])]
  if hits:matches.append(dict(source_id=r['source_id'],title=r['title'],creator=r['creator_label'],accession=r['accession_number'],matches=[{k:a.get(k) for k in ['id','title','date_display','accession_number','current_institution_id','unlinked_creator_label']} for a in hits]))
 d.save(folder/'title-candidates.json.gz',matches)
 print('Title candidates',len(matches),flush=True)
 for x in matches:print(x,flush=True)
 # Numeric NGMA inventories can be shared by city branches. Flag matching
 # numbers for editorial comparison, without equating local series blindly.
 ngma=collections.defaultdict(list)
 for r in rows:
  if r['provider'].startswith('jatan-ngma_'):
   number=re.sub(r'^(?:ngma-|acc-no-)','',r['accession_number'] or '',flags=re.I).lstrip('0')
   ngma[number].append(r)
 cross=[v for v in ngma.values() if len(v)>1]
 d.save(folder/'ngma-accession-candidates.json.gz',cross)
 print('NGMA cross-branch accession candidates',len(cross),flush=True)
 for v in cross:print([(r['source_id'],r['title'],r['creator_label']) for r in v],flush=True)

if __name__=='__main__':run()
