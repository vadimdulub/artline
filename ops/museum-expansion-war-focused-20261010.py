"""Protect existing comparators and inspect six related illustrated Karavia works."""
import hashlib,importlib.util,io,json
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageDraw
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-war-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN,PROOF=src.c,src.m,src.RUN,src.c.PROOF
ARTISTS=['6bc44dd0-9a43-4709-8fd4-454ead88bb15','e17bd3cc-0953-5aa6-9e0e-00a16419379d']
COMPARE=['3b47cf3e-cdc0-5c1c-9ec6-7ed34adc7009','4bb91b69-0f4d-5da4-b2e3-153756562a90','b6935028-b1e3-57d3-9591-c59aa2648d19','e041b943-8007-51fe-ac19-95decd8b7646','f8e6ad54-bd2f-56f6-90a2-dd2642c01631','797fca53-218a-54a9-830f-259164bcf86b']

def artist_state(db):
    out={}
    for key,sql in {'artists':'SELECT to_jsonb(x) row FROM artists x WHERE id=ANY(%s::uuid[]) ORDER BY id','aliases':'SELECT to_jsonb(x) row FROM artist_aliases x WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,id','identifiers':"SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id"}.items():out[key]=[x['row'] for x in db.execute(sql,(ARTISTS,))]
    return out

def main():
    p=RUN/'focused-comparators-001.json.gz';assert not p.exists();obs=m.load(RUN/'production-identity-001.json.gz');ids=obs['state']['artwork_ids']
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');snap=c.snapshot(db,ids);artists=artist_state(db)
    m.save(p,dict(at=m.now(),ids=ids,snapshot=snap,artist_ids=ARTISTS,artist_state=artists,identity_reference=c.ref(RUN/'production-identity-001.json.gz'),script_reference=c.ref(Path(__file__).resolve())))
    media={x['id']:x for x in snap['media_assets']};frames=[];folder=PROOF/'comparison-images';folder.mkdir(parents=True,exist_ok=True)
    for a in snap['artworks']:
        if a['id'] not in COMPARE:continue
        im=media[a['primary_media_id']];url='https://artlines.org'+im['storage_path'];response=requests.get(url,timeout=(15,35));response.raise_for_status();raw=response.content;digest=hashlib.sha256(raw).hexdigest();assert digest==im['checksum_sha256']
        with Image.open(io.BytesIO(raw)) as picture:picture.load();size=picture.size
        dest=folder/(a['id']+'.jpg');assert not dest.exists();dest.write_bytes(raw)
        frame=dict(at=m.now(),artwork_id=a['id'],title=a['title'],url=url,path=str(dest),status=response.status_code,sha256=digest,bytes=len(raw),width=size[0],height=size[1]);m.save(RUN/'comparison-image-receipts'/(a['id']+'.json'),frame);frames.append(frame)
    assert len(frames)==6
    canvas=Image.new('RGB',(1440,820),'white');draw=ImageDraw.Draw(canvas)
    for j,row in enumerate(frames):
        with Image.open(row['path']) as im:thumb=ImageOps.contain(im.convert('RGB'),(468,365))
        x,y=j%3*480,j//3*410;canvas.paste(thumb,(x+(480-thumb.width)//2,y));draw.text((x+8,y+380),row['artwork_id'][:8]+' '+row['title'],fill='black')
    dest=PROOF/'existing-karavia-contact.jpg';assert not dest.exists();canvas.save(dest,quality=94)
    m.save(RUN/'focused-images-001.json',dict(at=m.now(),rows=frames,contact=dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()),visually_reviewed=False))
    source=m.load(RUN/'selected-source-records-001.json.gz')['rows'];authorities=[]
    for n in [12,3]:
        row=source[n-1];urls=sorted({a['url'] for a in row['field_enrichment_links'].get('Δημιουργός',[]) if '/aggregator/persons/' in a['url']})
        for url in urls:
            doc,rc=src.capture('creator-authority-'+url.rsplit('/',1)[-1]+'-001',url);authorities.append(dict(number=n,url=url,receipt=rc,title=doc.title.get_text(' ',strip=True),text=src.clean(doc.get_text(' ',strip=True))))
    m.save(RUN/'creator-source-corroboration-001.json',dict(at=m.now(),rows=authorities,policy='Source-observed creator links only. Existing two artist authorities protected; no new biographies, aliases or artist records.169sculpture attribution toKaravia remains separately disputed.'))
    print(json.dumps(dict(comparators=len(ids),images=len(frames),authorities=len(authorities))),flush=True)

if __name__=='__main__':main()
