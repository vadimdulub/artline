#!/usr/bin/env python3
"""Read-only discovery of open Chicago images for exact existing local gaps."""
import collections,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('recover-local-commons-images-20261005.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
core=base.core;RUN=core.ROOT/'docs/research/local-chicago-native-audit-20261006'

def audit():
 path=RUN/'gap-identifiers.json'
 if not path.exists():
  with base.connect() as db:
   rows=db.execute("""SELECT a.id::text artwork_id,a.title,a.date_display,a.work_type,a.accession_number,e.scheme,e.external_id
    FROM institutions i JOIN artworks a ON a.current_institution_id=i.id JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id
    WHERE i.slug='art-institute-of-chicago' AND e.scheme IN ('aic-object','european-chicago-art-institute-of-chicago-object')
    AND a.primary_media_id IS NULL AND a.status='review' AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
    AND artline_has_selection_evidence(a.id) ORDER BY a.id,e.scheme""").fetchall()
  if any(not re.fullmatch(r'\d+',c['external_id']) for c in rows):raise ValueError('Invalid native object ID')
  core.save_new(path,dict(at=core.now(),rows=rows))
 rows=json.loads(path.read_bytes())['rows'];byid=collections.defaultdict(list)
 for c in rows:byid[c['external_id']].append(c)
 ids=sorted(byid,key=int);fetch=core.Fetcher(RUN/'metadata');fetch.defer_long_cooldowns=True;captures=[];leads=[];missing=[];counts=collections.Counter()
 # Museum guidance: field-limited batched IDs, one thread, <=1 request/sec.
 for start in range(0,len(ids),100):
  group=ids[start:start+100];url='https://api.artic.edu/api/v1/artworks?'+urlencode(dict(ids=','.join(group),fields='id,image_id,is_public_domain,copyright_notice,main_reference_number',limit=100))
  data=fetch.metadata(url);receipt=json.loads((fetch.cache/(core.sha(url.encode())+'.receipt.json')).read_bytes());captures.append(receipt);objects=data['data']
  if len({str(x['id']) for x in objects})!=len(objects) or any(str(x['id']) not in group for x in objects):raise ValueError('Native batch identity mismatch')
  missing.extend(sorted(set(group)-{str(x['id']) for x in objects}))
  for o in objects:
   reason='no_image' if not o.get('image_id') else 'no_explicit_open_grant' if o.get('is_public_domain') is not True or o.get('copyright_notice') else 'open_image_lead'
   counts[reason]+=1
   if reason=='open_image_lead':leads.append(dict(native=o,local_matches=byid[str(o['id'])],capture=receipt))
  print('Chicago native metadata',min(start+100,len(ids)),'/',len(ids),'open leads',len(leads),flush=True)
 result=dict(at=core.now(),local_identifier_rows=len(rows),unique_native_ids=len(ids),counts=dict(counts),missing_native_ids=missing,open_image_leads=leads,pages=captures,images_requested=0,complete=True,policy='Metadata discovery for exact existing gaps only; each image lead requires full native identity, date, rights and visual review before attachment. No catalogue or holding writes.')
 core.save_new(RUN/'discovery.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('pages','open_image_leads')},indent=2))

if __name__=='__main__':audit()
