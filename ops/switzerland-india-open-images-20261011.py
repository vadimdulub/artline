#!/usr/bin/env python3
"""Retrieve only selected Rietberg ZIP members using public HTTP byte ranges."""
import argparse
import importlib.util
import io
import json
import struct
import zlib
import base64
import hashlib
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageDraw

s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('switzerland-india-delivery-20261011.py'))
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
RUN=d.RUN/'CH-wave3/images'
ORIG=Path.home()/'Library/Application Support/Artline/source-images'/d.OP
URL='https://data.stadt-zuerich.ch/dataset/mrz_drenowatz_sammlung/download/mrz_drenowatz_sammlung_bilder.zip'
POLICY='https://data.stadt-zuerich.ch/dataset/mrz_drenowatz_sammlung'

def ranged(start,end):
 assert not (RUN/'access-hold.json').exists()
 r=requests.get(URL,headers={'Range':f'bytes={start}-{end}'},stream=True,timeout=(15,50))
 if r.status_code in [401,403,429]:d.save(RUN/'access-hold.json',dict(at=d.now(),url=URL,status=r.status_code))
 try:
  assert r.status_code==206,('Range support required; full archive never downloaded',r.status_code)
  assert r.headers['Content-Range']==f'bytes {start}-{end}/230074577'
  raw=r.raw.read(end-start+2);assert len(raw)==end-start+1
  return raw
 finally:r.close()

