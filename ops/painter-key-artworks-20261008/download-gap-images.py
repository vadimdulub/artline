import importlib.util,requests,concurrent.futures,time,io,hashlib,re
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
originals=Path.home()/'Library/Application Support/Artline/source-images/painter-key-artworks-20261008';originals.mkdir(parents=True,exist_ok=True)
assets=Path.cwd()/'apps/web/public/assets/artworks/imported/painter-key-artworks-20261008';assets.mkdir(parents=True,exist_ok=True)
rows=m.base.load(m.RUN/'gap-reviewed-plan.json.gz')
def fetch(row):
 try:
  info=row['image_info'];url=info.get('thumburl') or info['url'];original=originals/(row['work_qid']+'.source')
  if original.exists():raw=original.read_bytes()
  else:
   time.sleep(.5);r=requests.get(url,headers={'User-Agent':'Artline/1.0 (selected artwork image research; artlines.org)'},timeout=45);r.raise_for_status();raw=r.content
   assert len(raw)<=25000000,'oversize source';original.write_bytes(raw)
  im=ImageOps.exif_transpose(Image.open(io.BytesIO(raw)));im.load();im=im.convert('RGB');im.thumbnail((1500,1500),Image.Resampling.LANCZOS)
  for quality in [86,80,74,68,62,56,50]:
   b=io.BytesIO();im.save(b,format='JPEG',quality=quality,optimize=True)
   if len(b.getvalue())<=100000:break
  while len(b.getvalue())>100000:
   im.thumbnail((int(im.width*.85),int(im.height*.85)),Image.Resampling.LANCZOS);b=io.BytesIO();im.save(b,format='JPEG',quality=65,optimize=True)
  digest=hashlib.sha256(b.getvalue()).hexdigest();name=row['work_qid'].lower()+'-'+digest[:16]+'.jpg';path=assets/name;path.write_bytes(b.getvalue())
  return dict(**row,prepared=dict(path='/assets/artworks/imported/painter-key-artworks-20261008/'+name,sha256=digest,byte_size=len(b.getvalue()),width=im.width,height=im.height,download_url=url,source_sha256=hashlib.sha256(raw).hexdigest()))
 except Exception as e:return dict(work_qid=row['work_qid'],error=str(e).split('?')[0])
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for i,r in enumerate(pool.map(fetch,rows)):
  results.append(r)
  if (i+1)%50==0:print('images prepared',i+1,'/',len(rows),flush=True)
m.save('gap-image-preparation.json.gz',results);good=[r for r in results if r.get('prepared')]
# Review sheets contain unchanged proportional thumbnails with stable identities.
for offset in range(0,len(good),24):
 subset=good[offset:offset+24];sheet=Image.new('RGB',(1200,1200),'white');draw=ImageDraw.Draw(sheet)
 for i,r in enumerate(subset):
  x=(i%6)*200;y=(i//6)*300;im=Image.open(Path.cwd()/'apps/web/public'/r['prepared']['path'].lstrip('/'));im.thumbnail((190,220));sheet.paste(im,(x+(200-im.width)//2,y));label=r['work_qid']+' '+r['artist_name']
  draw.text((x+4,y+222),label[:29],fill='black');draw.text((x+4,y+238),r['title'][:29],fill='black');draw.text((x+4,y+254),str(r['year'])+' '+r['rights_status'],fill='black')
 sheet.save(originals/('review-%03d.jpg'%(offset//24)),quality=85)
print('Prepared',len(good),'failed',len(results)-len(good),flush=True)
