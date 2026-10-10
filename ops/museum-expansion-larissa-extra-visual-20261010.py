"""Read only explicit image links on selected comparator pages; no URL guessing."""
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
spec=importlib.util.spec_from_file_location('e',Path(__file__).with_name('museum-expansion-larissa-extra-comparators-20261010.py'))
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
c,m,RUN,PROOF=e.c,e.m,e.RUN,e.PROOF

def main():
    pages=m.load(RUN/'extra-comparator-pages-001.json.gz')['pages'];selected=[]
    for p in pages:
        if p.get('og_image'):
            stem=p['og_image'].split('/')[-1].split('_')[0]
            urls=[x['src'] for x in p['images'] if '/wp-content/uploads/' in x['src'] and stem in x['src']];assert len(urls)==1
        else:urls=[x['src'] for x in p['images'] if x['alt']=='Printable main image'];assert len(urls)==1
        selected.append(dict(artwork_id=p['artwork_id'],url=urls[0],source_url=p['url']))
    rhodes=m.ROOT/'docs/research/museum-expansion-20261006/native/rhodes-final-20261009/captures/object-8ea36f90-2df1-4e1f-b262-6ee076c1e258-001.body.gz'
    source=json.loads(gzip.decompress(rhodes.read_bytes()));selected.append(dict(artwork_id='752ef8cd-c530-5691-8498-c0e5dcb99c45',url=source['coverFile']['viewUrl'],source_reference=c.ref(rhodes)))
    rows=[]
    for v in selected:
        res=e.v.get(v['url']);res.raise_for_status();raw=res.content;assert len(raw)<=12000000
        with Image.open(io.BytesIO(raw)) as im:im.load();size=im.size
        path=PROOF/'extra-images'/(v['artwork_id']+'.image');path.parent.mkdir(parents=True,exist_ok=True);assert not path.exists();path.write_bytes(raw)
        rows.append(dict(v,at=m.now(),status=res.status_code,final_url=res.url,path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),width=size[0],height=size[1]))
    m.save(RUN/'extra-visual-frames-001.json',dict(at=m.now(),rows=rows,script_reference=c.ref(Path(__file__).resolve()),purpose='Internal comparison only; no image attachment or legal ownership inference.'))
    originals={x['number']:x for x in m.load(c.RESEARCH/'visual-references-001.json')['rows']};items=[dict(label='LARISSA '+str(n),path=originals[n]['path']) for n in [7,8,9,48,49,63,122]]+[dict(label=x['artwork_id'][:8],path=x['path']) for x in rows]
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17);canvas=Image.new('RGB',(1600,1360),'white');draw=ImageDraw.Draw(canvas)
    for k,x in enumerate(items):
        x0=k%4*400;y0=k//4*340;draw.text((x0+4,y0+4),x['label'],font=font,fill='black')
        with Image.open(x['path']) as im:
            thumb=ImageOps.contain(im.convert('RGB'),(390,305));canvas.paste(thumb,(x0+(400-thumb.width)//2,y0+30+(305-thumb.height)//2))
    path=PROOF/'extra-comparison-contact.jpg';assert not path.exists();canvas.save(path,quality=94)
    m.save(RUN/'extra-visual-contact-001.json',dict(at=m.now(),path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),items=items))
    print(json.dumps(dict(frames=len(rows),contact=str(path))),flush=True)

if __name__=='__main__':main()
