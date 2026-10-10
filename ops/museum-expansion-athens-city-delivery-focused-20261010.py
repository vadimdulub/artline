"""Bounded physical-object comparisons and exact creator authority evidence."""
import gzip,hashlib,importlib.util,io,json,re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-athens-city-delivery-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF=c.m,c.RUN,c.PROOF
ARTISTS=['5c005acb-575b-44db-97c8-1680d829a479','6bc44dd0-9a43-4709-8fd4-454ead88bb15']
COMPARE=['69af1dd0-60bd-5bbb-aaaf-7db08fbf6308','2f999bf7-7098-4480-994d-a39b1ecafb47','727bae1c-b8c0-53f7-9973-caf07b2e792c']

def artist_state(db):
    out={}
    for key,sql in {
      'artists':'SELECT to_jsonb(x) row FROM artists x WHERE id=ANY(%s::uuid[]) ORDER BY id',
      'aliases':'SELECT to_jsonb(x) row FROM artist_aliases x WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,id',
      'identifiers':"SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id"}.items():
        out[key]=[x['row'] for x in db.execute(sql,(ARTISTS,))]
    return out

def main():
    assert not(RUN/'focused-review-inputs-001.json').exists()
    obs=m.load(RUN/'production-identity-001.json.gz');state=obs['state'];source=m.load(c.RESEARCH/'editorial-source-decisions-001.json.gz')['rows']
    ids=sorted(set(state['scoped_ids'])|{a['id'] for x in obs['comparisons'] for a in x['title_hits']}|{x['artwork_id'] for x in state['creator_links'] if x['artist_id'] in ARTISTS})
    path=RUN/'focused-comparators-001.json.gz'
    if path.exists():focus=m.load(path)
    else:
        with c.prod.connect() as db,db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');snap=c.snapshot(db,ids);artists=artist_state(db)
        focus=dict(at=m.now(),ids=ids,snapshot=snap,artist_ids=ARTISTS,artist_state=artists,identity_reference=c.ref(RUN/'production-identity-001.json.gz'));m.save(path,focus)
    media={v['id']:v for v in focus['snapshot']['media_assets']};frames=[]
    for a in focus['snapshot']['artworks']:
        if a['id'] not in COMPARE:continue
        im=media[a['primary_media_id']];url='https://artlines.org'+im['storage_path'];receipt=RUN/'comparison-image-receipts'/(a['id']+'.json')
        if receipt.exists():frame=m.load(receipt)
        else:
            response=requests.get(url,timeout=(15,40));response.raise_for_status();raw=response.content;digest=hashlib.sha256(raw).hexdigest();assert digest==im['checksum_sha256'];image=Image.open(io.BytesIO(raw));image.load();dest=PROOF/'comparison-images'/(a['id']+'.jpg');dest.parent.mkdir(parents=True,exist_ok=True);dest.open('xb').write(raw)
            frame=dict(at=m.now(),artwork_id=a['id'],title=a['title'],url=url,status=response.status_code,path=str(dest),sha256=digest,bytes=len(raw),width=image.width,height=image.height);m.save(receipt,frame)
        frames.append(frame)
    selected=[dict(path=v['path'],label=v['artwork_id'][:8]+' '+v['title']) for v in frames]
    selected += [dict(path=x['visual_reference']['path'],label='Athens '+str(x['number'])+' '+x['title']) for x in source if x['number'] in [10,11,19,20,103,117,133,162]]
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16);sheet=Image.new('RGB',(1440,1080),'#eeeae3');draw=ImageDraw.Draw(sheet)
    for j,v in enumerate(selected):
        im=Image.open(v['path']);im.thumbnail((340,305));x=j%4*360+(360-im.width)//2;y=j//4*360;sheet.paste(im,(x,y));draw.text((j%4*360+8,y+315),v['label'][:40],fill='black',font=font)
    dest=PROOF/'focused-contact.jpg';assert not dest.exists();sheet.save(dest,quality=92)
    m.save(RUN/'focused-review-inputs-001.json',dict(at=m.now(),frames=frames,selected=selected,contact=dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()),snapshot_reference=c.ref(path),script_reference=c.ref(Path(__file__).resolve())))
    q=c.module('q','museum-expansion-kazantzakis-source-20261009.py');q.RUN=RUN;q.CAP=RUN/'captures';q.CAP.mkdir(parents=True,exist_ok=True);authorities=[]
    for n in [103,117]:
        row=next(x for x in source if x['number']==n);html=BeautifulSoup(gzip.decompress((m.ROOT/row['source_receipt']['body_path']).read_bytes()),'html.parser')
        urls=sorted({'https://www.searchculture.gr'+a['href'] for a in html.select('a[href]') if re.fullmatch(r'/aggregator/persons/-?\d+',a['href'])})
        for url in urls:
            doc,receipt=q.capture('authority-'+url.rsplit('/',1)[-1]+'-001',url)
            authorities.append(dict(number=n,url=url,receipt=receipt,title=doc.title.get_text(' ',strip=True),text=doc.get_text(' ',strip=True),object_reference=row['source_receipt']))
    m.save(RUN/'creator-source-corroboration-001.json',dict(at=m.now(),rows=authorities,policy='Observed object-page links only; sitter authorities are comparison evidence, not creators. No authority records changed.'))
    print(json.dumps(dict(focused=len(ids),images=len(frames),contact_frames=len(selected),authority_pages=len(authorities))),flush=True)

if __name__=='__main__':main()
