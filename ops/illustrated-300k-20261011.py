#!/usr/bin/env python3
"""Resumable selected native museum images toward 300,000 illustrated objects.

Exact source identities, full-frame derivatives, explicit sampled visual review,
create-only uploads, bounded transactions, independent verification. Local DB RO.
"""
import argparse,base64,collections,concurrent.futures,fcntl,hashlib,importlib.util,io,itertools,json,os,re,shutil,subprocess,threading,time,uuid
from pathlib import Path
from urllib.parse import urlsplit
import psycopg,requests
from PIL import Image,ImageOps,ImageStat,ImageDraw,ImageFont
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
m=module('million','million-catalogue-20261010.py');d=module('delivery','cesi-delivery-20261010.py');n=module('nga','million-nga-20261010.py')
OP='illustrated-300k-20261011';RUN=m.ROOT/'docs/research'/OP;DATA=Path.home()/'Library/Application Support/Artline/source-metadata'/OP;ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
TARGET=300000;SIZE=2000;IGNORE={'primary_media_id','updated_at','updated_by','revision'}
CFG={'rijks':dict(mid='b6a5755d-157e-4ebe-a5a9-3bc52964ebf5',scheme='european-rijks-rijksmuseum-object',name='Rijksmuseum',rights='public_domain',license='Public Domain Mark 1.0',policy='https://creativecommons.org/publicdomain/mark/1.0/',host='iiif.micr.io',limit=125000),'nga':dict(mid=n.MID,scheme=n.SCHEME,name='National Gallery of Art',rights='cc0',license='NGA Open Access — CC0',policy='https://www.nga.gov/terms-and-notices',host='api.nga.gov',limit=25000)}
_tls=threading.local();_hold_lock=threading.Lock()
CFG['wikiart']=dict(mid=None,scheme='wikiart-legacy-content-id',name='WikiArt',rights=None,license=None,policy='https://www.wikiart.org/en/terms-of-use',host=None,limit=5000)
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+key))
def session():
 if not hasattr(_tls,'session'):
  _tls.session=requests.Session();_tls.session.headers.update({'User-Agent':'Artline selected collection image enrichment (+https://artlines.org)'})
 return _tls.session
def saved(path,value):m.save(path,value);return value
def folder(batch):return RUN/'batches'/batch
def selected(batch):return m.load(folder(batch)/'selection.json.gz')
def coverage(db):
 return db.execute("""SELECT count(*) FILTER(WHERE a.status<>'archived') active,
 count(*) FILTER(WHERE a.status<>'archived' AND a.primary_media_id IS NOT NULL) illustrated,
 count(*) FILTER(WHERE a.status<>'archived' AND ma.id IS NOT NULL AND ma.mime_type LIKE 'image/%%' AND nullif(ma.storage_path,'') IS NOT NULL
 AND NOT coalesce(a.creation_year_end>1970 OR a.creation_year_start>1970,false)
 AND NOT coalesce(a.current_institution_id=%s AND a.accession_number ~* '\\((V|VERSO)\\)[[:space:]]*$',false)) qualifying_illustrated
 FROM artworks a LEFT JOIN media_assets ma ON ma.id=a.primary_media_id""",(CFG['rijks']['mid'],)).fetchone()
def baseline():
 dest=RUN/'baseline.json.gz'
 if dest.exists():return m.load(dest)
 with m.m.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');counts=coverage(db)
  source_counts=db.execute("SELECT i.slug,count(*) FILTER(WHERE a.primary_media_id IS NULL AND a.creation_year_end<=1955) image_gaps,count(*) FILTER(WHERE a.primary_media_id IS NOT NULL) illustrated FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE a.status<>'archived' GROUP BY i.slug ORDER BY image_gaps DESC LIMIT 30").fetchall()
 with m.m.connect(local=True) as db:local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in ['artists','artworks','artwork_artists','media_assets']}
 out=dict(at=m.now(),target=TARGET,production=counts,source_gaps=source_counts,local_readonly_counts=local)
 saved(dest,out);BACKUP.mkdir(parents=True,exist_ok=True);BACKUP.chmod(0o700);saved(BACKUP/'baseline.json.gz',out)
 saved(RUN/'authorization.json',dict(at=m.now(),user_instruction='we need more illustrated artworks at least 300 000, find pictures',prior_instruction="nice, add more images use wikiart and don't think about rights!",production_image_enrichment_authorized=True,local_database_read_only=True,scope='Selected authentic reproductions for existing active artwork gaps; exact object/version evidence, established creation-date scope and source labels preserved. No metadata, status or holdings rewrites.'))
 print(json.dumps(out),flush=True);return out
