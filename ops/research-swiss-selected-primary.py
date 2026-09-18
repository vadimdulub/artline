#!/usr/bin/env python3
"""Capture exact Kunsthaus Zürich objects selected in a country research round.

Read-only source research. Museum dates and attribution changes are preserved
for individual editorial review; current-display text is not a holding claim.
"""
import argparse,importlib.util,json,os
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('g',Path(__file__).with_name('research-german-primary-objects.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);CORE=m.m.core
def capture(code,number):
 delivery=m.x.BASE/code/f'round-{number:02}'/'delivery';family=os.environ.get('ARTLINE_SWISS_PRIMARY_VERSION','swiss-primary');assert family in ('swiss-primary','swiss-primary-v2');folder=delivery/family;records=[]
 for f in sorted((delivery/'ready').glob('*.json')):
  r=json.loads(f.read_text())['record'];urls=[u for u in m.m.r.values(r['entity'],'P973') if isinstance(u,str) and urlparse(u).hostname=='collection.kunsthaus.ch' and '/collection/item/' in u]
  if len(urls)!=1:continue
  dest=folder/f.name
  if dest.exists():records.append(json.loads(dest.read_text()));continue
  e=dict(qid=r['qid'],at=CORE.now(),ready_sha256=CORE.sha(f.read_bytes()),museum='kunsthaus-zurich')
  try:
   soup,receipt=g.page(urls[0],folder/'captures',r['qid']);h=soup.select_one('h1');assert h
   fields={x.select_one('.CollectionItem-detailsItemLabel').get_text(' ',strip=True):x.select_one('.CollectionItem-detailsItemText').get_text(' ',strip=True) for x in soup.select('.CollectionItem-detailsItem') if x.select_one('.CollectionItem-detailsItemLabel') and x.select_one('.CollectionItem-detailsItemText')}
   makers=[dict(name=a.get_text(' ',strip=True),url='https://collection.kunsthaus.ch'+a['href'],context=a.parent.get_text(' ',strip=True)) for a in soup.select('a[href*="/artists/artist/"]')]
   makers=list({a['url']:a for a in makers}.values());date=h.parent.find('p');title=h.get_text(' ',strip=True)
   acc=fields.get('Inventory number');sameacc=bool(acc and r['accession'] and m.m.accession_key(acc)==m.m.accession_key(r['accession']))
   creator_match=len(makers)==1 and m.m.r.norm(makers[0]['name'])==m.m.r.norm(r['creator_label'])
   for node in soup(['script','style','nav','footer']):node.decompose()
   e.update(receipt=receipt,object=dict(title=title,date=date.get_text(' ',strip=True) if date else None,accession=acc,creator=makers[0]['name'] if len(makers)==1 else None,makers=makers,fields=fields,source_text=soup.get_text(' ',strip=True)),accession_match=sameacc,creator_match=creator_match,review='primary_object_and_creator_corroborated' if sameacc and creator_match else 'individual_primary_identity_review_required')
  except Exception as error:e.update(review='source_unavailable',reason=type(error).__name__+': '+str(error)[:300])
  CORE.save_new(dest,e);records.append(e)
 CORE.save_new(delivery/(family+'-review.json'),dict(at=CORE.now(),records=records,policy='Exact selected museum object pages only. Dates, ownership and attribution require individual review; display information is not published by this adapter.'))
 print(code,number,'Swiss primary',len(records),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--country',default='CH');p.add_argument('--round',type=int,required=True);a=p.parse_args();capture(a.country,a.round)
