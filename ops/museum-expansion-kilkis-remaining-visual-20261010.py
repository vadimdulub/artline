"""Selected18object thumbnails for scope and assemblage comparison; no attachments."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageFont
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-kilkis-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN;PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/kilkis-delivery-20261010'

def main():
    assert not(RUN/'remaining-visual-references-001.json').exists();rows=m.load(RUN/'remaining-source-records-001.json.gz')['rows'];frames=[]
    for row in rows:
        dest=RUN/'remaining-image-receipts'/(str(row['number'])+'.json')
        if dest.exists():frame=m.load(dest)
        else:
            url=row['thumbnail_url'];assert url.startswith('https://www.searchculture.gr/aggregator/thumbnails/')
            response=requests.get(url,timeout=(15,40));response.raise_for_status();raw=response.content;im=Image.open(io.BytesIO(raw));im.load();path=PROOF/'remaining-identity-images'/(str(row['number'])+'.jpg');path.parent.mkdir(parents=True,exist_ok=True);path.open('xb').write(raw)
            frame=dict(at=m.now(),number=row['number'],source_id=row['source_id'],url=url,status=response.status_code,path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),width=im.width,height=im.height);m.save(dest,frame)
        assert hashlib.sha256(Path(frame['path']).read_bytes()).hexdigest()==frame['sha256'];frames.append(frame)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16);sheets=[]
    for start in range(0,len(frames),12):
        canvas=Image.new('RGB',(1440,1080),'#eeeae3');draw=ImageDraw.Draw(canvas)
        for j,v in enumerate(frames[start:start+12]):
            im=Image.open(v['path']);im.thumbnail((340,310));x=j%4*360+(360-im.width)//2;y=j//4*360;canvas.paste(im,(x,y));draw.text((j%4*360+8,y+320),str(v['number'])+' | '+v['source_id'].split('-')[-1],fill='black',font=font)
        path=PROOF/('remaining-contact-'+str(len(sheets)+1)+'.jpg');assert not path.exists();canvas.save(path,quality=92);sheets.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    m.save(RUN/'remaining-visual-references-001.json',dict(at=m.now(),rows=frames,sheets=sheets,script_reference=c.ref(Path(__file__).resolve()),purpose='Physical-object scope, separate components versus assemblage, decoration and view identity; not production attachments.'))
    print(json.dumps(dict(frames=len(frames),sheets=len(sheets))),flush=True)

if __name__=='__main__':main()
