"""Read-only institution/source/creator/title reconciliation for selected Kazantzakis records."""
import difflib,importlib.util,json,re,time
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-kazantzakis-facts-20261009.py');q=module('q','museum-expansion-royal-identity-base-20261009.py');prod=module('prod','catalogue-expansion-20261008.py');s=f.s;m=f.m;RUN=f.RUN;q.RUN=RUN
TERMS={'hughey','kirk hughey','hans erni','hans enri','anemoyannis','anemoyiannis','anemogiannis','ανεμογιάνν','ανεμογιαν'}
def params(rows):
 titles={'odyssey','odyssey illustration','costume design','the barber of baghdad','madama butterfly','countess maritza','un ballo in maschera','the beggar student','anna of the thousand days','nikos kazantzakis a biography from his letters'};urls=set()
 for r in rows:
  v=r['facts'];titles.add(m.norm(v['title']));urls.update(v['native_page_urls'])
 return dict(patterns=['%'+t+'%'for t in sorted(TERMS)],raw_patterns=['%'+t+'%'for t in sorted(TERMS)],title_keys=sorted(titles),inventories=[],source_urls=sorted(urls),qids=[],native_object_ids=[],source_ids=[r['source_id']for r in rows])

def base_queries(db,p):
 # Inspectable one-off reconciliation: one regex scan replaces100+ ILIKE tests per row.
 raw_labels=[r['facts']['creator_label'] for r in f.rows() if r['facts']['creator_label'] and 'γνωστο'not in m.norm(r['facts']['creator_label'])]
 pattern='|'.join(re.escape(t)for t in sorted({x.strip('%')for x in p['patterns']}|set(raw_labels)))
 plans={};timings={}
 def query(key,sql,args):
  plans[key]=db.execute('EXPLAIN (FORMAT JSON) '+sql,args).fetchone();start=time.monotonic();result=db.execute(sql,args).fetchall();timings[key]=dict(seconds=round(time.monotonic()-start,3),rows=len(result));print(json.dumps(dict(query=key,**timings[key])),flush=True);return result
 artists=query('artists','SELECT id::text,display_name,normalized_name,slug,birth_year,death_year FROM artists WHERE normalized_name LIKE ANY(%s) OR display_name ~* %s ORDER BY id',(p['patterns'],pattern))
 aliases=query('aliases','SELECT aa.artist_id::text,aa.alias,a.display_name FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias LIKE ANY(%s) OR aa.alias ~* %s ORDER BY aa.artist_id,aa.alias',(p['patterns'],pattern))
 ids=sorted({a['id']for a in artists}|{a['artist_id']for a in aliases});aids=query('artist_works','SELECT DISTINCT artwork_id::text FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]) ORDER BY artwork_id LIMIT100001'.replace('LIMIT100001','LIMIT 100001'),(ids,));assert len(aids)<=100000
 unlinked=query('unlinked_creators','SELECT id::text FROM artworks WHERE unlinked_creator_label ~* %s ORDER BY id LIMIT 20001',(pattern,));assert len(unlinked)<=20000
 exact=query('exact_titles','SELECT id::text FROM artworks WHERE normalized_title=ANY(%s) ORDER BY id LIMIT 20001',(p['title_keys'],));assert len(exact)<=20000
 scoped=m.load(RUN/'production-initial-scope-001.json.gz')['scoped_ids']
 inv=query('scoped_inventory','SELECT id::text FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s) ORDER BY id',(s.IID,p['inventories']))
 cites=query('source_urls',"SELECT entity_id::text,source_url,field_name FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) ORDER BY entity_id,source_url,field_name",(p['source_urls'],))
 external=query('external_urls',"SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) ORDER BY entity_id,scheme,external_id",(p['source_urls'],))
 workids=sorted({v.get('artwork_id',v.get('id'))for v in aids+unlinked+exact+inv}|{v['entity_id']for v in cites+external}|set(scoped));assert len(workids)<=120000
 arts=query('bounded_artworks','SELECT '+q.ARTCOLS+' FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(workids,));links=query('bounded_artist_links','SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(workids,))
 return dict(artists=artists,aliases=aliases,artworks=arts,links=links,source_hits=cites,external_hits=external,artist_ids=ids,artwork_ids=workids,query_plans=plans,query_timings=timings,query_limitation='One-time bounded research snapshot, not a10million-row performance proof. Unlinked creator reconciliation still scans the catalogue; no schema/index changes made.')
