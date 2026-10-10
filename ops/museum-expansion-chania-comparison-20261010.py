"""Bounded comparisons from captured frames and four observed aggregator thumbnails."""
import hashlib
import importlib.util
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-chania-visual-20261010.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
m,RUN,PROOF=v.m,v.RUN,v.PROOF

def main():
    sources={r['number']:r for r in m.load(RUN/'selected-source-records-001.json.gz')['rows']}
    frames={r['number']:r for r in m.load(RUN/'visual-references-001.json')['rows']}
    extra=[]
    for n in [36,38,110,161]:
        s=sources[n];p=PROOF/('aggregator-thumbnail-'+str(n)+'.jpg')
        r=requests.get(s['thumbnail_url'],timeout=(15,45));r.raise_for_status()
        assert r.headers.get('Content-Type','').startswith('image/') and not p.exists()
        p.write_bytes(r.content)
        with Image.open(p)as im:width,height=im.size;fmt=im.format
        rc=dict(v.ref(p),number=n,url=s['thumbnail_url'],final_url=r.url,status=r.status_code,content_type=r.headers.get('Content-Type'),bytes=len(r.content),width=width,height=height,format=fmt,at=m.now())
        m.save(RUN/'captures'/('comparison-thumbnail-'+str(n)+'-001.json'),rc);extra.append(rc)
    groups=[('suspect-36',[36]),('suspect-38',[38]),('suspect-110',[110]),('suspect-161',[161]),
        ('cauldron',[120,108,109,133,143,144]),('paired-ornaments',[67,151]),('bosses',[7,22]),
        ('necklaces',[75,85,99,100]),('skyphoi',[32,43]),('mirrors',[60,88,148])]
    sheets=[];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
    for name,ns in groups:
        refs=[dict(number=n,label='native '+str(n),path=frames[n]['path'])for n in ns]
        if name.startswith('suspect-'):
            refs += [dict(number=n,label='aggregator '+str(n),path=next(r['path']for r in extra if r['number']==n))for n in ns]
        cols=min(len(refs),3);rows=(len(refs)+cols-1)//cols
        canvas=Image.new('RGB',(cols*360,rows*550),'white');draw=ImageDraw.Draw(canvas)
        for j,r in enumerate(refs):
            x,y=(j%cols)*360,(j//cols)*550;draw.text((x+5,y+5),r['label'],font=font,fill='black')
            with Image.open(r['path'])as im:
                rgba=im.convert('RGBA');bg=Image.new('RGBA',rgba.size,'white');bg.alpha_composite(rgba)
                thumb=ImageOps.contain(bg.convert('RGB'),(350,515));canvas.paste(thumb,(x+(360-thumb.width)//2,y+30+(515-thumb.height)//2))
        p=PROOF/('comparison-'+name+'.jpg');assert not p.exists();canvas.save(p,quality=92)
        sheets.append(dict(v.ref(p),numbers=ns,inputs=[dict(number=r['number'],label=r['label'],reference=v.ref(r['path']))for r in refs]))
    m.save(RUN/'comparison-references-001.json',dict(at=m.now(),thumbnails=extra,sheets=sheets,script_reference=v.ref(Path(__file__).resolve()),policy='Complete source frames shown proportionally on white. Internal identity review; no crop, retouch, inferred image swap or claim of visual completion.'))
    print(dict(thumbnails=len(extra),sheets=len(sheets)))

if __name__=='__main__':main()
