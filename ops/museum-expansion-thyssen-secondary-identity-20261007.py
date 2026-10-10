#!/usr/bin/env python3
"""Read-only bounded multilingual duplicate leads; no secondary metadata import."""
import collections,copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-thyssen-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);m=i.m;f=i.f;RUN=i.RUN
def checked(ref):
 p=m.ROOT/ref['path'];assert f.ref(p)==ref;return m.load(p)
def rows():
 source=RUN/'native-candidates-002.json.gz';original=m.load(source)['rows'];urls=collections.defaultdict(set);entities={};refs=[]
 for ref in m.load(RUN/'wikidata-url-crosswalk-001.json.gz')['batches']:
  b=checked(ref);assert 'error' not in b;refs.append(ref)
  for r in b['rows']:urls[r['url']].add(r['item'].rsplit('/',1)[-1])
 for ref in m.load(RUN/'wikidata-capture-001.json.gz')['batches']:
  b=checked(ref);refs.append(ref);entities.update(b['entities'])
 result=[]
 for row in original:
  if 'facts' not in row:continue
  r=copy.deepcopy(row);v=r['facts'];qids=sorted({qid for url in v['native_page_urls'] for qid in urls[url]});titles=[]
  for qid in qids:
   e=entities[qid]
   titles.extend(x['value'] for lang,x in e['labels'].items() if lang in ['en','es','fr','de','it','nl','ru','pt'])
   titles.extend(x['value'] for lang,vals in e['aliases'].items() if lang in ['en','es','fr','de','it','nl','ru','pt'] for x in vals)
  v['titles']=list(dict.fromkeys(v['titles']+titles));v['wikidata_ids']=qids
  r['secondary_identity_only']=dict(qids=qids,added_titles=titles,policy='Exact native URL crosswalk remains an identity lead, never an import fact or source precedence decision.')
  result.append(r)
 return result,refs
def main():
 rr,refs=rows();p=i.params(rr)
 with m.connect() as db:state=i.queries(db,p)
 dest=RUN/'identity-scope-003.json.gz';m.save(dest,dict(at=m.now(),rows=rr,params=p,state=state,candidate_reference=f.ref(RUN/'native-candidates-002.json.gz'),secondary_references=refs,reviewer_reference=f.ref(Path(__file__).resolve()),policy='Secondary titles/QIDs extend identity search only; native original facts remain separately pinned.'))
 cm=i.comparisons(rr,state);m.save(RUN/'identity-comparisons-003.json.gz',dict(at=m.now(),records=cm,scope_reference=f.ref(dest)))
 print(json.dumps(dict(rows=len(rr),secondary_rows=sum(bool(r['facts']['wikidata_ids']) for r in rr),counts={k:len(v) for k,v in state.items()})),flush=True)
if __name__=='__main__':main()
