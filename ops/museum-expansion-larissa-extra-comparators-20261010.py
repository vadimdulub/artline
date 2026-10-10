"""Official comparison pages and a captured public Rhodes image link."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageOps,ImageDraw,ImageFont

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-larissa-focused-visual-20261010.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
c,m,RUN,PROOF=v.c,v.m,v.RUN,v.PROOF

def main():
    focus=m.load(RUN/'focused-comparators-001.json.gz')['snapshot'];vis=m.load(RUN/'focused-visual-references-001.json');pages=[]
    ids=[x['artwork_id'] for x in vis['rows'] if x['state']!='captured_for_review']+['42a38a25-5d96-53ee-95ea-60ce01fa9ae3']
    for aid in ids:
        urls=sorted({x['source_url'] for x in focus['citations'] if x['entity_id']==aid and 'nationalgallery.gr/' in x['source_url']})
        if not urls:continue
        assert len(urls)==1
        res=v.get(urls[0]);raw=res.content;body=RUN/'captures'/('extra-'+aid+'.body.gz');assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));soup=BeautifulSoup(raw,'html.parser')
        page=dict(artwork_id=aid,at=m.now(),url=urls[0],final_url=res.url,status=res.status_code,body_reference=c.ref(body),sha256=hashlib.sha256(raw).hexdigest(),text=soup.get_text(' ',strip=True),images=[dict(src=urljoin(res.url,x['src']),alt=x.get('alt')) for x in soup.select('img[src]')])
        og=soup.find('meta',property='og:image');page['og_image']=urljoin(res.url,og['content']) if og and og.get('content') else None
        pages.append(page);m.save(RUN/'extra-page-receipts'/(aid+'.json'),page)
    # Courtould comparison is a distinct documented still-life candidate, not an image source for delivery.
    aid='d6138300-a23b-5d02-879c-8ac6779a7f33';url='https://gallerycollections.courtauld.ac.uk/object-p-1932-sc-179';res=v.get(url);raw=res.content;soup=BeautifulSoup(raw,'html.parser')
    body=RUN/'captures'/('extra-'+aid+'.body.gz');assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));page=dict(artwork_id=aid,at=m.now(),url=url,final_url=res.url,status=res.status_code,body_reference=c.ref(body),sha256=hashlib.sha256(raw).hexdigest(),text=soup.get_text(' ',strip=True),images=[dict(src=urljoin(res.url,x['src']),alt=x.get('alt')) for x in soup.select('img[src]')]);pages.append(page)
    rhodes=m.ROOT/'docs/research/museum-expansion-20261006/native/rhodes-final-20261009/captures/object-8ea36f90-2df1-4e1f-b262-6ee076c1e258-001.body.gz';raw=gzip.decompress(rhodes.read_bytes());assert hashlib.sha256(raw).hexdigest()=='87bca1b29ba6f485dc89f4a8bc531790f8f6dc4b7a43012217de270a26ff4934'
    data=json.loads(raw);url=data['coverFile']['thumbnails']['mediumUrl'];res=v.get(url);res.raise_for_status();image=res.content;path=PROOF/'focused-images/rhodes-greek-funeral-feast.image';assert not path.exists();path.write_bytes(image)
    with Image.open(path) as im:im.load();size=im.size
    m.save(RUN/'rhodes-frame-001.json',dict(at=m.now(),url=url,final_url=res.url,status=res.status_code,path=str(path),sha256=hashlib.sha256(image).hexdigest(),width=size[0],height=size[1],source_reference=c.ref(rhodes),existing_artwork_id='752ef8cd-c530-5691-8498-c0e5dcb99c45'))
    m.save(RUN/'extra-comparator-pages-001.json.gz',dict(at=m.now(),pages=pages,script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(pages=[dict(id=x['artwork_id'],status=x['status'],og=x.get('og_image'),image_count=len(x['images']),text=x['text'][:200]) for x in pages],rhodes_frame=str(path)),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
