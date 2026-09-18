#!/usr/bin/env python3
"""Capture bounded current museum metadata by popular creator discovery terms."""
import argparse,importlib.util,json,time,collections
from pathlib import Path
from urllib.parse import quote,urlencode
s=importlib.util.spec_from_file_location('mia',Path(__file__).with_name('overnight-mia-images.py'));mia=importlib.util.module_from_spec(s);s.loader.exec_module(mia);core=mia.core
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();r=a.run;f=core.Fetcher(r/'search-cache');queries=json.loads((r/'query-counts.json').read_text());rows={};pages=[];totals=[];repeat=0
 for query in queries:
  q=query['source_query'];total=query['total'];assert total['relation']=='eq' and total['value']<10000;captured=0;seen=set()
  for offset in range(0,total['value'],200):
   if time.time()>=a.deadline:break
   u='https://search.artsmia.org/'+quote(q,safe='')+'?'+urlencode({'size':min(200,total['value']-offset),'from':offset});d=f.metadata(u);assert not d.get('error') and not d.get('timed_out') and d['query']==q and d['hits']['total']==total;receipt=json.loads((f.cache/(core.sha(u.encode())+'.receipt.json')).read_text());pages.append(receipt)
   for hit in d['hits']['hits']:
    o=hit['_source'];oid=str(o['id']);assert oid not in seen,'Repeated source object within artist query';seen.add(oid)
    if oid in rows:
     assert rows[oid]['object']==o,'Museum object differs across query captures';repeat+=1
    else:rows[oid]={'object':o,'metadata_capture':receipt}
   captured+=len(d['hits']['hits'])
   print(core.now(),query['artist_term'],'metadata',captured,'of',total['value'],flush=True)
  totals.append({'artist_term':query['artist_term'],'source_query':q,'expected':total['value'],'captured':captured})
 core.save_new(r/'prints-metadata.json',{'at':core.now(),'classification':'Prints','source_queries':totals,'captured':len(rows),'complete':False,'all_selected_query_pages_captured':all(v['expected']==v['captured'] for v in totals),'repeated_across_queries':repeat,'records':list(rows.values()),'pages':pages,'images_requested':0,'note':'A selection of popular creator search terms, not exhaustive museum coverage. Source creator identity, classification, rights and dates must be verified separately; search matches are discovery leads only.'})
if __name__=='__main__':main()
