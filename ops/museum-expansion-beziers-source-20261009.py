"""Bounded Béziers evidence discovery; all database connections are read-only."""
import argparse,gzip,hashlib,importlib.util,json,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-beziers-common-20261009.py');prod=module('prod','catalogue-expansion-20261008.py');m=s.m;RUN=s.RUN
def baseline():
 assert s.ref(s.CP)['sha256']=='820d619b2efa7387fa8d307ecba63a696b11344f258072f7307beca4f390f6d7'
 for key,connect in [('initial',m.connect),('production-initial',prod.connect)]:
  dest=RUN/(key+'-scope-001.json.gz');assert not dest.exists()
  with connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(s.IIDS,s.IIDS))];snap=s.snapshot(db,ids);counts=s.counts(db)
  m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,read_only=True,script_reference=s.ref(Path(__file__).resolve())))
  print(json.dumps(dict(target=key,scope=len(ids),counts=counts)),flush=True)
def capture(key,url):
 path=RUN/'captures'/(key+'.json');body=path.with_suffix('.body.gz');path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():
  rc=m.load(path);raw=gzip.decompress(body.read_bytes());assert hashlib.sha256(raw).hexdigest()==rc['sha256'];return raw,rc
 time.sleep(.7)
 with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded museum metadata)'},timeout=(15,60),stream=True) as response:
  raw=b''
  for chunk in response.iter_content(65536):raw+=chunk;assert len(raw)<5_000_000
  rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body_path=str(body.relative_to(m.ROOT)))
  assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));m.save(path,rc)
  response.raise_for_status()
 assert b'Access Denied' not in raw[:10000] and b'BotStopper' not in raw[:10000]
 return raw,rc
def source():
 url='https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/?Code_Museofile__exact=M0467&page_size=200';rows=[];receipts=[]
 for page in range(1,3):
  raw,rc=capture('joconde-page'+str(page)+'-001',url);data=json.loads(raw);rows+=data['data'];receipts.append(rc);print(json.dumps(dict(page=page,total=data['meta']['total'],selected=len(rows))),flush=True)
  url=data['links']['next']
  if not url:break
  assert url.startswith('https://tabular-api.data.gouv.fr/')
 assert len({v['Reference'] for v in rows})==len(rows) and all(v['Code_Museofile']=='M0467' for v in rows)
 m.save(RUN/'joconde-current-001.json.gz',dict(at=m.now(),receipts=receipts,rows=rows,total=data['meta']['total'],next_page=url,policy='At most400 national object metadata records from one museum. Metadata only; remaining pages tracked explicitly.'))
def context():
 rows=[]
 for key,url in [('fayet','https://www.ville-beziers.fr/culture/musee-fayet'),('fayet-faq','https://www.ville-beziers.fr/culture/musee-fayet/titre-par-defaut'),('fabregat-faq','https://www.ville-beziers.fr/culture/centre-detude-et-de-conservation-fabregat/faq-fabregat')]:
  raw,rc=capture(key+'-001',url);soup=BeautifulSoup(raw,'html.parser');main=soup.select_one('main') or soup
  rows.append(dict(key=key,receipt=rc,text=main.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),url=a['href']) for a in main.select('a[href]')]))
 m.save(RUN/'native-context-001.json.gz',dict(at=m.now(),rows=rows,policy='Fayet and Fabrégat form Fine Arts collection context. Future merged museum is not current institutional identity. No object-level on-view assertion.'))
 print(json.dumps(dict(context_pages=len(rows))),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['baseline','source','context']);v=p.parse_args();globals()[v.command]()
