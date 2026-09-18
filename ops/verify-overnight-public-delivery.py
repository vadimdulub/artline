#!/usr/bin/env python3
"""Read-only anonymous public API and image delivery canaries."""
import argparse,collections,concurrent.futures,hashlib,importlib.util,json,time
from pathlib import Path
import psycopg,requests
from psycopg.rows import dict_row
s=importlib.util.spec_from_file_location('delivery',Path(__file__).with_name('upload-overnight-prepared-images.py'));delivery=importlib.util.module_from_spec(s);s.loader.exec_module(delivery);core=delivery.core
BASE='https://artline-web-lpuqqlugnq-ew.a.run.app'
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();done=delivery.complete_ids(a.run);by_provider=collections.defaultdict(list)
 for line in (a.run/'local-attachments.jsonl').read_text().splitlines():
  j=json.loads(line)
  if j['artwork_id'] in done and j['outcome'] in ('attached','already_attached'):by_provider[j['provider']].append(j)
 selected=[]
 for provider,rows in sorted(by_provider.items()):
  ims=[json.loads(Path(j['receipt']).read_text()) for j in rows];ims.sort(key=lambda c:(not c.get('popular'),c['work_type']!='painting',c['title']))
  im=ims[0];receipt=a.run/'production-resume'/provider/'images'/provider/(im['artwork_id']+'.json')
  if receipt.exists():im=json.loads(receipt.read_text())
  selected.append(im)
 with psycopg.connect(core.cloud_dsn(),autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
  rows=db.execute("""SELECT a.id::text,i.slug museum_slug,(SELECT p.slug FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id LEFT JOIN artist_discovery_selection d ON d.artist_id=p.id WHERE aa.artwork_id=a.id ORDER BY d.is_popular DESC NULLS LAST,p.slug LIMIT 1) artist_slug
   FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE a.id=ANY(%s::uuid[])""",([im['target_ids']['cloud'] for im in selected],)).fetchall();locations={x['id']:x for x in rows}
 def check(im):
  aid=im['target_ids']['cloud'];location=locations.get(aid,{});out={'provider':im['provider'],'artwork_id':aid,'title':im['title'],'source_url':im['page'],'checks':{}}
  def image_check():
   res=requests.get(BASE+im['path'],timeout=30);res.raise_for_status();assert res.headers.get('Content-Type','').startswith('image/jpeg');assert len(res.content)==im['bytes'] and hashlib.sha256(res.content).hexdigest()==im['sha256'];return {'http_status':res.status_code,'verified':True,'bytes':len(res.content)}
  try:out['checks']['image']=image_check()
  except Exception as exc:out['checks']['image']={'verified':False,'error':str(exc)[:250]}
  for kind,key in [('museums','museum_slug'),('artists','artist_slug')]:
   if not location.get(key):continue
   url=BASE+'/api/backend/v1/'+kind+'/'+location[key]+'/works/'+aid;started=time.monotonic();entry={'url':url}
   try:
    res=requests.get(url,timeout=30);entry['http_status']=res.status_code;res.raise_for_status();record=res.json()
    for field,wanted in [('title',im['title']),('media_url',im['path']),('status','review'),('license_url',im['policy_url']),('source_page_url',im['page'])]:assert record[field]==wanted,field+' differs'
    entry['verified']=True
   except Exception as exc:entry.update(verified=False,error=str(exc)[:250])
   entry['seconds']=round(time.monotonic()-started,2);out['checks'][kind]=entry
  print(core.now(),im['provider'],{k:v.get('verified') for k,v in out['checks'].items()},flush=True);return out
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(check,selected))
 core.save_new(a.output,{'at':core.now(),'anonymous_requests':True,'checks':results,'image_canaries_verified':sum(x['checks']['image']['verified'] for x in results),'image_canaries_total':len(results),'api_checks_verified':sum(c['verified'] for x in results for k,c in x['checks'].items() if k!='image'),'api_checks_total':sum(len(x['checks'])-1 for x in results),'limitation':'Canary verification of selected public routes and byte-exact images; not a full browser or load test.'})
if __name__=='__main__':main()
