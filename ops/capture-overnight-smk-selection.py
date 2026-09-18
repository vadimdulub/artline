#!/usr/bin/env python3
"""Capture current public SMK metadata with image rights; never download images."""
import argparse,collections,importlib.util,json,time
from pathlib import Path
from urllib.parse import urlencode
s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True);f=core.Fetcher(a.run/'metadata');seen=set();accessions=collections.Counter();pages=[];total=None;offset=0
 while time.time()<a.deadline:
  url='https://api.smk.dk/api/v1/art/search?'+urlencode({'keys':'*','filters':'[public_domain:true],[has_image:true]','offset':offset,'rows':100})
  result=f.metadata(url);assert result['offset']==offset and result['rows']==100
  if total is None:total=result['found']
  if total!=result['found']:raise RuntimeError('Museum source count changed during capture; inspect checkpoint')
  receipt=json.loads((f.cache/(core.sha(url.encode())+'.receipt.json')).read_text());pages.append(receipt)
  for o in result['items']:
   oid=o['id'];assert oid not in seen,'Duplicate source object ID in paginated API results';seen.add(oid);accessions[o['object_number']]+=1
  offset+=len(result['items']);print(core.now(),'SMK metadata captured',offset,'of',total,flush=True)
  if not result['items'] or offset>=total:break
  time.sleep(.05)
 report={'at':core.now(),'source_total':total,'source_objects_captured':len(seen),'complete':len(seen)==total,'pages':pages,'duplicate_accession_numbers':{k:v for k,v in accessions.items() if v>1},'images_requested':0,'selection_note':'Metadata discovery only. Repeated accession numbers belong to distinct API IDs and must be held for physical-object review. Exact artwork class, source creation wording, existing painter identity and per-image PDM still need verification before any download.'}
 core.save_new(a.run/'capture.json',report)
if __name__=='__main__':main()
