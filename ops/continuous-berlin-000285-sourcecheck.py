import importlib.util,gzip,json,requests
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000285.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
# Refresh only the three previously selected metadata notices; no bulk collection fetch.
D=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000285';D.mkdir(parents=True,exist_ok=True)
refresh=[]
for oid in b.SELECTED:
 old,rc=b.native(oid);dest=b.E/'source-captures'/('fresh-'+oid+'.receipt.json')
 if dest.exists():fresh=h.load(dest);raw=gzip.decompress(Path(fresh['body_path']).read_bytes())
 else:
  r=requests.get('https://search.smb.museum/en/object/obj-'+oid,timeout=(15,40));raw=r.content;body=D/('fresh-'+oid+'.body.gz');body.write_bytes(gzip.compress(raw,mtime=0))
  fresh=dict(at=h.now(),url=r.url,status=r.status_code,sha256=h.sha(raw),body_path=str(body),retry_after=r.headers.get('Retry-After'));h.save(dest,fresh)
 assert fresh['status']==200,'Source access failed; no retry'
 d=json.loads(b.BeautifulSoup(raw,'html.parser').select_one('#__NUXT_DATA__').string)
 def unpack(idx):
  if idx<0:return None
  v=d[idx]
  if isinstance(v,dict):return {k:unpack(n) for k,n in v.items()}
  if isinstance(v,list):
   if v and isinstance(v[0],str):return unpack(v[1]) if len(v)>1 else v
   return [unpack(n) for n in v]
  return v
 o=next(v for v in unpack(0)['data'].values() if isinstance(v,dict) and v.get('id')=='obj-'+oid)
 keys=['id','ident','title','org_unit','dating','actors','geography','provenance','acq_note','material_desc','dimensions','html_text','images'];assert all(o.get(k)==old.get(k) for k in keys),'Native metadata changed'
 refresh.append(dict(source_id=oid,fresh_receipt=fresh,prior_source_sha256=rc['sha256'],identity_date_creator_ownership_image_fields_unchanged=True,selected_image_asset=b.front(o)['id']))
b.save('independent-source-refresh-verification.json',dict(at=h.now(),rows=refresh,source_requests=3,held_provider_retries=0))
print('Three official notices refreshed HTTP200; relevant source fields unchanged')
