"""Preserve26focused records and compare existing public image frames."""
import gzip
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
    assert not(RUN/'focused-review-inputs-001.json').exists();obs=m.load(RUN/'production-identity-001.json.gz');state=obs['state'];titles=set(obs['params']['titles']);scope=set(state['scoped_ids'])
    ids=sorted({v['id'] for v in state['artworks'] if v['id'] in scope or v['normalized_title'] in titles});assert len(ids)==26
    path=RUN/'focused-comparators-001.json.gz'
    if path.exists():focus=m.load(path)
    else:
        with c.prod.connect() as db,db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');snap=c.snapshot(db,ids)
        focus=dict(at=m.now(),ids=ids,snapshot=snap,identity_reference=c.ref(RUN/'production-identity-001.json.gz'));m.save(path,focus)
    media={v['id']:v for v in focus['snapshot']['media_assets']};frames=[]
    for a in focus['snapshot']['artworks']:
        if not a['primary_media_id']:continue
        im=media[a['primary_media_id']];url='https://artlines.org'+im['storage_path'];receipt=RUN/'comparison-image-receipts'/(a['id']+'.json')
        if receipt.exists():frame=m.load(receipt)
        else:
            response=requests.get(url,timeout=(15,40));response.raise_for_status();raw=response.content;digest=hashlib.sha256(raw).hexdigest();assert digest==im['checksum_sha256'];image=Image.open(io.BytesIO(raw));image.load();dest=PROOF/'comparison-images'/(a['id']+'.jpg');dest.parent.mkdir(parents=True,exist_ok=True);dest.open('xb').write(raw)
            frame=dict(at=m.now(),artwork_id=a['id'],title=a['title'],url=url,status=response.status_code,path=str(dest),sha256=digest,bytes=len(raw),width=image.width,height=image.height);m.save(receipt,frame)
        frames.append(frame)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16);sheet=Image.new('RGB',(1440,1080),'#eeeae3');draw=ImageDraw.Draw(sheet)
    selected=[dict(path=v['path'],label=v['artwork_id'][:8]+' '+v['title']) for v in frames]
    prepared=m.load(RUN/'image-inputs-001.json')['rows'];selected += [dict(path=v['prepared_path'],label='Kilkis '+v['source_id'].split('-')[-1]) for v in prepared if v['source_id'].split('-')[-1] in ['9328','1091','4154','5409']]
    assert len(selected)<=12
    for j,v in enumerate(selected):
        im=Image.open(v['path']);im.thumbnail((340,310));x=j%4*360+(360-im.width)//2;y=j//4*360;sheet.paste(im,(x,y));draw.text((j%4*360+8,y+320),v['label'],fill='black',font=font)
    dest=PROOF/'focused-contact.jpg';assert not dest.exists();sheet.save(dest,quality=92)
    m.save(RUN/'focused-review-inputs-001.json',dict(at=m.now(),frames=frames,contact=dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()),snapshot_reference=c.ref(path),source_citations_reference=c.ref(RUN/'production-identity-citations-001.json.gz'),script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(focused=len(ids),images=len(frames),selected_comparison_frames=len(selected))),flush=True)

if __name__=='__main__':main()
