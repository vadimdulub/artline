#!/usr/bin/env python3
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('research-armenian-georgian-artworks.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
titles=['Niko Pirosmani','David Kakabadze','Lado Gudiashvili','Elene Akhvlediani','Mariam Aslamazyan','Yeranuhi Aslamazyan','Lavinia Bazhbeuk-Melikyan','Shalva Kikodze','Gigo Gabashvili','Yeghishe Tadevosyan','Natela Iankoshvili']
data,receipt=b.fetch('https://www.wikidata.org/w/api.php?'+urlencode({'action':'wbgetentities','sites':'enwiki','titles':'|'.join(titles),'props':'labels|descriptions|aliases|claims|sitelinks','languages':'en|hy|ka|ru|mul','format':'json','maxlag':5}))
selected=[];discoveries=[]
for q,e in data['entities'].items():
 if q.startswith('-'):continue
 p=b.s.RUN/'priority-artist-entities'/(q+'.json');b.s.save(p,{'entity':e,'receipt':receipt})
 query='SELECT DISTINCT ?work ?collection WHERE { ?work wdt:P170 wd:'+q+' . OPTIONAL { ?work wdt:P195 ?collection } } ORDER BY ?work LIMIT 100'
 cache=b.s.RUN/'priority-work-discovery'/(q+'.json')
 if cache.exists():rows=json.loads(cache.read_bytes())['rows']
 else:
  try:result=b.s.fetch('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}));rows=result['results']['bindings']
  except (RuntimeError,b.r.requests.RequestException) as error:
   discoveries.append({'qid':q,'name':b.r.label(e),'status':'provider_unavailable','error':str(error)[:150]});print(q,'source deferred',flush=True);continue
 b.s.save(b.s.RUN/'priority-work-discovery'/(q+'.json'),{'query':query,'rows':rows,'possibly_truncated':len(rows)==100})
 ids=list(dict.fromkeys(x['work']['value'].rsplit('/',1)[-1] for x in rows));chosen=ids[:20];selected+=chosen;discoveries.append({'qid':q,'name':b.r.label(e),'rows':len(rows),'selected':len(chosen)});print(b.r.label(e),len(ids),'works',flush=True)
b.s.save(b.s.RUN/'priority-selection.json',{'artists':discoveries,'work_ids':list(dict.fromkeys(selected)),'basis':'Targeted follow-up for Georgian modernists, women artists and qualified lifespan records missed by the first bounded authority sample.'});b.r.entities(list(dict.fromkeys(selected)))
