#!/usr/bin/env python3
"""Capture current source metadata for selected CC0 artwork classes; no images."""
import argparse,importlib.util,json,time,collections
from pathlib import Path
from urllib.parse import urlencode
s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
FIELDS='id,accession_number,title,alternate_titles,type,creators,creation_date,creation_date_earliest,creation_date_latest,share_license_status,images,collection,department,url,creditline,rights_and_reproductions,legal_status,record_type,on_loan,accession_date,technique,measurements,dimensions,related_works,inseparable_parts,part_visible,cover_accession_number'
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True);f=core.Fetcher(a.run/'metadata');pages=[];totals={};seen={};duplicates=collections.Counter();conflicting=set()
 for typ in ['Painting','Drawing','Print']:
  offset=0;total=None
  while time.time()<a.deadline:
   u='https://openaccess-api.clevelandart.org/api/artworks/?'+urlencode({'type':typ,'has_image':1,'cc0':1,'limit':100,'skip':offset});d=f.metadata(u)
   if total is None:total=d['info']['total']
   assert d['info']['total']==total,'Source total changed during capture';receipt=json.loads((f.cache/(core.sha(u.encode())+'.receipt.json')).read_text());pages.append({'type':typ,'offset':offset,**receipt})
   for o in d['data']:
    digest=core.sha(core.encode(o));oid=o['id']
    if oid in seen:
     duplicates[str(oid)]+=1
     if seen[oid]!=digest:conflicting.add(str(oid))
    else:seen[oid]=digest
   offset+=len(d['data']);print(core.now(),typ,'metadata',offset,'of',total,flush=True)
   if not d['data'] or offset>=total:break
  totals[typ]={'expected':total,'captured':offset}
 core.save_new(a.run/'capture.json',{'at':core.now(),'complete':all(v['captured']==v['expected'] for v in totals.values()) and len(totals)==3,'totals':totals,'unique_objects':len(seen),'unique_count_matches_source_total':len(seen)==sum(v['expected'] for v in totals.values()),'duplicate_page_entries':dict(duplicates),'conflicting_object_ids':sorted(conflicting),'images_requested':0,'pages':pages,'policy':'Complete describes the page walk, not guaranteed unique collection coverage. API pagination repeats some objects; identical repeats are deduplicated and conflicting repeats held. No claim of exhaustive unique collection coverage. Exact date, physical-object identity, primary maker, ownership and CC0 image fields require verification before import or download.'})
if __name__=='__main__':main()
