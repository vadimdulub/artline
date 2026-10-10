"""Prepare only source-selected, pre-1956 Theocharakis reproductions; no uploads."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageDraw,ImageFont
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-theocharakis-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/theocharakis-delivery-20261010'

def main():
    assert not(RUN/'image-delivery-prepared-001.json').exists()
    selected=[];cached={}
    for root,wave in [(c.RESEARCH,'first'),(c.DATED,'dated')]:
        units=m.load(root/'candidate-physical-units-001.json.gz')['rows'];unitmap={sid:u for u in units for sid in u['source_ids']}
        for f in sorted(root.glob('comparison-references-*.json')):
            for v in m.load(f)['rows']:cached[v['source_id']]=v
        for v in m.load(root/'editorial-source-decisions-001.json.gz')['rows']:
            if v['source_id'] not in unitmap or v['last'] is None or v['last']>1955 or v.get('image_further_identity_evidence_required'):continue
            selected.append(dict(v,research_wave=wave,primary_source_id=unitmap[v['source_id']]['primary_source_id']))
    assert len(selected)==114
    results=[]
    for index,v in enumerate(selected,1):
        sid=v['source_id'];key=sid.split('-')[-1];url=v['full_image_url'];receipt_path=RUN/'image-receipts'/(key+'.json');assert url.startswith('https://exhibition.thfdigital.gr/')
        if receipt_path.exists():receipt=m.load(receipt_path)
        elif sid in cached:
            old=cached[sid];assert old['url']==url and hashlib.sha256(Path(old['path']).read_bytes()).hexdigest()==old['sha256']
            receipt=dict(old,cached_capture_reused=True);m.save(receipt_path,receipt)
        else:
            response=requests.get(url,timeout=(15,40))
            if response.status_code!=200:
                m.save(RUN/('image-access-hold-'+key+'-001.json'),dict(at=m.now(),url=url,status=response.status_code));response.raise_for_status();raise ValueError('Non200image')
            data=response.content;image=Image.open(io.BytesIO(data));image.load();dest=PROOF/'originals'/(key+'.jpg');dest.parent.mkdir(parents=True,exist_ok=True);dest.open('xb').write(data)
            receipt=dict(at=m.now(),source_id=sid,url=url,final_url=response.url,status=response.status_code,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),path=str(dest),width=image.width,height=image.height,content_type=response.headers.get('Content-Type'),cached_capture_reused=False);m.save(receipt_path,receipt)
        raw=Path(receipt['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
        original=Image.open(io.BytesIO(raw));original.load();image=ImageOps.exif_transpose(original).convert('RGB');original_size=image.size;quality=95
        while True:
            out=io.BytesIO();image.save(out,format='JPEG',quality=quality,optimize=True,progressive=True);data=out.getvalue()
            if len(data)<=100000:break
            if quality>55:quality-=5
            else:image.thumbnail((int(image.width*.9),int(image.height*.9)),Image.Resampling.LANCZOS);quality=90
        dest=PROOF/'prepared'/(key+'.jpg');dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert dest.read_bytes()==data
        else:dest.open('xb').write(data)
        results.append(dict(number=index,research_number=v['number'],research_wave=v['research_wave'],source_id=sid,primary_source_id=v['primary_source_id'],source_title=v['title'],title=v['title'],source_url=v['source_url'],native_url=v['native_url'],verified_https_source_image_url=url,image_url=url,original_reference=dict(path=receipt['path'],sha256=receipt['sha256']),original_image_receipt=receipt,prepared_path=str(dest),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),width=image.width,height=image.height,mime_type='image/jpeg',quality=quality,original_dimensions=original_size,source_receipt=v['source_receipt'],native_receipt=v['native_receipt'],image_retrieved_at=receipt['at'],image_source='B & M Theocharakis Foundation',rights_label='CC BY-SA 4.0',rights_url='https://creativecommons.org/licenses/by-sa/4.0/',rights_status='licensed',credit='Collection of the B & M Theocharakis Foundation; Spyros Papaloukas',changes='Complete source frame; JPEG compression and proportional resizing if needed. No crop.',view_label='Primary source view' if sid==v['primary_source_id'] else 'Other side of the same sheet — editorial physical-support match',image_identity_confidence_editorial=.98,identity_basis='Individual native foundation object image and matching aggregator/source metadata; prior physical-sheet comparisons retained. Final prepared frame review required.',user_approved_source_policy='Greek museum/artist source continuation,20September and8October2026: selected works created by1955; actual CC BY-SA4.0 source label retained separately from user authorization.',ready_to_attach=False))
        if index%20==0:print(json.dumps(dict(prepared=index,total=114)),flush=True)
    sheets=[];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
    for start in range(0,len(results),16):
        group=results[start:start+16];canvas=Image.new('RGB',(1280,1200),'#eeeae3');draw=ImageDraw.Draw(canvas)
        for j,row in enumerate(group):
            im=Image.open(row['prepared_path']);im.thumbnail((302,254));x=(j%4)*320+(320-im.width)//2;y=(j//4)*300;canvas.paste(im,(x,y));label=str(row['number'])+' | '+row['source_id'].split('-')[-1]+' | '+row['research_wave'];draw.text(((j%4)*320+8,y+260),label,fill='black',font=font);draw.text(((j%4)*320+8,y+279),row['title'][:38],fill='black',font=font)
        dest=PROOF/('prepared-contact-'+str(len(sheets)+1).zfill(2)+'.jpg');canvas.save(dest,quality=90);sheets.append(dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
    m.save(RUN/'image-delivery-prepared-001.json',dict(at=m.now(),rows=results,sheets=sheets,images=114,physical_artworks=len({v['primary_source_id'] for v in results}),source_qualified_only=True,visual_review_pending=True,script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(prepared=114,sheets=len(sheets),physical_artworks=len({v['primary_source_id'] for v in results}))),flush=True)
if __name__=='__main__':main()
