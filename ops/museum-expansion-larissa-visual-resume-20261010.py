"""Continue after one missing native file; preserve 404 and use observed source thumbnails."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageFont,ImageOps

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-larissa-visual-20261010.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
m,RUN,PROOF=v.m,v.RUN,v.PROOF

def fetch(src):
    n=src['number'];rp=RUN/'captures'/('native-image-'+str(n).zfill(3)+'-001.json')
    if not rp.exists():
        try:return v.fetch(src)
        except Exception:
            if not rp.exists()or m.load(rp).get('status')!=404:raise
    rc=m.load(rp)
    if rc['status']==200:return v.fetch(src)
    assert rc['status']==404
    v.STOP.clear()
    url=src['thumbnail_url'];res=requests.get(url,timeout=(15,45));res.raise_for_status();raw=res.content
    assert res.headers.get('Content-Type','').startswith('image/')
    p=PROOF/'source-images'/(str(n).zfill(3)+'-aggregator.jpg');assert not p.exists();p.write_bytes(raw)
    with Image.open(p)as im:im.load();width,height=im.size;fmt=im.format
    row=dict(rc,at=m.now(),url=url,final_url=res.url,status=res.status_code,content_type=res.headers.get('Content-Type'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),path=str(p),width=width,height=height,format=fmt,
        media_source='SearchCulture museum-supplied thumbnail; native file returned404',native_missing_receipt=v.ref(rp),source_resolution='Aggregator thumbnail; no high-resolution claim')
    m.save(RUN/'captures'/('aggregator-image-'+str(n).zfill(3)+'-001.json'),row);return row

def main():
    missing=m.load(RUN/'captures/native-image-046-001.json');assert missing['status']==404
    m.save(RUN/'missing-native-image-continuation-001.json',dict(at=m.now(),receipt=v.ref(RUN/'captures/native-image-046-001.json'),
        policy='First image pass terminated on a missing native d-04.jpg file. No retry or path guessing for that file. Continue other selected public frames sequentially; a404 may use its already-observed SearchCulture thumbnail, labelled separately. Stop on any access denial/rate limit/server/network failure.',script_reference=v.ref(Path(__file__).resolve())))
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows'];rows=[]
    for src in sources:
        rows.append(fetch(src))
        if len(rows)%40==0:print(json.dumps(dict(images=len(rows),total=216)),flush=True)
    sheets=[];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',12)
    for page,start in enumerate(range(0,len(rows),20),1):
        batch=rows[start:start+20];canvas=Image.new('RGB',(1400,1200),'white');draw=ImageDraw.Draw(canvas)
        for k,row in enumerate(batch):
            x,y=k%5*280,k//5*300;draw.text((x+4,y+4),str(row['number'])+' | '+(row['date']or'Unknown')+(' | OLD'if row['role']=='existing_comparator'else''),font=font,fill='black')
            draw.text((x+4,y+24),row['title'][:35],font=small,fill='black');draw.text((x+4,y+41),(row['creator']or'Unknown')[:37],font=small,fill='black')
            with Image.open(row['path'])as im:
                thumb=ImageOps.contain(im.convert('RGB'),(272,238));canvas.paste(thumb,(x+(280-thumb.width)//2,y+58+(238-thumb.height)//2))
        p=PROOF/('contact-'+str(page)+'.jpg');assert not p.exists();canvas.save(p,quality=94);sheets.append(dict(v.ref(p),numbers=[row['number']for row in batch]))
    groups=collections.defaultdict(list)
    for row in rows:groups[row['sha256']].append(row['number'])
    m.save(RUN/'visual-references-001.json',dict(at=m.now(),rows=rows,sheets=sheets,exact_duplicate_images=[ns for ns in groups.values()if len(ns)>1],
        source_reference=v.ref(RUN/'selected-source-records-001.json.gz'),selection_reference=v.ref(RUN/'object-selection-001.json'),script_reference=v.ref(Path(__file__).resolve()),
        original_script_reference=v.ref(Path(v.__file__).resolve()),policy='Selected full repository frames; missing native files use their observed museum-supplied aggregator thumbnail and retain404evidence. Contact sheets internal; no crop, reconstruction or production eligibility implied.'))
    print(json.dumps(dict(images=len(rows),fallbacks=[row['number']for row in rows if row.get('media_source')],contacts=len(sheets),exact_duplicates=[ns for ns in groups.values()if len(ns)>1])),flush=True)

if __name__=='__main__':main()
