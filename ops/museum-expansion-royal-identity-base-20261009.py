"""Bounded identity SQL copied from the established Yale helper, with a lightweight context import."""
import re,importlib.util
from pathlib import Path
z=importlib.util.spec_from_file_location("s",Path(__file__).with_name("museum-expansion-royal-common-20261009.py"));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN

def compact(value):return re.sub(r'[^a-z0-9]','',m.norm(value or ''))

def tokens(v):return set(m.norm(v or '').split())-{'the','and','van','von','de','di','da','del','der','le','la','sir','after','attributed','to','of','unknown','school','workshop','studio','copy','younger','elder','i','ii','iii','follower','manner','circle','or'}

def search_terms(facts):
 out=set()
 for raw in [facts['creator_label'],facts.get('detail_creator_label')]+facts.get('identity_creator_labels',[]):
  if not raw or re.fullmatch(r'.*\bSchool(?: \(\d+\))?',raw,re.I) or raw=='Anonymous Artist':continue
  # Existing authorities also use the mononym; surname-only Rijn misses them.
  if 'rembrandt' in tokens(raw):out.add('rembrandt')
  if 'vermeer' in tokens(raw):out.add('vermeer')
  surname=re.search(r'([^\s]+-[^\s]+)$',raw.strip())
  if surname:out.update(t for t in m.norm(surname[1]).split() if len(t)>=3)
  raw=re.sub(r'\bII of Ipswich\b','II',raw)
  raw=re.sub(r'\s+der (?:Ältere|Jüngere)\b','',raw,flags=re.I)
  for chunk in re.split(r'\s+or\s+|\s+and\s+|[,()&]',raw):
   ts=[v for v in m.norm(chunk).split() if v in tokens(chunk)]
   if ts and len(ts[-1])>=3:out.add(ts[-1])
 return sorted(out)

ARTCOLS='a.id::text,a.title,a.normalized_title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.accession_number,a.current_institution_id::text,a.medium_text,a.dimensions_text,a.work_type,a.unlinked_creator_label'

def queries(db,params):
 p=params
 artists=db.execute('SELECT id::text,display_name,normalized_name,slug,birth_year,death_year FROM artists WHERE normalized_name LIKE ANY(%s) OR lower(display_name) LIKE ANY(%s) ORDER BY id',(p['patterns'],p['raw_patterns'])).fetchall()
 aliases=db.execute('SELECT aa.artist_id::text,aa.alias,a.display_name FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias LIKE ANY(%s) OR lower(aa.alias) LIKE ANY(%s) ORDER BY aa.artist_id,aa.alias',(p['patterns'],p['raw_patterns'])).fetchall()
 ids=sorted({a['id'] for a in artists}|{a['artist_id'] for a in aliases})
 aids=db.execute('SELECT DISTINCT artwork_id::text FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]) ORDER BY artwork_id LIMIT 100001',(ids,)).fetchall();assert len(aids)<=100000,'creator scope limit'
 unlinked=db.execute('SELECT id::text FROM artworks WHERE unlinked_creator_label ILIKE ANY(%s) ORDER BY id LIMIT 20001',(p['raw_patterns']+p['patterns'],)).fetchall();assert len(unlinked)<=20000,'unlinked scope limit'
 exact=db.execute('SELECT id::text FROM artworks WHERE normalized_title=ANY(%s) ORDER BY id LIMIT 20001',(p['title_keys'],)).fetchall();assert len(exact)<=20000,'title scope limit'
 inv=db.execute('SELECT id::text FROM artworks WHERE accession_number=ANY(%s) ORDER BY id LIMIT 20001',(p['inventories'],)).fetchall();assert len(inv)<=20000,'inventory scope limit'
 cites=db.execute("SELECT entity_id::text,source_url,field_name FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) ORDER BY entity_id,source_url,field_name",(p['source_urls'],)).fetchall()
 external=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme='wikidata' AND external_id=ANY(%s)) OR (scheme IN ('yale-object','yuag-object','museum-expansion-yale-object') AND external_id=ANY(%s))) ORDER BY entity_id,scheme,external_id",(p['source_urls'],p['qids'],p['native_object_ids'])).fetchall()
 scope=m.load(RUN/'initial-scope-001.json.gz')['scoped_ids'];workids=sorted({x.get('artwork_id',x.get('id')) for x in aids+unlinked+exact+inv}|{x['entity_id'] for x in cites+external}|set(scope))
 assert len(workids)<=120000
 arts=db.execute('SELECT '+ARTCOLS+''' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(workids,)).fetchall()
 links=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(workids,)).fetchall()
 return dict(artists=artists,aliases=aliases,artworks=arts,links=links,source_hits=cites,external_hits=external,artist_ids=ids,artwork_ids=workids)
