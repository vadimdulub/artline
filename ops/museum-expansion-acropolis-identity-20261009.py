"""Bounded Acropolis inventory/source/title/creator reconciliation; all queries read-only."""
import difflib,importlib.util,json,re
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-acropolis-facts-20261009.py');q=module('q','museum-expansion-royal-identity-base-20261009.py');prod=module('prod','catalogue-expansion-20261008.py');s=f.s;m=f.m;RUN=f.RUN;q.RUN=RUN
NAMES={'calf bearer','moschophoros','peplos kore','kore in a peplos','antenor kore','euthydikos kore','euthydicus kore','euthydikos','blond boy','blonde boy','kore from chios','chiot kore','kore with almond eyes','lyon kore','pensive athena','mourning athena','lenormant relief','lenormant trireme relief','kore 674','kore 675','kore 679','kore 670','kore 672','kore 685','kore 684','acro 670','kritios boy'}
def params(rows):
 titles=set(NAMES);inv=set();urls=set();terms={'antenor','praxiteles','kalamis','calamis','leochare','kresila','alcamene','alkamene','kritios','kritias','nesiotes','phaidimo','phaimo','archermo','archermu','sculpture ancient greek'}
 for r in rows:
  v=r['facts'];label=v['creator_label'];names=q.tokens(label)-{'sculptor','attic','ionic','attica','workshop','greek','unidentified','anonymous','roman','athenian','local','ancient','island','naxian','unknown','related','works','perhaps','probably','influence','influences'}
  terms|={w for w in names if len(w)>4};titles|={m.norm(v['title']),m.norm(v['title']).removeprefix('statue of a ')}
  titles|={m.norm(t)for t in re.findall(r'"([^"]+)"',v['title'])};inventory=v['inventory'];inv|={inventory,inventory.replace('Ακρ.','Acr.'),inventory.replace('Ακρ.','Akr.'),inventory.replace('Ακρ.','Acropolis'),inventory.replace('Ακρ.','') .strip()}
  for u in v['native_page_urls']:urls|={u,u.rstrip('/')+'/',u.replace('/en/','/'),u.replace('/en/','/el/')}
 return dict(patterns=['%'+t+'%'for t in sorted(terms)],raw_patterns=['%'+t+'%'for t in sorted(terms)],title_keys=sorted(titles),inventories=sorted(inv),source_urls=sorted(urls),qids=[],native_object_ids=[],source_ids=[r['source_id']for r in rows])
def queries(db,p):
 state=q.queries(db,p);scoped=[v['id']for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(s.IIDS,s.IIDS))]
 ex=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND scheme='acropolis-museum-object' AND external_id=ANY(%s) ORDER BY entity_id,scheme,external_id",(p['source_ids'],)).fetchall();ci=db.execute("SELECT entity_id::text,source_record_id,source_url,field_name FROM citations WHERE entity_type='artwork' AND source_record_id=ANY(%s) AND source_url LIKE 'https://www.theacropolismuseum.gr/%%' ORDER BY entity_id,source_record_id,source_url,field_name",(p['source_ids'],)).fetchall()
 extra=sorted((set(scoped)|{a['entity_id']for a in ex+ci})-set(state['artwork_ids']));state['artworks']+=db.execute('SELECT '+q.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(extra,)).fetchall();state['artwork_ids']=sorted(set(state['artwork_ids'])|set(extra));state['artworks'].sort(key=lambda v:v['id']);state['links']+=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(extra,)).fetchall();state['links'].sort(key=lambda v:(v['artwork_id'],v['artist_id']));state.update(scoped_ids=scoped,native_id_hits=ex,source_record_hits=ci);return state
def comparisons(rows,state):
 out=[]
 for row in rows:
  v=row['facts'];tt={m.norm(t)for t in v['titles']}|{m.norm(t)for t in re.findall(r'"([^"]+)"',v['title'])};hits=[];urls=set(v['native_page_urls'])
  for a in state['artworks']:
   at={m.norm(a['title']),m.norm(a['alternate_title'])};sim=max(difflib.SequenceMatcher(None,t,u).ratio()for t in tt for u in at);reasons=[]
   if tt&at:reasons.append('exact_title')
   if f.invkey(a['accession_number'])==f.invkey(v['inventory']):reasons.append('inventory')
   if sim>=.7:reasons.append('similar_title')
   if reasons:hits.append(dict(a,hit_types=reasons,same_museum=a['id']in state['scoped_ids'],title_similarity=round(sim,4)))
  sources=[c for c in state['source_hits']+state['external_hits']+state['native_id_hits']+state['source_record_hits']if(c.get('source_url')or c.get('canonical_url')or'').rstrip('/')in{u.rstrip('/')for u in urls}or(c.get('scheme')=='acropolis-museum-object'and c.get('external_id')==row['source_id'])]
  out.append(dict(number=row['number'],source_id=row['source_id'],hits=hits,source_hits=sources))
 return out
def main():
 rows=f.rows()[0];p=params(rows)
 with prod.connect()as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');initial=m.load(RUN/'production-initial-scope-001.json.gz');assert s.snapshot(db,initial['scoped_ids'])==initial['snapshot'];state=queries(db,p);cs=[v['row']for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 comp=comparisons(rows,state);m.save(RUN/'production-identity-001.json.gz',dict(at=m.now(),rows=rows,params=p,state=state,comparisons=comp,source_reference=s.ref(RUN/'candidate-facts-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),read_only=True));m.save(RUN/'production-identity-citations-001.json.gz',dict(at=m.now(),citations=cs,read_only=True));print(json.dumps(dict(candidates=len(rows),artworks=len(state['artwork_ids']),citations=len(cs),source_hits=sum(len(v['source_hits'])for v in comp))),flush=True)
if __name__=='__main__':main()
