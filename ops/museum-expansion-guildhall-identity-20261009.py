"""Bounded current Guildhall,creator,source and exact-title identity comparisons."""
import importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-guildhall-facts-20261009.py');i=module('i','museum-expansion-italy-fourth-identity-v2-20261008.py');m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked;IID=f.IID;i.RUN=RUN;i.q.RUN=RUN;i.IIDS=[IID]
def terms(facts):
 base=i.q.search_terms(facts);aliases={'nouy':['lecomte'],'moller':['moeller'],'nebot':['nebot'],'waggoner':['waggoner','waggener'],'griffier':['griffier'],'herbert':['herbert']}
 for t in list(base):base+=aliases.get(t,[])
 return sorted(set(base))
i.terms=terms;params_for=i.params_for;queries=i.queries

def main():
 dest=RUN/'native-identity-001.json.gz';assert not dest.exists();candidate=RUN/'native-candidates-001.json.gz';rows=m.load(candidate)['rows'];p=params_for(rows)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';state=queries(db,p);cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 print(json.dumps(dict(query_counts={k:len(v) for k,v in state.items()},citations=len(cs))),flush=True);comps=i.comparisons(rows,state)
 m.save(dest,dict(at=m.now(),rows=rows,candidate_reference=ref(candidate),params=p,state=state,comparisons=comps,within_batch=i.within_batch(rows),script_reference=ref(Path(__file__).resolve()),read_only=True,policy='All36 selected publisher records including unknown-date/modern holds. Scores are discovery only. Full museum and bounded creator/source/title scopes; accession remains absent rather than fabricated.'))
 m.save(RUN/'identity-citations-001.json.gz',dict(at=m.now(),identity_reference=ref(dest),citations=cs,read_only=True));print(json.dumps(dict(comparisons=len(comps),hits=sum(len(v['hits']) for v in comps),source_hits=sum(len(v['source_hits']) for v in comps))),flush=True)
if __name__=='__main__':main()
