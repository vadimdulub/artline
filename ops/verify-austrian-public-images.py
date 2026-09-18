#!/usr/bin/env python3
"""Verify every delivered Austrian image and its unauthenticated museum API record."""
import argparse,concurrent.futures,importlib.util,json,time
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('upload-overnight-prepared-images.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);core=d.core
SITE='https://artline-web-lpuqqlugnq-ew.a.run.app'
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);args=p.parse_args();done=d.complete_ids(args.run);rows={}
 for line in (args.run/'local-attachments.jsonl').read_text().splitlines():
  x=json.loads(line)
  if x['artwork_id'] in done and x['outcome'] in ('attached','already_attached'):rows[x['artwork_id']]=json.loads(Path(x['receipt']).read_text())
 def check(im):
  urls=[SITE+im['path'],SITE+'/api/backend/v1/museums/'+im['institution_slug']+'/works/'+im['target_ids']['cloud']];out={'artwork_id':im['target_ids']['cloud'],'checks':[]}
  for kind,url in zip(('image','museum_artwork_api'),urls):
   try:
    response=requests.get(url,timeout=(10,45));response.raise_for_status()
    if kind=='image':assert response.headers.get('Content-Type','').startswith('image/jpeg') and core.sha(response.content)==im['sha256'] and len(response.content)==im['bytes']
    else:
     body=response.json()
     for k,v in [('title',im['title']),('media_url',im['path']),('status','review'),('license_url',im['policy_url']),('source_page_url',im['page'])]:assert body[k]==v,k+' differs'
    out['checks'].append({'kind':kind,'url':url,'status':response.status_code,'verified':True,'response_sha256':core.sha(response.content)})
   except Exception as exc:out['checks'].append({'kind':kind,'url':url,'verified':False,'reason':str(exc)[:160]})
  return out
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,rows.values()))
 errors=[dict(artwork_id=r['artwork_id'],**c) for r in results for c in r['checks'] if not c['verified']];core.save_new(args.run/'public-all-images-final.json',{'at':core.now(),'anonymous_requests':True,'artworks':len(results),'checks':results,'errors':errors});print('Public artwork/image checks',len(results)*2,'errors',len(errors));assert not errors
if __name__=='__main__':main()
