import importlib.util,requests,hashlib,time
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
qids=sorted({r['artist_qid'] for r in m.base.load(m.RUN/'gap-reviewed-plan.json.gz')})
for offset in range(0,len(qids),25):
 batch=qids[offset:offset+25];path=m.RUN/'artist-entities'/(hashlib.sha256('|'.join(batch).encode()).hexdigest()+'.json')
 if path.exists():continue
 time.sleep(5);r=requests.get('https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(batch),'props':'claims|labels','languages':'en','format':'json'},headers={'User-Agent':'Artline/1.0 (selected painter artwork research; artlines.org)'},timeout=45);
 if r.status_code==429:
  time.sleep(60);r=requests.get(r.url,headers={'User-Agent':'Artline/1.0 (selected painter artwork research; artlines.org)'},timeout=45)
 r.raise_for_status();m.base.save(path,r.json())
print('Artist life evidence captured',len(qids))
