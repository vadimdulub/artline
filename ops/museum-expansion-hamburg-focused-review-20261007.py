#!/usr/bin/env python3
"""Supplement broad identity leads with exact creator-authority/name comparisons, without writes."""
import collections,difflib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('x',Path(__file__).with_name('museum-expansion-hamburg-identity-20261007.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x);m=x.m;RUN=x.RUN;f=x.f
def main():
 source=RUN/'identity-scope-001.json.gz';scope=m.load(source);state=scope['state'];links=collections.defaultdict(list)
 for l in state['links']:links[l['artwork_id']].append(l)
 out=[]
 for row in scope['rows']:
  facts=row['facts'];qid=facts.get('creator_qid');names={m.norm(v) for v in [facts['creator_label']]+facts['identity_creator_labels']}
  ids={r['entity_id'] for r in scope['creator_authorities'] if qid and r['external_id']==qid}
  ids|={r['id'] for r in state['artists'] if m.norm(r['display_name']) in names}
  ids|={r['artist_id'] for r in state['aliases'] if m.norm(r['alias']) in names}
  pool=[]
  for art in state['artworks']:
   if not (ids&{l['artist_id'] for l in links[art['id']]} or m.norm(art['unlinked_creator_label']) in names):continue
   v=dict(art,artist_links=links[art['id']]);v['title_similarity']=max((difflib.SequenceMatcher(None,m.norm(t),m.norm(art[k])).ratio() for t in facts['titles'] for k in ['title','alternate_title'] if art.get(k)),default=0);pool.append(v)
  out.append(dict(source_id=row['source_id'],creator_qid=qid,authority_or_exact_name_ids=sorted(ids),creator_pool_ids=[a['id'] for a in pool],top=sorted(pool,key=lambda a:a['title_similarity'],reverse=True)[:15]))
 m.save(RUN/'identity-focused-comparisons-001.json.gz',dict(at=m.now(),scope_reference=f.ref(source),records=out,policy='Supplementary exact authority/full-name comparison; broad surname, source-ID, inventory and generic-title leads remain in the prior artifact. No absence-of-duplicate approval is implied.'))
 print('Focused comparisons',len(out),flush=True)
if __name__=='__main__':main()
