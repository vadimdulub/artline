"""Resume native image preparation; normalize harmless whitespace in source alt labels."""
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont,ImageOps
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-kilkis-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN;PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/kilkis-delivery-20261010'
PERIODS={'Ρωμαϊκή Eποχή','Ελληνιστική Eποχή','Βυζαντινή Εποχή','Κλασική Εποχή','Εποχή Σιδήρου','Αρχαϊκή Εποχή','Νεολιθική Περίοδος','Γεωμετρική Περίοδος'}

def main():
    assert not(RUN/'image-inputs-001.json').exists();source=m.load(RUN/'source-review-001.json.gz')['rows']
    rows=[v for v in source if v['decision']!='hold' and v['native_receipt'] and v['source_id']!='Efa_Kilkis_col/000224-AEMK-2'];assert len(rows)==53
    frames=[]
    for row in rows:
        sid=row['source_id'];nrc=row['native_receipt'];raw=gzip.decompress((m.ROOT/nrc['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==nrc['sha256']
        soup=BeautifulSoup(raw,'html.parser');main=soup.find('main') or soup;native=[x for x in main.select('img[src]') if 'www.efa-kilkis.gr/wp-content/uploads/' in urljoin(row['native_url'],x['src'])];assert native
        # The first native frame belongs to the object heading, before related-item cards.
        el=native[0];assert ' '.join(el.get('alt','').split())==' '.join(row['title'].split()),(sid,el.get('alt'),row['title']);url=urljoin(row['native_url'],el['src'])
        assert row['date_display'] in PERIODS and row['native_fields']['Άδεια Χρήσης']=='CC BY-NC-ND 4'
        receipt=RUN/'native-image-receipts'/(sid.split('/')[-1]+'.json')
        if receipt.exists():frame=m.load(receipt)
        else:
            response=requests.get(url,timeout=(15,45));response.raise_for_status();data=response.content;im=Image.open(io.BytesIO(data));im.load();assert im.format in ['JPEG','PNG']
            original=PROOF/'native-originals'/(sid.split('/')[-1]+('.jpg' if im.format=='JPEG' else '.png'));original.parent.mkdir(parents=True,exist_ok=True);original.open('xb').write(data)
            if im.format=='JPEG' and len(data)<=100000:
                prepared=data;size=im.size;changes='Exact source JPEG bytes retained; no crop, resizing, recompression or colour changes.'
            else:
                scaled=ImageOps.exif_transpose(im).convert('RGB');scaled.thumbnail((1600,1600));prepared=None
                while prepared is None:
                    for quality in [92,88,84,80,76,72,68,64,60,56,52]:
                        buf=io.BytesIO();scaled.save(buf,format='JPEG',quality=quality,optimize=True,progressive=True)
                        if len(buf.getvalue())<=100000:prepared=buf.getvalue();break
                    if prepared is None:scaled.thumbnail((int(scaled.width*.85),int(scaled.height*.85)))
                size=scaled.size;changes='Complete source frame retained; JPEG compression and proportional reduction as needed to100000bytes. EXIF display orientation respected; no crop or retouching.'
            digest=hashlib.sha256(prepared).hexdigest();dest=PROOF/'prepared-images'/(sid.split('/')[-1]+'-'+digest[:16]+'.jpg');dest.parent.mkdir(parents=True,exist_ok=True);dest.open('xb').write(prepared)
            frame=dict(at=m.now(),number=row['number'],source_id=sid,source_url=row['source_url'],native_url=row['native_url'],url=url,status=response.status_code,original_reference=dict(path=str(original),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),width=im.width,height=im.height),prepared_path=str(dest),sha256=digest,bytes=len(prepared),width=size[0],height=size[1],mime_type='image/jpeg',changes=changes,source_title=row['title'],source_receipt=row['source_receipt'],native_receipt=nrc,image_period_literal=row['date_display'],date_policy_passed=True,date_policy_basis='The native object is explicitly assigned to an ancient or Byzantine period, wholly before1956. This establishes image-policy scope without supplying invented numeric creation bounds. Original catalogue numeric dates remain null.',rights_label='CC BY-NC-ND 4.0',rights_url='http://creativecommons.org/licenses/by-nc-nd/4.0/',rights_status='restricted',credit='Υπουργείο Πολιτισμού / Εφορεία Αρχαιοτήτων Κιλκίς',image_source='Kilkis Ephorate of Antiquities',complete_source_frame=True,ready_to_attach=False)
            m.save(receipt,frame)
        assert hashlib.sha256(Path(frame['prepared_path']).read_bytes()).hexdigest()==frame['sha256'];frames.append(frame)
        print(json.dumps(dict(prepared=len(frames),total=53,source_id=sid,bytes=frame['bytes'])),flush=True)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16);sheets=[]
    for start in range(0,len(frames),16):
        canvas=Image.new('RGB',(1440,1440),'#eeeae3');draw=ImageDraw.Draw(canvas)
        for j,v in enumerate(frames[start:start+16]):
            im=Image.open(v['prepared_path']);im.thumbnail((340,310));x=j%4*360+(360-im.width)//2;y=j//4*360;canvas.paste(im,(x,y));draw.text((j%4*360+8,y+318),str(v['number'])+' | '+v['source_id'].split('-')[-1],fill='black',font=font);draw.text((j%4*360+8,y+340),v['source_title'][:38],fill='black',font=font)
        dest=PROOF/('prepared-contact-'+str(len(sheets)+1)+'.jpg');assert not dest.exists();canvas.save(dest,quality=92);sheets.append(dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
    m.save(RUN/'image-inputs-001.json',dict(at=m.now(),rows=frames,sheets=sheets,source_reference=c.ref(RUN/'source-review-001.json.gz'),script_reference=c.ref(Path(__file__).resolve()),production_uploaded=0,production_attached=0,pending='Visual QA and fresh global identity reconciliation before exact-hash delivery.'))
    print(json.dumps(dict(prepared=53,sheets=len(sheets))),flush=True)

if __name__=='__main__':main()
