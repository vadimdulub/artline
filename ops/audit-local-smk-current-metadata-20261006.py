#!/usr/bin/env python3
"""Read-only current SMK open-image index discovery; no image or DB writes."""
import collections,importlib.util,json
from pathlib import Path
from urllib.parse import urlencode

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('recover-local-commons-images-20261005.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
core=base.core;RUN=core.ROOT/'docs/research/local-smk-current-metadata-20261006'

def audit():
 fetch=core.Fetcher(RUN/'metadata');pages=[];items=[];total=None
 for offset in range(0,60000,2000):
  url='https://api.smk.dk/api/v1/art/search?'+urlencode(dict(keys='*',filters='[public_domain:true],[has_image:true]',fields='object_number,public_domain,modified',sort='object_number',sort_type='asc',offset=offset,rows=2000))
  obj=fetch.metadata(url)
  if total is None:total=obj['found']
  if obj['found']!=total or obj['offset']!=offset or len(obj['items'])!=min(2000,total-offset):raise ValueError('Current metadata paging changed')
  if any(x.get('public_domain') is not True or not x.get('object_number') for x in obj['items']):raise ValueError('Current open-image index differs')
  items.extend(obj['items']);pages.append(json.loads((fetch.cache/(core.sha(url.encode())+'.receipt.json')).read_bytes()))
  print('Current metadata records',len(items),'of',total,flush=True)
  if len(items)==total:break
 if len(items)!=total:raise ValueError('Incomplete bounded metadata index')
 available=collections.Counter(x['object_number'] for x in items)
 with base.connect() as db:
  gaps=db.execute("""SELECT a.id::text artwork_id,a.title,a.date_display,a.work_type,a.accession_number,e.external_id,e.scheme,e.canonical_url,
   ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.id) creators
   FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id JOIN institutions i ON i.id=a.current_institution_id
   WHERE e.entity_type='artwork' AND e.scheme IN ('smk-object','european-smk-statens-museum-for-kunst-object') AND i.slug='statens-museum-for-kunst'
   AND a.primary_media_id IS NULL AND a.status='review' AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
   AND artline_has_selection_evidence(a.id) ORDER BY a.id,e.scheme""").fetchall()
 leads=[dict(c,current_index_occurrences=available[c['external_id']]) for c in gaps if c['external_id'] in available]
 data=dict(at=core.now(),source_total=total,captured=len(items),pages=pages,duplicate_accession_numbers={k:v for k,v in available.items() if v>1},eligible_missing_identifier_rows=len(gaps),current_leads=leads,images_requested=0,complete=True,policy='Metadata discovery only. Each lead requires an exact current object, creator, type, date and image-rights review before download. No catalogue or holding writes.')
 core.save_new(RUN/'capture.json',data)
 print(json.dumps({k:v for k,v in data.items() if k not in ('pages','duplicate_accession_numbers')},ensure_ascii=False,indent=2))

if __name__=='__main__':audit()
