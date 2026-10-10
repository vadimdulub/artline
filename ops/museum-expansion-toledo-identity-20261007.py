#!/usr/bin/env python3
"""Read-only source identity and creator/title/inventory scopes for selected Toledo objects."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-toledo-web-20261007.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('museum-expansion-courtauld-identity-20261007.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
m=w.m;RUN=w.RUN;IID=w.d.IID;base.RUN=RUN;base.IID=IID
def params_for(rows):return base.params_for(rows)
def queries(db,params):return base.queries(db,params)
def main():
 source=RUN/'native-candidates-003.json.gz';rows=[r for r in m.load(source)['rows'] if r['state']=='candidate'];params=params_for(rows)
 with m.connect() as db:state=queries(db,params)
 m.save(RUN/'native-identity-001.json.gz',dict(at=m.now(),candidate_reference=w.ref(source),params=params,state=state,policy='Read-only creator, alias, exact-title, inventory and native-URL comparisons. Names and similarity are discovery leads only.'))
 comparisons=base.comparisons(rows,state)
 m.save(RUN/'native-comparisons-001.json.gz',dict(at=m.now(),records=comparisons));print(json.dumps(dict(candidates=len(rows),scopes={k:len(v) for k,v in state.items()})),flush=True)
if __name__=='__main__':main()
