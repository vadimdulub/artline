#!/usr/bin/env python3
"""Documented native continuation after cooldown, with slow bounded requests."""
import argparse,datetime,gzip,hashlib,importlib.util,json,time
from pathlib import Path
from urllib.parse import urlparse
import requests
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-detroit-native-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;IID=d.IID;BASE=d.BASE;RUN=m.RUN/'native/detroit-resume';ref=d.ref
QUEUE=d.RUN/'selected-official-queue-001.json';GATE=d.RUN/'partial-capture-001.json';CADENCE_SECONDS=25
def epoch(value):return datetime.datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
def preflight():
 gate=m.load(GATE);assert gate['state']=='stopped_on_http429';failed=gate['failures'][0];p=m.ROOT/failed['reference']['path'];assert ref(p)==failed['reference'];assert ref(m.ROOT/failed['body_reference']['path'])==failed['body_reference'];assert failed['receipt']['status']==429
 elapsed=time.time()-epoch(failed['receipt']['retrieved_at']);assert elapsed>=1800,'Minimum30minute cooldown has not elapsed';assert not list((RUN/'errors').glob('*.json')),'A new source error requires review before any continuation'
 checkpoint=m.RUN/'native/next-samples/delivery-checkpoint-001.json';assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()=='c17aac8fd1a0947ad96b076f5a15418e5e0cf1ca9e4b06e77d79c8286f72ba82'
 return dict(prior_rate_limit_reference=ref(GATE),prior_error_receipt=failed['reference'],elapsed_since_rate_limit_seconds=round(elapsed,1),minimum_cooldown_seconds=1800,cadence_seconds=CADENCE_SECONDS,queue_reference=ref(QUEUE),baseline_checkpoint_reference=ref(checkpoint))
def scope():
 assert not (RUN/'initial-scope-001.json.gz').exists();d.d.d.scope('detroit-resume',IID)
def capture(row):
 path=RUN/'objects-001'/('object-%03d.json.gz'%row['number']);assert not path.exists();gate=preflight()
 prior=sorted((RUN/'captures').glob('*.json'));latest=max((epoch(m.load(p)['completed_at']) for p in prior),default=0);wait=max(0,CADENCE_SECONDS-(time.time()-latest))
 if wait:time.sleep(wait)
 requested_at=m.now();url=row['url'];assert url.startswith(BASE+'/collection/')
 try:
  with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected metadata; max one request per25seconds; no images)'},timeout=(12,45),stream=True) as response:
   raw=b''
   for chunk in response.iter_content(65536):raw+=chunk;assert len(raw)<4_000_000,'Metadata response exceeds4MB'
   receipt=dict(url=url,final_url=response.url,status=response.status_code,requested_at=requested_at,completed_at=m.now(),retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),headers={k:v for k,v in response.headers.items() if k.lower() in ['retry-after','date','content-type','etag','last-modified','cache-control','server']},gate=gate)
   stem='object-%03d'%row['number'];folder=RUN/'captures';folder.mkdir(parents=True,exist_ok=True);bodypath=folder/(stem+'.body.gz');assert not bodypath.exists();bodypath.write_bytes(gzip.compress(raw,mtime=0));m.save(folder/(stem+'.json'),receipt)
   response.raise_for_status();assert urlparse(response.url).netloc=='dia.org';assert 'html' in response.headers.get('Content-Type','')
   cap=dict(receipt=receipt,body_path=str(bodypath.relative_to(m.ROOT)));m.save(path,dict(at=m.now(),number=row['number'],index=row,queue_reference=ref(QUEUE),capture=cap,cooldown_reference=ref(GATE)))
   print(json.dumps(dict(number=row['number'],source_id=row['source_id'],status=response.status_code,bytes=len(raw))),flush=True)
 except Exception as ex:
  m.save(RUN/'errors'/('object-%03d.json'%row['number']),dict(at=m.now(),number=row['number'],url=url,error=type(ex).__name__+': '+str(ex),gate=gate,policy='Stop this native continuation on any source error. Preserve captured HTTP status, headers and body where available. No retries or alternate-transport bypass.'))
  raise
def run(limit):
 assert 1<=limit<=118;rows=m.load(QUEUE)['selected'];gate=preflight()
 if not (RUN/'continuation-start-001.json').exists():m.save(RUN/'continuation-start-001.json',dict(at=m.now(),**gate,policy='One direct selected-object probe after at least30minutes. Continue only on HTTP200, maximum one request every25seconds. Preserve all response headers needed for cooldown, original bytes and failures. Stop on any source error. No images or database writes.'))
 for row in rows[:limit]:
  path=RUN/'objects-001'/('object-%03d.json.gz'%row['number'])
  if path.exists():x=m.load(path);assert x['index']==row;d.body(x['capture']);continue
  capture(row)
 print('Completed requested bounded prefix',limit,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['scope','run']);p.add_argument('--limit',type=int,default=1);v=p.parse_args();scope() if v.command=='scope' else run(v.limit)
