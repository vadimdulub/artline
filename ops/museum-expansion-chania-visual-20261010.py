"""Selected native source frames for internal review; never a production upload."""
import collections
import concurrent.futures
import hashlib
import importlib.util
import json
import threading
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageFont,ImageOps
spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-chania-selected-20261010.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m,RUN,q=s.m,s.RUN,s.q
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/chania-20261010'
DEST=PROOF/'source-images'
SCOPE_HOLDS={46,106,114,115,121,124,136,147,162,163,173,190,196,203}
STOP=threading.Event()

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ref(path):
    p=Path(path)
    return dict(path=str(p.relative_to(m.ROOT))if p.is_relative_to(m.ROOT)else str(p),sha256=sha(p))

def fetch(src):
    if STOP.is_set():raise RuntimeError('Source image pass stopped')
    sid=src['source_id'].rsplit('-',1)[1];im=src['native_images'][0];url=im['src']
    assert url.startswith('https://amch.gr/wp-content/uploads/')
    path=DEST/(sid+Path(url).suffix.lower());rp=RUN/'captures'/('native-image-'+sid+'-001.json')
    if rp.exists():
        rc=m.load(rp);assert rc['status']==200 and sha(path)==rc['sha256'];return rc
    try:
        res=requests.get(url,timeout=(15,45));raw=res.content
        rc=dict(at=m.now(),number=src['number'],source_id=src['source_id'],source_url=src['source_url'],native_url=src['native_url'],
            url=url,final_url=res.url,status=res.status_code,content_type=res.headers.get('Content-Type'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),path=str(path),
            title=(src['fields'].get('Τίτλος')or[src['native_dynamic_text'][0]])[0],role=src['role'],source_date=src['native_fields'].get('Χρονολόγηση'),
            native_image_attributes=im,rights_links=src['rights_links'],purpose='Internal selected-object identity review. No production eligibility, licence independence or attachment inferred.')
        if res.status_code!=200 or not(rc['content_type']or'').startswith('image/'):
            m.save(rp,rc);raise RuntimeError('Image source unavailable: '+sid)
        assert not path.exists();path.write_bytes(raw)
        with Image.open(path)as image:rc.update(width=image.width,height=image.height,format=image.format)
        m.save(rp,rc);return rc
    except Exception as e:
        STOP.set()
        if not rp.exists():m.save(rp,dict(at=m.now(),source_id=src['source_id'],url=url,error_type=type(e).__name__,message=str(e),status=None,policy='No retry; remaining new image requests stopped.'))
        raise

def main():
    allrows=m.load(RUN/'selected-source-records-001.json.gz')['rows'];selected=[r for r in allrows if r['number']not in SCOPE_HOLDS]
    assert len(selected)==198
    m.save(RUN/'previsual-scope-selection-001.json',dict(at=m.now(),selected_numbers=[r['number']for r in selected],scope_hold_numbers=sorted(SCOPE_HOLDS),
        policy='Description-level selection of decorative vessels, figurative/seal objects, sculpture, jewellery, coins and explicitly decorated weapons. Fourteen plain tools, administrative records, plain beehive/stove or unresolved art-scope objects are held before images. These are research holds, not deletions or assertions they can never qualify. Six secondary fragment/pair pages remain visual comparators, not presumed additional works.',
        source_reference=ref(RUN/'selected-source-records-001.json.gz'),script_reference=ref(Path(__file__).resolve())))
    DEST.mkdir(parents=True,exist_ok=True);rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
        futures=[pool.submit(fetch,src)for src in selected]
        try:
            for fut in concurrent.futures.as_completed(futures):
                rows.append(fut.result())
                if len(rows)%30==0:print(json.dumps(dict(images=len(rows),total=198)),flush=True)
        except Exception:
            STOP.set()
            for fut in futures:fut.cancel()
            raise
    rows.sort(key=lambda r:r['number']);sheets=[]
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
    for page,start in enumerate(range(0,len(rows),20),1):
        batch=rows[start:start+20];canvas=Image.new('RGB',(1600,1480),'white');draw=ImageDraw.Draw(canvas)
        for k,r in enumerate(batch):
            x,y=(k%5)*320,(k//5)*370
            draw.text((x+4,y+4),str(r['number'])+' | '+r['source_id'].rsplit('-',1)[1]+(' | EXISTING'if r['role']=='existing_comparator'else''),font=font,fill='black')
            draw.text((x+4,y+25),r['title'][:42],font=small,fill='black');draw.text((x+4,y+44),(r['source_date']or'Unknown')[:45],font=small,fill='black')
            with Image.open(r['path'])as im:
                rgba=im.convert('RGBA');background=Image.new('RGBA',rgba.size,'white');background.alpha_composite(rgba)
                thumb=ImageOps.contain(background.convert('RGB'),(310,300));canvas.paste(thumb,(x+(320-thumb.width)//2,y+65+(300-thumb.height)//2))
        path=PROOF/('contact-'+str(page)+'.jpg');assert not path.exists();canvas.save(path,quality=94)
        sheets.append(dict(ref(path),numbers=[r['number']for r in batch]))
    groups=collections.defaultdict(list)
    for r in rows:groups[r['sha256']].append(r['number'])
    m.save(RUN/'visual-references-001.json',dict(at=m.now(),rows=rows,sheets=sheets,exact_duplicate_images=[ns for ns in groups.values()if len(ns)>1],
        scope_selection_reference=ref(RUN/'previsual-scope-selection-001.json'),source_reference=ref(RUN/'selected-source-records-001.json.gz'),script_reference=ref(Path(__file__).resolve()),
        policy='Selected198 native files only; complete original bytes preserved in Library. Contact sheets are internal review aids, with transparent backgrounds displayed on white; no crop or invented detail. No claim of completed visual review until separate decisions. No production images prepared or uploaded.'))
    print(json.dumps(dict(images=len(rows),contacts=len(sheets),exact_duplicate_groups=[ns for ns in groups.values()if len(ns)>1])),flush=True)

if __name__=='__main__':main()
