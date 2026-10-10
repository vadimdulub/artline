#!/usr/bin/env python3
"""Read-only Dulwich identity scope; names/title similarity are leads, not approvals."""
import argparse,difflib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-dulwich-web-review-20261007.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w);m=w.m;RUN=w.RUN;IID=w.d.IID

def compact(value):return re.sub(r'[^a-z0-9]','',m.norm(value or ''))
def tokens(v):return set(m.norm(v or '').split())-{'the','and','van','von','de','di','da','del','der','le','la','sir','after','attributed','to','of','unknown','school','workshop','studio','copy','younger','elder','i','ii','iii','follower','manner','circle','or'}
def search_terms(facts):
 out=set()
 for raw in [facts['creator_label'],facts.get('detail_creator_label')]:
  if not raw or re.fullmatch(r'.*\bSchool(?: \(\d+\))?',raw,re.I) or raw=='Anonymous Artist':continue
  # Existing authorities also use the mononym; surname-only Rijn misses them.
  if 'rembrandt' in tokens(raw):out.add('rembrandt')
  if 'vermeer' in tokens(raw):out.add('vermeer')
  raw=re.sub(r'\bII of Ipswich\b','II',raw)
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
 external=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme='wikidata' AND external_id=ANY(%s))) ORDER BY entity_id,scheme,external_id",(p['source_urls'],p['qids'])).fetchall()
 scope=m.load(RUN/'initial-scope-001.json.gz')['scoped_ids'];workids=sorted({x.get('artwork_id',x.get('id')) for x in aids+unlinked+exact+inv}|{x['entity_id'] for x in cites+external}|set(scope))
 assert len(workids)<=120000
 arts=db.execute('SELECT '+ARTCOLS+''' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(workids,)).fetchall()
 links=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(workids,)).fetchall()
 return dict(artists=artists,aliases=aliases,artworks=arts,links=links,source_hits=cites,external_hits=external,artist_ids=ids,artwork_ids=workids)

def params_for(rows):
 terms=sorted({t for r in rows for t in search_terms(r['facts'])})
 invs=sorted({v for r in rows for v in [r['facts']['inventory'],compact(r['facts']['inventory']).upper()] if v})
 titlekeys=sorted({m.norm(v) for r in rows for v in r['facts']['titles']+[re.sub(r'^The ','',r['facts']['title'])]})
 urls=sorted({r['facts']['source_url'] for r in rows}|{r['facts']['source_url'].replace('https:','http:') for r in rows})
 return dict(patterns=['%'+t+'%' for t in terms],raw_patterns=['%'+t+'%' for t in terms],title_keys=titlekeys,inventories=invs,source_urls=urls,qids=[])

def comparisons(rows,state):
 artists=state['artists'];aliases=state['aliases'];links={}
 for link in state['links']:links.setdefault(link['artwork_id'],[]).append(link)
 out=[];oldscope=set(m.load(RUN/'initial-scope-001.json.gz')['scoped_ids'])
 for r in rows:
  f=r['facts'];terms=set(search_terms(f));ids={a['id'] for a in artists if tokens(a['display_name'])&terms}|{a['artist_id'] for a in aliases if tokens(a['alias'])&terms}
  pool=[];exact=[];invs=[]
  titlekeys={m.norm(t) for t in f['titles']};qids=set()
  for a in state['artworks']:
   hit=bool(ids & {x['artist_id'] for x in links.get(a['id'],[])}) or bool(tokens(a['unlinked_creator_label'])&terms)
   exact_hit=m.norm(a['title']) in titlekeys
   inventory_hit=compact(a['accession_number'])==compact(f['inventory'])
   if not (hit or exact_hit or inventory_hit):continue
   b=dict(a,creators=[x['display_name'] for x in links.get(a['id'],[])],artist_links=links.get(a['id'],[]))
   score=max((difflib.SequenceMatcher(None,m.norm(t),m.norm(a[k])).ratio() for t in f['titles'] for k in ['title','alternate_title'] if a.get(k)),default=0);b['title_similarity']=round(score,4)
   if hit:pool.append(b)
   if exact_hit:exact.append(b)
   if inventory_hit:invs.append(dict(b,relevant=(hit or a['id'] in oldscope or a['current_institution_id']==IID)))
  source=[x for x in state['source_hits'] if x['source_url'].replace('http:','https:')==f['source_url']]+[x for x in state['external_hits'] if x['canonical_url'] and x['canonical_url'].replace('http:','https:')==f['source_url'] or x['scheme']=='wikidata' and x['external_id'] in qids]
  out.append(dict(source_id=f['source_id'],creator_terms=sorted(terms),artist_ids=sorted(ids),creator_pool_ids=sorted(a['id'] for a in pool),untitled_creator_hits=[a for a in pool if not a.get('title') and not a.get('alternate_title')],leads=sorted(pool,key=lambda a:a['title_similarity'],reverse=True)[:10],exact_title_hits=exact,inventory_hits=invs,source_hits=source))
 return out

def main(suffix):
 dest=RUN/f'native-identity-{suffix}.json.gz';assert not dest.exists();candidate=RUN/f'native-candidates-{suffix}.json.gz';rows=[r for r in m.load(candidate)['rows'] if r['state']=='candidate'];params=params_for(rows)
 with m.connect() as db:state=queries(db,params)
 m.save(dest,dict(at=m.now(),candidate_reference=w.ref(candidate),params=params,state=state,policy='Read-only creator-scoped, exact-title, exact-inventory, native-URL and native-Wikidata identity leads. Surname/title similarity is discovery, never an approval. Bare inventory numbers are not globally unique.'))
 comps=comparisons(rows,state);m.save(RUN/f'native-comparisons-{suffix}.json.gz',dict(at=m.now(),records=comps))
 print({k:len(v) for k,v in state.items()});print('Comparisons',len(comps))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);a=p.parse_args();assert re.fullmatch(r'\d{3}',a.suffix);main(a.suffix)
