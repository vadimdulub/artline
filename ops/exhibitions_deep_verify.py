#!/usr/bin/env python3
"""Audit the running loopback research API using genuine source-backed records."""
import json,collections,datetime
from pathlib import Path
import requests
root=Path.home()/'Library/Application Support/Artline/source-metadata/exhibitions-deep-local-20261011'
rows=json.loads((root/'review-corpus.json').read_text())['records'];lookup={r['id']:r for r in rows}
s=requests.Session();base='http://127.0.0.1:8098/api/v1/exhibitions'
seen=[];after=''
while True:
 response=s.get(base,params={'limit':23,'after':after});response.raise_for_status();page=response.json();assert page['total']==len(rows)
 assert len(page['items'])<=23
 seen.extend(r['id'] for r in page['items'])
 if not page['hasMore']:break
 assert page['nextCursor'];after=page['nextCursor']
assert len(seen)==len(set(seen))==len(rows) and set(seen)==set(lookup)
entries=0
for r in rows:
 after='';ids=[]
 while True:
  response=s.get(base+'/'+r['id']+'/entries',params={'limit':17,'after':after});response.raise_for_status();page=response.json()
  assert page['total']==r['entryCount'] and len(page['items'])<=17
  ids.extend(x['id'] for x in page['items'])
  if not page['hasMore']:break
  after=page['nextCursor']
 assert len(ids)==len(set(ids))==r['entryCount']
 entries+=len(ids)
for qs in ['start=2000&end=1800','after=invalid','limit=101','limit=0','person=invalid','artist=invalid','state=invented']:
 assert s.get(base+'?'+qs).status_code==400,qs
assert s.post(base,json={}).status_code==405
assert s.get('http://127.0.0.1:8098/api/v1/auth/session').status_code==404
featured=next(r for r in rows if r.get('featured'));detail=s.get(base+'/'+featured['id']).json();assert detail['related']
for item in detail['related']:
 current={p['artist_id'] for p in featured['participants'] if p.get('artist_id')};other={p['artist_id'] for p in lookup[item['id']]['participants'] if p.get('artist_id')};assert current & other
for theme in ['Abstraction','Cubism','Landscape']:
 data=s.get(base,params={'theme':theme,'limit':100}).json();expected=[r for r in rows if theme in r['research']['concepts']];assert data['total']==len(expected);assert all(theme in r['research']['concepts'] for r in data['items'])
assert s.get(base,params={'source':'moma','theme':'Cubism'}).json()['total']==0
assert s.get(base,params={'collection':'archive','theme':'Cubism'}).json()['total']==sum('Cubism' in r['research']['concepts'] for r in rows)
archive=s.get(base,params={'collection':'archive','limit':5}).json();assert archive['total']>=100000 and len(archive['items'])==5
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'uniqueExhibitionsPaged':len(seen),'entriesPaged':entries,'duplicateExhibitionOrEntryIDs':0,'invalidQueriesRejected':7,'writeRequestsRejected':True,'relatedArtistsVerified':len(detail['related']),'themeFiltersVerified':5,'fullArchiveStillAvailable':archive['total'],'productionWrites':0,'localCatalogueWrites':0}
(root/'api-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
