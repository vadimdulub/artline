#!/usr/bin/env python3
"""Bounded delivery for the two completed, pinned local research batches."""
import collections,hashlib,importlib.util,json
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('planner',Path(__file__).with_name('plan-production-release-20260927.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p);r=p.r
OUT=r.ROOT/'docs/research/production-followup-20260927'
old=json.loads((r.ROOT/'docs/research/production-release-20260927/catalogue-delivery-plan-v2.json').read_bytes());meta=old['metadata'];maps=old['remaps'];foreign=old['foreign']
batches=[json.loads((r.ROOT/'docs/research'/n/'plan.json').read_bytes()) for n in ['event-images-20260927','decolonization-20260927']]
ids=[v['artwork_id'] for b in batches for v in b['records']];assert len(ids)==51
allowed_updates={'work_type','medium_text','dimensions_text','current_institution_id','accession_number','description_md','updated_by'}
result={'at':r.core.now(),'inserts':{},'updates':{},'metadata':meta,'foreign':foreign,'remaps':maps,'scope':'42 new museum objects plus completed decolonization batch (7 new, 2 reconciled, 17 existing thematic selections). No deletes or publication.'}
rows={};done=set();preserved=collections.Counter()
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
 add('sources',fetch('sources',"slug LIKE 'event-images-20260927-%%' OR slug LIKE 'decolonization-20260927-%%'",()))
 sourceids=[v['id'] for v in rows['sources'].values()]
 for t in ['citations','external_identifiers','artwork_location_assertions','media_rights_evidence']:add(t,fetch(t,'source_id=ANY(%s::uuid[])',(sourceids,)))
 # Follow only outgoing catalogue dependencies. Existing target parents are
 # verified by identity and preserved; no recursive whole-collection queries.
 while True:
  pending=[(t,k,v) for t,group in rows.items() for k,v in group.items() if (t,k) not in done]
  if not pending:break
  for t,k,v in pending:
   done.add((t,k));mapped=remap(t,v);actual=p.fetch(dst,t,meta[t],[mapped])
   if actual:
    before=actual[0]
    if t=='artworks' and v['id'] in ids:
     diff={f:{'before':before.get(f),'after':mapped.get(f)} for f in allowed_updates if before.get(f)!=mapped.get(f)}
     # No silent differences in identity, dates, review or attached media.
     assert all(before.get(f)==mapped.get(f) for f in ['slug','title','creation_year_start','creation_year_end','status','primary_media_id']),('unreviewed artwork change',v['id'])
     if diff:result['updates'].setdefault(t,[]).append({'before':before,'source':{**before,**{f:mapped[f] for f in diff}},'changes':diff})
    else:preserved[t]+=1
   else:
    assert t not in ['artists','editor_accounts','regions'],('Unplanned parent',t,k)
    if t=='artworks':assert v['id'] in ids and mapped['status']=='review' and mapped['published_at'] is None
    if t=='institutions':assert not dst.execute('SELECT 1 FROM institutions WHERE slug=%s OR normalized_name=%s',(mapped['slug'],mapped['normalized_name'])).fetchone()
    if t=='artworks':assert not dst.execute('SELECT 1 FROM artworks WHERE slug=%s OR (current_institution_id=%s AND accession_number=%s)',(mapped['slug'],mapped['current_institution_id'],mapped['accession_number'])).fetchone()
    result['inserts'].setdefault(t,[]).append(mapped)
   # Existing parent's own dependencies already exist on target.
   if actual and t not in ['artworks','artwork_artists','artwork_places','artwork_media']:continue
   for child,f,parent,pf in foreign:
    if child!=t or not v.get(f) or parent not in meta:continue
    if parent=='artworks' and v[f] not in ids:continue
    add(parent,fetch(parent,sql.SQL('{}=%s').format(sql.Identifier(pf)).as_string(src),(v[f],)))
result['preserved_existing']=dict(preserved)
for t in result['inserts']:
 result['inserts'][t].sort(key=lambda v:p.keys(v,meta[t]))
assert len(result['inserts']['artworks'])==49 and len(result['updates']['artworks'])==2
assert len(result['inserts']['media_assets'])==43
r.core.save_new(OUT/'catalogue-plan.json',result)
summary={'inserts':{t:len(v) for t,v in result['inserts'].items()},'updates':{t:len(v) for t,v in result['updates'].items()},'fields':{t:sorted({f for v in vs for f in v['changes']}) for t,vs in result['updates'].items()},'sha256':hashlib.sha256((OUT/'catalogue-plan.json').read_bytes()).hexdigest()}
r.core.save_new(OUT/'catalogue-plan-summary.json',summary);print(json.dumps(summary,indent=2))
