#!/usr/bin/env python3
"""Validate every selected source object and its paged bidirectional API links."""
import collections
import json
import requests
import exhibition_artworks_local as x

corpus=x.c.load(x.DATA/'review-corpus.json')
from exhibition_images_local import DATA as IMAGE_DATA, attach
if (IMAGE_DATA/'selected.json.gz').exists():corpus=attach(corpus)
baseline=x.c.load(x.DATA/'baseline.json.gz')
old_entries={e['id']:e for r in baseline['records'] for e in r['entries']}
artworks={a['id']:a for a in corpus['artworks']}
s=requests.Session();base='http://127.0.0.1:8098/api/v1/exhibitions'

def get(path,params=None):
    response=s.get(base+path,params=params,timeout=15);response.raise_for_status();return response.json()

seen_entries=set();participation=collections.Counter()
for event in corpus['records']:
    assert event['entries']
    detail=get('/'+event['id']);assert detail['participationCounts']==event['participationCounts']
    expected={e['id']:e for e in event['entries']};actual={};after=''
    while True:
        page=get('/'+event['id']+'/entries',{'limit':17,'after':after});assert len(page['items'])<=17 and page['total']==len(expected)
        for entry in page['items']:
            assert entry['id'] not in actual and entry==expected[entry['id']]
            actual[entry['id']]=entry
            old=old_entries[entry['id']]
            for field in ['title','artworkId']:
                assert entry[field]==old[field],(entry['id'],field)
            if old.get('image'):assert entry['image']==old['image']
            if old.get('date'):assert entry['date']==old['date']
            assert entry['localArtworkId'] in artworks
            assert any(a['id']==entry['id'] and a['exhibitionId']==event['id'] for a in artworks[entry['localArtworkId']]['appearances'])
            participation[entry['participation']]+=1
        if not page['hasMore']:break
        after=page['nextCursor'];assert after
    assert set(actual)==set(expected)
    assert not seen_entries.intersection(actual);seen_entries.update(actual)
    confirmed=get('/'+event['id']+'/entries',{'limit':100,'participation':'exhibited'})
    assert confirmed['total']==event['participationCounts'].get('exhibited',0)
    assert all(e['participation']=='exhibited' for e in confirmed['items'])
print('All exhibitions and evidence filters verified',flush=True)

paged=0;total_appearances=0
for i,artwork in enumerate(artworks.values()):
    detail=get('/artworks/'+artwork['id'])
    assert 'appearances' not in detail and detail=={k:v for k,v in artwork.items() if k!='appearances'}
    seen=[];after=''
    while True:
        page=get('/artworks/'+artwork['id']+'/exhibitions',{'limit':2,'after':after})
        assert page['total']==artwork['appearanceCount'] and len(page['items'])<=2
        seen.extend(page['items'])
        if not page['hasMore']:break
        after=page['nextCursor'];assert after;paged+=1
    assert seen==artwork['appearances'] and len({a['id'] for a in seen})==len(seen)
    total_appearances+=len(seen)
    if i%1000==0:print('Artwork objects verified',i+1,flush=True)
assert total_appearances==len(seen_entries)
one=next(iter(artworks));event=corpus['records'][0]['id']
for path,status in [('/artworks/invalid',404),('/artworks/00000000-0000-0000-0000-000000000000',404),
                    (f'/artworks/{one}/exhibitions?after=bad',400),(f'/artworks/{one}/exhibitions?limit=101',400),
                    (f'/artworks/{one}/exhibitions?limit=0',400),(f'/artworks/{one}/unknown',404),
                    (f'/{event}/entries?participation=invented',400)]:
    assert s.get(base+path,timeout=10).status_code==status,path
assert s.post(base+'/artworks/'+one,json={},timeout=10).status_code==405
result=dict(at=x.c.now(),exhibitions=len(corpus['records']),artworkObjects=len(artworks),entries=len(seen_entries),
  appearances=total_appearances,participation=dict(participation),extraAppearancePages=paged,
  invalidRequestsRejected=7,writeRequestsRejected=True,originalTitlesDatesImagesAndCanonicalLinksPreserved=True,
  databaseWrites=0)
(x.DATA/'api-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
