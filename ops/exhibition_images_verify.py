#!/usr/bin/env python3
"""Check every actual local image, source object and exhibition attachment."""
import collections
import hashlib
import json
from PIL import Image
import requests
import exhibition_images_local as x

corpus=x.c.load(x.DATA/'review-corpus.json');original=x.c.load(x.DATA/'baseline.json.gz')
before={a['id']:a for a in original['artworks']}
outcomes={p.stem:x.c.load(p) for folder in ['images','museum-images','reviewed-images'] for p in (x.DATA/folder).glob('*.json')}
original_hashes=collections.defaultdict(list);checked=0;total_bytes=0
for a in corpus['artworks']:
    old=before[a['id']]
    for field in ['title','creator','date','medium','artworkId','artists','appearances']:
        assert old[field]==a[field],(a['id'],field)
    if old.get('image'):
        assert all(old.get(key)==a.get(key) for key in ['image','imageCredit','imageLicense','imageSource'])
        continue
    record=outcomes[a['id']];assert record['state']=='prepared',(a['id'],record)
    assert record['sourceArtworkID']==a['sourceArtworkID'] and record['provider']==a['provider']
    assert record['image']==a['image'] and a['image'].startswith('/assets/artworks/exhibitions-local/')
    path=x.c.ROOT/'apps/web/public'/a['image'].lstrip('/');content=path.read_bytes()
    assert 0<len(content)<=100000 and len(content)==record['bytes']
    assert hashlib.sha256(content).hexdigest()==record['sha256']
    raw=__import__('pathlib').Path(record['originalPath']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==record['originalSHA256']
    with Image.open(path) as image:
        assert image.size==(record['width'],record['height']) and image.format=='JPEG'
        assert abs(image.width/image.height-record['sourceWidth']/record['sourceHeight'])<.025
        image.verify()
    original_hashes[record['originalSHA256']].append(a['id']);checked+=1;total_bytes+=len(content)

artworks={a['id']:a for a in corpus['artworks']};appearances=0
for event in corpus['records']:
    assert event['illustratedArtworkCount']==len(event['entries']) and event['previewWorks']
    for entry in event['entries']:
        assert entry['image']==artworks[entry['localArtworkId']]['image'];appearances+=1
    assert len(event['previewWorks'])<=3 and all(e['image'] for e in event['previewWorks'])

session=requests.Session();http_checked=0
for event in corpus['records']:
    response=session.get('http://127.0.0.1:8098/api/v1/exhibitions/'+event['id'],timeout=15);response.raise_for_status()
    assert response.json()['illustratedArtworkCount']==len(event['entries'])
    for preview in event['previewWorks'][:1]:
        response=session.get('http://127.0.0.1:3107'+preview['image'],timeout=20);response.raise_for_status()
        assert response.headers['Content-Type'].startswith('image/') and response.content
        http_checked+=1

result=dict(at=x.c.now(),exhibitions=len(corpus['records']),exhibitionsWithAllEntriesIllustrated=len(corpus['records']),
  illustratedArtworks=len(artworks),illustratedAppearances=appearances,newImagesChecked=checked,existingImagesPreserved=sum(bool(a.get('image')) for a in before.values()),
  newBytes=total_bytes,allNewImagesUnder100000Bytes=True,originalAndDerivativeHashesVerified=True,
  metadataAndParticipationUnchanged=True,exhibitionImageResponsesChecked=http_checked,
  sharedOriginalImageGroups=sum(len(ids)>1 for ids in original_hashes.values()),databaseWrites=0)
(x.DATA/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
