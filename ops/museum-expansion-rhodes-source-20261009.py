"""Bounded official Rhodes collection research. Never logs public client credentials."""
import argparse,gzip,hashlib,importlib.util,json,re,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-rhodes-common-20261009.py');src=module('src','museum-expansion-beziers-source-20261009.py');m=s.m;RUN=s.RUN;src.RUN=RUN
PREV=m.RUN/'native/acropolis-more-20261009';PARENT='37532a1a-6753-4111-8b0b-434cb8131deb'
FIELDS=dict(inventory='67fc8514-6ab6-4511-82c2-91f27660cc1e',title='b26d5f89-d42f-4400-8abd-031746597fca',creator='4c7953e0-47e5-4a28-b55f-7f7808c32553',date='fce195b9-7a32-4de1-996f-062f36ecbaca',type='1d813c78-d2d8-40f3-8a19-5ac777453c4b',description='2cf30d2e-bf48-4db1-b278-ba3cd57f51ae',material='59da0ca3-1356-4124-9cf3-f56cd0b14c9e',dimensions='8c7b297a-7af7-4b16-b7c5-331daabe67c9',copyright='acce67dd-5726-4591-8db4-02d5bf2ab4bc',source='e7f1a3a7-c6cf-4fbd-a596-c1d688b0173a',onlineAt='cbfaa08a-ac16-41fe-a040-5b5f5a87b468')
def capture(key,path,payload=None):
 assert path.startswith(('/v2/public/containers/','/public/containers/'))
 rcpath=RUN/'captures'/(key+'.json');body=rcpath.with_suffix('.body.gz');rcpath.parent.mkdir(parents=True,exist_ok=True)
 if rcpath.exists():
  rc=m.load(rcpath);raw=gzip.decompress(body.read_bytes());assert hashlib.sha256(raw).hexdigest()==rc['sha256'];assert rc['status']==200;return json.loads(raw),rc
 js=gzip.decompress((PREV/'captures/rhodes-portal-main-js-001.body.gz').read_bytes()).decode();credential=re.search(r'Authorization:"([^"]+)"',js).group(1)
 headers={'Content-Type':'application/json','X-TenantID':'mga_rodou','Authorization':credential,'User-Agent':'ArtlineMuseumResearch/1.0 (bounded selected metadata)'}
 time.sleep(.6);url='https://repox.mgamuseum.gr/api'+path
 response=requests.request('GET' if payload is None else 'POST',url,json=payload,headers=headers,timeout=(15,45));raw=response.content;assert len(raw)<5_000_000
 rc=dict(url=url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body_path=str(body.relative_to(m.ROOT)),request_body=payload,header_policy='Published normal portal frontend client configuration; credentials excluded. Only public collection metadata endpoints. No image downloads.')
 assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));m.save(rcpath,rc);response.raise_for_status();return json.loads(raw),rc
def fields(data):
 props={v['schemaPropertyUuid']:v for v in data.get('properties',[])}
 return {k:(props.get(uid,{}).get('value') if k=='inventory' else props.get(uid,{}).get('valueAsText')) for k,uid in FIELDS.items()}
def context():
 rows=[]
 for key,url in [('museum','https://mgamuseum.gr/en/the-museum/'),('visit','https://mgamuseum.gr/en/your-visit/')]:
  raw,rc=src.capture(key+'-001',url);soup=BeautifulSoup(raw,'html.parser');main=soup.select_one('main') or soup
  rows.append(dict(key=key,receipt=rc,text=main.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),url=a['href']) for a in main.select('a[href]')]))
 m.save(RUN/'native-context-001.json.gz',dict(at=m.now(),rows=rows));print(json.dumps(dict(context_pages=len(rows))),flush=True)
def sample():
 data=m.load(PREV/'next-museum-rhodes-public-index-001.json.gz');rows=[]
 for n,v in enumerate(data['data']['content']):
  d,rc=capture('object-'+v['uuid']+'-001','/v2/public/containers/'+v['uuid']);row=dict(n=n,uuid=v['uuid'],fields=fields(d),receipt=rc,source_url='https://portal.mgamuseum.gr/collections/'+v['uuid']);rows.append(row)
  print(json.dumps({k:row[k]for k in ['n','uuid','fields']},ensure_ascii=False),flush=True)
 m.save(RUN/'native-sample-001.json.gz',dict(at=m.now(),index_reference=s.ref(PREV/'next-museum-rhodes-public-index-001.json.gz'),rows=rows,policy='First20 metadata records inspected for individual dates and creator selection. Administrative repository identities/timestamps omitted from derived artwork facts. No images fetched.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['context','sample']);args=p.parse_args();globals()[args.command]()
