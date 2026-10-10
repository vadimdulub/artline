#!/usr/bin/env python3
"""Bounded metadata search; inventory variants require Prado context."""
import importlib.util, collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('p',ROOT/'ops/deliver-prado-museum-images-20261006.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p);r=p.r
RUN=p.m.RUN/'original-gap-refinement'
def run():
 frozen=RUN/'targets.json.gz'
 if frozen.exists():targets=r.load(frozen)
 else:
  v=r.load(p.m.RUN/'latest-verification.json');current=r.load((p.m.RUN/v['receipt']).parent/'catalogue-snapshot.json.gz')
  baseline=r.load(p.m.RUN/'production-baseline.json.gz')['records'];plan={x['artwork_id']:x for x in r.load(p.m.RUN/'production-plan.json.gz')['records']}
  targets=[plan[b['artwork']['id']]for b in baseline if not current[b['artwork']['id']]['primary_media_id']]
  r.save_gz(frozen,targets)
 fetch=p.core.Fetcher(RUN/'captures');fetch.defer_long_cooldowns=True;counts=collections.Counter()
 for n,x in enumerate(targets,1):
  dest=RUN/'objects'/(x['artwork_id']+'.json')
  if dest.exists():counts['resumed']+=1;continue
  number=int(x['accession'][1:]);variants=[f'P{number:06}',f'P{number:05}',f'P{number}']
  title=x['object']['Título'].split(' (')[0].split(' o ')[0]
  queries=['('+' OR '.join('insource:"'+v+'"'for v in dict.fromkeys(variants))+') insource:"Prado"','"'+title.replace('"','')+'" insource:"Prado"']
  attempts=[];pages={}
  for query in queries:
   response=p.cm.api(fetch,'commons.wikimedia.org',{'action':'query','generator':'search','gsrsearch':query,'gsrnamespace':6,'gsrlimit':15,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'})
   attempts.append({'at':r.now(),'query':query,'response':response});pages.update(response.get('query',{}).get('pages',{}))
  result={'at':r.now(),'artwork_id':x['artwork_id'],'accession':x['accession'],'title':x['object']['Título'],'creator':x['creator_label'],'source_id':x['source_id'],'pages':pages,'attempts':attempts,'status':'leads_only_not_verified_matches'}
  r.save(dest,result);counts['objects_with_leads'if pages else'no_result']+=1
  if n%10==0:print('Refined original-gap metadata search',n,'/',len(targets),dict(counts),flush=True)
 r.save(RUN/'summary.json',{'at':r.now(),'targets':len(targets),'outcomes':dict(counts),'scope':'No image download or automatic attachment; verify museum-native identity and source before selecting.'})
 print('Refinement complete',dict(counts),flush=True)
if __name__=='__main__':run()
