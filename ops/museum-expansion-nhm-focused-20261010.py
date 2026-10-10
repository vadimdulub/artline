"""Read-only full comparator snapshot, bridge accessions and existing Skene identity."""
import hashlib,importlib.util,json
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageDraw
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-nhm-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
ARTISTS=['0b969b0e-ec3e-5c85-8772-d5768b521db8']

def artist_state(db):
    out={}
    for key,sql in {'artists':'SELECT to_jsonb(x) row FROM artists x WHERE id=ANY(%s::uuid[]) ORDER BY id','aliases':'SELECT to_jsonb(x) row FROM artist_aliases x WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,id','identifiers':"SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id"}.items():out[key]=[x['row'] for x in db.execute(sql,(ARTISTS,))]
    return out

def main():
    p=RUN/'focused-comparators-001.json.gz';assert not p.exists();obs=m.load(RUN/'production-identity-001.json.gz');ids=obs['state']['artwork_ids']
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');snap=c.snapshot(db,ids);artists=artist_state(db)
        bridge=db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s) ORDER BY id',(['15153-52','15153-7'],)).fetchall();assert not bridge
    m.save(p,dict(at=m.now(),ids=ids,snapshot=snap,artist_ids=ARTISTS,artist_state=artists,bridge_accession_hits=bridge,identity_reference=c.ref(RUN/'production-identity-001.json.gz'),script_reference=c.ref(Path(__file__).resolve())))
    src=c.module('src','museum-expansion-nhm-source-20261010.py');authorities=[]
    for key,url in [('skene-native-publication-001','https://nhmuseum.gr/ekdoseis/imerologia/item/179-imerologio-2017'),('skene-getty-001','https://www.getty.edu/vow/ULANFullDisplay?find=&nation=&role=&subjectid=500016543')]:
        doc,rc=src.capture(key,url);authorities.append(dict(url=url,title=doc.title.get_text(' ',strip=True),text=src.clean(doc.get_text(' ',strip=True)),receipt=rc))
    m.save(RUN/'creator-source-corroboration-001.json',dict(at=m.now(),rows=authorities,policy='Existing James Skene painter identity only. No artist creation, aliases, biographies or existing metadata changes.'))
    bridges=m.load(RUN/'bridge-native-comparators-001.json')['rows'];folder=c.PROOF/'bridge-native-images';folder.mkdir(parents=True,exist_ok=True);rows=[]
    for b in bridges:
        n=b['number'];url=b['images'][0]['url'];dest=folder/(str(n)+'.jpg');assert not dest.exists();r=requests.get(url,timeout=(15,45));r.raise_for_status();raw=r.content;dest.write_bytes(raw)
        with Image.open(dest) as im:im.load();assert im.format=='JPEG';size=im.size
        rows.append(dict(at=m.now(),number=n,url=url,status=r.status_code,path=str(dest),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),width=size[0],height=size[1],object_reference=b['receipt']))
    canvas=Image.new('RGB',(1000,700),'white');draw=ImageDraw.Draw(canvas);thumbs={x['number']:x for x in m.load(RUN/'visual-references-001.json')['rows']}
    for i,b in enumerate(rows):
        for j,r in enumerate([thumbs[b['number']],b]):
            with Image.open(r['path']) as im:thumb=ImageOps.contain(im.convert('RGB'),(490,300))
            x=j*500;y=i*350;canvas.paste(thumb,(x+(500-thumb.width)//2,y));draw.text((x+8,y+310),str(b['number'])+(' aggregator' if j==0 else ' native'),fill='black')
    contact=c.PROOF/'bridge-native-comparison.jpg';assert not contact.exists();canvas.save(contact,quality=94)
    m.save(RUN/'bridge-image-references-001.json',dict(at=m.now(),rows=rows,contact=dict(path=str(contact),sha256=hashlib.sha256(contact.read_bytes()).hexdigest()),visually_reviewed=False))
    print(json.dumps(dict(protected=len(ids),bridge_hits=len(bridge),artist=artists['artists'][0]['display_name'],authorities=[x['title'] for x in authorities]),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
