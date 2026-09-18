#!/usr/bin/env python3
"""Prepare only QA-selected, explicitly CC0 Met images; application is separate."""
import argparse,importlib.util,json,io,time
from pathlib import Path
from urllib.parse import urlparse
import requests
from PIL import Image,ImageOps,ImageDraw
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
x=m.x;CORE=m.m.core
def prepare(code,n):
 delivery=x.BASE/code/f'round-{n:02}/delivery';run=delivery/'primary-images-met-reviewed'
 if (run/'preparation.json').exists():return
 qa=json.loads((delivery/'quality-review.json').read_text());assert qa['approved'];selected=[];byqid={}
 for family in ('met-primary','met-primary-v2'):
  for f in (delivery/family).glob('Q*.json'):byqid[f.stem]=(f,json.loads(f.read_text()))
 for q,(f,e) in sorted(byqid.items()):
  r=json.loads((delivery/f'ready/{q}.json').read_text());o=e.get('object') or {}
  if q in qa.get('held_records',{}) or q in qa.get('held_images',{}) or r.get('image'):continue
  if e['review']!='primary_object_and_creator_corroborated' or not o.get('is_public_domain') or not o.get('primary_image'):continue
  rec=r['record'];rec.update({k:v for k,v in qa.get('metadata_overrides',{}).get(q,{}).items() if k in ('date','title','work_type')})
  if not rec['date']['eligible']:continue
  assert rec['date']['last']<=1970 and o['accession'] and m.m.accession_key(o['accession'])==m.m.accession_key(rec['accession'])
  url=o['primary_image'];assert urlparse(url).scheme=='https' and urlparse(url).hostname=='images.metmuseum.org'
  selected.append(dict(qid=q,evidence_file=str(f),evidence_sha256=CORE.sha(f.read_bytes()),record=rec,primary=e))
 assert len(selected)<=80;sp=run/'selected.json'
 if sp.exists():assert json.loads(sp.read_text())['selected']==selected
 else:CORE.save_new(sp,dict(at=CORE.now(),selected=selected,policy='Already selected catalogue artwork with exact primary object ID/accession/maker, manual round QA, source-supported pre1971date, Met isPublicDomain true and exact primary image. No exhaustive museum/image download.'))
 images=[];failures=[]
 for e in selected:
  q=e['qid'];dest=run/f'prepared/{q}.json'
  if dest.exists():images.append(json.loads(dest.read_text()));continue
  rec=e['record'];p=e['primary'];o=p['object'];url=o['primary_image'];original=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images')/x.SESSION_NAME/x.CAMPAIGN/code/f'round-{n:02}/met-primary/{q}.jpg';rp=run/f'downloads/{q}.json'
  try:
   if original.exists():raw=original.read_bytes();rc=json.loads(rp.read_text());assert CORE.sha(raw)==rc['sha256']
   else:
    time.sleep(1);res=requests.get(url,timeout=(15,60));res.raise_for_status();raw=res.content;assert len(raw)<15_000_000
    with Image.open(io.BytesIO(raw)) as im:assert im.format in ('JPEG','PNG');im.verify()
    rc=dict(url=res.url,retrieved_at=CORE.now(),bytes=len(raw),sha256=CORE.sha(raw),status=res.status_code,content_type=res.headers.get('Content-Type'));CORE.save_new(original,raw);CORE.save_new(rp,rc)
   encoded,w,h,quality=CORE.compress(raw);sha=CORE.sha(encoded);path='/assets/artworks/imported/'+x.SESSION_NAME+'/met-primary/'+q.lower()+'-'+sha[:16]+'.jpg';CORE.save_new(x.ROOT/'apps/web/public'/path.lstrip('/'),encoded)
   lic='https://creativecommons.org/publicdomain/zero/1.0/';credit=rec['creator_label']+'; The Metropolitan Museum of Art';page=p['data'].get('objectURL') or p['receipt']['url']
   im=dict(key=q,media_id=m.m.uid(x.SESSION_NAME+'/primary-image/'+q+'/'+sha),path=path,sha256=sha,bytes=len(encoded),width=w,height=h,quality=quality,title=rec['title'],artist=rec['creator_label'],page=page,provider_name='The Metropolitan Museum of Art',source_slug=x.SESSION_NAME+'-met-selected-images',source_name='The Metropolitan Museum of Art — selected Open Access reproductions',source_root='https://www.metmuseum.org/',source_image_url=url,rights_status='cc0',license_label='CC0',license_url=lic,creator_credit=credit,attribution_text=rec['title']+'. '+credit+'. CC0 ('+lic+'). Full-frame resize and JPEG compression.',download=rc,checked_at=CORE.now(),adapter_version='met-selected-reviewed-v1',identity=dict(choice=dict(page=dict(title=o['accession']),receipt=p['receipt']),identity_basis='Exact selected Met object maker/accession, isPublicDomain=true and primaryImage from API; Open Access CC0policy. No present-day display claim.',primary=p,policy_url='https://www.metmuseum.org/about-the-met/policies-and-documents/open-access'))
   CORE.save_new(dest,im);images.append(im);print(code,n,q,'Met image prepared',flush=True)
  except Exception as err:failures.append(dict(qid=q,reason=type(err).__name__+': '+str(err)[:250]));print(code,n,q,'image unavailable',flush=True)
 canvas=Image.new('RGB',(1250,max(1,(len(images)+4)//5)*220),'#f0eee9');draw=ImageDraw.Draw(canvas)
 for i,im in enumerate(images):
  with Image.open(x.ROOT/'apps/web/public'/im['path'].lstrip('/')) as photo:
   tile=ImageOps.contain(photo.convert('RGB'),(240,170));left=i%5*250;top=i//5*220;canvas.paste(tile,(left+(250-tile.width)//2,top));draw.text((left+5,top+176),im['key']+' '+im['artist'][:21],fill='black');draw.text((left+5,top+195),im['title'][:35],fill='black')
 sheet=run/'contact-sheet.jpg';sheet.parent.mkdir(parents=True,exist_ok=True);canvas.save(sheet,quality=90);CORE.save_new(run/'preparation.json',dict(at=CORE.now(),images=len(images),failures=failures,contact_sheet_sha256=CORE.sha(sheet.read_bytes()),prepared_hashes={p.name:CORE.sha(p.read_bytes()) for p in (run/'prepared').glob('*.json')}));print(code,n,'selected Met images for actual review',len(images),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--country',required=True);p.add_argument('--round',required=True,type=int);a=p.parse_args();prepare(a.country,a.round)