def prepare():
 RUN.mkdir(parents=True,exist_ok=True);ORIG.mkdir(parents=True,exist_ok=True)
 directory=d.load(d.RUN/'CH/rietberg-zip-directory.json')
 rows=[r for r in d.load(d.RUN/'CH-wave3/source-records.json.gz') if r.get('image_candidate')]
 selected=[]
 for row in rows:
  name='Bilder Kunstwerke/'+row['image_candidate']+('.JPG' if row['image_candidate']=='RCH 1023' else '.jpg')
  entry=next(x for x in directory if x['name']==name)
  selected.append(dict(key=row['provider']+'/'+row['source_id'],accession=row['accession_number'],title=row['title'],creator=row['creator_label'],entry=entry))
 d.save(RUN/'selected-members.json',selected)
 prepared=[]
 for row in selected:
  e=row['entry'];tag=row['accession'].replace(' ','-');original=ORIG/(tag+'.source');rp=ORIG/(tag+'.receipt.json')
  if original.exists():raw=original.read_bytes();receipt=d.load(rp);assert d.sha(raw)==receipt['sha256']
  else:
   head=ranged(e['header_offset'],e['header_offset']+29);parts=struct.unpack('<4s5H3L2H',head)
   assert parts[0]==b'PK\x03\x04' and parts[3]==e['compression']==8
   n,extra=parts[-2:];body_start=e['header_offset']+30
   body=ranged(body_start,body_start+n+extra+e['compressed_size']-1)
   assert body[:n].decode('utf-8')==e['name']
   raw=zlib.decompress(body[n+extra:],-15);assert len(raw)==e['size'] and zlib.crc32(raw)==e['crc']
   receipt=dict(retrieved_at=d.now(),source_url=URL,zip_member=e,sha256=d.sha(raw),bytes=len(raw),transport='Exact local-header and compressed member HTTP ranges; archive not downloaded')
   original.write_bytes(raw);d.save(rp,receipt)
  im=ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB');original_size=im.size
  im.thumbnail((1800,1800));quality=90
  while True:
   buf=io.BytesIO();im.save(buf,'JPEG',quality=quality,optimize=True)
   if buf.tell()<=100000:break
   if quality>54:quality-=6
   else:im.thumbnail((round(im.width*.85),round(im.height*.85)));quality=84
  output=buf.getvalue();path=RUN/(tag+'.jpg');path.write_bytes(output)
  prepared.append(dict(**row,path=str(path),original_path=str(original),receipt=receipt,sha256=d.sha(output),bytes=len(output),width=im.width,height=im.height,original_size=original_size,rights_status='public_domain',license_label='Museum Rietberg open data: image files public domain',license_url=POLICY,creator_credit='Foto: Rainer Wolfensberger / Museum Rietberg'))
 d.save(RUN/'prepared.json',prepared)
 sheet=Image.new('RGB',(1200,1000),'#eee');draw=ImageDraw.Draw(sheet)
 for j,r in enumerate(prepared):
  im=Image.open(r['path']);im.thumbnail((380,900));sheet.paste(im,(j*400+(400-im.width)//2,40+(900-im.height)//2));draw.text((j*400+10,10),r['accession'],fill='black')
 target=Path('/private/tmp/artline-swiss-rietberg-contact.jpg');sheet.save(target)
 print(json.dumps(dict(prepared=len(prepared),sheet=str(target),members=[r['accession'] for r in prepared])),flush=True)

def deliver():
 from google.cloud import storage
 from google.api_core.exceptions import PreconditionFailed
 spec=importlib.util.spec_from_file_location('core',Path(__file__).with_name('enrich-artwork-images.py'))
 core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
 plan,pin=d.pinned('CH-wave3');assert d.load(d.RUN/'CH-wave3/applied.json')['plan_sha256']==pin
 assert d.load(d.RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'
 reviews=d.load(RUN/'visual-review.json');facts={r['key']:r for r in plan['records']}
 rows=[r for r in d.load(RUN/'prepared.json') if reviews[r['key']]['decision']=='accept']
 assert len(rows)==1 and rows[0]['accession']=='RCH 1021'
 assert not (RUN/'applied.json').exists()
 policy=d.load(d.RUN/'CH/native-discovery/rietberg-open.json')
 assert 'Die Bilder stehen in der Public Domain' in policy['text']
 bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
 for im in rows:
  r=facts[im['key']];raw=Path(im['path']).read_bytes();assert len(raw)<=100000 and d.sha(raw)==im['sha256']==reviews[im['key']]['sha256']
  im['storage_path']='/assets/artworks/imported/'+d.OP+'/'+r['artwork_id']+'-'+im['sha256'][:16]+'.jpg'
  im['media_id']=d.uid('media/'+im['key']+'/'+im['sha256'])
  local=d.ROOT/'apps/web/public'/im['storage_path'].lstrip('/');local.parent.mkdir(parents=True,exist_ok=True)
  if local.exists():assert local.read_bytes()==raw
  else:local.write_bytes(raw)
  blob=bucket.blob(im['storage_path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'operation':d.OP};blob.cache_control='public,max-age=31536000,immutable'
  try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0)
  except PreconditionFailed:pass
  blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
  response=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,60));response.raise_for_status();assert d.sha(response.content)==im['sha256']
  d.save(RUN/'upload.json',dict(at=d.now(),storage_path=im['storage_path'],sha256=im['sha256'],generation=blob.generation,public_verified=True))
 ids=[facts[im['key']]['artwork_id'] for im in rows]
 with d.connect(True) as db,db.transaction():
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(d.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
  before=d.snapshot(db,ids);d.save(d.BACKUP/'CH-wave3/images-before.json.gz',before)
  for im in rows:
   r=facts[im['key']];a=before[r['artwork_id']]['artwork'];assert a['primary_media_id'] is None and a['status']=='review' and a['accession_number']==im['accession'] and a['creation_year_end']==1574
   sid=d.uid('source/'+r['provider']+'/'+r['museum']);credit=im['creator_credit']+'. '+im['accession']+'; '+r['creator_label']+'; '+r['title']+'; '+r['date_display']+'.'
   d.batch_insert(db,'media_assets',[dict(id=im['media_id'],storage_kind='local',storage_path=im['storage_path'],source_page_url=POLICY,provider_name='Museum Rietberg / Open Data Zürich',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=r['title']+' — '+r['creator_label'],rights_status=im['rights_status'],license_label=im['license_label'],license_url=POLICY,creator_credit=credit,attribution_text=credit+' Complete source image proportionally resized and JPEG compressed; no cropping.',retrieved_at=im['receipt']['retrieved_at'],verified_at=d.now(),verified_by=d.ACTOR)])
   evidence=dict(plan_sha256=pin,native_fields=r['native_fields'],metadata_receipt=r['evidence'],policy_receipt=policy['evidence'],image_policy_excerpt='Die Bilder stehen in der Public Domain, sind also gemeinfrei nutzbar.',download=im['receipt'],visual_review=reviews[im['key']],identity_basis='Exact RCH 1021 archive member and inventory-linked metadata; creator, subject and full image dimensions corroborate identity.',metadata_license_note='Dataset metadata CC BY-SA; the publisher separately declares the image files public domain.')
   d.batch_insert(db,'media_rights_evidence',[dict(media_id=im['media_id'],source_id=sid,source_record_id=r['source_id'],source_checksum=r['evidence']['sha256'],source_image_url=URL+'#'+im['entry']['name'],policy_url=POLICY,rights_basis='Museum-owned open dataset explicitly releases its image files into the public domain; source credit retained.',adapter_version=d.OP,checked_at=d.now(),evidence_json=json.dumps(evidence,ensure_ascii=False))])
   order=db.execute('SELECT coalesce(max(sort_order),-1)+1 n FROM artwork_media WHERE artwork_id=%s',(r['artwork_id'],)).fetchone()['n']
   d.batch_insert(db,'artwork_media',[dict(artwork_id=r['artwork_id'],media_id=im['media_id'],sort_order=order,view_label=reviews[im['key']]['view_label'])])
   db.execute('UPDATE artworks SET primary_media_id=%s,updated_by=%s,updated_at=now(),revision=revision+1 WHERE id=%s',(im['media_id'],d.ACTOR,r['artwork_id']))
  after=d.snapshot(db,ids)
  for aid,state in before.items():
   assert all(after[aid]['artwork'][k]==v for k,v in state['artwork'].items() if k not in ['primary_media_id','updated_by','updated_at','revision'])
   assert after[aid]['holdings']==state['holdings'] and after[aid]['creators']==state['creators']
 d.save(RUN/'applied.json',dict(at=d.now(),images=len(rows),artwork_ids=ids,media_ids=[r['media_id'] for r in rows],public_bytes_verified=True,metadata_changes=0,publication_changes=0,local_database_changes=0))
 print('Attached and publicly verified',len(rows),'image(s)',flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','deliver']);args=parser.parse_args();globals()[args.action]()
