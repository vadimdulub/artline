import importlib.util,concurrent.futures,hashlib,time,requests
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
qids=sorted({r['selected']['value'].split('/')[-1] for p in (m.RUN/'gap-candidates').glob('*.json') for r in m.base.load(p)['results']['bindings']})
def fetch(batch):
 query='''SELECT ?work ?workLabel ?date ?precision ?image ?creator ?collection ?inventory ?wikiart ?type WHERE { VALUES ?work { '''+' '.join('wd:'+q for q in batch)+''' } ?work wdt:P170 ?creator; p:P571/psv:P571 ?dateNode . ?dateNode wikibase:timeValue ?date; wikibase:timePrecision ?precision . OPTIONAL { ?work wdt:P18 ?image } OPTIONAL { ?work wdt:P195 ?collection } OPTIONAL { ?work wdt:P217 ?inventory } OPTIONAL { ?work wdt:P3467 ?wikiart } OPTIONAL { ?work wdt:P31 ?type } SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr,de,es,it,ru,el" } }'''
 path=m.RUN/'gap-metadata'/(hashlib.sha256(query.encode()).hexdigest()+'.json')
 if path.exists():return
 for i in range(3):
  try:
   r=requests.get('https://query.wikidata.org/sparql',params={'query':query,'format':'json'},headers={'User-Agent':'Artline/1.0 (selected painter artwork research; artlines.org)'},timeout=55);r.raise_for_status();data=r.json();m.base.save(path,data);return
  except Exception:
   if i==2:raise
   time.sleep(2)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(fetch,[qids[i:i+35] for i in range(0,len(qids),35)]))
print('metadata captured',len(qids),flush=True)
