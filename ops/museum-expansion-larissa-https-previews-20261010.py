"""Selected museum-supplied SearchCulture HTTPS frames for exact source evidence."""
import concurrent.futures
import hashlib
import importlib.util
import io
import json
import threading
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageOps,ImageDraw,ImageFont

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-larissa-common-v2-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/larissa-delivery-20261010'
STOP=threading.Event()

def fetch(d):
    if STOP.is_set():raise RuntimeError('Provider access hold')
    n=d['number'];src=m.load(c.RESEARCH/'editorial-source-decisions-001.json.gz')['rows'][n-1];assert src['number']==n
    body=m.ROOT/src['source_receipt']['body_path']
    import gzip
    soup=BeautifulSoup(gzip.decompress(body.read_bytes()),'html.parser');node=soup.select_one('img.record-view-thumbnail[src]');assert node
    url=urljoin(src['source_url'],node['src']);assert url.startswith('https://www.searchculture.gr/aggregator/thumbnails/edm-record/larisa_gallery/')
    rp=RUN/'https-preview-receipts'/(str(n).zfill(3)+'.json');assert not rp.exists()
    res=requests.get(url,timeout=(15,40));raw=res.content
    rc=dict(at=m.now(),number=n,url=url,final_url=res.url,status=res.status_code,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),content_type=res.headers.get('Content-Type'),source_id=d['source_id'],native_http_reference=d['original_reference'])
    if res.status_code in [401,403,429]:STOP.set()
    if res.status_code!=200 or not raw or not (rc['content_type']or'').startswith('image/'):
        rc['state']='unavailable';m.save(rp,rc);return rc
    path=PROOF/'https-source-images'/(str(n).zfill(3)+'.jpg');path.parent.mkdir(parents=True,exist_ok=True);assert not path.exists();path.write_bytes(raw)
    with Image.open(io.BytesIO(raw)) as im:im.load();rc.update(width=im.width,height=im.height,format=im.format)
    rc.update(state='captured_pending_visual_comparison',path=str(path),same_bytes_as_native=rc['sha256']==d['original_reference']['sha256'])
    m.save(rp,rc);return rc

def main():
    selected=m.load(c.RESEARCH/'image-delivery-prepared-001.json')['rows'];assert len(selected)==205
    assert not(RUN/'https-preview-selection-001.json').exists()
    m.save(RUN/'https-preview-selection-001.json',dict(at=m.now(),numbers=[x['number'] for x in selected],source_reference=c.ref(c.RESEARCH/'image-delivery-prepared-001.json'),
        reason='Native original URLs are HTTP; the production evidence schema requires HTTPS. An exact-path HTTPS native probe timed out. Use the explicitly displayed museum-supplied SearchCulture image URL, with a new exact-byte and full-frame comparison; never relabel native HTTP bytes as an unverified HTTPS source.',script_reference=c.ref(Path(__file__).resolve())))
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for rc in pool.map(fetch,selected):
            rows.append(rc)
            if len(rows)%30==0:print(json.dumps(dict(selected_https_frames=len(rows),of=len(selected))),flush=True)
    sheets=[];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    for page,start in enumerate(range(0,len(rows),20),1):
        batch=rows[start:start+20];canvas=Image.new('RGB',(1400,1200),'white');draw=ImageDraw.Draw(canvas)
        for k,x in enumerate(batch):
            x0=k%5*280;y0=k//5*300;draw.text((x0+4,y0+4),str(x['number'])+' | HTTPS source',font=font,fill='black')
            if not x.get('path'):draw.text((x0+4,y0+28),'NO FRAME',font=font,fill='red');continue
            with Image.open(x['path']) as im:
                image=ImageOps.contain(im.convert('RGB'),(272,266));canvas.paste(image,(x0+(280-image.width)//2,y0+29+(266-image.height)//2))
        path=PROOF/('https-preview-contact-'+str(page)+'.jpg');assert not path.exists();canvas.save(path,quality=92);sheets.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),numbers=[x['number'] for x in batch]))
    m.save(RUN/'https-preview-frames-001.json',dict(at=m.now(),rows=rows,sheets=sheets,script_reference=c.ref(Path(__file__).resolve()),ready_for_public_attachment=False))
    print(json.dumps(dict(captured=sum(bool(x.get('path')) for x in rows),same_bytes_as_native=sum(x.get('same_bytes_as_native',False) for x in rows),contacts=len(sheets))),flush=True)

if __name__=='__main__':main()
