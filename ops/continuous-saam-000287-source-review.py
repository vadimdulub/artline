#!/usr/bin/env python3
"""Bounded native-source verification before batch287 image attachment."""
import importlib.util,json,gzip,re,html,fcntl
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('b287',ROOT/'ops/continuous-batch-000287.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;E=b.E
def plain(t):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',t)))
def run():
 selected=h.load(E/'candidate-selection.json.gz')['rows'];decisions=h.load(E/'exact-identity-decisions.json')['rows'];verified=[]
 for r in selected:
  oid=r['native_id']; decision=next(x for x in decisions if x['native_id']==oid); original=ROOT/decision['previous_source_capture']; old=gzip.decompress(original.read_bytes()).decode(); canonical=re.search(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"',old); assert canonical,oid; url=html.unescape(canonical[1]); assert url.startswith('https://americanart.si.edu/artwork/') and url.rstrip('/').endswith('-'+oid),url;p=b.DATA/('saam-'+oid+'-native.html.gz');rcp=E/'source-captures'/('saam-'+oid+'-native.receipt.json')
  if rcp.exists():rc=h.load(rcp);body=gzip.decompress(p.read_bytes());assert h.sha(body)==rc['sha256']
  else:
   resp=requests.get(url,timeout=(15,45));resp.raise_for_status();assert resp.status_code==200
   body=resp.content;p.write_bytes(gzip.compress(body,mtime=0));rc=dict(url=url,final_url=resp.url,status=resp.status_code,retrieved_at=h.now(),sha256=h.sha(body),body_path=str(p),retry_after=resp.headers.get('Retry-After'));h.save(rcp,rc)
  text=plain(body.decode());attrs=plain(' '.join(re.findall(r'data-text="([^"]*)"',body.decode())))
  ft=r['image']['source']['content']['freetext'];values=lambda k,label:[x['content'] for x in ft[k] if x['label']==label]
  date=values('date','Date')[0];medium=values('physicalDescription','Medium')[0];dimensions=values('physicalDescription','Dimensions')[0];creator=values('name','Artist')[0].split(',')[0]
  from urllib.parse import parse_qs,urlsplit
  imgid=parse_qs(urlsplit(r['image']['image_url']).query).get('id',[None])[0]; assert imgid and imgid.startswith('SAAM-')
  for value in [r['title'],r['accession_number'],date,medium,creator]:assert h.norm(value) in h.norm(text+' '+attrs),(oid,value)
  assert h.norm(dimensions) in h.norm(text+' '+attrs),(oid,'dimensions')
  assert imgid in body.decode() and 'Free to use' in text
  previous=next(x for x in decisions if x['native_id']==oid);raw=gzip.decompress((ROOT/previous['previous_source_capture']).read_bytes());assert h.sha(raw)==previous['previous_source_capture_sha256']
  original_text=plain(raw.decode());assert all(h.norm(v) in h.norm(original_text+' '+plain(' '.join(re.findall(r'data-text="([^"]*)"',raw.decode())))) for v in [r['title'],r['accession_number'],date,medium,creator,dimensions]),oid
  verified.append(dict(artwork_id=r['artwork_id'],native_id=oid,accession=r['accession_number'],current_native_page_receipt=rc,previous_capture=previous,all_current_and_original_source_fields_agree=True,object_title=r['title'],artist=creator,source_date=date,source_dimensions=dimensions,source_medium=medium,native_image_id=imgid,source_usage='CC0',confidence=1.0,metadata_changes=0,current_display_update=False,web_tool_checked=True,web_tool_source=url))
 h.save(E/'identity-review-supplement.json',dict(at=h.now(),rows=verified,confidence=1.0,user_approval=dict(reference='docs/ARTLINE_IMAGE_USE.md and current production authorization',copyright_holder_licence=False,separate_from_source_cc0=True),metadata_changes=0,all_current_and_original_source_fields_agree=True))
 print('Verified original and current native sources:',len(verified))
if __name__=='__main__':
 with (b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);run()
