#!/usr/bin/env python3
"""Read-only supplementary title/creator comparisons; no catalogue writes."""
import importlib.util,re,collections,difflib
s=importlib.util.spec_from_file_location('i','ops/museum-expansion-birmingham-identity-20261007.py');i=importlib.util.module_from_spec(s);s.loader.exec_module(i);m=i.m
rows=[r for r in m.load(i.RUN/'native-candidates-002.json.gz')['rows'] if r['state']=='candidate'];st=m.load(i.RUN/'native-identity-002.json.gz')['state'];links=collections.defaultdict(list)
for x in st['links']:links[x['artwork_id']].append(x)
stop={'american','scottish','french','british','english','italy','florence','dutch','flemish','netherlands','spain','german','germany','austrian','danish','irish','scotland','france','states','united','japan','china','tibet','unknown','artist','possibly','formerly','active','attributed','workshop','and'}
outs=[]
for r in rows:
 f=r['facts'];terms=set(i.search_terms(f))
 terms={t for t in terms if t not in stop and not t.isnumeric() and not re.match(r'^\d',t)}
 ids={a['id'] for a in st['artists'] if i.tokens(a['display_name'])&terms}|{a['artist_id'] for a in st['aliases'] if i.tokens(a['alias'])&terms}
 pool=[a for a in st['artworks'] if ids&{x['artist_id'] for x in links[a['id']]} or i.tokens(a['unlinked_creator_label'])&terms]
 leads=[]
 for a in pool:
  score=max((difflib.SequenceMatcher(None,m.norm(t),m.norm(a[k])).ratio() for t in f['titles'] for k in ['title','alternate_title'] if a.get(k)),default=0)
  if score>=.62:leads.append(dict(a,creators=[x['display_name'] for x in links[a['id']]],score=round(score,3)))
 outs.append(dict(source_id=f['source_id'],filtered_terms=sorted(terms),pool_ids=sorted(x['id'] for x in pool),leads=sorted(leads,key=lambda a:-a['score'])))
 if leads:
  print('\n'+f['source_id']+' | '+f['creator_label']+' | '+str(f['date_display']))
  for a in sorted(leads,key=lambda a:-a['score'])[:15]:print(a['id'],a['title'],a['date_display'],a['medium_text'],a['dimensions_text'],a['accession_number'],a['creators'],a['unlinked_creator_label'],a['score'])
m.save(i.RUN/'native-filtered-comparisons-002.json.gz',dict(at=m.now(),records=outs,policy='Supplementary same-name comparison removes nationality/year tokens from the broader pinned identity scope; all original scope and leads retained. Not an automatic identity approval.'))
