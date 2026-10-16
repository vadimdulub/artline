import importlib.util,json,gzip,time
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000289.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
D=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000289';D.mkdir(parents=True,exist_ok=True)
checks=[]
for oid in b.SELECTED:
 old,rc=b.native(oid);url='https://search.smb.museum/en/object/obj-'+oid
 rp=b.E/'fresh-captures'/f'{oid}.json'
 if rp.exists():
  receipt=h.load(rp);raw=gzip.decompress(Path(receipt['body_path']).read_bytes());assert h.sha(raw)==receipt['sha256'];status=receipt['status']
 else:
  i.provider_slot('search.smb.museum');r=i.session().get(url,timeout=(15,40));raw=r.content;status=r.status_code;p=D/(oid+'-fresh.html.gz');p.write_bytes(gzip.compress(raw,mtime=0))
  receipt=dict(at=h.now(),url=url,final_url=r.url,status=status,sha256=h.sha(raw),body_path=str(p),retry_after=r.headers.get('Retry-After'));h.save(rp,receipt)
 if status in [401,403,429]:h.save(b.E/'access-hold.json',receipt);raise RuntimeError('Provider access hold')
 assert status==200;d=json.loads(BeautifulSoup(raw,'html.parser').select_one('#__NUXT_DATA__').string)
 def unpack(idx):
  if idx<0:return None
  v=d[idx]
  if isinstance(v,dict):return {k:unpack(n) for k,n in v.items()}
  if isinstance(v,list):
   if v and isinstance(v[0],str):return unpack(v[1]) if len(v)>1 else v
   return [unpack(n) for n in v]
  return v
 obj=next(v for v in unpack(0)['data'].values() if isinstance(v,dict) and v.get('id')=='obj-'+oid);assert {k:v for k,v in obj.items() if k!='additionalItems'}=={k:v for k,v in old.items() if k!='additionalItems'},'Native object changed'
 checks.append(dict(source_id=oid,prior_capture_sha256=rc['sha256'],fresh_capture_sha256=receipt['sha256'],native_object_equal=True,status=status,excluded_dynamic_field="additionalItems (unrelated suggested objects)"));print(oid,'unchanged HTTP200',flush=True)
h.save(b.E/'fresh-source-verification.json',dict(at=h.now(),records=checks))
