"""Bounded public preservation previews and internal physical-identity comparisons."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageOps

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-zongolopoulos-paintings-visual-20261010.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
m,RUN,PROOF=v.m,v.RUN,v.PROOF

def ref(p):
    p=Path(p)
    return dict(path=str(p.relative_to(m.ROOT))if p.is_relative_to(m.ROOT)else str(p),sha256=v.sha(p))

def main():
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows'];by={s['number']:s for s in sources}
    visual=m.load(RUN/'visual-references-001.json');images={s['number']:s for s in visual['rows']}
    dest=PROOF/'focused-review';dest.mkdir(parents=True,exist_ok=True)
    previews=[]
    for number in [1,97,61,44,50]:
        s=by[number];sid=s['source_id'].rsplit('-',1)[1]
        soup=BeautifulSoup(gzip.decompress((m.ROOT/s['receipt']['body_path']).read_bytes()),'html.parser')
        links={urljoin(s['source_url'],a['href'])for a in soup.select('a[href]')if '/'+s['source_id']+'/files/'in a['href']}
        assert len(links)==1
        soup,receipt=v.q.q.capture('file-viewer-'+sid+'-001',links.pop())
        media=soup.select('img.files-thumbnail');assert len(media)==1
        url=urljoin(receipt['final_url'],media[0]['src'])
        assert '/digital-files-from-preservator/file/'in url
        path=dest/(sid+'-preservation-preview.jpg');rp=RUN/'captures'/('preservation-preview-'+sid+'-001.json')
        if rp.exists():
            rc=m.load(rp);assert rc['status']==200 and v.sha(path)==rc['sha256']
        else:
            res=requests.get(url,timeout=(15,45))
            rc=dict(at=m.now(),number=number,source_id=s['source_id'],url=url,final_url=res.url,status=res.status_code,
                    content_type=res.headers.get('Content-Type'),bytes=len(res.content),sha256=hashlib.sha256(res.content).hexdigest(),path=str(path),viewer_receipt=receipt)
            if res.status_code!=200 or not rc['content_type'].startswith('image/'):
                m.save(rp,rc);raise RuntimeError('Preservation preview unavailable; stop provider pass')
            assert not path.exists();path.write_bytes(res.content)
            with Image.open(path)as im:rc.update(width=im.width,height=im.height)
            m.save(rp,rc)
        previews.append(rc)
        print(json.dumps(dict(preview=number,width=rc['width'],height=rc['height'],bytes=rc['bytes'])),flush=True)
    groups=[('landscape-supports',[6,44,50]),('window-scenes',[27,28,82,83,115,130]),
        ('illustrated-maps',[65,74]),('book-reference-pair',[37,43]),('paper-collages',[18,26,31]),
        ('balsa-collages',[56,68,75,85]),('description-comparisons',[33,41,46,61,95]),
        ('date-evidence',[1,90,97]),('geometric-sheets',[131,132,133,134,135,140,144,145,146,147])]
    sheets=[];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',19)
    for name,numbers in groups:
        cols=min(3,len(numbers));canvas=Image.new('RGB',(cols*510,((len(numbers)+cols-1)//cols)*530),'white');draw=ImageDraw.Draw(canvas)
        for i,n in enumerate(numbers):
            x,y=(i%cols)*510,(i//cols)*530;s=by[n]
            draw.text((x+5,y+5),str(n)+' | '+s['source_id'].rsplit('-',1)[1],font=font,fill='black')
            with Image.open(images[n]['path'])as im:
                thumb=ImageOps.contain(im.convert('RGB'),(500,490));canvas.paste(thumb,(x+(510-thumb.width)//2,y+35+(490-thumb.height)//2))
        path=dest/(name+'.jpg');assert not path.exists();canvas.save(path,quality=94)
        sheets.append(dict(ref(path),numbers=numbers))
    old=m.load(v.t.OLD/'visual-references-001.json');oldhash={r['sha256']:r for r in old['rows']}
    m.save(RUN/'comparison-references-001.json',dict(at=m.now(),sheets=sheets,preservation_previews=previews,
        exact_duplicate_images_with_previous=[dict(current=r['source_id'],previous=oldhash[r['sha256']]['source_id'])for r in visual['rows']if r['sha256']in oldhash],
        source_reference=ref(RUN/'selected-source-records-001.json.gz'),visual_reference=ref(RUN/'visual-references-001.json'),
        prior_visual_reference=ref(v.t.OLD/'visual-references-001.json'),script_reference=ref(Path(__file__).resolve()),
        policy='Selected internal review only. Public viewer and preview URLs observed in captured HTML; no guessed URLs or bulk originals. Montages preserve full thumbnail frames and do not establish dates. No production image files or uploads.'))

if __name__=='__main__':main()
