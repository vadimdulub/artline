#!/usr/bin/env python3
"""Capture bounded public Mia metadata search pages, without requesting images."""
import argparse,importlib.util,json,time
from pathlib import Path
from urllib.parse import quote,urlencode
s=importlib.util.spec_from_file_location('mia',Path(__file__).with_name('overnight-mia-images.py'));mia=importlib.util.module_from_spec(s);s.loader.exec_module(mia);core=mia.core

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--classification',choices=['Paintings','Drawings','Prints'],required=True);p.add_argument('--max-records',type=int,default=10000);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True);f=core.Fetcher(a.run/'search-cache');query='classification:"'+a.classification+'" AND rights_type:"Public Domain"';rows={};total=None;pages=[]
 for offset in range(0,a.max_records,200):
  if time.time()>=a.deadline:break
  url='https://search.artsmia.org/'+quote(query,safe='')+'?'+urlencode({'size':min(200,a.max_records-offset),'from':offset})
  o=f.metadata(url)
  if o.get('error') or o.get('timed_out') or o.get('query')!=query:raise RuntimeError('Search query failed or changed')
  total_value=o['hits']['total'];assert total_value['relation'] in ('eq','gte');count=total_value['value']
  if total is None:total=count;total_relation=total_value['relation']
  if total!=count:raise RuntimeError('Source collection changed during bounded capture; review checkpoint')
  hits=o['hits']['hits'];receipt=json.loads((f.cache/(core.sha(url.encode())+'.receipt.json')).read_text());pages.append(receipt)
  for h in hits:
   obj=h['_source'];oid=str(obj['id']);assert oid not in rows,'Duplicate object in paginated search; review source ordering'
   # The search index can return mixed classifications. Preserve source facts
   # here; the later exact object classifier must decide eligibility.
   rows[oid]={'object':obj,'metadata_capture':receipt}
  print(core.now(),a.classification,'metadata captured',len(rows),'of',total,flush=True)
  if offset+len(hits)>=total or not hits:break
 report={'at':core.now(),'classification':a.classification,'source_query':query,'source_total':total,'source_total_relation':total_relation,'captured':len(rows),'complete':total_relation=='eq' and len(rows)==total,'records':list(rows.values()),'pages':pages,'images_requested':0}
 core.save_new(a.run/(a.classification.lower()+'-metadata.json'),report)
if __name__=='__main__':main()
