#!/usr/bin/env python3
"""Selected open museum reproductions: prepare, visually review, deliver, attach."""
import argparse,base64,collections,concurrent.futures,datetime,hashlib,importlib.util,io,json,subprocess,threading,time
from pathlib import Path
from urllib.parse import urlsplit
import requests
from PIL import Image,ImageOps,ImageDraw,ImageStat
from google.cloud import storage
from google.oauth2.credentials import Credentials
from google.api_core.exceptions import PreconditionFailed
from psycopg.types.json import Jsonb
spec=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-random-country-collections-20261009.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ARCHIVE=Path.home()/'Library/Application Support/Artline/source-images'/m.OP
HOSTLOCKS=collections.defaultdict(threading.Lock);LAST={};BLOCKED=set()
def select(phase):
 p,digest=m.pinned(phase);rows=[];held=[]
 enrichment_file=m.RUN/phase/'image-enrichment.json.gz';enrichment=m.load(enrichment_file) if enrichment_file.exists() else {}
 access_file=m.RUN/'source-access-holds.json';access=m.load(access_file) if access_file.exists() else {}
 with m.connect() as db:states=m.snapshot(db,[r['artwork_id'] for r in p['records']])
 for r in p['records']:
  r=dict(r,**enrichment.get(r['key'],{}))
  if not(r.get('image_url') and r.get('image_license_url')):continue
  if urlsplit(r['image_url']).netloc in access:
   held.append(dict(key=r['key'],reason=access[urlsplit(r['image_url']).netloc]));continue
  if not r['date_decision'].startswith('within_cutoff'):continue
  if r.get('year_end') is None or r['year_end']>1955:
   held.append(dict(key=r['key'],reason='Existing museum image workflow cutoff: creation by 1955; catalogue metadata retained through 1970.'));continue
  if r.get('decision')!='research_candidate':continue
  if states[r['artwork_id']]['artwork']['primary_media_id']:continue
  if r['provider']=='mia':
   raw=r['raw'];loc=(raw.get('Cache_Location') or '').replace('\\','/')
   if loc.split('/')[-1]!=r['source_id'] or raw.get('image')!='valid' or raw.get('Rights_Image_Display')!='Full':continue
  rows.append(dict(record=r,before=states[r['artwork_id']],identity_confidence=r.get('image_identity_confidence',.99),identity_basis=r.get('image_identity_basis') or 'Exact native museum object, inventory and reproduction URL from the same captured museum record. Source date/attribution preserved.'))
 m.save(m.RUN/phase/'image-selection.json.gz',dict(at=m.now(),catalogue_plan_sha256=digest,records=rows,source_access_holds=held));print('Selected images',phase,len(rows),'access-held',len(held),flush=True)
def prepare(phase):
 selected=m.load(m.RUN/phase/'image-selection.json.gz')['records'];folder=m.RUN/phase/'images';folder.mkdir(parents=True,exist_ok=True)
 def one(row):
  r=row['record'];aid=r['artwork_id'];receipt=folder/(aid+'.json')
  if receipt.exists():return m.load(receipt)
  url=r['image_url'];host=urlsplit(url).netloc
  try:
   archive=ARCHIVE/phase/(aid+'.source');archive.parent.mkdir(parents=True,exist_ok=True)
   if archive.exists():raw=archive.read_bytes();download=m.load(archive.with_suffix('.json'))
   else:
    with HOSTLOCKS[host]:
     if host in BLOCKED:raise ValueError('Provider paused after access restriction')
     time.sleep(max(0,LAST.get(host,0)+.22-time.monotonic()));LAST[host]=time.monotonic()
     response=requests.get(url,timeout=(12,45),headers={'User-Agent':'Artline selected museum image delivery'},stream=True)
     if response.status_code in [401,403,429]:BLOCKED.add(host)
     response.raise_for_status();raw=b''
     for chunk in response.iter_content(65536):raw+=chunk;assert len(raw)<30_000_000
    download=dict(at=m.now(),source_url=url,final_url=response.url,status=response.status_code,sha256=m.sha(raw),bytes=len(raw));archive.write_bytes(raw);m.save(archive.with_suffix('.json'),download)
   with Image.open(io.BytesIO(raw)) as im:im.load();picture=ImageOps.exif_transpose(im).convert('RGB')
   assert picture.width>=80 and picture.height>=80 and max(ImageStat.Stat(picture).stddev)>3,'Blank or unusable image'
   original_size=picture.size;picture.thumbnail((1500,1500),Image.Resampling.LANCZOS)
   for size in [1500,1300,1100,900,750,600]:
    picture.thumbnail((size,size),Image.Resampling.LANCZOS)
    for quality in [88,80,72,64,55,45]:
     buf=io.BytesIO();picture.save(buf,'JPEG',quality=quality,optimize=True);result=buf.getvalue()
     if len(result)<=100000:break
    if len(result)<=100000:break
   assert len(result)<=100000
   digest=m.sha(result);path='/assets/artworks/imported/random-country-collections-20261009/'+phase+'/'+aid+'-'+digest[:12]+'.jpg'
   dest=m.ROOT/'apps/web/public'/path.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists():assert dest.read_bytes()==result
   else:dest.write_bytes(result)
   out=dict(artwork_id=aid,source_record_key=r['key'],source_url=url,source_archive=str(archive),source_sha256=download['sha256'],source_size=list(original_size),path=path,sha256=digest,bytes=len(result),width=picture.width,height=picture.height,retrieved_at=download['at'],media_id=m.uid('media/'+phase+'/'+aid+'/'+digest),license_url=r['image_license_url'],license_label=r['image_rights_label'],prepared=True)
   m.save(receipt,out);return out
  except Exception as e:
   return dict(artwork_id=aid,source_record_key=r['key'],prepared=False,error=str(e)[:300])
 outcomes=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for n,out in enumerate(pool.map(one,selected),1):
   outcomes.append(out)
   if n%50==0:print('Prepared',phase,n,'/',len(selected),flush=True)
 m.save(m.RUN/phase/'image-preparation.json.gz',dict(at=m.now(),records=outcomes));print('Prepared',sum(x['prepared'] for x in outcomes),'errors',sum(not x['prepared'] for x in outcomes),flush=True)
