#!/usr/bin/env python3
"""Bounded additive delivery of completed starting-point and decolonisation research."""
import collections,hashlib,importlib.util,json
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('planner',Path(__file__).with_name('plan-production-release-20260927.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p);r=p.r
OUT=r.ROOT/'docs/research/production-starting-points-20260928';OUT.mkdir(parents=True,exist_ok=True)
old=json.loads((r.ROOT/'docs/research/production-release-20260927/catalogue-delivery-plan-v2.json').read_bytes());meta=old['metadata'];maps=old['remaps'];foreign=old['foreign']
campaigns=['all-starting-points-expansion-20260928','decolonization-deep-20260928']
batches=[json.loads((r.ROOT/'docs/research'/n/'plan.json').read_bytes()) for n in campaigns]
ids=[v['artwork_id'] for b in batches for v in b['records']];assert len(ids)==891
country=json.loads((r.ROOT/'docs/research'/campaigns[0]/'country-links-applied.json').read_bytes())
result={'at':r.core.now(),'inserts':{},'updates':{},'metadata':meta,'foreign':foreign,'remaps':maps,'scope':'873 reviewed museum/archive works, 18 completed decolonisation research records, their selected reproductions and dependencies, and three documented US artist affiliations. No deletes or publication.'}
rows={};preserved=collections.Counter()
def remap(t,v):
 v=dict(v)
 if 'id' in v:v['id']=maps.get(t,{}).get(v['id'],v['id'])
 for child,f,parent,pf in foreign:
  if child==t and pf=='id' and v.get(f):v[f]=maps.get(parent,{}).get(v[f],v[f])
 if v.get('entity_id') and v.get('entity_type'):v['entity_id']=maps.get({'artwork':'artworks','artist':'artists','media':'media_assets','institution':'institutions'}.get(v['entity_type']),{}).get(v['entity_id'],v['entity_id'])
 return v
with r.connect('local') as src,r.connect('cloud') as dst:
 for db in [src,dst]:db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');db.execute("SET LOCAL timezone='UTC'")
 def fetch(t,where,args):return [v[0] for v in src.execute(sql.SQL('SELECT to_jsonb(t) FROM {} t WHERE ').format(sql.Identifier(t))+sql.SQL(where),args)]
 def add(t,new):
  for v in new:rows.setdefault(t,{})[p.keys(v,meta[t])]=v
 add('artworks',fetch('artworks','id=ANY(%s::uuid[])',(ids,)))
 for t in ['artwork_artists','artwork_places','artwork_media']:add(t,fetch(t,'artwork_id=ANY(%s::uuid[])',(ids,)))
 add('sources',fetch('sources','slug LIKE ANY(%s::text[])',([n+'-%' for n in campaigns],)))
 sourceids=[v['id'] for v in rows['sources'].values()]
 for t in ['citations','external_identifiers','artwork_location_assertions','media_rights_evidence','curated_collection_items']:add(t,fetch(t,'source_id=ANY(%s::uuid[])',(sourceids,)))
 add('artist_countries',fetch('artist_countries',"artist_id=ANY(%s::uuid[]) AND country_code='US' AND relationship_type='cultural_affiliation'",(country['artist_ids'],)))
 # Discover only outgoing dependencies for this finite set. Batch reads by FK.
 done=set()
 while True:
  pending=[(t,k,v) for t,g in rows.items() for k,v in g.items() if (t,k) not in done]
  if not pending:break
  requests=collections.defaultdict(set)
  for t,k,v in pending:
   done.add((t,k))
   for child,f,parent,pf in foreign:
    if child==t and v.get(f) and parent in meta:requests[(parent,pf)].add(v[f])
  for (parent,pf),values in requests.items():
   if pf=='id':values-=set(v['id'] for v in rows.get(parent,{}).values())
   if not values:continue
   clause=sql.SQL('{}::text=ANY(%s::text[])').format(sql.Identifier(pf)).as_string(src)
   add(parent,fetch(parent,clause,([str(v) for v in values],)))
 for t,group in rows.items():
  proposed=[remap(t,v) for v in group.values()];actual={p.keys(v,meta[t]):v for v in p.fetch(dst,t,meta[t],proposed)}
  for v in proposed:
   before=actual.get(p.keys(v,meta[t]))
   if before:
    if t in ['artworks','artists','institutions']:
     assert before['slug']==v['slug'],('identity mismatch',t,v['id'])
    if t=='artworks' and v['id'] in ids:assert {k:x for k,x in before.items() if k not in p.IGNORE}=={k:x for k,x in v.items() if k not in p.IGNORE},('unexpected existing batch artwork',v['id'])
    preserved[t]+=1
   else:
    assert t not in ['artists','editor_accounts','regions'],('unplanned parent',t,p.keys(v,meta[t]))
    if t=='artworks':assert v['id'] in ids and v['status']=='review' and v['published_at'] is None
    result['inserts'].setdefault(t,[]).append(v)
  print(t,'new',len(result['inserts'].get(t,[])),'preserved',preserved[t],flush=True)
 # Natural identities must also be absent, without global enrichment.
 for t in ['artworks','institutions','sources']:
  new=result['inserts'].get(t,[])
  if new:assert not dst.execute(sql.SQL('SELECT slug FROM {} WHERE slug=ANY(%s::text[])').format(sql.Identifier(t)),([v['slug'] for v in new],)).fetchall(),('duplicate slug',t)
result['preserved_existing']=dict(preserved)
for t in result['inserts']:result['inserts'][t].sort(key=lambda v:p.keys(v,meta[t]))
assert len(result['inserts']['artworks'])==891 and len(result['inserts']['media_assets'])==883
assert len(result['inserts']['artist_countries'])==3
r.core.save_new(OUT/'catalogue-plan.json',result)
summary={'inserts':{t:len(v) for t,v in result['inserts'].items()},'updates':{},'sha256':hashlib.sha256((OUT/'catalogue-plan.json').read_bytes()).hexdigest()}
r.core.save_new(OUT/'catalogue-plan-summary.json',summary);print(json.dumps(summary,indent=2))
