"""Museum scoped object identity plus indexed source,inventory,title and named creator discovery."""
import collections,difflib,importlib.util,json,re
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-mbp-facts-20261009.py');q=module('q','museum-expansion-royal-identity-base-20261009.py');prod=module('prod','catalogue-expansion-20261008.py');s=f.s;m=f.m;RUN=f.RUN;q.RUN=RUN
def params(rows):
 terms=set()
 for row in rows:
  for cr in row['facts']['source_fields'].get('creators') or []:
   for lang in ['en','gr']:
    ts=m.norm(cr.get(lang)).split()
    if ts:terms.add(ts[0])
 terms|={'poulakis','poulakes','papadopoulos','zefarovic','zhefarovich','mesmer','messmer','iordanitis','tziolakoglou','triantaphyllou','zoulianis','zuliani','mytilinaios','mytilineos','kaldis','parthenios','ithakisios','karavias','stefanopoulos','stephanopoulos','rokou','nikodimos'}
 urls=[]
 for row in rows:
  for u in row['facts']['native_page_urls']+row['facts']['native_metadata_urls']:
   urls.extend([u,u.rstrip('/')+'/',u.replace('?language=en',''),u.replace('?language=en','?language=el')])
 return dict(patterns=['%'+t+'%'for t in sorted(terms)],raw_patterns=['%'+t+'%'for t in sorted(terms)],title_keys=sorted({m.norm(t) for r in rows for t in r['facts']['titles']}),inventories=sorted({r['facts']['inventory'] for r in rows}),source_urls=sorted(set(urls)),qids=[],native_object_ids=[],source_ids=[r['source_id']for r in rows])
def queries(db,p):
 state=q.queries(db,p)
 ei=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) ORDER BY entity_id,scheme,external_id",(p['source_ids'],)).fetchall()
 ci=db.execute("SELECT entity_id::text,source_record_id,source_url,field_name FROM citations WHERE entity_type='artwork' AND source_record_id=ANY(%s) ORDER BY entity_id,source_record_id,source_url,field_name",(p['source_ids'],)).fetchall()
 scoped=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(s.IIDS,s.IIDS))]
 extra=sorted(({v['entity_id']for v in ei+ci}|set(scoped))-set(state['artwork_ids']))
 state['artworks']+=db.execute('SELECT '+q.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(extra,)).fetchall();state['artwork_ids']=sorted(set(state['artwork_ids'])|set(extra));state['artworks'].sort(key=lambda v:v['id'])
 state['links']+=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(extra,)).fetchall();state['links'].sort(key=lambda v:(v['artwork_id'],v['artist_id']))
 state.update(native_id_hits=ei,source_record_hits=ci,scoped_ids=scoped);return state
def comparisons(rows,state):
 out=[];scoped=set(state['scoped_ids'])
 for row in rows:
  facts=row['facts'];tt={m.norm(t)for t in facts['titles']};hits=[];urls=set(facts['native_page_urls']+facts['native_metadata_urls']);rid=row['source_id']
  for a in state['artworks']:
   at={m.norm(a['title']),m.norm(a['alternate_title'])};reasons=[];score=max(difflib.SequenceMatcher(None,t,u).ratio()for t in tt for u in at)
   if tt & at:reasons.append('exact_title')
   if f.invkey(a['accession_number'])==f.invkey(facts['inventory']):reasons.append('inventory')
   if a['id']in scoped and score>=.48:reasons.append('museum_similar_title')
   if reasons:hits.append(dict(a,hit_types=reasons,same_museum=a['id']in scoped,title_similarity=round(score,4)))
  source=[]
  for v in state['source_hits']+state['external_hits']+state['native_id_hits']+state['source_record_hits']:
   u=v.get('source_url')or v.get('canonical_url')or''
   if (u in urls or v.get('source_record_id')==rid or v.get('external_id')==rid) and ('nationalarchive.culture.gr/'in u or '/edm/mnam/'in u or v.get('scheme')=='greek-national-archive-exhibit'):source.append(v)
  out.append(dict(number=row['number'],source_id=rid,hits=hits,source_hits=source))
 return out
def main():
 rows=f.rows()[0];p=params(rows)
 with prod.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');initial=m.load(RUN/'production-initial-scope-001.json.gz');assert s.snapshot(db,initial['scoped_ids'])==initial['snapshot'];state=queries(db,p);cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 m.save(RUN/'production-identity-001.json.gz',dict(at=m.now(),rows=rows,params=p,state=state,comparisons=comparisons(rows,state),source_reference=s.ref(RUN/'candidate-facts-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),read_only=True))
 m.save(RUN/'production-identity-citations-001.json.gz',dict(at=m.now(),citations=cs,read_only=True));print(json.dumps(dict(candidates=len(rows),artworks=len(state['artwork_ids']),citations=len(cs),source_hits=sum(len(v['source_hits'])for v in comparisons(rows,state)))),flush=True)
if __name__=='__main__':main()
