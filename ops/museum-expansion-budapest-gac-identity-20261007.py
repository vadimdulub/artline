#!/usr/bin/env python3
"""Read-only creator/object identity comparisons for the Budapest partner selection."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-budapest-gac-facts-20261007.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-courtauld-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
m=w.m;RUN=w.RUN;IID=w.d.IID;i.RUN=RUN;i.IID=IID
def params_for(rows):
 params=i.params_for(rows);urls=set(params['source_urls'])
 for row in rows:
  for url in row['facts']['native_external_links']:
   for protocol in ['http:','https:']:
    u=url.replace('http:',protocol).replace('https:',protocol);urls.update([u.rstrip('/'),u.rstrip('/')+'/'])
 params['source_urls']=sorted(urls);return params
def queries(db,params):return i.queries(db,params)
def main():
 source=RUN/'gac-candidates-001.json.gz';rows=[r for r in m.load(source)['rows'] if r['state']=='candidate'];params=params_for(rows)
 with m.connect() as db:state=queries(db,params)
 m.save(RUN/'gac-identity-001.json.gz',dict(at=m.now(),candidate_reference=w.ref(source),params=params,state=state,policy='Read-only creator-scoped and exact title/inventory/source URL comparison. Names and similarities are leads, not approvals.'))
 comps=i.comparisons(rows,state)
 # Include museum-native external links as exact identity leads as well.
 for row,cmp in zip(rows,comps):
  urls={u.replace('http:','https:').rstrip('/') for u in row['facts']['native_external_links']}
  cmp['native_url_hits']=[h for h in state['source_hits'] if h['source_url'].replace('http:','https:').rstrip('/') in urls]+[h for h in state['external_hits'] if h['canonical_url'] and h['canonical_url'].replace('http:','https:').rstrip('/') in urls]
 m.save(RUN/'gac-comparisons-001.json.gz',dict(at=m.now(),records=comps));print(json.dumps({k:len(v) for k,v in state.items()}),flush=True)
if __name__=='__main__':main()
