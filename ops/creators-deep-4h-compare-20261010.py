#!/usr/bin/env python3
"""Research-only contact sheets for selected WikiArt/native object comparisons."""
import importlib.util,sys,json,io,textwrap,os
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image,ImageDraw,ImageOps
spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name(os.environ.get('ARTLINE_CREATOR_DRIVER','creators-deep-4h-20261010.py')))
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x);x.configure(sys.argv[1])
mapping=json.loads(Path(sys.argv[2]).read_text())
prefix=sys.argv[3] if len(sys.argv)>3 else 'museum'
rows=x.r.load(x.RUN/os.environ.get('ARTLINE_CREATOR_SELECTION','research-selection.json.gz'))['rows']
root=x.ORIGINALS/x.SLUG/'identity-review';root.mkdir(parents=True,exist_ok=True)
values=[];blocked=set()
for hold in (x.RUN/'native-image-holds').glob('*.json'):
    rc=x.r.load(hold)
    if rc.get('status') in [403,429]:blocked.add(urlsplit(rc['url']).netloc)
for item in mapping:
    row=rows[item['index']-1];page=item['page_url'];native=x.r.load(x.RUN/'native-objects'/(x.r.sha(page.encode())+'.json'))
    url=item.get('image_url') or native['images'][0]['url']
    key=x.r.sha(url.encode());dest=root/(key+'.body');rp=x.RUN/'native-image-receipts'/(key+'.json')
    if urlsplit(url).netloc in blocked:
        print('HELD native comparison image host',url,flush=True);continue
    if dest.exists():
        raw=dest.read_bytes();rc=x.r.load(rp);assert x.r.sha(raw)==rc['sha256']
    else:
        response=x.m.requests.get(url,timeout=(15,45))
        if response.status_code!=200:
            x.r.save(x.RUN/'native-image-holds'/(key+'.json'),dict(url=url,status=response.status_code,reason='Native comparison image unavailable. Do not bypass or retry denial. WikiArt source remains separate.'))
            if response.status_code in [403,429]:blocked.add(urlsplit(url).netloc)
            print('HELD native comparison image',response.status_code,url,flush=True);continue
        raw=response.content
        assert len(raw)<15_000_000
        with Image.open(io.BytesIO(raw)) as im:im.verify()
        rc=dict(url=url,final_url=response.url,at=x.r.now(),sha256=x.r.sha(raw),bytes=len(raw),path=str(dest),purpose='Research-only comparison; native image not uploaded or attached')
        x.r.save(dest,raw);x.r.save(rp,rc)
    original,wrc=x.d.download(row['page']['image_url'])
    values.append(dict(**item,native_receipt=rc,wikiart_receipt=wrc,wikiart_original_path=str(x.d.ORIGINALS/(x.r.sha(wrc['url'].encode())+'.body')),title=row['work']['title']))
for start in range(0,len(values),4):
    group=values[start:start+4];canvas=Image.new('RGB',(1320,len(group)*420),'#eeeae4');draw=ImageDraw.Draw(canvas)
    for j,v in enumerate(group):
        for col,path in enumerate([v['wikiart_original_path'],v['native_receipt']['path']]):
            im=ImageOps.exif_transpose(Image.open(path)).convert('RGB');im.thumbnail((630,345))
            xx=col*660;yy=j*420;canvas.paste(im,(xx+(660-im.width)//2,yy+(345-im.height)//2))
            label=('WikiArt '+str(v['index'])+': '+v['title']) if col==0 else ('Native: '+v.get('label',v['page_url']))
            draw.text((xx+10,yy+355),'\n'.join(textwrap.wrap(label,85)),fill='black')
    dest=root/(prefix+'-comparison-'+str(start//4+1)+'.jpg');canvas.save(dest,quality=92);print(dest,flush=True)
x.r.save_gz(x.RUN/('native-image-crosswalk'+('-'+prefix if prefix!='museum' else '')+'.json.gz'),values)
