"""Selected public native preview frames for physical-object comparison."""
import collections
import concurrent.futures
import hashlib
import importlib.util
import json
import threading
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageFont,ImageOps

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-larissa-source-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF=c.m,c.RUN,c.PROOF
STOP=threading.Event()

def ref(p):
    p=Path(p);return dict(path=str(p.relative_to(m.ROOT))if p.is_relative_to(m.ROOT)else str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())

def fetch(src):
    if STOP.is_set():raise RuntimeError('Source image pass stopped')
    n=src['number'];url=src['native_images'][0]['absolute_url'];dest=PROOF/'source-images'/(str(n).zfill(3)+Path(url).suffix.lower())
    assert url.startswith('http://www.larissa-katsigras-gallery.gr/uploads/gallery/')
    rp=RUN/'captures'/('native-image-'+str(n).zfill(3)+'-001.json')
    if rp.exists():rc=m.load(rp);assert ref(dest)['sha256']==rc['sha256']and rc['status']==200;return rc
    try:
        res=requests.get(url,timeout=(15,45));raw=res.content
        rc=dict(at=m.now(),number=n,source_id=src['source_id'],source_url=src['source_url'],native_url=src['native_url'],url=url,final_url=res.url,status=res.status_code,
            content_type=res.headers.get('Content-Type'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),path=str(dest),role=src['role'],title=src['native_fields']['Τίτλος έργου'],
            creator=src['native_fields'].get('Καλλιτέχνης'),date=src['native_fields'].get('Χρονολογία έργου'),rights_links=src['rights_links'],
            purpose='Internal selected native object/image matching. No public eligibility or upload inferred, including unknown-dated historical comparators and ranges crossing1955.')
        if res.status_code!=200 or not(rc['content_type']or'').startswith('image/'):
            m.save(rp,rc);raise RuntimeError('Source image unavailable: '+str(n))
        assert not dest.exists();dest.write_bytes(raw)
        with Image.open(dest)as im:im.load();rc.update(width=im.width,height=im.height,format=im.format)
        m.save(rp,rc);return rc
    except Exception:
        STOP.set();raise

def main():
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows'];assert len(sources)==216
    (PROOF/'source-images').mkdir(parents=True,exist_ok=True);rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
        futures=[pool.submit(fetch,src)for src in sources]
        try:
            for future in concurrent.futures.as_completed(futures):
                rows.append(future.result())
                if len(rows)%40==0:print(json.dumps(dict(images=len(rows),total=216)),flush=True)
        except Exception:
            STOP.set()
            for future in futures:future.cancel()
            raise
    rows.sort(key=lambda r:r['number']);sheets=[];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',12)
    for page,start in enumerate(range(0,len(rows),20),1):
        batch=rows[start:start+20];canvas=Image.new('RGB',(1400,1200),'white');draw=ImageDraw.Draw(canvas)
        for k,row in enumerate(batch):
            x,y=k%5*280,k//5*300
            draw.text((x+4,y+4),str(row['number'])+' | '+(row['date']or'Unknown')+(' | EXISTING'if row['role']=='existing_comparator'else''),font=font,fill='black')
            draw.text((x+4,y+24),row['title'][:35],font=small,fill='black');draw.text((x+4,y+41),(row['creator']or'Unknown')[:37],font=small,fill='black')
            with Image.open(row['path'])as im:
                thumb=ImageOps.contain(im.convert('RGB'),(272,238));canvas.paste(thumb,(x+(280-thumb.width)//2,y+58+(238-thumb.height)//2))
        p=PROOF/('contact-'+str(page)+'.jpg');assert not p.exists();canvas.save(p,quality=94);sheets.append(dict(ref(p),numbers=[row['number']for row in batch]))
    groups=collections.defaultdict(list)
    for row in rows:groups[row['sha256']].append(row['number'])
    m.save(RUN/'visual-references-001.json',dict(at=m.now(),rows=rows,sheets=sheets,exact_duplicate_images=[ns for ns in groups.values()if len(ns)>1],
        source_reference=ref(RUN/'selected-source-records-001.json.gz'),selection_reference=ref(RUN/'object-selection-001.json'),script_reference=ref(Path(__file__).resolve()),
        policy='216 selected native repository frames, complete original bytes.11 internal contacts with proportional scaling only. No high-resolution route guessing or exhaustive downloads. Visual decisions and production image eligibility remain separate.'))
    print(json.dumps(dict(images=len(rows),contacts=len(sheets),exact_duplicates=[ns for ns in groups.values()if len(ns)>1])),flush=True)

if __name__=='__main__':main()
