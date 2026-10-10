"""Selected original image capture after dated art metadata selection, no upload."""
import concurrent.futures,gzip,hashlib,importlib.util,io,json,re
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageDraw,UnidentifiedImageError
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-asfa-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF=c.m,c.RUN,c.PROOF

def main():
    assert not (RUN/'original-image-references-001.json').exists()
    source=m.load(RUN/'selected-source-records-001.json.gz')['rows'];native={x['number']:x for x in m.load(RUN/'native-source-records-001.json.gz')['rows']};selected=[]
    for row in source:
        date=row['fields'].get('Ημερομηνία δημιουργίας',[''])[0];years=[int(x) for x in re.findall(r'\d{4}',date)]
        if (years and max(years)<=1955 and not row['index']['historical_source_match']) or row['number'] in [171,172]:selected.append(row)
    assert len(selected)==148
    sp=RUN/'original-image-selection-001.json'
    if not sp.exists():m.save(sp,dict(at=m.now(),numbers=[x['number'] for x in selected],pre1956_delivery_leads=146,research_only_numbers=[171,172],source_reference=c.ref(RUN/'selected-source-records-001.json.gz'),native_reference=c.ref(RUN/'native-source-records-001.json.gz'),terms_reference=c.ref(RUN/'captures/native-terms-001.json'),rights='Native terms say CC BY-NC-ND4.0 and personal/academic use, unlike SearchCulture CC BY-SA4.0. Native originals remain restricted; user Greek museum/artist workflow approval is separate, not a copyright-holder licence.',policy='Only146selected dated pre1956new leads plus two1956print comparators. Final physical-unit and global counterpart reconciliation remains pending. No uploads or attachments.'))
    dest=PROOF/'source-originals';dest.mkdir(parents=True,exist_ok=True)
    def fetch(row):
        n=row['number'];path=dest/(str(n).zfill(3)+'.jpg');receipt=RUN/'original-image-receipts'/(str(n).zfill(3)+'.json')
        if receipt.exists():
            r=m.load(receipt);assert r['status']==200 and hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'];return r
        u=native[n]['image_url'];assert u.startswith('https://exhibition.asktdigital.gr/wp-content/uploads/')
        response=requests.get(u,timeout=(15,45));raw=response.content;r=dict(at=m.now(),number=n,source_id=row['source_id'],url=u,status=response.status_code,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),content_type=response.headers.get('Content-Type'),path=str(path),source_page_url=row['native_url'],research_only=n in [171,172])
        if response.status_code!=200:
            fail=dest/(str(n).zfill(3)+'-http-error.body');fail.write_bytes(raw);r['path']=str(fail);m.save(receipt,r);response.raise_for_status()
        with Image.open(io.BytesIO(raw)) as im:im.load();assert im.format=='JPEG';r.update(width=im.width,height=im.height)
        assert not path.exists();path.write_bytes(raw);m.save(receipt,r);return r
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(fetch,selected):
            rows.append(row)
            if len(rows)%25==0:print(json.dumps(dict(originals=len(rows),selected=len(selected))),flush=True)
    sheets=[]
    for start in range(0,len(rows),24):
        batch=rows[start:start+24];canvas=Image.new('RGB',(1440,((len(batch)+5)//6)*240),'white');draw=ImageDraw.Draw(canvas)
        for j,row in enumerate(batch):
            with Image.open(row['path']) as im:thumb=ImageOps.contain(ImageOps.exif_transpose(im).convert('RGB'),(228,207))
            x=j%6*240;y=j//6*240;canvas.paste(thumb,(x+(240-thumb.width)//2,y+(210-thumb.height)//2));draw.text((x+5,y+215),str(row['number'])+' | native original',fill='black')
        path=PROOF/('native-contact-'+str(start//24+1)+'.jpg');assert not path.exists();canvas.save(path,quality=93);sheets.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),numbers=[r['number'] for r in batch]))
    m.save(RUN/'original-image-references-001.json',dict(at=m.now(),rows=rows,sheets=sheets,selection_reference=c.ref(sp),script_reference=c.ref(Path(__file__).resolve()),visually_reviewed=False,uploaded=0,attached=0))
    print(json.dumps(dict(originals=len(rows),contacts=len(sheets))),flush=True)

if __name__=='__main__':main()
