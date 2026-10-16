#!/usr/bin/env python3
"""Selected exhibition images in local storage. No database or production writes."""
import argparse
import collections
import concurrent.futures
import hashlib
import io
import json
import threading
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests
from PIL import Image, ImageOps
from bs4 import BeautifulSoup
import exhibition_artworks_local as works

c=works.c
DATA=works.DATA.parent/'exhibition-images-local-20261012'
ASSETS=c.ROOT/'apps/web/public/assets/artworks/exhibitions-local'
ALLOWED={'d32dm0rphc51dk.cloudfront.net','openaccess-cdn.clevelandart.org','piction.clevelandart.org'}
STOP=threading.Event()
LOCAL=threading.local()
Image.MAX_IMAGE_PIXELS=40_000_000


def prepare():
    if not (DATA/'baseline.json.gz').exists():c.save(DATA/'baseline.json.gz',c.load(works.DATA/'review-corpus.json'))
    corpus=c.load(DATA/'baseline.json.gz');sources={}
    accepted=set(c.load(works.BASE/'accepted.json'))
    for native in accepted:
        saved=c.load(works.BASE/'shows'/f'{native}.json')
        for edge in saved['show']['artworksConnection']['edges']:
            obj=edge['node'];sources[obj['internalID']]=dict(object=obj,receipt=saved['receipt'])
    selected=[]
    for artwork in corpus['artworks']:
        if artwork.get('image'):continue
        source_id=artwork['sourceArtworkID'];provider=artwork['provider']
        if provider=='artsy':
            source=sources[source_id];obj=source['object']
            image_url=(obj.get('image') or {}).get('url');rights=obj.get('imageRights') or None
            credit=f"{artwork.get('creator') or 'Creator not recorded'}. {artwork.get('title') or 'Title not recorded'}. Image supplied with the Artsy object record."
        else:
            source=c.load(works.DATA/'cleveland'/f'{source_id}.json.gz');obj=source['artwork']
            image_url=((obj.get('images') or {}).get('web') or {}).get('url');rights=obj.get('copyright') or obj.get('share_license_status')
            credit=f"{artwork.get('creator') or 'Creator not recorded'}. {artwork.get('title') or 'Title not recorded'}. The Cleveland Museum of Art; {obj.get('creditline') or ''}."
        if image_url and (urlparse(image_url).scheme!='https' or urlparse(image_url).hostname not in ALLOWED):raise RuntimeError('Unexpected image source host')
        selected.append(dict(id=artwork['id'],sourceArtworkID=source_id,provider=provider,imageURL=image_url,sourceURL=artwork['sourceURL'],
          rights=rights,credit=credit,sourceReceipt=source['receipt'],scope='User-requested missing images for the selected local exhibition preview, 12 October 2026; not a production delivery or independent licence.'))
    c.save(DATA/'selected.json.gz',selected)
    print(json.dumps(dict(selected=len(selected),withSourceImage=sum(bool(s['imageURL']) for s in selected),existingImagesPreserved=sum(bool(a.get('image')) for a in corpus['artworks']))))


def derivative(raw,reviewed_extreme=False):
    with Image.open(io.BytesIO(raw)) as check:check.verify()
    with Image.open(io.BytesIO(raw)) as original:
        original.load();source_size=original.size
        if min(source_size)<=0 or (not reviewed_extreme and (min(source_size)<80 or max(source_size)/min(source_size)>15)):raise ValueError('Image dimensions require individual review')
        image=ImageOps.exif_transpose(original).convert('RGB')
    image.thumbnail((1400,1400),Image.Resampling.LANCZOS)
    while min(image.size)>=(1 if reviewed_extreme else 80):
        for quality in [88,82,76,70,64,58,52]:
            out=io.BytesIO();image.save(out,'JPEG',quality=quality,optimize=True,progressive=True)
            if len(out.getvalue())<=100000:return out.getvalue(),source_size,image.size
        image.thumbnail((round(image.width*.82),round(image.height*.82)),Image.Resampling.LANCZOS)
    raise ValueError('Could not prepare a complete-frame image within the size bound')


