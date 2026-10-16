#!/usr/bin/env python3
"""Reuse parsed evidence only when its raw capture is identical to the selected cache."""
import importlib.util,gzip,copy
from pathlib import Path
sp=importlib.util.spec_from_file_location('b','ops/random-ten-twenty-batches-20261010.py');b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
r=b.r;cache=r.load(b.RUN/'capture-cache.json');reused=[];counts={}
for pair in b.cohort():
 aid=pair['artist']['id'];index=r.load(b.RUN/'indexes'/(aid+'.json.gz'))
 for item in index['items']:
  if item['date'] and item['date']['creation_year_start']>1970:continue
  key=r.sha(item['url'].encode());dest=b.RUN/'pages'/aid/(key+'.json.gz')
  if dest.exists():continue
  old=cache.get(item['url'])
  if not old:continue
  parent=(b.ROOT/old['receipt_path']).parent.parent
  candidates=[parent/folder/aid/(key+'.json.gz') for folder in ['page-retries','pages']]
  for path in candidates:
   if not path.exists():continue
   data=r.load(path)
   if data.get('outcome')!='captured':continue
   page=data['page']
   if page.get('receipt',{}).get('sha256')!=old['sha256'] or page.get('url')!=item['url']:continue
   if page['metadata']['artistUrl']!=b.m.urlsplit(pair['source']['url']).path:continue
   if not {'title','fields','rights_label','rights_status','image_url'}<=set(page):continue
   body=b.ROOT/old['body_path'];raw=body.read_bytes();raw=gzip.decompress(raw) if body.suffix=='.gz' else raw;assert r.sha(raw)==old['sha256']
   assert page['rights_status']==('public_domain' if page['rights_label']=='Public domain' else 'unknown' if page['rights_label']=='Rights label not supplied' else 'restricted')
   result=dict(artist_id=aid,index=item,outcome='captured',page=page,parsed_evidence_reuse=dict(path=str(path.relative_to(b.ROOT)),sha256=r.sha(path.read_bytes()),raw_source_sha256=old['sha256'],basis='Exact raw page checksum matches the already selected source capture; creator identity and required source fields verified. Original retrieval timestamp retained.'))
   r.save_gz(dest,result);reused.append(dict(artist_id=aid,url=item['url'],source_file=str(path.relative_to(b.ROOT)),source_sha256=r.sha(path.read_bytes()),raw_sha256=old['sha256']));break
 if reused:print('Cached structured pages',pair['artist']['display_name'],len(reused),flush=True)
r.save_gz(b.RUN/'parsed-page-reuse.json.gz',dict(at=r.now(),reused=reused));print('Reused',len(reused),'checksum-identical parsed source pages',flush=True)
