"""Low-resolution identity review for selected metadata; no publication/upload."""
import collections
import concurrent.futures
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageDraw,UnidentifiedImageError

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-athens-city-photographs-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF=c.m,c.RUN,c.PROOF

def main():
    assert not(RUN/'visual-references-001.json').exists()
    allrows=m.load(RUN/'selected-source-records-001.json.gz')['rows']
    rows=allrows;assert len(rows)==65
    selection=RUN/'visual-selection-001.json'
    if not selection.exists():m.save(selection,dict(at=m.now(),numbers=[x['number'] for x in rows],skipped={},source_reference=c.ref(RUN/'selected-source-records-001.json.gz'),policy='65selected source thumbnails for capture/physical-print/version and duplicate review only. Source dates1960–1970exclude these from the pre1956Greek image-delivery selection; no upload or preparation for delivery.'))
    folder=PROOF/'identity-thumbnails';folder.mkdir(parents=True,exist_ok=True)
    def fetch(row):
        num=row['number']
        rp=RUN/'visual-image-receipts'/(str(num).zfill(3)+'.json');dest=folder/(str(num).zfill(3)+'.jpg')
        if rp.exists():
            value=m.load(rp)
            if value.get('image_decode_failed'):return None
            assert value['status']==200 and hashlib.sha256(dest.read_bytes()).hexdigest()==value['sha256'];return value
        url=row['thumbnail_url'];assert url and url.startswith('https://www.searchculture.gr/aggregator/thumbnails/edm-record/')
        response=requests.get(url,timeout=(15,45));raw=response.content;value=dict(at=m.now(),number=num,source_id=row['source_id'],url=url,status=response.status_code,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),path=str(dest),content_type=response.headers.get('Content-Type'))
        if response.status_code!=200:
            failure=folder/(str(num).zfill(3)+'-http-error.body');failure.write_bytes(raw);value['path']=str(failure);m.save(rp,value);response.raise_for_status()
        try:
            with Image.open(io.BytesIO(raw)) as im:assert im.format=='JPEG';value.update(width=im.width,height=im.height)
        except UnidentifiedImageError:
            failure=folder/(str(num).zfill(3)+'-nonimage.body');assert not failure.exists();failure.write_bytes(raw);value.update(image_decode_failed=True,path=str(failure));m.save(rp,value);return None
        assert not dest.exists();dest.write_bytes(raw);m.save(rp,value);return value
    images=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for value in pool.map(fetch,rows):
            if value is None:continue
            images.append(value)
            if len(images)%25==0:print(json.dumps(dict(thumbnails=len(images),total=len(rows))),flush=True)
    sheets=[]
    for start in range(0,len(images),24):
        batch=images[start:start+24];canvas=Image.new('RGB',(1440,((len(batch)+5)//6)*240),'#ffffff');draw=ImageDraw.Draw(canvas)
        for j,row in enumerate(batch):
            with Image.open(row['path']) as src:im=ImageOps.contain(ImageOps.exif_transpose(src).convert('RGB'),(228,207))
            x=(j%6)*240;y=(j//6)*240;canvas.paste(im,(x+(240-im.width)//2,y+(210-im.height)//2));draw.text((x+7,y+216),str(row['number'])+' | '+str(row['width'])+'x'+str(row['height']),fill='#111111')
        dest=PROOF/('contact-'+str(start//24+1)+'.jpg');assert not dest.exists();canvas.save(dest,quality=93);sheets.append(dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),numbers=[x['number'] for x in batch]))
    groups=collections.defaultdict(list)
    for row in images:groups[row['sha256']].append(row['number'])
    duplicate=[dict(sha256=k,numbers=ns) for k,ns in groups.items() if len(ns)>1]
    m.save(RUN/'visual-references-001.json',dict(at=m.now(),rows=images,sheets=sheets,exact_duplicate_groups=duplicate,selection_reference=c.ref(selection),script_reference=c.ref(Path(__file__).resolve()),visually_reviewed=False,unavailable_numbers=sorted({x['number'] for x in rows}-{x['number'] for x in images}),prepared_delivery_images=0,applied=False))
    print(json.dumps(dict(thumbnails=len(images),sheets=len(sheets),exact_duplicate_groups=duplicate)),flush=True)

if __name__=='__main__':main()
