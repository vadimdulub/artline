"""Bounded MBP metadata discovery from the Ministry public catalogue."""
import argparse,gzip,hashlib,importlib.util,json,time
from pathlib import Path
import requests
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-mbp-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s)
m=s.m;RUN=s.RUN;LABEL='Μουσείο Βυζαντινού Πολιτισμού Θεσσαλονίκης';NA='https://nationalarchive.culture.gr'
def search():
 rows=[];receipts=[]
 for offset in (0,100):
  key='national-search-'+str(offset)+'-001';path=RUN/'captures'/(key+'.json');bodypath=path.with_suffix('.body.gz')
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
 m.save(RUN/'national-discovery-001.json.gz',dict(at=m.now(),rows=rows,receipts=receipts,next_offset=len(rows),policy='At most200 metadata discovery records scoped to this museum; individual selection and identity review required. No images downloaded.'))
def greek():
 from bs4 import BeautifulSoup
 rows=[]
 for n,slug in enumerate(['lithografia-i-ypodochi-tis-zonis-tis-theo','chalkografia-o-agios-georgios-kai-i-mon'],1):
  raw,rc=s.src.capture('greek-print-'+str(n)+'-001','https://www.mbp.gr/exhibit/'+slug+'/');soup=BeautifulSoup(raw,'html.parser');rows.append(dict(receipt=rc,text=soup.get_text(' ',strip=True)))
 m.save(RUN/'greek-print-resolution-001.json.gz',dict(at=m.now(),rows=rows))
def details():
 discovery=m.load(RUN/'national-discovery-001.json.gz');selected=[];deferred=[]
 kinds={'Etching','Engraving','Lithograph','Xylography','Chromolithograph','Overpainted etching','Portable icon','Bilateral icon','Triptych','Altarscreen door','Labarum (liturgical textile)','Wallpainting','Wall mosaic','Floor mosaic','Painting','Double-sided panel','Corinthian capital','Capital','Colonette'}
 for v in discovery['rows']:
  (selected if any(t.get('en') in kinds for t in v.get('types') or []) else deferred).append(v)
 assert len(selected)<=140;rows=[]
 selection=RUN/'national-selection-001.json';value=dict(source_reference=s.s.ref(RUN/'national-discovery-001.json.gz'),selected_ids=[v['recordId'] for v in selected],deferred_ids=[v['recordId'] for v in deferred],policy='Selected icons,prints,paintings,mosaics and carved architectural sculptures from200discovery records. Individual edition,date,component and identity review still required. Coins,seals,ordinaryvessels andtools deferred, not quota placeholders.')
 if selection.exists():assert m.load(selection)==value
 else:m.save(selection,value)
 for n,v in enumerate(selected,1):
  raw,rc=s.src.capture('national-object-'+str(v['recordId'])+'-001',NA+'/portal-api/exhibits/'+str(v['recordId']));r=json.loads(raw);assert r['recordId']==v['recordId'] and r['storeLocation']['name']['gr']==LABEL
  rows.append(dict(raw=r,receipt=rc));print(json.dumps(dict(n=n,total=len(selected),id=r['recordId'],title=r['title'].get('en'),first=r.get('start'),last=r.get('end'))),flush=True)
 m.save(RUN/'national-details-001.json.gz',dict(at=m.now(),rows=rows,selection_reference=s.s.ref(selection),policy='Fresh individual object metadata. Raw bilingual descriptions,registry,dates,rights and provenance retained. No reproductions downloaded.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['search','greek','details']);a=p.parse_args();globals()[a.command]()
