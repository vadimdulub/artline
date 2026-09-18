#!/usr/bin/env python3
"""Primary Met metadata for selected, ID-scoped artworks; no DB/image writes."""
import argparse,importlib.util,json,re,time,os
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);x=m.x;CORE=m.m.core
def capture(code,number):
 delivery=x.BASE/code/f'round-{number:02}'/'delivery';family=os.environ.get('ARTLINE_MET_PRIMARY_VERSION','met-primary');assert family in ('met-primary','met-primary-v2');folder=delivery/family;out=[]
 if (delivery/(family+'-review.json')).exists():return
 for f in sorted((delivery/'ready').glob('*.json')):
  r=json.loads(f.read_text())['record'];ids=x.r.values(r['entity'],'P3634')
  if len(ids)!=1 or not str(ids[0]).isdigit():continue
  dest=folder/f.name
  if dest.exists():out.append(json.loads(dest.read_text()));continue
  q=r['qid'];e=dict(qid=q,at=CORE.now(),museum='met',ready_sha256=CORE.sha(f.read_bytes()),review='primary_review_required');rawpath=x.SESSION_BASE/'primary-museums/met-selected'/(q+'.raw.json');rp=rawpath.with_suffix('.receipt.json')
  try:
   url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+str(ids[0])
   if rawpath.exists() and rp.exists():
    raw=rawpath.read_bytes();receipt=json.loads(rp.read_text());assert CORE.sha(raw)==receipt['sha256'];data=json.loads(raw)
   elif rawpath.exists():
    # An earlier selected capture may have its receipt in the round artifact.
    sources=list(x.SESSION_BASE.glob('*/??/round-*/delivery/british-primary/'+q+'.json'));assert len(sources)==1
    old=json.loads(sources[0].read_text());raw=rawpath.read_bytes();receipt=old['receipt'];assert CORE.sha(raw)==receipt['sha256'] and receipt['url']==url;data=json.loads(raw);CORE.save_new(rp,receipt)
   else:
    time.sleep(1.5);res=requests.get(url,timeout=(15,45));res.raise_for_status();raw=res.content;assert len(raw)<2_000_000;data=res.json();receipt=dict(url=res.url,retrieved_at=CORE.now(),bytes=len(raw),sha256=CORE.sha(raw),status=res.status_code);CORE.save_new(rawpath,raw);CORE.save_new(rp,receipt)
   assert data['objectID']==int(ids[0]);acc=data.get('accessionNumber');sameacc=bool(acc and r['accession'] and m.m.accession_key(acc)==m.m.accession_key(r['accession']))
   name=data.get('artistDisplayName','');artisturl=data.get('artistWikidata_URL','');names={x.r.norm(v) for v in x.r.labels(r['creator_entity'])};exactname=x.r.norm(name) in names;authority=artisturl.rstrip('/').endswith('/'+r['creator_qid']);qualified=bool(re.search(r'attributed|workshop|circle|school|after|copy|and |;|unknown|anonymous',name,re.I))
   e.update(receipt=receipt,data=data,object=dict(accession=acc,title=data.get('title'),creator=name,date=data.get('objectDate'),date_begin=data.get('objectBeginDate'),date_end=data.get('objectEndDate'),type=data.get('classification'),medium=data.get('medium'),dimensions=data.get('dimensions'),artist_nationality=data.get('artistNationality'),artist_wikidata_url=artisturl,primary_image=data.get('primaryImage'),is_public_domain=data.get('isPublicDomain')),accession_match=sameacc,creator_match=bool((authority or exactname) and not qualified),review='primary_object_and_creator_corroborated' if sameacc and (authority or exactname) and not qualified else 'individual_primary_identity_review_required',policy='Museum accession/objectID and explicit maker crosswalk. Prototype or artist lifespan dates are not automatically interpreted as creation. No display assertion, automatic nationality replacement or image download.')
  except Exception as error:e.update(reason=type(error).__name__+': '+str(error)[:350])
  CORE.save_new(dest,e);out.append(e);print(code,number,'Met',q,e['review'],flush=True)
 CORE.save_new(delivery/(family+'-review.json'),dict(at=CORE.now(),records=out))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--country',required=True);p.add_argument('--round',type=int,required=True);a=p.parse_args();capture(a.country,a.round)
