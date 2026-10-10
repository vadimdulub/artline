#!/usr/bin/env python3
"""Search file metadata for the frozen original gaps, scoped by museum identity."""
import importlib.util,re,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('p',ROOT/'ops/deliver-prado-museum-images-20261006.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);r=p.r
RUN=p.m.RUN/'original-gap-source-search'
def run():
 baseline=r.load(p.m.RUN/'production-baseline.json.gz')['records'];selected={x['artwork_id']for x in r.load(p.RUN/'selection.json.gz')['ready']}
 plan={x['artwork_id']:x for x in r.load(p.m.RUN/'production-plan.json.gz')['records']}
 targets=[plan[x['artwork']['id']]for x in baseline if not x['artwork']['primary_media_id'] and x['artwork']['id']not in selected]
 fetch=p.core.Fetcher(RUN/'captures');fetch.defer_long_cooldowns=True;counts=collections.Counter()
 for n,x in enumerate(targets,1):
  aid=x['artwork_id'];dest=RUN/'objects'/(aid+'.json')
  if dest.exists():counts[r.load(dest)['outcome']]+=1;continue
  attempts=[];found={};queries=['insource:"'+x['source_id']+'"','"'+x['accession']+'" OR "'+re.sub(r'^P0*','P',x['accession'])+'"']
  for query in queries:
   data=p.cm.api(fetch,'commons.wikimedia.org',{'action':'query','generator':'search','gsrsearch':query,'gsrnamespace':6,'gsrlimit':10,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'})
   attempts.append({'query':query,'at':r.now(),'response':data});found.update(data.get('query',{}).get('pages',{}))
   if found:break
  result={'at':r.now(),'artwork_id':aid,'accession':x['accession'],'source_id':x['source_id'],'title':x['object']['Título'],'outcome':'file_leads_for_identity_review'if found else'no_exact_native_or_inventory_file_result','queries':attempts,'pages':found}
  r.save(dest,result);counts[result['outcome']]+=1
  if n%10==0:print('Original-gap exact-source searches',n,'/',len(targets),dict(counts),flush=True)
 r.save(RUN/'summary.json',{'at':r.now(),'targets':len(targets),'outcomes':dict(counts),'scope':'File metadata only, exact selected Prado native GUID or inventory; no image downloads or automatic matches.'});print('Gap search complete',dict(counts),flush=True)
if __name__=='__main__':run()
