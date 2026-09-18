#!/usr/bin/env python3
"""Acquire only 26 selected, explicitly CC0 primary museum reproductions."""
import importlib.util,json,requests,io
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('apply-greek-primary-images.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;CORE=a.CORE;RUN=m.x.BASE/'finland/primary-followup/images';ORIGINALS=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/overnight-countries-20260913/fng-primary')
def prepare():
 selected=json.loads((RUN/'selected.json').read_text())['selected'];assert len(selected)<=30;images=[]
 for e in selected:
  q=e['qid'];dest=RUN/'prepared'/(q+'.json')
  if dest.exists():images.append(json.loads(dest.read_text()));continue
  url=e['source_image_url'];assert url.startswith('https://kokoelma.kansallisgalleria.fi/media-assets/') and e['image']['license']=='CC0'
  source=ORIGINALS/(q+'.museum-thumbnail.jpg');rp=RUN/'downloads'/(q+'.json')
  if source.exists():raw=source.read_bytes();receipt=json.loads(rp.read_text());assert CORE.sha(raw)==receipt['sha256']
  else:
   resp=requests.get(url,timeout=(15,45));resp.raise_for_status();raw=resp.content;assert len(raw)<10_000_000 and raw.startswith(b'\xff\xd8\xff')
   with Image.open(io.BytesIO(raw)) as decoded:assert decoded.format=='JPEG';decoded.verify()
   receipt=dict(url=url,retrieved_at=CORE.now(),sha256=CORE.sha(raw),bytes=len(raw),kind='Museum-provided 1000px rendition',status=resp.status_code,content_type=resp.headers.get('Content-Type'),verified_format='JPEG');CORE.save_new(source,raw);CORE.save_new(rp,receipt)
  enc,w,h,quality=CORE.compress(raw);sha=CORE.sha(enc);path='/assets/artworks/imported/fng-primary/'+q.lower()+'-'+sha[:16]+'.jpg';CORE.save_new(m.x.ROOT/'apps/web/public'/path.lstrip('/'),enc)
  obj=e['evidence']['primary_object'];person=next(p for p in obj['people'] if p.get('role',{}).get('en')=='Artist');artist=person.get('firstName','')+' '+person.get('familyName','');title=e['evidence']['candidate_title'];credit=artist+'; Finnish National Gallery'+('; photograph: '+e['image']['photographer_name'] if e['image'].get('photographer_name') else '');license='https://creativecommons.org/publicdomain/zero/1.0/'
  im=dict(key=q,media_id=m.m.uid('fng-primary-image/'+q+'/'+sha),path=path,sha256=sha,bytes=len(enc),width=w,height=h,quality=quality,title=title,artist=artist,page=e['evidence']['object_url'],provider_name='Finnish National Gallery',source_slug='overnight-finnish-primary-selected-images-20260913',source_name='Finnish National Gallery selected CC0 reproductions',source_root='https://kokoelma.kansallisgalleria.fi/',source_image_url=url,rights_status='cc0',license_label='CC0',license_url=license,creator_credit=credit,attribution_text=f'{title}. {credit}. CC0 ({license}). Full-frame resize and JPEG compression.',download=receipt,checked_at=CORE.now(),identity=dict(choice=dict(page=dict(title=str(obj['objectId'])),receipt=e['evidence']['primary_receipt']),identity_basis='Exact current primary museum object ID, inventory, title and maker crosswalk; unique preferred museum image explicitly licensed CC0 in primary API. Collection connection and creation date established separately. No current display inference.',primary=e))
  CORE.save_new(dest,im);images.append(im);print('FNG selected image prepared',q,flush=True)
 canvas=Image.new('RGB',(1250,((len(images)+4)//5)*220),'#f0eee9');draw=ImageDraw.Draw(canvas)
 for i,im in enumerate(images):
  photo=Image.open(m.x.ROOT/'apps/web/public'/im['path'].lstrip('/'));tile=ImageOps.contain(photo.convert('RGB'),(240,170));x=i%5*250;y=i//5*220;canvas.paste(tile,(x+(250-tile.width)//2,y));draw.text((x+5,y+176),im['key']+' '+im['artist'][:20],fill='black');draw.text((x+5,y+195),im['title'][:35],fill='black')
 path=RUN/'contact-sheet.jpg';canvas.save(path,quality=90);CORE.save_new(RUN/'preparation.json',dict(at=CORE.now(),images=len(images),contact_sheet_sha256=CORE.sha(path.read_bytes()),prepared_hashes={p.name:CORE.sha(p.read_bytes()) for p in (RUN/'prepared').glob('*.json')}));print('FNG 26-image contact sheet ready for actual review',flush=True)
if __name__=='__main__':prepare()
