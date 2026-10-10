"""Bounded MBP metadata discovery from the Ministry public catalogue."""
import argparse,gzip,hashlib,importlib.util,json,time
from pathlib import Path
import requests
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-mbp-more-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s)
m=s.m;RUN=s.RUN;LABEL='Μουσείο Βυζαντινού Πολιτισμού Θεσσαλονίκης';NA='https://nationalarchive.culture.gr'
def search():
 rows=[];receipts=[]
 for offset in (200,300):
  key='national-search-'+str(offset)+'-001';path=RUN/'captures'/(key+'.json');bodypath=path.with_suffix('.body.gz');path.parent.mkdir(parents=True,exist_ok=True)
  url=NA+'/portal-api/exhibits/_search?limit=100&offset='+str(offset)
  body=dict(language='en',sortOrder='asc',filters=dict(materials=[],types=[],creators=[],storeLocations=[LABEL],providers=[],stolen=False,repatriated=False))
  if path.exists():
   rc=m.load(path);raw=gzip.decompress(bodypath.read_bytes());assert hashlib.sha256(raw).hexdigest()==rc['sha256']
  else:
   time.sleep(1)
   r=requests.post(url,json=body,timeout=(15,45),headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected metadata)'})
   raw=r.content;assert len(raw)<5_000_000
   rc=dict(url=url,request=body,method='POST',status=r.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body_path=str(bodypath.relative_to(m.ROOT)))
   bodypath.write_bytes(gzip.compress(raw,mtime=0));m.save(path,rc);r.raise_for_status()
  data=json.loads(raw);batch=data['exhibits'];assert all(v['storeLocation']['name']['gr']==LABEL for v in batch)
  rows+=batch;receipts.append(rc);print(json.dumps(dict(offset=offset,records=len(batch),top_level_keys=list(data),totals={k:v for k,v in data.items() if k not in ['exhibits','aggregations']})),flush=True)
  if len(batch)<100:break
 assert len({v['recordId'] for v in rows})==len(rows)
 m.save(RUN/'national-discovery-001.json.gz',dict(at=m.now(),rows=rows,receipts=receipts,next_offset=200+len(rows),policy='At most200 further metadata discovery records scoped to this museum; individual selection and identity review required. No images downloaded.'))
if __name__=='__main__':search()
