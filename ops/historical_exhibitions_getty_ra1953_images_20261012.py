#!/usr/bin/env python3
"""Prepare selected Getty drawings' CC0 primary reproductions; no DB writes."""
import json,io,concurrent.futures
from PIL import Image,ImageOps,ImageDraw
import exhibitions_common as c
from historical_exhibitions_getty_ra1953_discovery_20261012 import OUT
DEST=OUT/'images'
def prepare(o, bounded=False):
 key=o['id'].rsplit('/',1)[-1];d=c.load(OUT/'objects'/(key+'.json'))['data'];manifestURL=next(s['id']for s in d['subject_of']if '/manifest/3/'in s['id']);raw,rc=c.capture(manifestURL);m=json.loads(raw);c.save(DEST/(key+'-manifest.json'),dict(receipt=rc,data=m));canvas=m['items'][0];rights=canvas.get('rights',m.get('rights'));assert rights and rights.rstrip('/').endswith('/publicdomain/zero/1.0')
 body=canvas['items'][0]['items'][0]['body'];url=body['id']
 if bounded:
  service=body['service'][0];size=max((s for s in service['sizes']if max(s.values())<=2000),key=lambda s:s['width']);url=service['id']+'/full/'+str(size['width'])+',/0/default.jpg'
 raw,imrc=c.capture(url);original=DEST/(key+'-original.jpg');original.write_bytes(raw);im=Image.open(io.BytesIO(raw)).convert('RGB');size=im.size;im.thumbnail((1400,1400))
 for q in range(90,24,-5):
  b=io.BytesIO();im.save(b,format='JPEG',quality=q,optimize=True)
  if len(b.getvalue())<=100000:break
 while len(b.getvalue())>100000:
  im.thumbnail((int(im.width*.85),int(im.height*.85)));b=io.BytesIO();im.save(b,format='JPEG',quality=65,optimize=True);q=65
 assert len(b.getvalue())<=100000
 path=DEST/(key+'.jpg');path.write_bytes(b.getvalue());result=dict(objectID=o['id'],accession=o['accession'],title=o['title'],manifestReceipt=rc,canvasID=canvas['id'],canvasLabel=canvas.get('label'),otherCanvases=[x.get('label')for x in m['items'][1:]],rights=rights,imageReceipt=imrc,originalSize=size,derivativeSize=im.size,bytes=len(b.getvalue()),sha256=c.sha(b.getvalue()),path=str(path),fullFrame=True,quality=q,visualReview='pending')
 c.save(DEST/(key+'-prepared.json'),result);return result

def main():
 DEST.mkdir(parents=True,exist_ok=True);objects=c.load(OUT/'discovery.json.gz')['objects'];rows=[];errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
  jobs={pool.submit(prepare,o):o for o in objects}
  for f in concurrent.futures.as_completed(jobs):
   try:rows.append(f.result());print('Prepared',rows[-1]['accession'],flush=True)
   except Exception as e:errors.append(dict(objectID=jobs[f]['id'],error=str(e)))
 rows.sort(key=lambda r:r['accession']);c.save(DEST/'prepared-batch.json',dict(at=c.now(),images=rows,errors=errors))
 sheet=Image.new('RGB',(1200,((len(rows)+3)//4)*430),'white');draw=ImageDraw.Draw(sheet)
 for i,r in enumerate(rows):
  im=Image.open(r['path']);im.thumbnail((280,375));x=(i%4)*300;y=(i//4)*430;sheet.paste(im,(x+(300-im.width)//2,y));draw.text((x+8,y+382),r['accession'],fill='black');draw.text((x+8,y+400),r['title'][:35],fill='black')
 sheet.save('/tmp/getty-ra1953-contact.jpg');print('Complete',len(rows),'images',len(errors),'errors')
if __name__=='__main__':main()
