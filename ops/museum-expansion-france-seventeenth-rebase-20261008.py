"""Capture concurrent changes after the original transaction safely rolled back."""
import collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-seventeenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def changes(before,after):
 b=collections.Counter(json.dumps(v,sort_keys=True) for v in before);c=collections.Counter(json.dumps(v,sort_keys=True) for v in after)
 return dict(removed=[json.loads(x) for x in (b-c).elements()],added=[json.loads(x) for x in (c-b).elements()])
def main():
 p,digest=a.validate_plan();ix=m.load(a.r.IDENTITY);ci=m.load(a.r.CITATIONS)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
  before=a.snapshot(db,p['scoped_ids']);counts=a.counts(db);prior=a.prior_state(db,p['prior_ids'])
  assert counts==p['before_counts'] and prior==p['prior_state']
  assert a.snapshot(db,m.load(a.RUN/'initial-scope-001.json.gz')['scoped_ids'])==m.load(a.RUN/'initial-scope-001.json.gz')['snapshot']
  state=a.r.identity.base.queries(db,ix['params'])
  citations=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 delta={}
 for key in state:
  if state[key]!=ix['state'][key]:delta[key]=changes(ix['state'][key],state[key])
 new=dict(at=m.now(),original_plan_reference=a.reference(a.PLAN),original_identity_reference=a.reference(a.r.IDENTITY),params=ix['params'],state=state,citations=citations,scoped_ids=p['scoped_ids'],before=before,counts=counts,prior_state=prior,identity_state_changes=delta,citation_changes=changes(ci['citations'],citations),protected_snapshot_changes={k:changes(p['before'][k],v) for k,v in before.items() if p['before'][k]!=v},database_writes=0)
 dest=a.RUN/'concurrent-state-rebase-001.json.gz';assert not dest.exists();m.save(dest,new)
 print(json.dumps(dict(reference=a.reference(dest),state_changes={k:{s:len(v) for s,v in x.items()} for k,x in delta.items()},citation_changes={k:len(v) for k,v in new['citation_changes'].items()},state_differences=delta),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