def native_image(provider,row):
 if row['last']>1955 or re.search(r'\((?:V|VERSO)\)\s*$',row['accession_number'],re.I):return None
 if provider=='rijks':
  raw=row['raw'];urls=raw.get('source_images',[])
  if raw.get('rights')!=['http://creativecommons.org/publicdomain/mark/1.0/'] or len(urls)!=1:return None
  if not re.fullmatch(r'https://iiif\.micr\.io/[A-Za-z0-9_-]+/full/max/0/default\.jpg',urls[0]):return None
  return dict(native_url=urls[0],image_url=urls[0].replace('/full/max/','/full/!1200,1200/'),source=raw,receipt=raw['page_receipt'])
 ims=[im for im in row.get('images',[]) if im['openaccess']=='1' and im['viewtype']=='primary' and im['depictstmsobjectid']==row['native_id'] and im['iiifurl'].startswith('https://api.nga.gov/iiif/')]
 if not ims:return None
 ims.sort(key=lambda im:(int(im['sequence']),im['uuid']));im=ims[0]
 return dict(native_url=im['iiifurl'],image_url=im['iiifurl']+'/full/!1200,1200/0/default.jpg',source=im,receipt=m.load(m.RUN/'sources/nga/published_images.csv.receipt.json'))
def discover():
 baseline();dest=RUN/'discovery.json'
 if dest.exists():return
 for provider in ['rijks','nga']:
  cfg=CFG[provider]
  output=DATA/(provider+'-candidates.json.gz')
  if output.exists():continue
  paths=sorted((m.RUN/'rijks').glob('*/plan.json.gz')) if provider=='rijks' else [m.RUN/'nga/plan-v2.json.gz'];rows=[];pins={}
  for path in paths:
   assert (path.parent/'full-verification.json').exists();p=m.load(path);pin=m.sha(path.read_bytes());pins[str(path.relative_to(m.ROOT))]=pin
   for row in p['new_artworks']:
    im=native_image(provider,row)
    if im:
     keep={k:row[k] for k in ['artwork_id','native_id','title','creator_label','source_url','accession_number','first','last','precision','work_type']}
     rows.append(dict(keep,provider=provider,image=im,plan_path=str(path),plan_sha256=pin))
  urls=collections.Counter(r['image']['native_url'] for r in rows);held=[dict(artwork_id=r['artwork_id'],reason='native_image_reused_for_multiple_objects',native_url=r['image']['native_url']) for r in rows if urls[r['image']['native_url']]>1];rows=[r for r in rows if urls[r['image']['native_url']]==1]
  # Scope current catalogue enrichment by candidate IDs, never a global artwork CTE.
  present={};query='SELECT id::text,title,creation_year_start,creation_year_end,date_precision,accession_number,current_institution_id::text,status,primary_media_id FROM artworks WHERE id=ANY(%s::uuid[])'
  with m.m.connect() as db:
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');qp=db.execute('EXPLAIN (FORMAT JSON) '+query,([r['artwork_id'] for r in rows[:2000]],)).fetchone()
   for ids in m.chunks([r['artwork_id'] for r in rows],2000):present.update({a['id']:a for a in db.execute(query,(ids,))})
  valid=[]
  for row in rows:
   a=present.get(row['artwork_id'])
   if not a or a['status']=='archived' or a['primary_media_id'] is not None:continue
   if (a['title'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['accession_number'],a['current_institution_id'])!=(row['title'],row['first'],row['last'],row['precision'],row['accession_number'],cfg['mid']):held.append(dict(artwork_id=row['artwork_id'],reason='catalogue_fields_changed_since_native_plan'));continue
   valid.append(row)
  rank={'painting':0,'drawing':1,'watercolor':2,'sculpture':3,'print':4,'photograph':5}
  valid.sort(key=lambda r:(rank.get(r['work_type'],9),r['creator_label'],r['first'],r['native_id']))
  # Select a bounded portion of available native-image gaps; never download a collection dump.
  chosen=valid[:cfg['limit']]
  saved(output,dict(at=m.now(),provider=provider,eligible_gaps=len(valid),rows=chosen,source_plans=pins,held=held,query_plan=qp))
  print(provider,'eligible native image gaps',len(valid),'selected candidates',len(chosen),flush=True)
 summary={}
 for provider in ['rijks','nga']:
  p=m.load(DATA/(provider+'-candidates.json.gz'));groups=list(m.chunks(p['rows'],SIZE));summary[provider]=dict(eligible_gaps=p['eligible_gaps'],selected=len(p['rows']),batches=len(groups),types=dict(collections.Counter(r['work_type'] for r in p['rows'])))
  for i,rows in enumerate(groups):
   batch=provider+'-'+str(i).zfill(3);path=folder(batch)/'selection.json.gz'
   if not path.exists():saved(path,dict(at=m.now(),provider=provider,batch=batch,rows=rows,selection_basis='Bounded existing primary-image gaps with exact native object/inventory IDs and literal creation end through 1955. Single primary museum image, unchanged native catalogue fields, no explicit verso records or repeated native images. Pictures are selected before download.'))
   pin=folder(batch)/'pin.json'
   if not pin.exists():saved(pin,dict(sha256=m.sha(path.read_bytes())))
 saved(dest,dict(at=m.now(),sources=summary,metadata_only=True));print(json.dumps(summary),flush=True)
def provider_slot(host):
 # Share the existing provider lock/cooldown. The two validated museum IIIF
 # Rijks' validated CDN uses at most sixteen requests/second after 44,000
 # successful preparations without a rate denial. NGA retains eight/second.
 # Workers overlap image decoding and response latency within that shared cap.
 # This is an operational ceiling, not a claimed provider-published quota.
 # Other image hosts retain four/second. Denials stop the source immediately.
 interval=.0625 if host=='iiif.micr.io' else (.125 if host=='api.nga.gov' else .25)
 directory=Path.home()/'Library/Application Support/Artline/research-rate-limits';directory.mkdir(parents=True,exist_ok=True);path=directory/(m.sha(host.encode())+'.lock')
 while True:
  with path.open('a+') as f:
   fcntl.flock(f,fcntl.LOCK_EX);f.seek(0)
   try:next_at=float(f.read() or 0)
   except ValueError:next_at=0
   wait=next_at-time.time()
   if wait<=0:f.seek(0);f.truncate();f.write(str(time.time()+interval));f.flush();return
  time.sleep(min(wait,30))
def prepare_one(row,batch):
 aid=row['artwork_id'];dest=folder(batch)/'prepared'/(aid+'.json')
 if dest.exists():return m.load(dest)
 cfg=CFG[row['provider']];host=cfg['host'] or urlsplit(row['image']['image_url']).hostname;hold=RUN/'access-holds'/(host+'.json');out=dict(artwork_id=aid,provider=row['provider'],title=row['title'],artist=row['creator_label'])
 try:
  assert not hold.exists(),'Source surface access held';assert shutil.disk_usage(ORIG.parent).free>30*1024**3,'Disk headroom threshold reached'
  original=ORIG/batch/(aid+'.source');receipt=original.with_suffix('.receipt.json');original.parent.mkdir(parents=True,exist_ok=True)
  if receipt.exists():rc=m.load(receipt);raw=original.read_bytes();assert m.sha(raw)==rc['sha256']
  else:
   url=row['image']['image_url'];assert urlsplit(url).hostname==host;provider_slot(host);assert not hold.exists(),'Source surface access held'
   with session().get(url,timeout=(15,60),stream=True,allow_redirects=False) as response:
    rc=dict(url=url,status=response.status_code,retrieved_at=m.now(),content_type=response.headers.get('Content-Type'),etag=response.headers.get('ETag'),response_header_seconds=response.elapsed.total_seconds() if getattr(response,'elapsed',None) else None)
    if response.status_code in [401,403,429]:
     with _hold_lock:
      hold.parent.mkdir(parents=True,exist_ok=True)
      with hold.with_suffix('.lock').open('a+') as lock:
       fcntl.flock(lock,fcntl.LOCK_EX)
       if not hold.exists():saved(hold,dict(rc,retry_after=response.headers.get('Retry-After')))
    response.raise_for_status();assert response.status_code==200 and (rc['content_type'] or '').startswith('image/'),'Unexpected source image response'
    payload=bytearray()
    for chunk in response.iter_content(65536):payload.extend(chunk);assert len(payload)<=12000000,'Source image byte limit exceeded'
   raw=bytes(payload);rc.update(bytes=len(raw),sha256=m.sha(raw));temp=original.with_suffix('.part');temp.write_bytes(raw);os.replace(temp,original);saved(receipt,rc)
  with Image.open(io.BytesIO(raw)) as source:
   assert source.width*source.height<=12000000;source.load();im=ImageOps.exif_transpose(source).convert('RGB');original_size=im.size;outbytes=None
   for edge in [1200,1050,900,800,700,600]:
    resized=im.copy();resized.thumbnail((edge,edge),Image.Resampling.LANCZOS)
    for quality in [88,82,76,70,64,58]:
     buf=io.BytesIO();resized.save(buf,'JPEG',quality=quality,optimize=True,progressive=True)
     if buf.tell()<=100000:outbytes=buf.getvalue();break
    if outbytes:break
   assert outbytes and min(resized.size)>=40 and max(resized.size)>=200,'Image too small or exceeds derivative budget'
   assert abs(resized.width/resized.height-original_size[0]/original_size[1])<max(.03,2/resized.height),'Image proportions changed'
   gray=resized.convert('L');thumb=gray.resize((9,8));px=list(thumb.getdata());dhash=0
   for y in range(8):
    for x in range(8):dhash=(dhash<<1)|(px[y*9+x]>px[y*9+x+1])
   stat=ImageStat.Stat(gray);entropy=gray.entropy();flags=[]
   if min(resized.size)<150:flags.append('low_resolution')
   if max(resized.size)/min(resized.size)>5:flags.append('extreme_aspect_ratio')
   if entropy<3 or stat.stddev[0]<8:flags.append('low_information_image')
   if re.search(r'\b(detail|fragment|gedeelte|verso|recto|achterzijde|kopie|copy|reproductie|panel|wing|triptych|diptych|altar|altarpiece)\b',row['title'],re.I):flags.append('object_or_version_wording')
   if re.search(r'\b(?:two|three|four|five|six) panels\b|\baltarpiece\b',row['image']['source'].get('assistivetext',''),re.I):flags.append('source_multicomponent_description')
   if row.get('manual_visual_required'):flags.append('source_display_placeholder')
   digest=m.sha(outbytes);sp='/assets/artworks/imported/'+OP+'/'+aid+'-'+digest[:16]+'.jpg';local=m.ROOT/'apps/web/public'/sp.lstrip('/');local.parent.mkdir(parents=True,exist_ok=True)
   if local.exists():assert m.sha(local.read_bytes())==digest
   else:local.write_bytes(outbytes)
   out.update(state='prepared',path=str(local),storage_path=sp,sha256=digest,bytes=len(outbytes),width=resized.width,height=resized.height,original_dimensions=original_size,source_sha256=rc['sha256'],source_image_url=row['image']['image_url'],original_path=str(original),download=rc,media_id=uid('media/'+aid+'/'+digest),dhash=format(dhash,'016x'),gray_entropy=entropy,quality=quality,flags=flags)
 except Exception as exc:out.update(state='held',reason=type(exc).__name__+': '+str(exc)[:500])
 return saved(dest,out)
def prepare(batch):
 p=selected(batch);ORIG.mkdir(parents=True,exist_ok=True);counts=collections.Counter()
 assert m.sha((folder(batch)/'selection.json.gz').read_bytes())==m.load(folder(batch)/'pin.json')['sha256']
 # Threaded preparation saturated roughly one CPU core. Separate processes
 # overlap image processing as well as network I/O; provider_slot remains
 # a cross-process file lock and every row writes its own immutable receipt.
 with concurrent.futures.ProcessPoolExecutor(max_workers=16) as pool:
  for i,r in enumerate(pool.map(prepare_one,p['rows'],itertools.repeat(batch)),1):
   counts[r['state']]+=1
   if i%100==0:print(batch,'prepared',i,dict(counts),flush=True)
 saved(folder(batch)/'preparation-summary.json',dict(at=m.now(),counts=dict(counts)));print(batch,dict(counts),flush=True)
def opaque_edge_bands(image):
 gray=image.convert('L');w,h=gray.size;band=max(1,h//8);edges=[]
 for label,box in [('top',(2,0,w-2,band)),('bottom',(2,h-band,w-2,h))]:
  stat=ImageStat.Stat(gray.crop(box))
  if stat.mean[0]<=2 and stat.stddev[0]<=2:edges.append(label)
 return edges
def audit(batch):
 dest=folder(batch)/'quality-audit.json'
 if dest.exists():return
 p=selected(batch);rows={r['artwork_id']:r for r in p['rows']};images=[m.load(folder(batch)/'prepared'/(aid+'.json')) for aid in rows];ready=[im for im in images if im['state']=='prepared'];holds={};dups=collections.defaultdict(list)
 for im in ready:dups[im['sha256']].append(im['artwork_id'])
 for ids in dups.values():
  if len(ids)>1:
   for aid in ids:holds[aid]='Same image bytes selected for different museum objects; resolve identity before counting'
 with m.m.connect() as db:
  for hashes in m.chunks(list(dups),1000):
   for r in db.execute('SELECT id::text,checksum_sha256::text FROM media_assets WHERE checksum_sha256=ANY(%s)',(hashes,)):
    for aid in dups[r['checksum_sha256']]:holds[aid]='Identical derivative already exists in catalogue media; requires object reconciliation'
 # Cross-batch repeats are held before attachment, even when prior batches are not yet applied.
 previous={}
 for path in sorted((RUN/'batches').glob('*/quality-audit.json')):
  for im in m.load(path)['prepared_images']:previous.setdefault(im['sha256'],[]).append(im['artwork_id'])
 for im in ready:
  if im['sha256'] in previous:holds[im['artwork_id']]='Identical derivative in a prior selected batch; requires object reconciliation'
 usable=[im for im in ready if im['artwork_id'] not in holds];sample={};bytype=collections.defaultdict(list);byartist=collections.defaultdict(list)
 for im in usable:
  with Image.open(im['path']) as source:
   if opaque_edge_bands(source):im['flags']=list(dict.fromkeys(im['flags']+['opaque_edge_band']))
  if re.search(r'\b(album|albums|sketchbook|schetsboek|portfolio|portefeuille|ensemble)\b',im['title'],re.I):im['flags']=list(dict.fromkeys(im['flags']+['collection_or_cover_wording']))
 seenartists=set()
 for path in (RUN/'batches').glob('*/visual-review.json'):
  for decision in m.load(path)['decisions']:seenartists.add(decision['artist'])
 for im in usable:
  bytype[rows[im['artwork_id']]['work_type']].append(im);byartist[im['artist']].append(im)
  if im['flags']:sample[im['artwork_id']]=im
 for ims in bytype.values():
  for i in sorted({0,len(ims)//2,len(ims)-1}):sample[ims[i]['artwork_id']]=ims[i]
 for artist,ims in byartist.items():
  if artist not in seenartists:sample[ims[0]['artwork_id']]=ims[0]
 for im in sorted(usable,key=lambda im:m.sha(im['artwork_id'].encode()))[:max(20,len(usable)//25)]:sample[im['artwork_id']]=im
 if p['provider']=='wikiart':sample={im['artwork_id']:im for im in usable}
 out=dict(at=m.now(),batch=batch,prepared_images=ready,preparation_holds=[im for im in images if im['state']!='prepared'],identity_holds=holds,sample_ids=list(sample),sample_policy='Every file: native object/image identity, decode, dimensions, full-frame proportions, bytes, checksums and exact-duplicate checks. Visual review: all quality/version flags, each newly encountered creator, first/middle/last per object type and deterministic 4% batch sample. Unsampled files are not represented as individually visually inspected.')
 if p['provider']=='wikiart':out['sample_policy']='Every selected WikiArt image individually visually reviewed, in addition to exact current source-page, title, creator, date, original-image identity, technical and checksum checks. Assemblies, montage images, details and version overlaps held when unresolved.'
 saved(dest,out)
 font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
 for i,group in enumerate(m.chunks(list(sample.values()),40)):
  canvas=Image.new('RGB',(2400,1900),'#eeeeee');draw=ImageDraw.Draw(canvas)
  for j,im in enumerate(group):
   x=j%8*300;y=j//8*380
   with Image.open(im['path']) as image:image.thumbnail((290,310));canvas.paste(image,(x+(300-image.width)//2,y+(310-image.height)//2))
   draw.text((x+4,y+314),str(j+1)+'. '+im['title'][:35],font=font,fill='black');draw.text((x+4,y+337),im['artist'][:36],font=font,fill='black');draw.text((x+4,y+359),','.join(im['flags'])[:36],font=font,fill='red')
  path=ORIG/batch/('review-'+str(i).zfill(3)+'.jpg');canvas.save(path,quality=94);saved(folder(batch)/'sheets'/(str(i).zfill(3)+'.json'),dict(path=str(path),sha256=m.sha(path.read_bytes()),images=[dict(artwork_id=im['artwork_id'],sha256=im['sha256'],title=im['title'],artist=im['artist'],flags=im['flags']) for im in group]))
 print(batch,'prepared',len(ready),'identity holds',len(holds),'visual samples',len(sample),flush=True)
def accepted(batch):
 audit=m.load(folder(batch)/'quality-audit.json');review=m.load(folder(batch)/'visual-review.json');decisions={r['artwork_id']:r for r in review['decisions']};assert set(audit['sample_ids'])<=set(decisions),'Every selected visual sample needs an explicit decision'
 for im in audit['prepared_images']:
  if im['artwork_id'] in decisions:assert decisions[im['artwork_id']]['sha256']==im['sha256']
 assert review.get('batch_quality_decision')=='accept','Sampling found a batch-level issue; expand review before delivery'
 return [im for im in audit['prepared_images'] if im['artwork_id'] not in audit['identity_holds'] and (im['artwork_id'] not in decisions or decisions[im['artwork_id']]['decision']=='accept')],audit,review
def upload(batch):
 images,audit,review=accepted(batch);credentials=d.core.GcloudCredentials();credentials.refresh(None);client=storage.Client(project='artline-508319',credentials=credentials)
 client._http.mount('https://',requests.adapters.HTTPAdapter(pool_connections=32,pool_maxsize=32,pool_block=True));bucket=client.bucket(d.core.BUCKET)
 def one(im):
  dest=folder(batch)/'uploads'/(im['artwork_id']+'.json')
  if dest.exists():return
  raw=Path(im['path']).read_bytes();assert m.sha(raw)==im['sha256'];blob=bucket.blob(im['storage_path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'operation':OP};blob.cache_control='public,max-age=31536000,immutable'
  try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0)
  except PreconditionFailed:pass
  blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode();r=session().get('https://artlines.org'+im['storage_path'],timeout=(15,60));r.raise_for_status();assert m.sha(r.content)==im['sha256']
  saved(dest,dict(at=m.now(),sha256=im['sha256'],generation=blob.generation,public_byte_hash_verified=True))
 with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
  for i,_ in enumerate(pool.map(one,images),1):
   if i%200==0:print(batch,'uploaded/public verified',i,flush=True)
def transaction_groups(batch,images):
 dest=folder(batch)/'transaction-layout.json';ids=[im['artwork_id'] for im in images]
 if dest.exists():layout=m.load(dest)
 else:
  # Existing interrupted 100-row batches retain their exact recovery boundaries.
  old=any((folder(batch)/'applied').glob('*.json')) or any((BACKUP/batch).glob('before-*.json.gz'))
  size=100 if old else 500
  layout=saved(dest,dict(at=m.now(),group_size=size,ids=ids,review_sha256=m.sha((folder(batch)/'visual-review.json').read_bytes())))
 assert layout['ids']==ids and layout['review_sha256']==m.sha((folder(batch)/'visual-review.json').read_bytes()),'Attachment/review selection changed after transaction layout was pinned'
 assert layout['group_size'] in [100,500]
 return m.chunks(images,layout['group_size'])
def apply(batch):
 assert m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL','Successful recovery backup required before attachments'
 p=selected(batch);rows={r['artwork_id']:r for r in p['rows']};images,audit,review=accepted(batch);cfg=CFG[p['provider']];pin=m.load(folder(batch)/'pin.json')['sha256'];assert pin==m.sha((folder(batch)/'selection.json.gz').read_bytes());reviews={r['artwork_id']:r for r in review['decisions']}
 credits={}
 if p['provider']=='nga':credits={r['artwork_id']:r['raw'].get('creditline','') for r in m.load(m.RUN/'nga/plan-v2.json.gz')['new_artworks']}
 for i,group in enumerate(transaction_groups(batch,images)):
  receipt=folder(batch)/'applied'/(str(i).zfill(3)+'.json')
  if receipt.exists():assert m.load(receipt)['ids']==[im['artwork_id'] for im in group],'Saved transaction boundaries differ';continue
  ids=[im['artwork_id'] for im in group];expected={im['artwork_id']:im for im in group};backup=BACKUP/batch/('before-'+str(i).zfill(3)+'.json.gz')
  for im in group:assert m.load(folder(batch)/'uploads'/(im['artwork_id']+'.json'))['sha256']==im['sha256']
  with m.m.connect(write=True) as db:
   db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall();before=d.snapshot(db,ids)
   recovered=[aid for aid in ids if before[aid]['artwork']['primary_media_id']==expected[aid]['media_id']]
   if recovered:
    assert len(recovered)==len(ids),'Partial recovered transaction';old=m.load(backup)
    for aid in ids:assert all(before[aid]['artwork'][k]==v for k,v in old[aid]['artwork'].items() if k not in IGNORE)
    saved(receipt,dict(at=m.now(),ids=ids,images=len(ids),recovered=True));continue
   # Concurrent image additions must never be overwritten or counted again.
   for aid in ids:assert before[aid]['artwork']['primary_media_id'] is None,'Concurrent primary image; replan this bounded batch'
   collisions=db.execute('SELECT id::text,checksum_sha256::text FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in group],)).fetchall()
   assert not collisions,'Image checksum appeared after audit; reconcile before this transaction'
   native_ids={r['entity_id']:r['external_id'] for r in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND scheme=%s",(ids,cfg['scheme']))}
   if p['provider']=='wikiart':db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,'WikiArt verified legacy image references','collection_page','https://www.wikiart.org',%s) ON CONFLICT(id) DO NOTHING",(uid('source/wikiart'),OP+'-wikiart',OP))
   saved(backup,before);tables=collections.defaultdict(list)
   for im in group:
    aid=im['artwork_id'];r=rows[aid];a=before[aid]['artwork'];assert a['status']!='archived';assert (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])==(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],r.get('expected_museum_id',cfg['mid']))
    assert native_ids.get(aid)==r['native_id'],'Native identity changed'
    rights=r.get('rights_status',cfg['rights']);license=r.get('rights_label',cfg['license']);assert rights and license
    if r.get('expected_primary_artist_id'):assert any(c['artist_id']==r['expected_primary_artist_id'] and c['attribution_role']=='primary' for c in before[aid]['creators'])
    credit=(r['creator_label']+'. ' if r['creator_label'] else '')+(credits.get(aid,'')+'. ' if credits.get(aid) else '')+cfg['name']+'. '+license+'.'
    tables['media_assets'].append(dict(id=im['media_id'],storage_kind='local',storage_path=im['storage_path'],source_page_url=r['source_url'],provider_name=cfg['name'],mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=r['title']+' — '+r['creator_label'],rights_status=rights,license_label=license,license_url=cfg['policy'],creator_credit=credit,attribution_text=credit+' Full source frame preserved; proportional resizing and JPEG compression.',retrieved_at=im['download']['retrieved_at'],verified_at=m.now(),verified_by=m.ACTOR))
    evidence=dict(selection_sha256=pin,native_source=r['image']['source'],source_receipt=r['image']['receipt'],original_catalogue_plan_sha256=r['plan_sha256'],download=im['download'],technical_checks={k:im[k] for k in ['width','height','original_dimensions','bytes','sha256','quality','gray_entropy','flags']},visual_review=reviews.get(aid),batch_visual_review_sha256=m.sha((folder(batch)/'visual-review.json').read_bytes()),visual_sample_policy=audit['sample_policy'],identity='Exact native museum inventory/object and primary image from pinned source record; catalogue identity and dates rechecked at attachment. No holdings or metadata mutation.')
    if p['provider']=='wikiart':evidence.update(identity=r['identity_basis'],identity_confidence=r['identity_confidence'],user_approval=m.load(RUN/'authorization.json'))
    tables['media_rights_evidence'].append(dict(media_id=im['media_id'],source_id=uid('source/wikiart') if p['provider']=='wikiart' else m.uid('source/'+p['provider']),source_record_id=r.get('current_source_id',r['native_id']),source_checksum=r['image']['receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=cfg['policy'],rights_basis=r.get('rights_basis',license+' explicitly supplied by the native museum image metadata; actual evidence preserved.'),adapter_version=OP,checked_at=m.now(),evidence_json=json.dumps(evidence,ensure_ascii=False)))
    order=max([v['sort_order'] for v in before[aid]['attachments']],default=-1)+1;tables['artwork_media'].append(dict(artwork_id=aid,media_id=im['media_id'],sort_order=order,view_label=cfg['name']+' primary object reproduction'))
   for table in ['media_assets','media_rights_evidence','artwork_media']:n.copy_rows(db,table,tables[table])
   db.execute('UPDATE artworks a SET primary_media_id=x.mid,updated_by=%s,updated_at=now(),revision=revision+1 FROM unnest(%s::uuid[],%s::uuid[]) x(aid,mid) WHERE a.id=x.aid',(m.ACTOR,ids,[expected[aid]['media_id'] for aid in ids]))
   after=d.snapshot(db,ids)
   for aid in ids:
    assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in IGNORE)
    assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings'];assert after[aid]['artwork']['primary_media_id']==expected[aid]['media_id']
   db.commit()
  saved(receipt,dict(at=m.now(),ids=ids,images=len(ids),selection_sha256=pin));print(batch,'attached',i,len(ids),flush=True)
def verify(batch):
 dest=folder(batch)/'verification.json'
 if dest.exists():return
 images,audit,review=accepted(batch);expected={im['artwork_id']:im for im in images};counts=collections.Counter();assert len(expected)==sum(m.load(p)['images'] for p in (folder(batch)/'applied').glob('*.json'))
 with m.m.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  for path in sorted((folder(batch)/'applied').glob('*.json')):
   receipt=m.load(path);ids=receipt['ids'];before=m.load(BACKUP/batch/('before-'+path.name.replace('.json','.json.gz')));after=d.snapshot(db,ids)
   media={r['id']:r for r in db.execute('SELECT id::text,checksum_sha256::text,storage_path FROM media_assets WHERE id=ANY(%s::uuid[])',([expected[aid]['media_id'] for aid in ids],))}
   for aid in ids:
    im=expected[aid];a=after[aid];assert a['artwork']['primary_media_id']==im['media_id'];assert all(a['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in IGNORE);assert a['creators']==before[aid]['creators'] and a['holdings']==before[aid]['holdings'];assert media[im['media_id']]['checksum_sha256']==im['sha256'] and media[im['media_id']]['storage_path']==im['storage_path'];assert any(x['media_id']==im['media_id'] for x in a['attachments']);assert m.load(folder(batch)/'uploads'/(aid+'.json'))['public_byte_hash_verified'];counts['images']+=1
   counts['rights_evidence']+=db.execute('SELECT count(*) n FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[]) AND adapter_version=%s',([expected[aid]['media_id'] for aid in ids],OP)).fetchone()['n']
   counts['search_documents']+=db.execute('SELECT count(*) n FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.primary_media_id=a.primary_media_id AND s.status=a.status AND s.title=a.title',(ids,)).fetchone()['n']
  progress=coverage(db)
 with m.m.connect(local=True) as db:local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in baseline()['local_readonly_counts']}
 assert local==baseline()['local_readonly_counts'];assert counts['images']==counts['rights_evidence']==counts['search_documents']==len(images)
 public=[]
 for im in images[:3]:
  url='https://artlines.org/api/backend/v1/atlas/artworks/'+im['artwork_id'];r=session().get(url,timeout=(15,60));r.raise_for_status();assert im['storage_path'] in r.text;public.append(dict(url=url,status=r.status_code))
 saved(dest,dict(at=m.now(),batch=batch,checks=dict(counts),production=progress,local_baseline_equal=True,metadata_creators_holdings_and_state_preserved=True,public_byte_checks=len(images),public_routes=public));print(json.dumps(dict(batch=batch,checks=dict(counts),coverage=progress)),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['baseline','discover','prepare','audit','upload','apply','verify']);p.add_argument('--batch');a=p.parse_args()
 if a.action in ['baseline','discover']:globals()[a.action]()
 else:assert a.batch and re.fullmatch(r'(rijks|nga|wikiart)-\d{3}',a.batch);globals()[a.action](a.batch)