def one(item,folder='images'):
    record_path=DATA/folder/f"{item['id']}.json"
    if record_path.exists():return c.load(record_path)
    result=dict(item)
    if not item['imageURL']:
        result.update(state='missing_source_image');c.save(record_path,result);return result
    if STOP.is_set():return dict(state='provider_hold')
    try:
        if not hasattr(LOCAL,'session'):
            LOCAL.session=requests.Session()
            LOCAL.session.headers.update({'User-Agent':'ArtlineLocalExhibitionResearch/1.0'})
        for attempt in range(3):
            if STOP.is_set():return dict(state='provider_hold')
            response=LOCAL.session.get(item['imageURL'],timeout=(10,40),stream=True,allow_redirects=False)
            if response.status_code in [401,403,429]:
                STOP.set();raise ValueError(f'Provider access hold: {response.status_code}')
            if response.status_code>=500 and attempt<2:
                response.close();time.sleep(2*(attempt+1));continue
            response.raise_for_status();break
        if response.status_code!=200:raise ValueError(f'Unexpected HTTP status {response.status_code}')
        raw=bytearray()
        for chunk in response.iter_content(128*1024):
            raw.extend(chunk)
            if len(raw)>25_000_000:raise ValueError('Source image exceeds selected download bound')
        response.close();raw=bytes(raw);sha=hashlib.sha256(raw).hexdigest()
        original=DATA/'originals'/f'{sha}.bin'
        original.parent.mkdir(parents=True,exist_ok=True)
        if not original.exists() or hashlib.sha256(original.read_bytes()).hexdigest()!=sha:
            temp=original.with_suffix(f'.{threading.get_ident()}.tmp');temp.write_bytes(raw);temp.replace(original)
        prepared,source_size,size=derivative(raw,bool(item.get('dimensionReview')));digest=hashlib.sha256(prepared).hexdigest()
        path=ASSETS/f"{item['id']}-{digest[:16]}.jpg";path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():
            temp=path.with_suffix('.tmp');temp.write_bytes(prepared);temp.replace(path)
        result.update(state='prepared',image='/assets/artworks/exhibitions-local/'+path.name,width=size[0],height=size[1],bytes=len(prepared),sha256=digest,
          originalPath=str(original),originalSHA256=sha,sourceWidth=source_size[0],sourceHeight=source_size[1],retrievedAt=c.now(),
          modification='Full-frame proportional resize and JPEG compression; no crop, reconstruction or generated content.')
    except (requests.RequestException,ValueError,OSError) as exc:
        result.update(state='needs_review',issue=str(exc))
    c.save(record_path,result)
    time.sleep(.15)
    return result


def download():
    selected=c.load(DATA/'selected.json.gz');stats=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for i,result in enumerate(pool.map(one,selected),1):
            stats[result['state']]+=1
            if i%100==0 or i==len(selected):print(json.dumps(dict(completed=i,total=len(selected),states=dict(stats))),flush=True)
    if STOP.is_set():raise RuntimeError('A source access hold stopped this image pass; inspect the saved outcome before continuing.')


