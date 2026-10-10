"""Bounded source,creator,museum,inventory and title checks for80 selected native objects."""
import copy,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-southampton-facts-20261009.py');i=module('i','museum-expansion-italy-fourth-identity-v2-20261008.py');m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked;IID=f.IID;i.RUN=RUN;i.q.RUN=RUN;i.IIDS=[IID]
def terms(v):
 out=i.q.search_terms(v)
 if 'derby' in out:out+=['wright']
 if 'nuzi' in out:out+=['nuzzi']
 return sorted(set(out))
i.terms=terms
def comparison_rows(rows):
 out=copy.deepcopy(rows)
 for row in out:
  f=row['facts'];f['inventory']=';'.join([f['inventory']]+f['inventory_aliases'])
 return out
def params_for(rows):return i.params_for(comparison_rows(rows))
queries=i.queries
def comparisons(rows,state):return i.comparisons(comparison_rows(rows),state)
def main():
 dest=RUN/'native-identity-001.json.gz';assert not dest.exists();candidate=RUN/'native-candidates-001.json.gz';rows=m.load(candidate)['rows'];p=params_for(rows)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';state=queries(db,p);cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 print(json.dumps(dict(query_counts={k:len(v) for k,v in state.items()},citations=len(cs))),flush=True);comps=comparisons(rows,state)
 m.save(dest,dict(at=m.now(),rows=rows,candidate_reference=ref(candidate),params=p,state=state,comparisons=comps,within_batch=i.within_batch(comparison_rows(rows)),script_reference=ref(Path(__file__).resolve()),read_only=True,policy='All80 selected native objects including source holds. Exact original inventory remains catalogue fact; prefix-free and item/year versus year/item aliases are comparison-only. URL IDs never substitute for table inventory. Scores identify leads,not duplicate/maker approval. Full Southampton scope plus bounded creator,source,inventory and title lookups.'))
 m.save(RUN/'identity-citations-001.json.gz',dict(at=m.now(),identity_reference=ref(dest),citations=cs,read_only=True));print(json.dumps(dict(comparisons=len(comps),hits=sum(len(v['hits']) for v in comps),source_hits=sum(len(v['source_hits']) for v in comps))),flush=True)
if __name__=='__main__':main()
