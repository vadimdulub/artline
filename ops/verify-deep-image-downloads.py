#!/usr/bin/env python3
"""Verify staged image bytes and create a small contact sheet for visual review."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw

spec=importlib.util.spec_from_file_location('core',Path(__file__).with_name('enrich-artwork-images.py'))
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args()
report=json.loads((a.run/'download-report.json').read_text());rows=report['images'];errors=[]
for r in rows:
    data=Path(r['path']).read_bytes()
    if core.sha(data)!=r['sha256'] or len(data)!=r['bytes'] or len(data)>100000:errors.append({'id':r['object_id'],'reason':'Hash or size mismatch'})
    with Image.open(io.BytesIO(data)) as im:
        if im.size!=(r['width'],r['height']) or im.format!='JPEG':errors.append({'id':r['object_id'],'reason':'Dimensions or format mismatch'})
        im.verify()
pages=[]
for start in range(0,len(rows),15):
    subset=rows[start:start+15];canvas=Image.new('RGB',(1000,700),'#eeeae4');draw=ImageDraw.Draw(canvas)
    for index,r in enumerate(subset):
        x=index%5*200;y=index//5*230
        with Image.open(r['path']) as im:
            thumbnail=ImageOps.contain(im.convert('RGB'),(190,190))
            canvas.paste(thumbnail,(x+(200-thumbnail.width)//2,y+(190-thumbnail.height)//2))
        draw.text((x+4,y+194),r['object_id']+' / '+str(r['bytes'])+' B',fill='black')
        draw.text((x+4,y+208),r['artist'][:26],fill='black')
    output=io.BytesIO();canvas.save(output,'JPEG',quality=90)
    path=a.run/('contact-sheet-'+str(start//15+1)+'.jpg');core.save_new(path,output.getvalue());pages.append(str(path))
core.save_new(a.run/'file-verification.json',{'at':core.now(),'images':len(rows),'bytes':sum(r['bytes'] for r in rows),
    'max_bytes':max((r['bytes'] for r in rows),default=0),'report_sha256':core.sha((a.run/'download-report.json').read_bytes()),'contact_sheets':pages,'errors':errors})
print(json.dumps({'images':len(rows),'errors':errors,'contact_sheets':pages}),flush=True)
if errors:raise SystemExit(1)
