#!/usr/bin/env python3
"""Museum-connected works from the verified Armenian/Georgian authority roster."""
import importlib.util,json,collections
from pathlib import Path
from urllib.parse import urlencode
spec=importlib.util.spec_from_file_location('session',Path(__file__).with_name('research-armenian-georgian-session.py'));s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
spec=importlib.util.spec_from_file_location('catalogue',Path(__file__).with_name('research-wikimedia-catalogues.py'));r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.RUN=s.RUN;r.BACKUPS=s.BACKUP

def fetch(url):
 data=s.fetch(url);receipt=json.loads((s.RUN/'captures'/(s.core.sha(url.encode())+'.receipt.json')).read_bytes());return data,receipt
r.fetch=fetch

def discover():
 roster=json.loads((s.RUN/'artist-roster-discovery-v2.json').read_bytes());ids=sorted({x['artist']['value'].rsplit('/',1)[-1] for x in roster['rows']});allrows=[]
 for start in range(0,len(ids),40):
  part=ids[start:start+40];query='SELECT DISTINCT ?work ?artist ?collection WHERE { VALUES ?artist { '+' '.join('wd:'+q for q in part)+' } ?work wdt:P170 ?artist; wdt:P195 ?collection . } ORDER BY ?work LIMIT 1500'
  data=s.fetch('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}));rows=data['results']['bindings'];s.save(s.RUN/'work-discovery'/(str(start).zfill(4)+'.json'),{'artist_qids':part,'query':query,'rows':rows,'possibly_truncated':len(rows)==1500});allrows+=rows;print('Work discovery',start+len(part),'/',len(ids),len(allrows),'rows',flush=True)
 allids=sorted({x['work']['value'].rsplit('/',1)[-1] for x in allrows});groups=collections.defaultdict(list)
 for row in allrows:
  aq=row['artist']['value'].rsplit('/',1)[-1];entity=json.loads((s.RUN/'artist-entities'/(aq+'.json')).read_bytes());birth=r.year(entity,'P569')
  if birth is not None and birth<=1900:groups[aq].append(row['work']['value'].rsplit('/',1)[-1])
 for aq in groups:groups[aq]=sorted(set(groups[aq]),key=lambda q:int(q[1:]))
 workids=[]
 for depth in range(15):
  for aq in sorted(groups):
   if depth<len(groups[aq]) and groups[aq][depth] not in workids:workids.append(groups[aq][depth])
   if len(workids)>=350:break
  if len(workids)>=350:break
 s.save(s.RUN/'bounded-work-selection.json',{'selected_work_ids':workids,'all_discovered_count':len(allids),'basis':'At most 15 works per artist, 350 overall; initial research priority to documented births through 1900. This is a sampling budget, never artwork eligibility inferred from a lifespan.'});s.save(s.RUN/'work-discovery-summary.json',{'rows':allrows,'work_ids':allids});print('Artwork entities',len(workids),flush=True)
 for start in range(0,len(workids),30):r.entities(workids[start:start+30]);print('Artwork metadata',min(start+30,len(workids)),'/',len(workids),flush=True)
if __name__=='__main__':discover()