def sheets(phase):
 rows=[x for x in m.load(m.RUN/phase/'image-preparation.json.gz')['records'] if x['prepared']];sources={x['record']['artwork_id']:x['record'] for x in m.load(m.RUN/phase/'image-selection.json.gz')['records']}
 folder=m.RUN/phase/'contact-sheets';folder.mkdir(parents=True,exist_ok=True);index=[]
 for offset in range(0,len(rows),48):
  selected=rows[offset:offset+48];sheet=Image.new('RGB',(1440,1440),'#ededed');draw=ImageDraw.Draw(sheet)
  for n,r in enumerate(selected):
   x=(n%6)*240;y=(n//6)*180
   with Image.open(m.ROOT/'apps/web/public'/r['path'].lstrip('/')) as im:
    im.thumbnail((230,143));sheet.paste(im,(x+(240-im.width)//2,y+(143-im.height)//2))
   text=str(offset+n+1)+' '+sources[r['artwork_id']]['provider']+' '+sources[r['artwork_id']]['source_id']
   draw.text((x+4,y+145),text,fill='black');draw.text((x+4,y+160),sources[r['artwork_id']]['title'].encode('ascii','replace').decode()[:34],fill='black')
  dest=folder/(f'{offset//48+1:03d}.jpg');sheet.save(dest,'JPEG',quality=90)
  index.append(dict(sheet=str(dest.relative_to(m.ROOT)),sha256=m.sha(dest.read_bytes()),artwork_ids=[r['artwork_id'] for r in selected]))
 m.save(folder/'index.json',index);print('Contact sheets',len(index),flush=True)
def upload(phase):
 reviews=m.load(m.RUN/phase/'visual-review.json');accepted=set(reviews['accepted']);rejected=set(reviews['rejected']);assert not(accepted&rejected)
 rows=[x for x in m.load(m.RUN/phase/'image-preparation.json.gz')['records'] if x['prepared'] and x['artwork_id'] in accepted]
 assert len(rows)==len(accepted)
 token=subprocess.check_output(['gcloud','auth','print-access-token','--account=vadim@alingva.com'],text=True).strip()
 bucket=storage.Client(project='artline-508319',credentials=Credentials(token)).bucket('artline-508319-images')
 def one(r):
  receipt=m.RUN/phase/'uploads'/(r['artwork_id']+'.json')
  if receipt.exists():return m.load(receipt)
  raw=(m.ROOT/'apps/web/public'/r['path'].lstrip('/')).read_bytes();assert len(raw)==r['bytes']<=100000 and m.sha(raw)==r['sha256']
  blob=bucket.blob(r['path'].lstrip('/'));blob.metadata=dict(sha256=r['sha256'],operation=m.OP,artwork_id=r['artwork_id']);blob.cache_control='public,max-age=31536000,immutable'
  try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
  except PreconditionFailed:blob.reload(timeout=30)
  assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
  response=requests.get('https://artlines.org'+r['path'],timeout=(15,45));response.raise_for_status();assert m.sha(response.content)==r['sha256']
  out=dict(at=m.now(),artwork_id=r['artwork_id'],generation=str(blob.generation),path=r['path'],sha256=r['sha256'],public_bytes_verified=True);m.save(receipt,out);return out
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for n,_ in enumerate(pool.map(one,rows),1):
   if n%50==0:print('Uploaded and verified',phase,n,'/',len(rows),flush=True)
 print('Files delivered',phase,len(rows),flush=True)
def attach(phase):
 assert not(m.RUN/phase/'images-applied.json').exists()
 selection=m.load(m.RUN/phase/'image-selection.json.gz');byid={r['record']['artwork_id']:r for r in selection['records']};review=m.load(m.RUN/phase/'visual-review.json');ids=review['accepted']
 with m.connect(True) as db,db.transaction():
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall();before=m.snapshot(db,ids)
  assert before=={aid:byid[aid]['before'] for aid in ids},'Concurrent catalogue drift before image attachment'
  m.save(m.BACKUP/phase/'images-before.json.gz',dict(at=m.now(),artworks=before))
  media=[];evidence=[];attachments=[];updates=[]
  for aid in ids:
   row=byid[aid];r=row['record'];im=m.load(m.RUN/phase/'images'/(aid+'.json'));upload=m.load(m.RUN/phase/'uploads'/(aid+'.json'));assert upload['public_bytes_verified'] and upload['sha256']==im['sha256']
   sid=m.uid('source/'+r['provider']+'/'+r['museum']);license=im['license_url'];rights=r.get('image_rights_status') or ('cc0' if '/zero/' in license else 'cc_by' if '/by/' in license else 'public_domain')
   if r.get('image_source_provider'):
    sid=m.uid('source/images/'+r['image_source_provider'])
    if not db.execute('SELECT id FROM sources WHERE id=%s',(sid,)).fetchone():m.batch_insert(db,'sources',[dict(id=sid,slug=m.OP+'-images-'+r['image_source_provider'].lower(),name=r['image_source_provider'],source_type='collection_page',base_url=r['image_source_page_url'],adapter_key=m.OP)])
   credit='; '.join(str(x) for x in [r.get('creator_label'),r['museum'],r.get('credit')] if x)
   attribution=credit+'. '+str(im['license_label'])+' ('+license+'). Full-frame proportional resize and JPEG compression of the source reproduction.'
   media.append(dict(id=im['media_id'],storage_kind='local',storage_path=im['path'],source_page_url=r.get('image_source_page_url') or r['source_url'],provider_name=r.get('image_source_provider') or r['museum'],mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=r['title'],rights_status=rights,license_label=im['license_label'],license_url=license,creator_credit=credit,attribution_text=attribution,retrieved_at=im['retrieved_at'],verified_at=m.now(),verified_by=m.ACTOR))
   evidence.append(dict(media_id=im['media_id'],source_id=sid,source_record_id=r.get('image_source_record_id') or r['source_id'],source_checksum=(r.get('image_evidence') or r['evidence'])['sha256'],source_image_url=r['image_url'],policy_url=license,rights_basis=r.get('image_rights_basis') or 'Exact museum object open-image designation, supported by captured source metadata; original rights wording retained.',adapter_version=m.OP,checked_at=m.now(),evidence_json=Jsonb(dict(record=r,prepared=im,identity_confidence=row['identity_confidence'],identity_basis=row['identity_basis'],visual_review=review['method'],source_archive=im['source_archive'],original_sha256=im['source_sha256']))))
   attachments.append(dict(artwork_id=aid,media_id=im['media_id'],sort_order=1,view_label=review.get('view_labels',{}).get(aid) or (r.get('image_source_provider') or 'Museum')+' reproduction (full source frame)'));updates.append((im['media_id'],m.ACTOR,aid))
  m.batch_insert(db,'media_assets',media);m.batch_insert(db,'media_rights_evidence',evidence);m.batch_insert(db,'artwork_media',attachments)
  with db.cursor() as cur:cur.executemany('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_by=%s,updated_at=now() WHERE id=%s AND primary_media_id IS NULL',updates)
  after=m.snapshot(db,ids)
  for aid in ids:
   x=after[aid];old=before[aid];allowed={'primary_media_id','revision','updated_by','updated_at'}
   assert {k:v for k,v in x['artwork'].items() if k not in allowed}=={k:v for k,v in old['artwork'].items() if k not in allowed}
   assert x['holdings']==old['holdings'] and x['creators']==old['creators']
   assert x['artwork']['primary_media_id']==m.load(m.RUN/phase/'images'/(aid+'.json'))['media_id']
  m.save(m.BACKUP/phase/'images-after.json.gz',dict(at=m.now(),artworks=after))
 m.save(m.RUN/phase/'images-applied.json',dict(at=m.now(),target='production',images_attached=len(ids),artwork_ids=ids,metadata_and_publication_preserved=True,public_file_checksums_verified=True,local_database_changes=0));print('Images attached',phase,len(ids),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['select','prepare','sheets','upload','attach']);p.add_argument('phase',choices=['CH','US','CA']);a=p.parse_args();globals()[a.action](a.phase)
