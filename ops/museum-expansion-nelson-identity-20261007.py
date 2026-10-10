#!/usr/bin/env python3
"""Read-only physical identity leads for the selected official Nelson-Atkins works."""
import argparse,collections,copy,difflib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-nelson-facts-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;RUN=f.RUN;IID=f.IID
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-yale-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);i.RUN=RUN;i.IID=IID
SCHEMES=['nelson-object','nelson-atkins-object','nelson-emuseum-object','museum-expansion-nelson-object','european-nelson-object']
def rows(candidate_suffix="003"):
 source=RUN/('native-candidates-'+candidate_suffix+'.json.gz');rs=copy.deepcopy(m.load(source)['rows']);secondary=collections.defaultdict(list)
 for p in sorted((RUN/'wikidata-objects-001').glob('*.json.gz')):
  for q,e in m.load(p)['entities'].items():
   urls=re.findall(r'https?://art\.nelson-atkins\.org/objects/(\d+)',json.dumps(e));ids=set(urls)
   if len(ids)==1:secondary[next(iter(ids))].append(dict(qid=q,entity=e,source_reference=f.ref(p)))
 for row in rs:
  v=row['facts'];row['secondary_identity_leads']=secondary[v['source_id']]
  v['wikidata_ids']=[r['qid'] for r in row['secondary_identity_leads']]
  extra=[x['value'] for r in row['secondary_identity_leads'] for x in r['entity'].get('labels',{}).values()]
  extra += [x['value'] for r in row['secondary_identity_leads'] for vs in r['entity'].get('aliases',{}).values() for x in vs]
  v['titles']=list(dict.fromkeys(v['titles']+extra))
 return rs
def parameters(rs):
 p=i.params_for(rs);p['selected_native_ids']=sorted({r['source_id'] for r in rs});p['native_object_ids']=[]
 # A literal Unknown or school label is not a fabricated painter authority.
 # Exact titles, inventories, source IDs and selected URLs still cover them.
 p['patterns']=[x for x in p['patterns'] if x not in ['%unknown%','%school%']];p['raw_patterns']=[x for x in p['raw_patterns'] if x not in ['%unknown%','%school%']]
 return p
def queries(db,p):
 state=i.queries(db,p)
 hits=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s) ORDER BY entity_id,scheme,external_id",(SCHEMES,p['selected_native_ids'])).fetchall()
 extra=sorted({r['entity_id'] for r in hits}-set(state['artwork_ids']))
 if extra:
  arts=db.execute('SELECT '+i.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(extra,)).fetchall()
  links=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(extra,)).fetchall()
  state['artworks']=sorted(state['artworks']+arts,key=lambda r:r['id']);state['links']=sorted(state['links']+links,key=lambda r:(r['artwork_id'],r['artist_id']));state['artwork_ids']=sorted(set(state['artwork_ids'])|set(extra))
 state['external_hits']=sorted(state['external_hits']+[r for r in hits if r not in state['external_hits']],key=lambda r:(r['entity_id'],r['scheme'],r['external_id']))
 return state
def comparisons(rs,state):
 result=i.comparisons(rs,state);links=collections.defaultdict(list)
 for r in state['links']:links[r['artwork_id']].append(r)
 for row,cm in zip(rs,result,strict=True):
  v=row['facts'];names={m.norm(re.sub(r'^(?:Attributed to|Workshop of|Circle of|School of|Follower of|After|Studio of|Manner of) ','',x)) for x in [v['creator_label']]+v['identity_creator_labels'] if x}
  if any('rembrandt' in name.split() for name in names):names|={'rembrandt','rembrandt van rijn'}
  ids={r['id'] for r in state['artists'] if m.norm(r['display_name']) in names}|{r['artist_id'] for r in state['aliases'] if m.norm(r['alias']) in names}
  pool=[]
  for art in state['artworks']:
   if not (ids&{r['artist_id'] for r in links[art['id']]} or m.norm(art['unlinked_creator_label']) in names):continue
   score=max((difflib.SequenceMatcher(None,m.norm(t),m.norm(art[key])).ratio() for t in v['titles'] for key in ['title','alternate_title'] if art.get(key)),default=0)
   pool.append(dict(art,artist_links=links[art['id']],title_similarity=score))
  cm.update(focused_creator_ids=sorted(ids),focused_pool_ids=[a['id'] for a in pool],focused_top=sorted(pool,key=lambda a:a['title_similarity'],reverse=True)[:20],institution_native_id_hits=[r for r in state['external_hits'] if r['scheme'] in SCHEMES and r['external_id']==v['source_id']])
 return result
def main(suffix,candidate_suffix):
 rs=rows(candidate_suffix);p=parameters(rs)
 with m.connect() as db:state=queries(db,p)
 dest=RUN/('identity-scope-'+suffix+'.json.gz');m.save(dest,dict(at=m.now(),params=p,state=state,rows=rs,candidate_reference=f.ref(RUN/('native-candidates-'+candidate_suffix+'.json.gz')),policy='Real catalogue read-only scope by creators/aliases, exact titles, inventories and selected native/source IDs. Historical attributions and secondary multilingual labels expand identity discovery without changing native facts. Similarity is not approval.'))
 print(json.dumps(dict(rows=len(rs),counts={k:len(v) for k,v in state.items()})),flush=True)
 m.save(RUN/('identity-comparisons-'+suffix+'.json.gz'),dict(at=m.now(),records=comparisons(rs,state),scope_reference=f.ref(dest),policy='Broad and focused artist scopes retained. Every likely same-work identity, qualified attribution and grouping requires editorial review. No catalogue changes.'))
 print('Comparisons',len(rs),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);p.add_argument('--candidate-suffix',default='003');a=p.parse_args();main(a.suffix,a.candidate_suffix)
