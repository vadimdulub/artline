import datetime,gzip,hashlib,json,re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'docs/research/continuous-production-20261011/batches/000271';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000271';D=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000271'
for p in [E/'source-captures',E/'objects',D]:p.mkdir(parents=True,exist_ok=True)
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def capture(url,key):
 rp=E/'source-captures'/(key+'.receipt.json')
 if rp.exists():
  rc=json.loads(rp.read_text());return gzip.decompress(Path(rc['body_path']).read_bytes()),rc
 r=requests.get(url,timeout=(15,40));raw=r.content;p=D/(key+'.body.gz');p.write_bytes(gzip.compress(raw,mtime=0));rc=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),url=url,final_url=r.url,status=r.status_code,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body_path=str(p),retry_after=r.headers.get('Retry-After'));save(rp,rc);return raw,rc
def unpack_html(raw):
 s=BeautifulSoup(raw,'html.parser');d=json.loads(s.select_one('#__NUXT_DATA__').string)
 def unpack(i):
  if i<0:return None
  v=d[i]
  if isinstance(v,dict):return {k:unpack(n) for k,n in v.items()}
  if isinstance(v,list):
   if v and isinstance(v[0],str):return unpack(v[1]) if len(v)>1 else v
   return [unpack(n) for n in v]
  return v
 return unpack(0)
raw,rc=capture('https://search.smb.museum/?objectType=Tafelbild','berlin-index');assert rc['status']==200
ids=list(dict.fromkeys(re.findall(r'/object/obj-(\d+)',raw.decode())))[:10]
queue=json.loads((E.parents[1]/'source-queue.json').read_text());route=next(x for x in queue['sources'] if x['source_id']=='staatliche_museen_berlin');prior=set(route['resume_cursor']['inspected_object_ids']);results=[]
for oid in ids:
 if oid in prior:continue
 raw,rc=capture('https://search.smb.museum/en/object/obj-'+oid,'object-'+oid)
 if rc['status']!=200:results.append(dict(source_id=oid,hold='HTTP '+str(rc['status'])));break
 o=next(v for v in unpack_html(raw)['data'].values() if isinstance(v,dict) and v.get('id')=='obj-'+oid);save(E/'objects'/(oid+'.json'),o)
 row={k:o.get(k) for k in ['id','title','ident','dating','material_desc','dimensions','actors','org_unit','html_text']};row['images']=[{k:i.get(k) for k in ['id','asset_content','license','photographer','obj_ref','xl_path']} for i in o.get('images',[])];results.append(row)
 print(json.dumps(row,ensure_ascii=False),flush=True)
save(E/'berlin-discovery.json',dict(index_receipt=json.loads((E/'source-captures/berlin-index.receipt.json').read_text()),source_ids=ids,rows=results))
