"""Capture focused identity comparators and existing images without catalogue writes."""
import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageFont
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-zongolopoulos-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN;PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/zongolopoulos-delivery-20261010'

def main():
    assert not(RUN/'focused-review-inputs-001.json').exists();obs=m.load(RUN/'production-identity-001.json.gz');s=obs['state']
    rows=[v for root in [c.RESEARCH,c.DATED]for v in m.load(root/'editorial-source-decisions-001.json.gz')['rows']];titles={m.norm(v['title'])for v in rows}
    ids=sorted({a['id']for a in s['artworks']if a['id']in s['scoped_ids']or a['normalized_title']in titles or re.search(obs['params']['creator_pattern'],a['unlinked_creator_label']or'',re.I)or a['accession_number']in obs['params']['accession_keys']})
    dest=RUN/'focused-comparators-001.json.gz'
    if dest.exists():focus=m.load(dest)
    else:
        with c.prod.connect()as db,db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');snap=c.snapshot(db,ids)
        focus=dict(at=m.now(),ids=ids,snapshot=snap,read_only=True,artist_ids=s['artist_ids'],policy='No existing George or Helen authority resolved; retain literal and qualified object-level creator labels, no invented painter records. Literal Greek-title comparators remain included even when attributed to another maker because37newcandidates are anonymous.');m.save(dest,focus)
    media={v['id']:v for v in focus['snapshot']['media_assets']};frames=[]
    for a in focus['snapshot']['artworks']:
        if not a['primary_media_id']:continue
        mr=media[a['primary_media_id']];path=mr['storage_path'];url='https://artlines.org'+path if path.startswith('/')else path;assert url.startswith('https://artlines.org/')
        rc=RUN/'comparison-image-receipts'/(a['id']+'.json')
        if rc.exists():v=m.load(rc)
        else:
            response=requests.get(url,timeout=(15,40));response.raise_for_status();data=response.content;checksum=hashlib.sha256(data).hexdigest();assert checksum==mr['checksum_sha256'];im=Image.open(io.BytesIO(data));im.load();p=PROOF/'comparison-images'/(a['id']+'.jpg');p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write(data)
            v=dict(at=m.now(),artwork_id=a['id'],title=a['title'],url=url,status=response.status_code,path=str(p),sha256=checksum,width=im.width,height=im.height,source_page_url=mr['source_page_url']);m.save(rc,v)
        frames.append(v)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14);sheets=[]
    for start in range(0,len(frames),16):
        canvas=Image.new('RGB',(1440,1440),'#eeeae3');draw=ImageDraw.Draw(canvas)
        for j,v in enumerate(frames[start:start+16]):
            im=Image.open(v['path']);im.thumbnail((340,310));x=j%4*360+(360-im.width)//2;y=j//4*360;canvas.paste(im,(x,y));draw.text((j%4*360+8,y+313),v['artwork_id'][:8],fill='black',font=font);draw.text((j%4*360+8,y+335),v['title'][:42],fill='black',font=font)
        p=PROOF/('comparison-contact-'+str(len(sheets)+1)+'.jpg');canvas.save(p,quality=92);sheets.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    prepared=m.load(c.RESEARCH/'image-delivery-prepared-001.json')['rows'];canvas=Image.new('RGB',(1440,1800),'#eeeae3');draw=ImageDraw.Draw(canvas)
    for j,v in enumerate(prepared):
        im=Image.open(v['prepared_path']);im.thumbnail((340,310));x=j%4*360+(360-im.width)//2;y=j//4*360;canvas.paste(im,(x,y));draw.text((j%4*360+8,y+313),str(v['number'])+' | '+v['source_id'].split('-')[-1],fill='black',font=font);draw.text((j%4*360+8,y+335),v['title'][:42],fill='black',font=font)
    p=PROOF/'prepared-contact.jpg';canvas.save(p,quality=92)
    m.save(RUN/'focused-review-inputs-001.json',dict(at=m.now(),frames=frames,contacts=sheets,prepared_contact=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()),snapshot_reference=c.ref(dest),source_citations_reference=c.ref(RUN/'production-identity-citations-001.json.gz'),script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(focused=len(ids),comparison_images=len(frames),comparison_contacts=len(sheets),prepared_images=19)),flush=True)
if __name__=='__main__':main()
