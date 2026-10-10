#!/usr/bin/env python3
"""Expose surname spelling/alias variants already inside the read-only scope."""
import collections,difflib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-thyssen-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);m=i.m;f=i.f;RUN=i.RUN
def build(scope):
 state=scope['state'];links=collections.defaultdict(list)
 for a in state['links']:links[a['artwork_id']].append(a)
 out=[]
 for row in scope['rows']:
  v=row['facts'];terms=[p.strip('%') for p in i.params([row])['patterns']+i.params([row])['raw_patterns']];ids={a['id'] for a in state['artists'] if any(t in m.norm(a['display_name']) or t in a['display_name'].lower() for t in terms)}|{a['artist_id'] for a in state['aliases'] if any(t in m.norm(a['alias']) or t in a['alias'].lower() for t in terms)};pool=[]
  for a in state['artworks']:
   if not(ids&{x['artist_id'] for x in links[a['id']]} or any(t in m.norm(a['unlinked_creator_label']) or t in (a['unlinked_creator_label'] or '').lower() for t in terms)):continue
   score=max((difflib.SequenceMatcher(None,m.norm(t),m.norm(a[k])).ratio() for t in v['titles'] for k in ['title','alternate_title'] if a.get(k)),default=0)
   pool.append(dict(a,artist_links=links[a['id']],title_similarity=score))
  out.append(dict(source_id=row['source_id'],expanded_artist_ids=sorted(ids),expanded_pool_ids=sorted(a['id'] for a in pool),expanded_top=sorted(pool,key=lambda a:a['title_similarity'],reverse=True)[:25]))
 return out
def main():
 source=RUN/'identity-scope-003.json.gz';scope=m.load(source);records=build(scope);m.save(RUN/'identity-expanded-comparisons-001.json.gz',dict(at=m.now(),records=records,scope_reference=f.ref(source),reviewer_reference=f.ref(Path(__file__).resolve()),policy='Substring spelling/alias discovery, matching the already queried creator scope. Expands Stom/Stomer and equivalent candidate spellings; every match is a review lead, never artist or artwork identity approval.'))
 print('Expanded comparisons',len(records),flush=True)
if __name__=='__main__':main()
