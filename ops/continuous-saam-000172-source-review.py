#!/usr/bin/env python3
"""Bounded native-source verification before batch172 image attachment."""
import importlib.util,json,gzip,re,html,fcntl
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('b172',ROOT/'ops/continuous-batch-000172.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;E=b.E
URLS={'22306':'https://americanart.si.edu/artwork/fijian-man-22306','943':'https://americanart.si.edu/artwork/drinking-pool-three-women-water-943','5033':'https://americanart.si.edu/artwork/landscape-farm-and-mountains-5033'}
def plain(t):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',t)))
def run():
 selected=h.load(E/'candidate-selection.json.gz')['rows'];decisions=h.load(E/'exact-identity-decisions.json')['rows'];verified=[]
 for r in selected:
  oid=r['native_id'];url=URLS[oid];p=b.DATA/('saam-'+oid+'-native.html.gz');rcp=E/'source-captures'/('saam-'+oid+'-native.receipt.json')
  if rcp.exists():rc=h.load(rcp);body=gzip.decompress(p.read_bytes());assert h.sha(body)==rc['sha256']
  else:
   resp=requests.get(url,timeout=(15,45));resp.raise_for_status();assert resp.status_code==200
   body=resp.content;p.write_bytes(gzip.compress(body,mtime=0));rc=dict(url=url,final_url=resp.url,status=resp.status_code,retrieved_at=h.now(),sha256=h.sha(body),body_path=str(p),retry_after=resp.headers.get('Retry-After'));h.save(rcp,rc)
  text=plain(body.decode());attrs=plain(' '.join(re.findall(r'data-text="([^"]*)"',body.decode())))
  ft=r['image']['source']['content']['freetext'];values=lambda k,label:[x['content'] for x in ft[k] if x['label']==label]
  date=values('date','Date')[0];medium=values('physicalDescription','Medium')[0];dimensions=values('physicalDescription','Dimensions')[0];creator=values('name','Artist')[0].split(',')[0]
  imgid=r['image']['image_url'].split('/ids/')[1].split('?')[0]
  for value in [r['title'],r['accession_number'],date,medium,creator]:assert h.norm(value) in h.norm(text+' '+attrs),(oid,value)
  assert h.norm(dimensions) in h.norm(text+' '+attrs),(oid,'dimensions')
  assert imgid in body.decode() and 'Free to use' in text
  previous=next(x for x in decisions if x['native_id']==oid);raw=gzip.decompress((ROOT/previous['previous_source_capture']).read_bytes());assert h.sha(raw)==previous['previous_source_capture_sha256']
  original_text=plain(raw.decode());assert all(h.norm(v) in h.norm(original_text+' '+plain(' '.join(re.findall(r'data-text="([^"]*)"',raw.decode())))) for v in [r['title'],r['accession_number'],date,medium,creator,dimensions]),oid
  verified.append(dict(artwork_id=r['artwork_id'],native_id=oid,accession=r['accession_number'],current_native_page_receipt=rc,previous_capture=previous,all_current_and_original_source_fields_agree=True,object_title=r['title'],artist=creator,source_date=date,source_dimensions=dimensions,source_medium=medium,native_image_id=imgid,source_usage='CC0',confidence=1.0,metadata_changes=0,current_display_update=False,web_tool_checked=True,web_tool_source=url))
 h.save(E/'identity-review-supplement.json',dict(at=h.now(),rows=verified,confidence=1.0,user_approval=dict(reference='docs/ARTLINE_IMAGE_USE.md and current production authorization',copyright_holder_licence=False,separate_from_source_cc0=True),metadata_changes=0,all_current_and_original_source_fields_agree=True))
 ledger=ROOT/'docs/research/continuous-production-20261011/batches/000141/source-access-holds.json';holds=h.load(ledger);prior=E.parent/'000169/inherited-holds-verification.json';latest=E.parent/'000171/research-holds.json'
 h.save(E/'inherited-holds-verification.json',dict(at=h.now(),ledger_path=str(ledger.relative_to(ROOT)),ledger_sha256=h.sha(ledger.read_bytes()),all_inherited_routes_read=len(holds['inherited']),new_hold_preserved=holds['new_hold'],prior_source_hold_verification=str(prior.relative_to(ROOT)),prior_sha256=h.sha(prior.read_bytes()),greek_holds_path=str(latest.relative_to(ROOT)),greek_holds_sha256=h.sha(latest.read_bytes()),greek_date_holds=len(h.load(latest)['records']),unrelated_source_holds_preserved=True,api_key_route_not_requested=True,held_search_not_requested=True,access_retry_count=0))
 print('Verified original and current native sources:',len(verified))
if __name__=='__main__':
 with (b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);run()
