#!/usr/bin/env python3
"""Fresh read-only creator, title, inventory and native identity comparison."""
import importlib.util,json
from pathlib import Path
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
f=module('followup','museum-expansion-princeton-followup-supplement-20261008.py');i=module('identity','museum-expansion-princeton-identity-20261007.py')
m=f.m;RUN=f.RUN;IID=f.d.IID;ref=f.ref;checked=f.d.checked;i.RUN=RUN;i.i.RUN=RUN
original_terms=i.i.search_terms
def terms(facts):
    out=set(original_terms(facts))
    # Native Nainsukh of Basohli also occurs as the established mononym.
    if any('nainsukh' in (v or '').casefold() for v in facts.get('identity_creator_labels',[])):out.add('nainsukh')
    return sorted(out)
i.i.search_terms=terms
params_for=i.params_for;queries=i.queries;comparisons=i.comparisons
def main():
    candidate=RUN/'native-candidates-001.json.gz';dest=RUN/'native-identity-001.json.gz';assert not dest.exists();x=m.load(candidate)
    for dep in x['dependencies']:checked(dep)
    rows=x['rows'];p=params_for(rows)
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');state=queries(db,p);cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
    cmp=comparisons(rows,state)
    m.save(dest,dict(at=m.now(),candidate_reference=ref(candidate),query_reference=ref(Path(__file__).resolve()),query_references=[ref(Path(i.__file__).resolve()),ref(Path(i.i.__file__).resolve())],params=p,state=state,comparisons=cmp,read_only=True))
    m.save(RUN/'identity-citations-001.json.gz',dict(at=m.now(),identity_reference=ref(dest),selected_ids=state['artwork_ids'],citations=cs,read_only=True))
    print(json.dumps(dict(counts={k:len(v) for k,v in state.items()},citations=len(cs))),flush=True)
if __name__=='__main__':main()
