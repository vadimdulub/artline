"""Fresh museum, creator-alias, title, source-ID and inventory comparison."""
import importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-glasgow-facts-20261009.py');i=module('i','museum-expansion-italy-fourth-identity-v2-20261008.py');m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked;i.RUN=RUN;i.q.RUN=RUN;i.IIDS=f.s.IIDS;i.terms=i.q.search_terms
rows=lambda:f.rows()[0]
queries=i.queries;comparisons=i.comparisons

def params(rs):
 p=i.params_for(rs);p['qids']=sorted(r['source_id'] for r in rs);return p

def main():
 dest=RUN/'identity-001.json.gz';assert not dest.exists();rs=rows();p=params(rs)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');initial=m.load(RUN/'initial-scope-001.json.gz');assert f.s.snapshot(db,initial['scoped_ids'])==initial['snapshot'];state=queries(db,p);cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 print(json.dumps(dict(scope=len(state['artwork_ids']),citations=len(cs))),flush=True);comps=comparisons(rs,state);m.save(dest,dict(at=m.now(),rows=rs,params=p,state=state,comparisons=comps,within_batch=i.within_batch(rs),script_reference=ref(Path(__file__).resolve()),source_reference=ref(RUN/'candidate-facts-001.json.gz'),read_only=True));m.save(RUN/'identity-citations-001.json.gz',dict(at=m.now(),identity_reference=ref(dest),citations=cs,read_only=True));print(json.dumps(dict(comparisons=len(comps),hits=sum(len(v['hits']) for v in comps))),flush=True)
if __name__=='__main__':main()
