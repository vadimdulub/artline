#!/usr/bin/env python3
"""Selected PDM-labelled Rijksmuseum reproductions from native OAI identities."""
import argparse,collections,concurrent.futures,importlib.util,io,json,re
from pathlib import Path
from PIL import Image,ImageOps
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
im=module('delivery','million-met-images-20261010.py');r=module('rijks','million-rijks-20261010.py');m=r.m
r.SID=m.uid('source/rijks');im.met=r;im.RUN=r.RUN/'images-001';im.ORIG=im.ORIG.parent/'rijks-001';im.PROVIDER='rijks';im.NAME='Rijksmuseum';im.RIGHTS='public_domain';im.LICENSE='Public Domain Mark 1.0';im.VIEW='Rijksmuseum reproduction'
im.POLICY='https://creativecommons.org/publicdomain/mark/1.0/'
im.IDENTITY='Exact native Rijksmuseum object ID and accession in captured OAI record; edm:isShownBy supplies the primary reproduction. Source XML response and individual record hashes retained. Artist, source date and physical object selection checked before images.'
im.RIGHTS_BASIS='The native Rijksmuseum OAI aggregation explicitly labels this image Public Domain Mark 1.0. Actual rights URI retained; no inference from artist death. Native primary image URI and complete source frame checked.'
def select():
 path=im.RUN/'selection.json.gz'
 if path.exists():return
 folders=[r.RUN/'00000-01000'] if im.RUN.name=='images-001' else [f.parent for f in sorted(r.RUN.glob('*/full-verification.json')) if f.parent.name!='00000-01000']
 candidates=[];pins={};seen=collections.Counter();rows=[];rank={'painting':0,'drawing':1,'watercolor':2,'sculpture':3,'print':4,'photograph':5}
 for folder in folders:
  p=m.load(folder/'plan.json.gz');pin=m.load(folder/'pin.json')['sha256'];assert m.sha((folder/'plan.json.gz').read_bytes())==pin;pins[folder.name]=pin
  ep=folder/'execution-exclusions.json';excluded={x['artwork_id'] for x in m.load(ep)['rows']} if ep.exists() else set()
  candidates.extend(dict(x,source_plan_sha256=pin) for x in p['new_artworks'] if x['artwork_id'] not in excluded and x['last']<=1955 and x['raw']['rights']==['http://creativecommons.org/publicdomain/mark/1.0/'] and len(x['raw']['source_images'])==1 and not re.search(r'\((?:V|VERSO)\)\s*$',x['accession_number'],re.I))
 candidates.sort(key=lambda x:(rank[x['work_type']],x['first'],x['native_id']))
 for row in candidates:
  if seen[row['creator_label']]>=2:continue
  if not re.fullmatch(r'https://iiif\.micr\.io/[A-Za-z0-9_-]+/full/max/0/default\.jpg',row['raw']['source_images'][0]):continue
  rows.append(row);seen[row['creator_label']]+=1
  if len(rows)==240:break
 m.save(path,dict(at=m.now(),plan_sha256=m.sha(json.dumps(pins,sort_keys=True).encode()),source_plan_pins=pins,rows=rows,selection_basis='240 selected pre-1956, individually PDM-labelled native museum objects from independently verified phases; paintings first and at most two per creator label. Explicit verso views held. No exhaustive image downloads.'))
 m.save(im.RUN/'policy-observation.json',dict(at=m.now(),source_url=im.POLICY,supporting_url='https://data.rijksmuseum.nl/docs/iiif/image',method='Official IIIF Image API documentation and Creative Commons PDM deed read through web tool; per-image designation independently preserved in native OAI response',facts='Rijksmuseum identifies iiif.micr.io as its production image service. Only images explicitly carrying the Public Domain Mark URI in their object aggregation are selected.'))
 print('Selected',len(rows),dict(collections.Counter(x['work_type'] for x in rows)),flush=True)
def prepare():
 select();im.ORIG.mkdir(parents=True,exist_ok=True)
 def one(row):
  aid=row['artwork_id'];dest=im.RUN/'prepared'/(aid+'.json')
  if dest.exists():return m.load(dest)['state']
  native=row['raw']['source_images'][0];url=native.replace('/full/max/','/full/!1600,1600/');out=dict(artwork_id=aid,title=row['title'],artist=row['creator_label'],source_url=row['source_url'],source_image_url=url,api=dict(row['raw'],creditLine='Native museum collection image; source designation: Public Domain Mark 1.0'),api_receipt=row['raw']['page_receipt'])
  try:
   assert row['raw']['rights']==['http://creativecommons.org/publicdomain/mark/1.0/'];assert row['last']<=1955
   hold=im.RUN/'access-hold.json';assert not hold.exists(),'Image service access held'
   original=im.ORIG/(aid+'.source');receipt=im.ORIG/(aid+'.receipt.json')
   if receipt.exists():download=m.load(receipt);raw=original.read_bytes();assert m.sha(raw)==download['sha256']
   else:
    im.d.core.provider_rate_slot('iiif.micr.io');response=im.cap.session().get(url,timeout=(15,60));download=dict(url=url,source_primary_image_uri=native,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=m.sha(response.content),bytes=len(response.content),content_type=response.headers.get('Content-Type'))
    if response.status_code in (401,403,429):m.save(hold,download)
    response.raise_for_status();raw=response.content;assert download['content_type'].startswith('image/') and len(raw)<15000000;original.write_bytes(raw);m.save(receipt,download)
   with Image.open(io.BytesIO(raw)) as opened:
    assert opened.width*opened.height<=3000000;opened.load();image=ImageOps.exif_transpose(opened).convert('RGB');output=None
    for edge in [1200,1000,850,700,600,500]:
     image.thumbnail((edge,edge),Image.Resampling.LANCZOS)
     for quality in [90,85,80,75,70,65,60]:
      buf=io.BytesIO();image.save(buf,'JPEG',quality=quality,optimize=True,progressive=True)
      if buf.tell()<=100000:output=buf.getvalue();break
     if output:break
    assert output and min(image.size)>=40
    digest=m.sha(output);sp='/assets/artworks/imported/'+m.OP+'/'+aid+'-'+digest[:16]+'.jpg';local=m.ROOT/'apps/web/public'/sp.lstrip('/');local.parent.mkdir(parents=True,exist_ok=True)
    if local.exists():assert local.read_bytes()==output
    else:local.write_bytes(output)
    out.update(state='prepared',path=str(local),storage_path=sp,sha256=digest,bytes=len(output),width=image.width,height=image.height,media_id=m.uid('media/rijks/'+aid+'/'+digest),download=download,original_path=str(original))
  except Exception as error:out.update(state='held',reason=type(error).__name__+': '+str(error)[:500])
  m.save(dest,out);return out['state']
 counts=collections.Counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for i,state in enumerate(pool.map(one,im.selection()['rows']),1):
   counts[state]+=1
   if i%40==0:print('Prepared',i,dict(counts),flush=True)
 print(dict(counts),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['select','prepare','sheets','deliver']);ap.add_argument('--phase',choices=['001','002'],default='001');a=ap.parse_args();im.RUN=r.RUN/('images-'+a.phase);im.ORIG=im.ORIG.parent/('rijks-'+a.phase)
 if a.action in ['select','prepare']:globals()[a.action]()
 else:getattr(im,a.action)()
