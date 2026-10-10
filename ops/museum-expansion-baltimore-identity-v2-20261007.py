#!/usr/bin/env python3
"""Expanded creator discovery using primary-source aliases; no catalogue writes."""
import copy, importlib.util, json
from pathlib import Path
s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('museum-expansion-baltimore-identity-20261007.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
m=base.m;f=base.f;RUN=base.RUN;ref=base.ref
ALIASES={4:['Bernardino Passeri','Antonius Wierx'],9:['Diana Scultori','Diana Ghisi','Diana Mantovana','Diana Scultore','Diana Sculptor','Diana Scultor','Diane de Mantoue']}
def rows():
 out=copy.deepcopy(m.load(RUN/'native-candidates-001.json.gz')['rows'])
 for r in out:r['facts']['identity_creator_labels']+=ALIASES.get(r['number'],[])
 return out
def main():
 rs=rows();p=base.params_for(rs)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');state=base.queries(db,p)
  cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 dest=RUN/'native-identity-002.json.gz';assert not dest.exists()
 m.save(dest,dict(at=m.now(),candidate_reference=ref(RUN/'native-candidates-001.json.gz'),query_reference=ref(Path(__file__).resolve()),base_query_reference=ref(Path(base.__file__).resolve()),alias_primary_references=[ref(RUN/'version-web-001.json'),ref(RUN/'version-web-002.json')],aliases=ALIASES,params=p,state=state,comparisons=base.comparisons(rs,state),read_only=True,policy='Getty ULAN 500018707 supplies Diana variants; MSK Gent 2014-F supplies Passeri and Wierx spelling. Discovery only: preserve the literal Baltimore attribution and do not create or link painter authorities.'))
 m.save(RUN/'identity-citations-002.json.gz',dict(at=m.now(),identity_reference=ref(dest),selected_ids=state['artwork_ids'],citations=cs,read_only=True))
 print(json.dumps(dict(counts={k:len(v) for k,v in state.items()},citations=len(cs))),flush=True)
if __name__=='__main__':main()