def queries(db,p):
 state=base_queries(db,p);scoped=m.load(RUN/'production-initial-scope-001.json.gz')['scoped_ids'];ids=p['source_ids']
 ex=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND scheme='searchculture-edm' AND external_id=ANY(%s) ORDER BY entity_id,scheme,external_id",(ids,)).fetchall()
 cites=db.execute("SELECT entity_id::text,source_url,field_name,source_record_id FROM citations WHERE entity_type='artwork' AND source_record_id=ANY(%s) AND source_url LIKE 'https://www.searchculture.gr/%%' ORDER BY entity_id,source_url,field_name",(ids,)).fetchall();state['source_hits']+=cites
 extra=sorted((set(scoped)|{v['entity_id']for v in ex+cites})-set(state['artwork_ids']));state['artworks']+=db.execute('SELECT '+q.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(extra,)).fetchall();state['artwork_ids']=sorted(set(state['artwork_ids'])|set(extra));state['artworks'].sort(key=lambda v:v['id']);state['links']+=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(extra,)).fetchall();state['links'].sort(key=lambda v:(v['artwork_id'],v['artist_id']));state.update(scoped_ids=scoped,native_id_hits=ex);return state

def comparisons(rows,state):
 cached=[(a,{v for v in [m.norm(a['title']),m.norm(a['alternate_title'])]if v})for a in state['artworks']];out=[]
 for row in rows:
  v=row['facts'];tt={m.norm(t)for t in v['titles']}|{m.norm(v['title'].split('[')[0])}|{m.norm(t)for t in re.findall(r'\[([^\]]+)\]',v['title'])};tt.discard('');assert tt;hits=[];urls=set(v['native_page_urls'])
  for a,at in cached:
   reasons=[];sim=0
   if tt&at:reasons.append('exact_title');sim=1
   if v['inventory'] and a['accession_number'] and f.invkey(a['accession_number'])==f.invkey(v['inventory']):reasons.append('inventory')
   for t in tt:
    for u in at:
     matcher=difflib.SequenceMatcher(None,t,u)
     if matcher.real_quick_ratio()>=.8 and matcher.quick_ratio()>=.8:sim=max(sim,matcher.ratio())
   if sim>=.8:reasons.append('similar_title')
   if reasons:hits.append(dict(a,hit_types=reasons,same_museum=a['id']in state['scoped_ids'],title_similarity=round(sim,4)))
  sources=[c for c in state['source_hits']+state['external_hits']+state['native_id_hits']if(c.get('source_url')or c.get('canonical_url')or'').rstrip('/')in{u.rstrip('/')for u in urls}or c.get('external_id')==row['source_id']or c.get('source_record_id')==row['source_id']]
  out.append(dict(number=row['number'],source_id=row['source_id'],hits=hits,source_hits=sources))
 return out
def main():
 rows=f.rows();p=params(rows)
 with prod.connect()as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');initial=m.load(RUN/'production-initial-scope-001.json.gz');assert s.snapshot(db,initial['scoped_ids'])==initial['snapshot'];state=queries(db,p);cs=[v['row']for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 comp=comparisons(rows,state);m.save(RUN/'production-identity-001.json.gz',dict(at=m.now(),rows=rows,params=p,state=state,comparisons=comp,source_reference=s.ref(RUN/'candidate-facts-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),read_only=True));m.save(RUN/'production-identity-citations-001.json.gz',dict(at=m.now(),citations=cs,read_only=True));print(json.dumps(dict(candidates=len(rows),artworks=len(state['artwork_ids']),citations=len(cs),source_hits=sum(len(v['source_hits'])for v in comp))),flush=True)
if __name__=='__main__':main()
