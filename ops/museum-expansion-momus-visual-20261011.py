"""Review only 199 selected artwork primary previews; no catalogue mutations."""
import gzip,hashlib,importlib.util,json,math,time
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageOps
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-momus-common-20261011.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN

def main():
    dest=RUN/'visual-references-001.json';assert not dest.exists()
    source=RUN/'candidate-native-records-001.json.gz';selection=m.load(source)['rows'];assert len(selection)==199
    folder=c.PROOF/'selected-native-previews';folder.mkdir(parents=True,exist_ok=True);rows=[];held=[];consecutive=0
    with requests.Session() as session:
        for i,row in enumerate(selection):
            v=row['native'];url=v['url_original_s'].replace('/original/','/large/');target=folder/(str(row['number'])+'.jpg');assert not target.exists()
            try:
                response=session.get(url,timeout=(15,40));receipt=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),content_type=response.headers.get('Content-Type'),sha256=hashlib.sha256(response.content).hexdigest(),bytes=len(response.content))
                if response.status_code!=200:raise ValueError('Source HTTP '+str(response.status_code))
                assert len(response.content)<20000000
                target.write_bytes(response.content)
                with Image.open(target) as image:image.verify()
                with Image.open(target) as image:width,height=image.size;fmt=image.format
                rows.append(dict(number=row['number'],native_id=v['id'],native_inventory=v['momus_uuid_s'],title=v.get('dcterms_title_txt_en',v.get('dcterms_title_txt_el')),date_literal=row['date_literal'],path=str(target),sha256=receipt['sha256'],width=width,height=height,format=fmt,receipt=receipt,original_url=v['url_original_s'],image_role='Native public large preview of the primary image, URL transformation explicitly used by museum frontend.'))
                consecutive=0
            except Exception as exc:
                held.append(dict(number=row['number'],url=url,error=type(exc).__name__,detail=str(exc),receipt=receipt if 'receipt' in locals() else None));consecutive+=1
                if consecutive>=3 or ('receipt' in locals() and receipt['status'] in [401,403,429]):break
            if (i+1)%25==0:print(json.dumps(dict(attempted=i+1,images=len(rows),held=len(held))),flush=True)
    sheets=[];perpage=30
    for start in range(0,len(rows),perpage):
        subset=rows[start:start+perpage];sheet=Image.new('RGB',(1250,math.ceil(len(subset)/5)*235),'#e6e6e6');draw=ImageDraw.Draw(sheet)
        for j,row in enumerate(subset):
            with Image.open(row['path']) as im:thumb=ImageOps.contain(im.convert('RGB'),(240,190))
            x=(j%5)*250;y=(j//5)*235;sheet.paste(thumb,(x+(250-thumb.width)//2,y+(190-thumb.height)//2));draw.text((x+5,y+193),str(row['number'])+' | '+row['native_inventory'],fill='black');draw.text((x+5,y+210),row['date_literal'],fill='black')
        path=c.PROOF/('selected-contact-'+str(start//perpage+1).zfill(2)+'.jpg');assert not path.exists();sheet.save(path,quality=88);sheets.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),numbers=[r['number'] for r in subset]))
    hashes={}
    for row in rows:hashes.setdefault(row['sha256'],[]).append(row['number'])
    m.save(dest,dict(at=m.now(),source_reference=c.ref(source),rows=rows,held=held,contact_sheets=sheets,exact_duplicates=[v for v in hashes.values() if len(v)>1],selected=199,unattempted=199-len(rows)-len(held),policy='Selected source previews for artwork/version research. No image is approved for delivery by capture alone. Museum image delivery cutoff remains1955; actual image-source labels must be retained. No crop, synthetic image or catalogue writes.'))
    print(json.dumps(dict(images=len(rows),held=len(held),sheets=len(sheets),exact_duplicates=[v for v in hashes.values() if len(v)>1])),flush=True)

if __name__=='__main__':main()
