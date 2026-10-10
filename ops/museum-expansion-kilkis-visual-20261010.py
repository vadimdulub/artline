"""33 bounded reference thumbnails for originals,fragments andexistingcomparators."""
import gzip,hashlib,importlib.util,json,time
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont
z=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-source-20261009.py'));q=importlib.util.module_from_spec(z);z.loader.exec_module(q);m=q.m;RUN=m.RUN/'native/kilkis-review-20261010';DEST=Path.home()/'Library/Application Support/Artline/research-proofs/kilkis-20261010/identity-images';DEST.mkdir(parents=True,exist_ok=True)
rows=m.load(m.RUN/'native/kilkis-20261010/candidate-facts-001.json.gz')['rows']+m.load(RUN/'decorative-candidate-facts-001.json.gz')['rows'];selected=[]
for r in rows:
 soup=BeautifulSoup(gzip.decompress((m.ROOT/r['source_receipt']['body_path']).read_bytes()),'html.parser');im=soup.find('img',src=lambda v:v and '/thumbnails/edm-record/'+r['source_id']in v);assert im;url=urljoin(r['source_url'],im['src']);rights=sorted({a['href']for a in soup.select('a[href]')if 'creativecommons.org/licenses/'in a['href']});selected.append(dict(label=str(r['number']),source_id=r['source_id'],source_url=r['source_url'],thumbnail_url=url,rights=rights))
oldpaths={'C1593':'63c1b4cee3b2eb2445806c9bd3f1bdf74da91a744a4b3202a1beb622c3ee6c38','C4461':'b34cfa4833f69dfc02708f7b9e45276fcb0057e642cc8178f5a6761d6c7f2dfc','C1':'00882f010859e5975437a7952435fc5b59e8fe1c3ee29ac45959cdf2d2f19f36','C2':'bbf6b730f24f7b989d6cf52cee29cb58f6e62214367703e45b0c76fef4ee35ec'}
for label,key in oldpaths.items():
 p=m.ROOT/'docs/research/greek-museums-20261008/items'/(key+'.json');x=m.load(p);sid=x['url'].split('/aggregator/edm/')[1].split('?')[0];im=next(v['src']for v in x['images']if '/thumbnails/edm-record/'+sid in v['src']);selected.append(dict(label=label,source_id=sid,source_url=x['url'],thumbnail_url=im,rights=['https://creativecommons.org/licenses/by-nc-nd/4.0/'],historical_reference=q.s.ref(p)))
assert len(selected)==33;m.save(RUN/'visual-selection-001.json',dict(at=m.now(),rows=selected,policy='29metadataselectedcandidates plus4existingidentitycomparators. NC/ND internalreferenceuseonly; no productionassetattachment.'))
receipts=[]
for v in selected:
 p=DEST/(v['label']+'.jpg');assert not p.exists();r=requests.get(v['thumbnail_url'],timeout=(15,45));raw=r.content;assert len(raw)<2_000_000;available=r.status_code==200 and r.headers.get('Content-Type','').startswith('image/')
 if not available:p=p.with_suffix('.response')
 p.write_bytes(raw);width=height=None
 if available:im=Image.open(p);width,height=im.size
 rc=dict(**v,path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),status=r.status_code,content_type=r.headers.get('Content-Type'),available=available,width=width,height=height,retrieved_at=m.now());m.save(RUN/'captures'/('visual-'+v['label']+'-001.json'),rc);receipts.append(rc)
 if r.status_code in [403,429]:raise RuntimeError('Provider access hold '+str(r.status_code))
 print(json.dumps(dict(label=v['label'],available=available)),flush=True);time.sleep(.15)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',19);sheets=[]
for start in range(0,len(receipts),20):
 batch=receipts[start:start+20];canvas=Image.new('RGB',(1400,1280),'white');draw=ImageDraw.Draw(canvas)
 for j,v in enumerate(batch):
  x=(j%5)*280;y=(j//5)*320;draw.text((x+5,y+4),v['label']+' | '+v['source_id'].split('-')[-1],font=font,fill='black')
  if v['available']:
   im=Image.open(v['path']).convert('RGB');im.thumbnail((270,280));canvas.paste(im,(x+(280-im.width)//2,y+34+(280-im.height)//2))
 p=DEST/('contact-'+str(start//20+1)+'.jpg');canvas.save(p,quality=93);sheets.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),labels=[v['label']for v in batch]))
m.save(RUN/'visual-references-001.json',dict(at=m.now(),rows=receipts,sheets=sheets,script_reference=q.s.ref(Path(__file__).resolve()),policy='Sourcefilesuntouched; contactmontagesforinternalidentityQA. No publicimages orclaimof rightsapproval.'))
