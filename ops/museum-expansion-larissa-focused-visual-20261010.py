"""Capture bounded comparison images for the53 selected existing artwork identities."""
import collections
import concurrent.futures
import gzip
import hashlib
import importlib.util
import io
import json
import threading
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageOps,ImageDraw,ImageFont

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-larissa-common-v2-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/larissa-delivery-20261010'
LOCK=threading.Lock();HOLDS=set()

def get(url):
    host=urlparse(url).netloc
    with LOCK:assert host not in HOLDS,'Source access hold: '+host
    res=requests.get(url,timeout=(15,45))
    if res.status_code in [401,403,429]:
        with LOCK:HOLDS.add(host)
    return res

def one(v):
    art,media,citations=v;aid=art['id'];rc=dict(at=m.now(),artwork_id=aid,title=art['title'],date_display=art['date_display'],primary_media_id=art['primary_media_id'],purpose='Internal exact-work/version comparison only; no public reuse or creation date inferred.')
    dest=RUN/'focused-visual-receipts'/(aid+'.json');assert not dest.exists()
    try:
        if media:
            url='https://artlines.org'+media['storage_path'] if media['storage_kind']=='local' else media['delivery_url'];rc['existing_media']=media
        else:
            urls=sorted({x['source_url'] for x in citations if x['source_url'] and 'wikiart.org/' in x['source_url']})
            assert len(urls)==1,'No unique observed WikiArt source page for image lookup'
            page=get(urls[0]);raw=page.content;path=RUN/'captures'/('focused-'+aid+'.body.gz');path.parent.mkdir(parents=True,exist_ok=True);assert not path.exists();path.write_bytes(gzip.compress(raw,mtime=0))
            rc['page_receipt']=dict(url=urls[0],final_url=page.url,status=page.status_code,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body_path=str(path.relative_to(m.ROOT)))
            page.raise_for_status();soup=BeautifulSoup(raw,'html.parser');node=soup.find('meta',property='og:image');assert node and node.get('content'),'No explicit artwork image'
            url=urljoin(page.url,node['content']);rc['page_title']=soup.title.get_text(' ',strip=True) if soup.title else None
        image=get(url);raw=image.content;rc.update(image_url=url,final_image_url=image.url,image_status=image.status_code,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),content_type=image.headers.get('Content-Type'))
        image.raise_for_status();assert len(raw)<=8000000
        with Image.open(io.BytesIO(raw)) as im:im.load();rc.update(width=im.width,height=im.height,format=im.format)
        path=PROOF/'focused-images'/(aid+'.image');path.parent.mkdir(parents=True,exist_ok=True);assert not path.exists();path.write_bytes(raw);rc.update(path=str(path),state='captured_for_review')
    except Exception as e:rc.update(state='unavailable',error_type=type(e).__name__,error=str(e))
    m.save(dest,rc);return rc

def main():
    focus=m.load(RUN/'focused-comparators-001.json.gz');snap=focus['snapshot'];media={x['id']:x for x in snap['media_assets']};cites=collections.defaultdict(list)
    for x in snap['citations']:cites[x['entity_id']].append(x)
    inputs=[(a,media.get(a['primary_media_id']),cites[a['id']]) for a in snap['artworks']];assert len(inputs)==53
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        rows=[]
        for rc in pool.map(one,inputs):
            rows.append(rc)
            if len(rows)%10==0:print(json.dumps(dict(comparator_frames_processed=len(rows),captured=sum(x['state']=='captured_for_review' for x in rows))),flush=True)
    by={r['artwork_id']:r for r in rows};src={x['number']:x for x in m.load(c.RESEARCH/'image-delivery-prepared-001.json')['rows']};sheets=[]
    originals={x['number']:x for x in m.load(c.RESEARCH/'visual-references-001.json')['rows']}
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    for group,info in focus['groups'].items():
        items=[dict(label='LARISSA '+str(n),path=originals[n].get('path'),number=n) for n in info['numbers']]+[dict(label='EXISTING '+a[:8],path=by[a].get('path'),artwork_id=a,title=by[a]['title']) for a in info['ids']]
        for page,start in enumerate(range(0,len(items),16),1):
            batch=items[start:start+16];canvas=Image.new('RGB',(1400,1280),'white');draw=ImageDraw.Draw(canvas)
            for k,x in enumerate(batch):
                x0=k%4*350;y0=k//4*320;draw.text((x0+4,y0+4),x['label'],font=font,fill='black');draw.text((x0+4,y0+23),x.get('title','')[:42],font=font,fill='black')
                if not x.get('path'):draw.text((x0+4,y0+55),'NO COMPARISON FRAME',font=font,fill='red');continue
                with Image.open(x['path']) as im:
                    thumb=ImageOps.contain(im.convert('RGB'),(342,268));canvas.paste(thumb,(x0+(350-thumb.width)//2,y0+48+(268-thumb.height)//2))
            path=PROOF/('comparison-'+group+'-'+str(page)+'.jpg');assert not path.exists();canvas.save(path,quality=93);sheets.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),group=group,items=batch))
    m.save(RUN/'focused-visual-references-001.json',dict(at=m.now(),rows=rows,sheets=sheets,access_holds=sorted(HOLDS),script_reference=c.ref(Path(__file__).resolve()),source_reference=c.ref(RUN/'focused-comparators-001.json.gz')))
    print(json.dumps(dict(captured=sum(x['state']=='captured_for_review' for x in rows),unavailable=sum(x['state']!='captured_for_review' for x in rows),sheets=len(sheets),access_holds=sorted(HOLDS))),flush=True)

if __name__=='__main__':main()
