#!/usr/bin/env python3
"""Read-only creator/object identity comparisons for the National Gallery of Australia partner selection."""
import importlib.util,json,re,difflib
from urllib.parse import urlsplit,parse_qs
from pathlib import Path
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-ngaustralia-gac-facts-20261007.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-courtauld-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
m=w.m;RUN=w.RUN;IID=w.d.IID;i.RUN=RUN;i.IID=IID
compact=i.compact;tokens=i.tokens;original_search_terms=i.search_terms
def search_terms(facts):
 out=set(original_search_terms(facts))
 label=facts['creator_label'] or ''
 if 'BARAK' in label:out.add('barak')
 if 'MICKEY OF ULLADULLA' in label:out.update(['mickey','ulladulla'])
 return sorted(out)
i.search_terms=search_terms
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
   inventory_hit=bool(f['inventory']) and compact(a['accession_number'])==compact(f['inventory'])
   if not (hit or exact_hit or inventory_hit):continue
   b=dict(a,creators=[x['display_name'] for x in links.get(a['id'],[])],artist_links=links.get(a['id'],[]))
   score=max((difflib.SequenceMatcher(None,m.norm(t),m.norm(a[k])).ratio() for t in f['titles'] for k in ['title','alternate_title'] if a.get(k)),default=0);b['title_similarity']=round(score,4)
   if hit:pool.append(b)
   if exact_hit:exact.append(b)
   if inventory_hit:invs.append(dict(b,relevant=(hit or a['id'] in oldscope or a['current_institution_id']==IID)))
  source=[x for x in state['source_hits'] if x['source_url'].replace('http:','https:')==f['source_url']]+[x for x in state['external_hits'] if x['canonical_url'] and x['canonical_url'].replace('http:','https:')==f['source_url'] or x['scheme']=='wikidata' and x['external_id'] in qids]
  out.append(dict(source_id=f['source_id'],creator_terms=sorted(terms),artist_ids=sorted(ids),creator_pool_ids=sorted(a['id'] for a in pool),untitled_creator_hits=[a for a in pool if not a.get('title') and not a.get('alternate_title')],leads=sorted(pool,key=lambda a:a['title_similarity'],reverse=True)[:10],exact_title_hits=exact,inventory_hits=invs,source_hits=source))
 return out

def native_urls(f):
 urls=set(f['native_external_links']);irn=f['native_object_id']
 if irn:urls.update([f'https://searchthecollection.nga.gov.au/object/{irn}',f'https://artsearch.nga.gov.au/Detail.cfm?IRN={irn}'])
 return urls
def params_for(rows):
 params=i.params_for(rows);urls=set(params['source_urls'])
 for row in rows:
  for url in native_urls(row['facts']):
   for protocol in ['http:','https:']:
    u=url.replace('http:',protocol).replace('https:',protocol);urls.update([u.rstrip('/'),u.rstrip('/')+'/'])
 params['source_urls']=sorted(urls)
 # Some legacy records misused the native IRN as accession. This is a lead only.
 params['inventories']=sorted(set(params['inventories'])|{r['facts']['native_object_id'] for r in rows if r['facts']['native_object_id']});return params
def queries(db,params):return i.queries(db,params)
def main():
 source=RUN/'gac-candidates-002.json.gz';rows=[r for r in m.load(source)['rows'] if r['state']=='candidate'];params=params_for(rows)
 with m.connect() as db:state=queries(db,params)
 m.save(RUN/'gac-identity-003.json.gz',dict(at=m.now(),candidate_reference=w.ref(source),params=params,state=state,policy='Read-only creator-scoped and exact title/inventory/source URL comparison. Names and similarities are leads, not approvals.'))
 comps=comparisons(rows,state)
 # Include museum-native external links as exact identity leads as well.
 for row,cmp in zip(rows,comps):
  urls={u.replace('http:','https:').rstrip('/') for u in native_urls(row['facts'])}
  cmp['native_url_hits']=[h for h in state['source_hits'] if h['source_url'].replace('http:','https:').rstrip('/') in urls]+[h for h in state['external_hits'] if h['canonical_url'] and h['canonical_url'].replace('http:','https:').rstrip('/') in urls]
 for row,cmp in zip(rows,comps):
  cmp['legacy_irn_accession_leads']=[a for a in state['artworks'] if a['accession_number']==row['facts']['native_object_id']]
 m.save(RUN/'gac-comparisons-003.json.gz',dict(at=m.now(),records=comps));print(json.dumps({k:len(v) for k,v in state.items()}),flush=True)
if __name__=='__main__':main()
