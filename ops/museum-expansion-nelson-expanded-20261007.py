#!/usr/bin/env python3
"""Expand review using literal short-name variants in the retained identity scope."""
import collections,difflib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-nelson-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);f=i.f;m=i.m;RUN=i.RUN
NAMES={1:['George Ault'],2:['George Ault'],3:['George Ault'],6:['Gifford Beal'],7:['Gifford Beal'],8:['George Bellows'],9:['George Bellows'],10:['George Bellows'],62:['Willem van de Velde the Younger','William van de Velde the Younger'],64:['Joachim Wtewael'],133:['Guercino'],134:['Guercino'],140:['Canaletto'],143:['Giovanni Benedetto Castiglione'],144:['Bernardo Cavallino','Johann Heinrich Schönfeld'],145:['Giuseppe Cesari'],151:['Tanzio da Varallo'],157:['Herri met de Bles'],165:['Jan Gossaert'],182:['El Greco'],183:['El Greco'],184:['El Greco']}
def build():
 scope=m.load(RUN/'identity-scope-002.json.gz');state=scope['state'];links=collections.defaultdict(list)
 for l in state['links']:links[l['artwork_id']].append(l)
 out=[]
 for r in scope['rows']:
  num=r['number']
  if num not in NAMES:continue
  names={m.norm(n) for n in NAMES[num]};ids={a['id'] for a in state['artists'] if m.norm(a['display_name']) in names}|{a['artist_id'] for a in state['aliases'] if m.norm(a['alias']) in names}
  rows=[]
  for a in state['artworks']:
   if not (ids&{x['artist_id'] for x in links[a['id']]} or m.norm(a['unlinked_creator_label']) in names):continue
   score=max(difflib.SequenceMatcher(None,m.norm(t),m.norm(a[k])).ratio() for t in r['facts']['titles'] for k in ['title','alternate_title'] if a.get(k))
   rows.append(dict(a,artist_links=links[a['id']],title_similarity=score))
  out.append(dict(number=num,source_id=r['source_id'],search_labels=NAMES[num],artist_ids=sorted(ids),pool=sorted(rows,key=lambda a:(-a['title_similarity'],a['id']))))
 return out
if __name__=='__main__':
 rows=build();m.save(RUN/'expanded-comparisons-001.json.gz',dict(at=m.now(),rows=rows,scope_reference=f.ref(RUN/'identity-scope-002.json.gz'),script_reference=f.ref(Path(__file__).resolve()),policy='Review-only short-name variants expand focused comparisons inside retained scope; current qualified source creators stay unchanged and no artist links are made.'))
 for r in rows:
  print(r['number'],'pool',len(r['pool']), '|', ' ; '.join(a['id']+' '+a['title']+' '+str(a['date_display'])+' '+str(a['medium_text'])+' '+str(a['dimensions_text']).replace('\n',' ') for a in r['pool'][:5]))
