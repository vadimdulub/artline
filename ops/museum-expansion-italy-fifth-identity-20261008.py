"""Refresh the three pending museums against the actual post-wave75 catalogue."""
import importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
start=module('start','museum-expansion-italy-fifth-start-20261008.py');s=module('s','museum-expansion-italy-fourth-supplement-v2-20261008.py');i=s.i;f=i.f;m=start.m;RUN=start.RUN;SOURCE=s.RUN;ref=start.ref;checked=start.checked;prior=start.prior
TARGETS=['68c4a112-471f-538b-ba93-e45f76fcda8b','519972f3-9f4a-495f-abd2-80c6e53803fd','9f564ccc-072e-59fd-8aa8-eb1d96eda269']
def rows():return [v for v in s.rows() if v['institution_id'] in TARGETS]
queries=s.queries;comparisons=s.comparisons

def main():
 dest=RUN/'selected-identity-001.json.gz';assert not dest.exists();cont=m.load(RUN/'continuation-001.json');assert cont['verified_new']==135;rs=rows();params=i.params_for(rs)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';initial=m.load(RUN/'initial-scope-001.json.gz');assert i.snapshot(db,initial['scoped_ids'])==initial['snapshot'];state=queries(db,params)
  cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 print(json.dumps(dict(query_scope=len(state['artwork_ids']),citations=len(cs))),flush=True)
 comps=comparisons(rs,state);m.save(dest,dict(at=m.now(),rows=rs,params=params,state=state,comparisons=comps,within_batch=i.within_batch(rs),script_reference=ref(Path(__file__).resolve()),base_script_reference=ref(Path(s.__file__).resolve()),dependencies=[ref(SOURCE/n) for n in ['native-candidates-002.json.gz','source-editorial-working-002.json','comparison-source-context-001.json.gz']],read_only=True,policy='All candidate objects from the three pending museums; not approvals. Fresh post-wave75 comparisons, historical maker/title aliases and comparison-only Florence/Lucca scopes. Full source and physical-object checks required.'))
 m.save(RUN/'selected-citations-001.json.gz',dict(at=m.now(),identity_reference=ref(dest),citations=cs,read_only=True));print(json.dumps(dict(candidates=len(rs),hits=sum(len(v['hits']) for v in comps),source_hits=sum(len(v['source_hits']) for v in comps))),flush=True)
if __name__=='__main__':main()
