"""Download only90preselected dated, identity-reviewed museum digital reproductions."""
import hashlib,importlib.util,io,json
from pathlib import Path
from urllib.parse import urljoin
import requests
from PIL import Image,ImageOps,ImageDraw
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-war-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN,PROOF=src.c,src.m,src.RUN,src.c.PROOF

def main():
    assert not (RUN/'selected-digital-files-001.json').exists();decisions=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];selected=[x for x in decisions if x['image_candidate']];assert len(selected)==90
    source={x['number']:x for x in m.load(RUN/'selected-source-records-001.json.gz')['rows']};folder=PROOF/'selected-digital-files';folder.mkdir(parents=True,exist_ok=True);rows=[];held=[];stop=None
    m.save(RUN/'digital-file-selection-001.json',dict(at=m.now(),numbers=[x['number'] for x in selected],decision_reference=c.ref(RUN/'editorial-source-decisions-001.json.gz'),policy='Only90selectedpre1956creationworks with reviewed museum thumbnails; seek authentic source digital JPEG rather than assume thumbnail resolution is native. No oldprimary, crosscutoff, unknown-date, scope/identityheld or uncapturedmetadata object included. Final original-composition comparison stillrequired.'))
    for decision in selected:
        n=decision['number'];s=source[n]
        if stop:held.append(dict(number=n,reason='Not attempted after file-route access error'));continue
        if len(s['file_links'])!=1:held.append(dict(number=n,reason='No unique source-observed file wrapper',file_links=s['file_links']));continue
        key='selected-file-2773-001' if n==12 else 'selected-file-'+s['source_id'].split('000181-')[1]+'-001'
        try:
            doc,rc=src.capture(key,s['file_links'][0]);text=src.clean(doc.get_text(' ',strip=True));links=sorted({urljoin(rc['final_url'],im['src']) for im in doc.select('img[src]') if '/digital-files-from-preservator/file/' in im['src']})
            assert s['source_url'] in text and 'CC BY-SA 4.0' in text
            if len(links)!=1:held.append(dict(number=n,reason='No unique displayed digital image',receipt=rc,links=links));continue
            url=links[0];assert url.startswith('https://www.searchculture.gr/aggregator/digital-files-from-preservator/file/')
            response=requests.get(url,timeout=(15,45));raw=response.content;digest=hashlib.sha256(raw).hexdigest();image_rc=dict(at=m.now(),number=n,url=url,final_url=response.url,status=response.status_code,sha256=digest,bytes=len(raw),content_type=response.headers.get('Content-Type'),wrapper_receipt=rc)
            if response.status_code!=200:
                dest=folder/(str(n).zfill(3)+'-error.body');assert not dest.exists();dest.write_bytes(raw);image_rc['path']=str(dest);m.save(RUN/'digital-image-receipts'/(str(n).zfill(3)+'.json'),image_rc);response.raise_for_status()
            with Image.open(io.BytesIO(raw)) as im:im.load();assert im.format=='JPEG';size=im.size
            dest=folder/(str(n).zfill(3)+'.jpg');assert not dest.exists();dest.write_bytes(raw);image_rc.update(path=str(dest),width=size[0],height=size[1]);m.save(RUN/'digital-image-receipts'/(str(n).zfill(3)+'.json'),image_rc)
            rows.append(dict(number=n,source_id=s['source_id'],source_url=s['source_url'],wrapper_receipt=rc,wrapper_text=text,image=image_rc,rights_label='CC BY-SA 4.0',rights_url='http://creativecommons.org/licenses/by-sa/4.0/',visual_review_pending=True))
        except Exception as e:
            rp=RUN/'captures'/(key+'.json');stop=dict(number=n,error=type(e).__name__,wrapper_receipt=m.load(rp) if rp.exists() else None,policy='No retry or alternate request for failed route');held.append(stop)
        if len(rows)%15==0 or stop:print(json.dumps(dict(completed=len(rows),selected=90,held=len(held),stop=stop)),flush=True)
    sheets=[]
    for start in range(0,len(rows),24):
        batch=rows[start:start+24];canvas=Image.new('RGB',(1440,((len(batch)+5)//6)*260),'white');draw=ImageDraw.Draw(canvas)
        for j,row in enumerate(batch):
            im0=row['image']
            with Image.open(im0['path']) as im:thumb=ImageOps.contain(ImageOps.exif_transpose(im).convert('RGB'),(228,227))
            x,y=j%6*240,j//6*260;canvas.paste(thumb,(x+(240-thumb.width)//2,y+(230-thumb.height)//2));draw.text((x+7,y+238),str(row['number'])+' | '+str(im0['width'])+'x'+str(im0['height']),fill='black')
        dest=PROOF/('digital-contact-'+str(start//24+1)+'.jpg');assert not dest.exists();canvas.save(dest,quality=94);sheets.append(dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),numbers=[x['number'] for x in batch]))
    m.save(RUN/'selected-digital-files-001.json',dict(at=m.now(),rows=rows,held=held,access_stop=stop,sheets=sheets,script_reference=c.ref(Path(__file__).resolve()),selection_reference=c.ref(RUN/'digital-file-selection-001.json'),prepared_delivery=0,visually_reviewed=False,policy='Authentic source JPEGs at their actual resolution. No upscale, imagegen, retouching or croppedderivatives. Thumbnails independently archived; resolution and composition comparisons required before choosingdeliveryfile.'))
    print(json.dumps(dict(downloaded=len(rows),held=len(held),sheets=len(sheets))),flush=True)

if __name__=='__main__':main()
