"""Selected low-resolution references for physical-unit and duplicate review only."""
import collections,gzip,hashlib,importlib.util,json,time
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageDraw,ImageFont
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-kazantzakis-facts-20261009.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f);s=f.s;m=f.m;RUN=f.RUN
DEST=Path('/Users/vadimdulub/Library/Application Support/Artline/research-proofs/kazantzakis-20261009/identity-images');DEST.mkdir(parents=True,exist_ok=True)
def main():
 selected=[v for v in f.rows()if v['metadata_state']=='eligible_metadata_candidate'];out=[];session=requests.Session()
 for r in selected:
  n=r['number'];url=r['facts']['thumbnail_url'];assert url and url.startswith('https://www.searchculture.gr/aggregator/thumbnails/edm-record/');path=DEST/(str(n).zfill(3)+'.jpg');rcpath=RUN/'captures'/('visual-'+str(n).zfill(3)+'-001.json')
  if rcpath.exists():
   rc=m.load(rcpath);assert hashlib.sha256(Path(rc['path']).read_bytes()).hexdigest()==rc['sha256']
  else:
   res=session.get(url,timeout=(15,45));raw=res.content;assert len(raw)<2_000_000;available=res.status_code==200 and res.headers.get('Content-Type','').startswith('image/')
   if not available:path=path.with_suffix('.response');path.write_bytes(raw);width=height=None
   else:path.write_bytes(raw);im=Image.open(path);width,height=im.size
   rc=dict(url=url,final_url=res.url,status=res.status_code,content_type=res.headers.get('Content-Type'),available=available,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),width=width,height=height,path=str(path),source_url=r['facts']['source_url'],source_rights=r['facts']['rights'],purpose='Selected bounded thumbnail for internal physical identity review only. NC/ND labels preserved; no production delivery,attachment or public-image permission assertion. Metadata selection precedes these reads.');m.save(rcpath,rc)
   if res.status_code in [403,429]:raise RuntimeError('Provider access hold '+str(res.status_code))
   if not available:print(json.dumps(dict(number=n,thumbnail_unavailable=True,status=res.status_code,content_type=rc['content_type'])),flush=True)
   time.sleep(.3)
  out.append(dict(number=n,source_id=r['source_id'],receipt=rc))
  if len(out)%20==0:print(json.dumps(dict(review_thumbnails=len(out))),flush=True)
 sheets=[];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
 for group in range(0,len(out),24):
  batch=out[group:group+24];canvas=Image.new('RGB',(1440,1120),'white');draw=ImageDraw.Draw(canvas)
  for j,v in enumerate(batch):
   x=(j%6)*240;y=(j//6)*280
   if v['receipt'].get('available',True):
    im=Image.open(v['receipt']['path']).convert('RGB');im.thumbnail((228,245));canvas.paste(im,(x+(240-im.width)//2,y+28+(245-im.height)//2))
   else:draw.text((x+15,y+100),'Source image unavailable',fill='black',font=font)
   draw.text((x+5,y+3),str(v['number'])+' | '+v['source_id'].split('-')[-1],fill='black',font=font)
  path=DEST/('contact-'+str(group//24+1).zfill(2)+'.jpg');canvas.save(path,quality=92);sheets.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),numbers=[v['number']for v in batch]))
 groups=collections.defaultdict(list)
 for v in out:
  if v['receipt'].get('available',True):groups[v['receipt']['sha256']].append(v['number'])
 m.save(RUN/'visual-reference-captures-001.json',dict(at=m.now(),rows=out,contact_sheets=sheets,identical_byte_groups=[v for v in groups.values()if len(v)>1],script_reference=s.ref(Path(__file__).resolve()),policy='102 metadata-selected candidate reference thumbnails only,not an exhaustive collection download. Original source files untouched. Contact sheets for internal QA,no catalogue images.'))
 print(json.dumps(dict(thumbnails=len(out),sheets=len(sheets),identical_byte_groups=[v for v in groups.values()if len(v)>1])),flush=True)
if __name__=='__main__':main()
