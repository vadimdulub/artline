import importlib.util,concurrent.futures,hashlib,time,requests,urllib.parse
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=[r for p in (m.RUN/'gap-metadata').glob('*.json') for r in m.base.load(p)['results']['bindings']]
qids=sorted({r['work']['value'].split('/')[-1] for r in rows});files=sorted({urllib.parse.unquote(r['image']['value'].split('Special:FilePath/')[-1]).replace('_',' ') for r in rows if r.get('image')})
def fetch(job):
 kind,batch=job
 params={'action':'wbgetentities','ids':'|'.join(batch),'props':'claims|labels','languages':'en|fr|de|es|it|el|ru','format':'json'} if kind=='entities' else {'action':'query','titles':'|'.join('File:'+f for f in batch),'prop':'imageinfo','iiprop':'url|extmetadata|size|sha1','iiurlwidth':1280,'format':'json'}
 host='www.wikidata.org' if kind=='entities' else 'commons.wikimedia.org'
 path=m.RUN/kind/(hashlib.sha256('|'.join(batch).encode()).hexdigest()+'.json')
 if path.exists():return True
 for attempt in range(3):
  try:
   time.sleep(1.5); r=requests.get('https://'+host+'/w/api.php',params=params,headers={'User-Agent':'Artline/1.0 (selected painter artwork research; artlines.org)'},timeout=45);r.raise_for_status();data=r.json();assert 'error' not in data; m.base.save(path,data);return True
  except Exception as e:
   if attempt==2:return dict(kind=kind,error=str(e).split('?')[0],batch=batch)
   time.sleep(max(30, int(r.headers.get('Retry-After','60'))) if r.status_code==429 else 4)
jobs=[('entities',qids[i:i+25]) for i in range(0,len(qids),25)]+[('commons',files[i:i+20]) for i in range(0,len(files),20)]
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
 for i,r in enumerate(pool.map(fetch,jobs)):
  results.append(r)
  if (i+1)%10==0:print('evidence',i+1,'/',len(jobs),flush=True)
m.save('gap-evidence-fetch-retry.json',results);print('evidence completed',len(jobs),'failed',sum(r is not True for r in results),flush=True)
