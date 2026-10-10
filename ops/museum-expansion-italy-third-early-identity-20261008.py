"""Read-only identity research for the first completed institution capture."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-italy-third-identity-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
m=i.m;RUN=i.RUN
def main():
 dest=RUN/'oderzo-early-identity-001.json.gz';assert not dest.exists()
 rows,refs=i.f.build(False);rows=[r for r in rows if r['number']<=124]
 assert len(rows)==124 and all(r['institution_id']=='639ce135-5275-59aa-88ae-0deeaed377a2' for r in rows)
 candidates=[r for r in rows if r['state']=='candidate'];p=i.params_for(candidates)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';state=i.queries(db,p)
  citations=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 comps=i.comparisons(candidates,state)
 m.save(dest,dict(at=m.now(),rows=rows,params=p,state=state,comparisons=comps,within_batch=i.within_batch(candidates),citations=citations,source_references=[r for r in refs if int(Path(r['path']).name.split('-')[0])<=124],script_reference=i.ref(Path(__file__).resolve()),read_only=True,policy='Early research only while other museum captures complete. No additions approved. Full final identity and fresh transaction checks remain required.'))
 print(json.dumps(dict(candidates=len(candidates),artworks=len(state['artworks']),hit_pairs=sum(len(c['hits']) for c in comps),source_hits=sum(len(c['source_hits']) for c in comps))),flush=True)
if __name__=='__main__':main()
