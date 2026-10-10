"""Current scoped comparison for pending Verbania object identities."""
import collections,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-verbania-source-20261008.py');i=module('i','museum-expansion-italy-fourth-identity-v2-20261008.py');m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked;i.IIDS=[s.IID];i.RUN=RUN;i.q.RUN=RUN
def rows():
 out=[]
 for r in m.load(RUN/'source-context-001.json.gz')['rows']:
  g=s.graph(r);root=g[r['root']];a=r['artwork'];inv=sorted(set().union(*(g[u][s.CD+'inventoryIdentifier'] for u in root[s.CD+'hasInventorySituation'])));titles=sorted(root[s.CD+'title']|root[s.CD+'subject']|{a['title']});creator=a['unlinked_creator_label'];f=dict(source_id=r['source_id'],source_url=r['source_url'],title=a['title'],titles=titles,creator_label=creator,inventory='; '.join(inv),date_display=next(iter(root[s.DC+'date'])),source_fields={'ATTRIBUZIONI':creator},native_page_urls=[],native_metadata_urls=[r['root']])
  out.append(dict(number=r['number'],source_id=r['source_id'],institution_id=s.IID,facts=f,existing_artwork_id=a['id']))
 return out
def main():
 dest=RUN/'identity-001.json.gz';assert not dest.exists();rs=rows();p=i.params_for(rs)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');initial=m.load(RUN/'initial-scope-001.json.gz');assert s.snapshot(db,initial['scoped_ids'])==initial['snapshot'];state=i.queries(db,p)
  cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 comps=i.comparisons(rs,state);m.save(dest,dict(at=m.now(),rows=rs,params=p,state=state,comparisons=comps,within_batch=i.within_batch(rs),script_reference=ref(Path(__file__).resolve()),base_script_reference=ref(Path(i.__file__).resolve()),source_reference=ref(RUN/'source-context-001.json.gz'),read_only=True));m.save(RUN/'identity-citations-001.json.gz',dict(at=m.now(),identity_reference=ref(dest),citations=cs,read_only=True));print(json.dumps(dict(scope=len(state['artwork_ids']),comparisons=len(comps),hits=sum(len(v['hits']) for v in comps),citations=len(cs))),flush=True)
if __name__=='__main__':main()