def museum():
    for item in c.load(DATA/'selected.json.gz'):
        if item['provider']!='cleveland' or item['imageURL']:continue
        obj=c.load(works.DATA/'cleveland'/f"{item['sourceArtworkID']}.json.gz")['artwork']
        url=obj['url'].replace('https://clevelandart.org/','https://www.clevelandart.org/')
        raw,receipt=c.capture(url);soup=BeautifulSoup(raw,'html.parser')
        tag=soup.select_one('meta[property="og:image"]');image_url=tag.get('content') if tag else None
        if not image_url:continue
        parsed=urlparse(image_url);filename=(parse_qs(parsed.query).get('f') or [''])[0].replace('\\','/').rsplit('/',1)[-1]
        legacy_path=DATA/'museum-image-legacy-filename-evidence.json'
        legacy=c.load(legacy_path) if legacy_path.exists() else {}
        reviewed_legacy=(legacy.get('sourceArtworkID')==item['sourceArtworkID'] and legacy.get('accession')==obj['accession_number'] and legacy.get('imageFilename')==filename and legacy.get('imageURL')==image_url)
        if parsed.scheme!='https' or parsed.hostname!='piction.clevelandart.org' or (filename!=obj['accession_number']+'_w.jpg' and not reviewed_legacy):
            raise RuntimeError('Museum page image does not identify the exact accession')
        selected=dict(item,imageURL=image_url,pageImageReceipt=receipt)
        if reviewed_legacy:selected['individualReview']='Exact museum object page primary image under its legacy filename; original visually checked against the page description.'
        result=one(selected,'museum-images')
        print(json.dumps(dict(id=item['id'],accession=obj['accession_number'],state=result['state'])),flush=True)
        if STOP.is_set():raise RuntimeError('Museum image access hold')


def attach(corpus):
    records={p.stem:c.load(p) for p in (DATA/'images').glob('*.json')}
    records.update({p.stem:c.load(p) for p in (DATA/'museum-images').glob('*.json')})
    records.update({p.stem:c.load(p) for p in (DATA/'reviewed-images').glob('*.json')})
    by_id={a['id']:a for a in corpus.get('artworks',[])}
    for identity,artwork in by_id.items():
        item=records.get(identity)
        if artwork.get('image') or not item or item['state']!='prepared':continue
        path=c.ROOT/'apps/web/public'/item['image'].lstrip('/')
        if not path.is_file() or path.stat().st_size!=item['bytes']:raise RuntimeError('Missing or altered prepared image')
        artwork.update(image=item['image'],imageCredit=item['credit'],imageLicense=item['rights'] or 'Rights label not supplied',imageSource=item['sourceURL'],imageWidth=item['width'],imageHeight=item['height'],
          localImageEvidence=dict(sourceObjectID=item['sourceArtworkID'],originalSHA256=item['originalSHA256'],sha256=item['sha256'],retrievedAt=item['retrievedAt'],scope=item['scope'],modification=item['modification']))
    for event in corpus['records']:
        for entry in event['entries']:
            obj=by_id.get(entry.get('localArtworkId'))
            if obj:
                for key in ['image','imageCredit','imageLicense','imageSource','imageWidth','imageHeight']:
                    if key in obj:entry[key]=obj[key]
        pictures=[e for e in event['entries'] if e.get('image')]
        event['illustratedArtworkCount']=len(pictures)
        event['previewWorks']=pictures[:3]
    # Browser/API DTOs never carry originals, provider file URLs or local disk paths.
    return corpus


def build():
    corpus=attach(c.load(works.DATA/'review-corpus.json'))
    for path in [DATA/'review-corpus.json',works.BASE/'review-corpus.json']:
        temp=path.with_suffix('.tmp');temp.write_text(json.dumps(corpus,ensure_ascii=False));temp.replace(path)
    outcomes={p.stem:c.load(p) for folder in ['images','museum-images','reviewed-images'] for p in (DATA/folder).glob('*.json')}
    outcomes=list(outcomes.values())
    report=dict(exhibitions=len(corpus['records']),withImages=sum(bool(r['illustratedArtworkCount']) for r in corpus['records']),
      artworkObjects=len(corpus['artworks']),illustratedObjects=sum(bool(a.get('image')) for a in corpus['artworks']),
      illustratedAppearances=sum(r['illustratedArtworkCount'] for r in corpus['records']),states=dict(collections.Counter(r['state'] for r in outcomes)),
      newImageBytes=sum(r.get('bytes',0) for r in outcomes),localOnly=True,databaseWrites=0)
    (DATA/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','download','museum','build']);args=parser.parse_args()
    {'prepare':prepare,'download':download,'museum':museum,'build':build}[args.action]()
