import json,time,hashlib,gzip,requests
from pathlib import Path
base=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012';out=base/'cma-classification';out.mkdir(exist_ok=True)
entries=json.loads(gzip.decompress((base/'historical-entries-for-review.json.gz').read_bytes()));selected={str(e['evidence']['id'])for e in entries if e['evidence'].get('id')}
index={};session=requests.Session()
for skip in range(0,100000,1000):
 p=out/f'{skip:06d}.json.gz'
 if p.exists():doc=json.loads(gzip.decompress(p.read_bytes()))
 else:
  r=session.get('https://openaccess-api.clevelandart.org/api/artworks/',params={'fields':'id,type,technique,title','limit':1000,'skip':skip},timeout=(15,60));r.raise_for_status();doc=r.json();p.write_bytes(gzip.compress(r.content,mtime=0));(out/f'{skip:06d}-receipt.json').write_text(json.dumps({'url':r.url,'sha256':hashlib.sha256(r.content).hexdigest(),'status':r.status_code}))
 for row in doc['data']:
  if str(row['id'])in selected:index[str(row['id'])]=row
 print('Classification index',skip+len(doc['data']),'selected',len(index),'of',len(selected),flush=True)
 if skip+1000>=doc['info']['total']:break
 time.sleep(.15)
(base/'cma-selected-classifications.json').write_text(json.dumps(index,ensure_ascii=False,indent=2));print('Done',len(index))
