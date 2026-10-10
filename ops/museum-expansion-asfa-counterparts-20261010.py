"""Nine creator-scoped photographic comparisons; reuse existing source URLs only."""
import concurrent.futures,gzip,hashlib,importlib.util,io,json
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageDraw
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-asfa-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF=c.m,c.RUN,c.PROOF
IDS=['1ec41f08-01c0-523f-9165-dc32b210faaf','6f4e418a-e650-53ba-b654-c0f332ca67e6','4802adb0-4c1e-5872-984b-e3d0fe094bda','62d30e43-6b72-5906-b6ed-a26cf3854498','75cf084b-e18c-542c-990f-e070ac4806c9','a0b14f9e-50ae-520e-860b-8f6c59e2aeba','aa0e924a-68c8-5407-bc66-41a160b9399f','b318aa2a-7ae4-5d05-a195-a702783633d2','a91e096f-7c1b-5313-b336-e3f4dd549d6b']

def main():
    assert not (RUN/'counterpart-images-001.json').exists()
    q=c.module('q','museum-expansion-asfa-source-20261010.py').q;citations=m.load(RUN/'production-identity-citations-001.json.gz')['citations'];arts={x['id']:x for x in m.load(RUN/'production-identity-001.json.gz')['state']['artworks']};rows=[]
    for aid in IDS:
        urls=sorted({x['source_url'] for x in citations if x['entity_id']==aid and x['source_url'].startswith('https://www.wikiart.org/')});assert len(urls)==1;doc,rc=q.q.capture('counterpart-'+aid+'-001',urls[0]);meta=doc.select_one('meta[property="og:image"]');assert meta
        imurl=meta['content'];assert 'wikiart.org/' in imurl
        rp=RUN/'comparison-image-receipts'/(aid+'.json');path=PROOF/'comparison-images'/(aid+'.jpg');path.parent.mkdir(parents=True,exist_ok=True)
        if rp.exists():frame=m.load(rp);assert frame['status']==200 and hashlib.sha256(path.read_bytes()).hexdigest()==frame['sha256']
        else:
            response=requests.get(imurl,timeout=(15,45));raw=response.content;frame=dict(at=m.now(),artwork_id=aid,title=arts[aid]['title'],source_url=urls[0],url=imurl,status=response.status_code,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),path=str(path))
            if response.status_code!=200:path.with_suffix('.error').write_bytes(raw);m.save(rp,frame);response.raise_for_status()
            with Image.open(io.BytesIO(raw)) as im:im.load();frame.update(width=im.width,height=im.height)
            path.open('xb').write(raw);m.save(rp,frame)
        rows.append(dict(frame,source_receipt=rc,comparison_number=len(rows)+1))
    selected=[dict(path=x['path'],label='C'+str(x['comparison_number'])+' '+x['title']) for x in rows];selected += [dict(path=x['visual_reference']['path'],label='ASFA '+str(x['number'])) for x in m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'] if x['number'] in [7,17,24,33,49,58]]
    canvas=Image.new('RGB',(1500,900),'white');draw=ImageDraw.Draw(canvas)
    for j,row in enumerate(selected):
        with Image.open(row['path']) as im:thumb=ImageOps.contain(im.convert('RGB'),(285,265))
        x=j%5*300;y=j//5*300;canvas.paste(thumb,(x+(300-thumb.width)//2,y+(270-thumb.height)//2));draw.text((x+4,y+276),row['label'][:48],fill='black')
    path=PROOF/'counterpart-contact-001.jpg';assert not path.exists();canvas.save(path,quality=93)
    m.save(RUN/'counterpart-images-001.json',dict(at=m.now(),rows=rows,selected=selected,contact=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()),script_reference=c.ref(Path(__file__).resolve()),visually_reviewed=False,policy='Bounded existingcreator works and sourceidentity/titletranslation candidates. Source-page images for comparison only; no old metadata/media changes.'))
    print(json.dumps(dict(comparators=len(rows),contact_frames=len(selected))),flush=True)

if __name__=='__main__':main()
