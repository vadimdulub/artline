#!/usr/bin/env python3
"""Pinned Soviet Realism delivery: scoped identity checks, source images, atomic writes."""
import base64,collections,concurrent.futures,gzip,hashlib,importlib.util,io,json,re,subprocess,sys,threading,time
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image,ImageOps,ImageStat,ImageDraw,ImageFont
from psycopg.types.json import Jsonb
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
sp=importlib.util.spec_from_file_location('soviet',Path(__file__).with_name('soviet-realism-20261011.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
core=m.module('soviet_images','ops/enrich-artwork-images.py')
RUN=m.RUN;BACKUP=m.BACKUP;ROOT=m.ROOT;OP=m.OP;ACTOR=m.ACTOR
MOVEMENT=m.uid('movement/soviet-realism')

def source_rows():
 sov=m.load(RUN/'sovcom-records.json.gz')['rows']
 other=[m.load(p) for p in (RUN/'objects').glob('*.json.gz')]
 return sov+[r for r in other if not r.get('hold') and r.get('outcome')=='captured']

def snapshot(db,ids):return m.dbutil.snapshot(db,ids)
def identity_plan():
 artists=m.load(RUN/'artist-plan.json.gz');rows=source_rows();held=[];candidates=[]
 # Exile and nonrepresentational traditions must not be reclassified from a sale category.
 excluded=re.compile(r'Коровин Константин|Серебрякова|Бенуа|Рерих|Малявин|Гончарова Наталия|Ларионов Михаил|Бурлюк|Шагал|Кандинский|Тархов|Кислинг|Паскин|Сутин|Филонов|Малевич|Степанова Варвара|Родченко|Матюшин',re.I)
 for r in rows:
  r=dict(r);ap=artists.get(r['creator_url']);reason=None
  if not ap or ap['action']=='hold':reason='Creator identity requires reconciliation before movement association'
  elif excluded.search(ap['profile']['full_name']):reason='Emigrant or distinct avant-garde tradition; sale category does not establish Soviet Realism'
  elif r.get('date') is None or not 1917<=r['date']['creation_year_start']<=r['date']['creation_year_end']<=1970:reason='Creation date outside strict selected range'
  elif r['date']['creation_year_start']<(ap['profile'].get('birth_year') or 0)+10:reason='Source creation date predates plausible documented creator activity'
  elif re.search(r'копи[яи]|репродукци|Маха обнажен|по мотивам',r['source_title'],re.I):reason='Copy or source/version issue'
  if reason:held.append(dict(r,hold=reason));continue
  r.update(artist_id=ap['artist_id'],creator_full_name=ap['profile']['full_name'],scheme=r['provider']+'-catalogue-object')
  rc=r['receipt'];body=ROOT/rc['body_path'];assert m.sha(gzip.decompress(body.read_bytes()))==rc['sha256'] and rc['status']==200
  candidates.append(r)
 artist_ids=list({r['artist_id'] for r in candidates});urls=list({r['source_url'] for r in candidates})
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  query='''SELECT to_jsonb(a) v,aa.artist_id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' '''
  m.save(RUN/'scoped-query-plan.json',db.execute('EXPLAIN (FORMAT JSON) '+query,(artist_ids,)).fetchone())
  works=db.execute(query,(artist_ids,)).fetchall();bytitle=collections.defaultdict(list);byurl=collections.defaultdict(set)
  for w in works:
   for title in [w['v']['title'],w['v']['alternate_title']]:
    if title:bytitle[w['artist_id'],m.norm(title)].append(w['v'])
  for offset in range(0,len(urls),300):
   for e in db.execute("SELECT entity_id::text,canonical_url url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) UNION SELECT entity_id::text,source_url url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls[offset:offset+300],urls[offset:offset+300])):byurl[e['url']].add(e['entity_id'])
  selected=[];claimed={}
  for r in candidates:
   exact=byurl[r['source_url']];titles={a['id']:a for a in bytitle[r['artist_id'],m.norm(r['title'])]};reason=None;existing=None
   if len(exact)>1:reason='Multiple production objects share source identity'
   elif len(exact)==1:existing=next(iter(exact))
   elif titles:reason='Same creator/title already in production; version and translation evidence needed'
   key=(r['artist_id'],m.norm(r['title']),r['date']['creation_year_start'],r['date']['creation_year_end'],m.norm(r.get('dimensions_text')))
   if key in claimed:reason='Selected creator/title/date/dimensions collide; treat repeat listing as one object pending image comparison'
   if reason:held.append(dict(r,hold=reason,possible_existing_ids=list(titles)));continue
   aid=existing or m.uid('artwork/'+r['provider']+'/'+r['source_id']);r.update(artwork_id=aid,action='existing' if existing else 'create',identity_basis='Exact existing source identity' if existing else 'Distinct native source object, reconciled repeated source image and creator/title/date/dimensions, scoped production source and creator/title audit',confidence=.99 if existing else .95)
   selected.append(r);claimed[key]=aid
  before=snapshot(db,[r['artwork_id'] for r in selected if r['action']=='existing'])
  for r in selected:
   if r['action']=='existing':r['has_image']=bool(before[r['artwork_id']]['artwork']['primary_media_id'])
  existingartists={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(artist_ids,))}
  existingmedia=[dict(x) for x in db.execute('SELECT m.id::text,m.checksum_sha256,m.source_page_url,m.storage_path FROM media_assets m JOIN artworks a ON a.primary_media_id=m.id JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=ANY(%s::uuid[])',(artist_ids,))]
 data=dict(at=m.now(),rows=selected,held=held,artists=artists,existing_artists=existingartists,preimages=before,existing_media=existingmedia,authorization_sha256=m.sha((RUN/'authorization.json').read_bytes()))
 m.save(RUN/'identity-plan.json.gz',data);pin=m.sha((RUN/'identity-plan.json.gz').read_bytes());m.save(RUN/'identity-plan-pin.json',dict(sha256=pin));m.save(BACKUP/'identity-preimages.json.gz',dict(plan_sha256=pin,records=before,artists=existingartists))
 print('IDENTITY PLAN',dict(collections.Counter(r['action'] for r in selected)),'held',len(held),flush=True)

def plan():
 p=RUN/'identity-plan.json.gz';assert m.sha(p.read_bytes())==m.load(RUN/'identity-plan-pin.json')['sha256'];return m.load(p)

def download(url):
 host=urlsplit(url).hostname;assert host in ('www.socrealizm.com.ua','sovcom.ru')
 key=m.sha(url.encode());rp=RUN/'image-downloads'/(key+'.json');path=m.ORIGINALS/(key+'.body')
 if rp.exists():
  rc=m.load(rp);raw=path.read_bytes();assert m.sha(raw)==rc['sha256'];return raw,rc
 hold=RUN/'image-access-holds'/(host+'.json')
 with m.LOCKS[host]:
  if hold.exists():raise RuntimeError('Image provider access held: '+host)
  time.sleep(max(0,m.NEXT[host]-time.monotonic()));m.NEXT[host]=time.monotonic()+.25
 with m.requests.get(url,timeout=(15,45),stream=True) as response:
  if response.status_code in (401,403,429):
   with m.LOCKS[host]:
    if not hold.exists():m.save(hold,dict(at=m.now(),url=url,status=response.status_code,retry_after=response.headers.get('Retry-After')))
  response.raise_for_status();assert response.headers.get('Content-Type','').startswith('image/')
  raw=bytearray()
  for chunk in response.iter_content(65536):
   raw.extend(chunk)
   if len(raw)>20_000_000:raise ValueError('Selected source image exceeds byte budget')
  raw=bytes(raw);rc=dict(url=url,final_url=response.url,at=m.now(),sha256=m.sha(raw),bytes=len(raw),content_type=response.headers.get('Content-Type'))
 m.save(path,raw);m.save(rp,rc);return raw,rc

def prepare():
 data=plan();rows=[r for r in data['rows'] if not r.get('has_image')]
 def one(row):
  dest=RUN/'prepared-images'/(row['artwork_id']+'.json')
  if dest.exists():
   old=m.load(dest);assert old['source_image_url']==row['source_image_url'] and old['title']==row['title'];return old
  result=dict(artwork_id=row['artwork_id'],artist_id=row['artist_id'],title=row['title'],creator=row['creator_full_name'],source_image_url=row['source_image_url'],provider=row['provider'],outcome='held')
  try:
   original,rc=download(row['source_image_url']);raw,w,h,quality=core.compress(original)
   with Image.open(io.BytesIO(original)) as im:ow,oh=ImageOps.exif_transpose(im).size
   assert min(w,h)>=80 and max(w,h)>=200 and abs(w/h-ow/oh)<.025
   with Image.open(io.BytesIO(raw)) as im:
    im.load();gray=im.convert('L').resize((17,16));pix=list(gray.getdata());bits=''.join('1' if pix[y*17+x]>pix[y*17+x+1] else '0' for y in range(16) for x in range(16));dhash=hex(int(bits,2))[2:].zfill(64);std=ImageStat.Stat(im.convert('L')).stddev[0];assert std>2
   digest=m.sha(raw);urlpath='/assets/artworks/imported/'+OP+'/'+row['artwork_id']+'-'+digest[:16]+'.jpg';local=ROOT/'apps/web/public'/urlpath.lstrip('/');m.save(local,raw)
   result.update(outcome='prepared',path=urlpath,local_path=str(local),width=w,height=h,bytes=len(raw),sha256=digest,quality=quality,dhash=dhash,original_dimensions=[ow,oh],download=rc,media_id=m.uid('media/'+row['artwork_id']+'/'+digest))
  except Exception as exc:result['error']=str(exc)[:400]
  m.save(dest,result);return result
 counts=collections.Counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for n,r in enumerate(pool.map(one,rows),1):
   counts[r['outcome']]+=1
   if n%50==0:print('IMAGES',n,'/',len(rows),dict(counts),flush=True)
 print('IMAGE PREPARATION',dict(counts),flush=True)

def audits():
 data=plan();images=[m.load(p) for p in (RUN/'prepared-images').glob('*.json')];ready=[x for x in images if x['outcome']=='prepared'];holds={};groups=[]
 byartist=collections.defaultdict(list);byhash=collections.defaultdict(list)
 selected={r['artwork_id']:r for r in data['rows']};ready=[im for im in ready if im['artwork_id'] in selected]
 for im in ready:byartist[selected[im['artwork_id']]['artist_id']].append(im);byhash[im['download']['sha256']].append(im)
 for group in byhash.values():
  if len(group)>1:
   group.sort(key=lambda x:x['artwork_id']);groups.append(dict(type='identical-source-bytes',ids=[x['artwork_id'] for x in group]));holds.update({x['artwork_id']:'Identical source reproduction already selected under another native record' for x in group[1:]})
 for images in byartist.values():
  for i,l in enumerate(images):
   for r in images[i+1:]:
    distance=(int(l['dhash'],16)^int(r['dhash'],16)).bit_count()
    if distance<=8:
     groups.append(dict(type='near-duplicate',ids=[l['artwork_id'],r['artwork_id']],distance=distance))
     for x in [l,r]:holds.setdefault(x['artwork_id'],'Near-identical reproduction; object/version review needed')
 known={x['checksum_sha256'] for x in data['existing_media'] if x['checksum_sha256']}
 for im in ready:
  if im['sha256'] in known or im['download']['sha256'] in known:holds[im['artwork_id']]='Source or derivative bytes match a scoped existing artwork image'
 m.save(RUN/'image-audit.json',dict(at=m.now(),prepared=len(ready),groups=groups,held_artwork_ids=holds,automated_checks='Every selected image decoded, checksummed, proportion/byte/dimension checked; within-artist perceptual and cross-artist exact-original duplicate checks; scoped existing primary hashes compared. All remaining images receive contact-sheet review.'))
 print('IMAGE AUDIT',len(ready),'prepared;',len(holds),'held',flush=True)

def sheets():
 holds=m.load(RUN/'image-audit.json')['held_artwork_ids'] if (RUN/'image-audit.json').exists() else {}
 old=list((RUN/'visual-sheets').glob('*.json'));indexed={im['artwork_id'] for path in old for im in m.load(path)['images']}
 rows=[r for r in plan()['rows'] if r['artwork_id'] not in holds and r['artwork_id'] not in indexed];items=[]
 for row in rows:
  p=RUN/'prepared-images'/(row['artwork_id']+'.json')
  if p.exists():
   im=m.load(p)
   if im['outcome']=='prepared':items.append(im)
 folder=m.ORIGINALS/'contact-sheets';folder.mkdir(parents=True,exist_ok=True);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
 for start in range(0,len(items),40):
  ims=items[start:start+40];canvas=Image.new('RGB',(1400,1600),'#eeeae4');draw=ImageDraw.Draw(canvas)
  for i,im in enumerate(ims):
   x=(i%5)*280;y=(i//5)*200
   with Image.open(im['local_path']) as pic:
    pic.thumbnail((266,160));canvas.paste(pic,(x+(280-pic.width)//2,y+(160-pic.height)//2))
   draw.text((x+5,y+162),str(start+i+1)+' '+im['title'][:30],font=font,fill='black');draw.text((x+5,y+180),im['creator'][:31],font=font,fill='black')
  sheet=folder/f'{len(old)+start//40+1:03d}.jpg';canvas.save(sheet,quality=88)
  m.save(RUN/'visual-sheets'/f'{len(old)+start//40+1:03d}.json',dict(sheet=str(sheet),images=[dict(artwork_id=im['artwork_id'],sha256=im['sha256'],title=im['title'],creator=im['creator']) for im in ims]))
 print('VISUAL SHEETS',len(items),'images in',(len(items)+39)//40,'sheets',flush=True)

def existing_audit():
 data=plan();byartist=collections.defaultdict(list);held={};matches=[];missing=[];checked=0
 for r in data['rows']:
  im=m.load(RUN/'prepared-images'/(r['artwork_id']+'.json'))
  if im['outcome']=='prepared':byartist[r['artist_id']].append(im)
  if 'Шухаев' in r['creator_full_name'] and r['date']['creation_year_start']<1935:
   held[r['artwork_id']]='Creation falls in the documented emigrant period; Soviet Realism association of this specific work is not established.'
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY')
  old=[dict(r) for r in db.execute('''SELECT aa.artist_id::text,a.id::text artwork_id,m.id::text media_id,m.storage_path,m.checksum_sha256
   FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id JOIN media_assets m ON m.id=a.primary_media_id
   WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' ''',(list(byartist),))]
 for row in old:
  local=ROOT/'apps/web/public'/row['storage_path'].lstrip('/')
  if not local.exists():missing.append(row);continue
  raw=local.read_bytes()
  if row['checksum_sha256']:assert m.sha(raw)==row['checksum_sha256']
  with Image.open(io.BytesIO(raw)) as im:
   gray=ImageOps.exif_transpose(im).convert('L').resize((17,16));pix=list(gray.getdata())
   dh=int(''.join('1' if pix[y*17+x]>pix[y*17+x+1] else '0' for y in range(16) for x in range(16)),2)
  checked+=1
  for candidate in byartist[row['artist_id']]:
   distance=(dh^int(candidate['dhash'],16)).bit_count()
   if distance<=14:
    matches.append(dict(existing=row,candidate=candidate['artwork_id'],distance=distance))
    held[candidate['artwork_id']]='Perceptually similar to an existing image for the reconciled creator; hold pending exact object/version comparison.'
 m.save(RUN/'existing-image-audit.json',dict(at=m.now(),checked=checked,unavailable_local_images=missing,matches=matches,held_artwork_ids=held))
 print('EXISTING IMAGE AUDIT',checked,'checked;',len(missing),'unavailable;',len(held),'held',flush=True)

def freeze():
 data=plan();audit=m.load(RUN/'image-audit.json');decisions={};held=dict(audit['held_artwork_ids'])
 held.update(m.load(RUN/'existing-image-audit.json')['held_artwork_ids'])
 for path in sorted((RUN/'visual-decisions').glob('*.json')):
  d=m.load(path);sheet=m.load(RUN/'visual-sheets'/(path.stem+'.json'))
  assert d['sheet_sha256']==m.sha(Path(sheet['sheet']).read_bytes())
  assert set(d['approved'])|set(d['held'])=={im['artwork_id'] for im in sheet['images']}
  assert not set(d['approved'])&set(d['held'])
  decisions.update({aid:'approved' for aid in d['approved']});held.update(d['held'])
 rows=[];images={};gaps={}
 for r in data['rows']:
  aid=r['artwork_id'];path=RUN/'prepared-images'/(aid+'.json')
  if aid in held:continue
  if not path.exists():gaps[aid]='No prepared image';continue
  im=m.load(path)
  if im['outcome']!='prepared':gaps[aid]=im.get('error');continue
  assert aid in decisions,'Complete visual review before freezing'
  raw=Path(im['local_path']).read_bytes();assert m.sha(raw)==im['sha256'] and len(raw)<=100000
  rows.append(r);images[aid]=im
 # Broad creator coverage first; do not let one prolific portfolio consume the target.
 queues=collections.defaultdict(list)
 for r in rows:queues[r['artist_id']].append(r)
 for key in queues:queues[key].sort(key=lambda r:(r['date']['creation_year_start'],r['source_url']))
 chosen=[]
 while any(queues.values()) and len(chosen)<2500:
  for key in sorted(queues):
   if queues[key] and len(chosen)<2500:chosen.append(queues[key].pop(0))
 assert sum(r['action']=='create' for r in chosen)>=2000,'The minimum requires 2,000 distinct new, illustrated objects'
 final=dict(at=m.now(),rows=chosen,images={r['artwork_id']:images[r['artwork_id']] for r in chosen},held=held,image_gaps=gaps,
  identity_plan_sha256=m.load(RUN/'identity-plan-pin.json')['sha256'],authorization_sha256=data['authorization_sha256'],
  artists=data['artists'],existing_artists=data['existing_artists'],preimages={r['artwork_id']:data['preimages'][r['artwork_id']] for r in chosen if r['action']=='existing'},
  eligible_not_selected=[r['artwork_id'] for r in rows if r['artwork_id'] not in {c['artwork_id'] for c in chosen}],
  selection='Up to 2,500 distinct illustrated personal editorial selections, round-robin across reconciled creators; Soviet Realism survey, not a museum masterpiece designation.')
 m.save(RUN/'delivery-plan.json.gz',final);pin=m.sha((RUN/'delivery-plan.json.gz').read_bytes());m.save(RUN/'delivery-plan-pin.json',dict(sha256=pin));m.save(BACKUP/'delivery-preimages.json.gz',dict(plan_sha256=pin,records=final['preimages'],artists=final['existing_artists']))
 print('FROZEN',len(chosen),'artworks and images;',len({r['artist_id'] for r in chosen}),'creators',flush=True)

def final_plan():
 p=RUN/'delivery-plan.json.gz';pin=m.load(RUN/'delivery-plan-pin.json')['sha256'];assert m.sha(p.read_bytes())==pin
 data=m.load(p);assert data['authorization_sha256']==m.sha((RUN/'authorization.json').read_bytes());return data,pin

def backup():
 rows=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--limit=100','--format=json'],text=True))
 b=next(r for r in rows if r.get('description')=='Before Soviet Realism catalogue 20261011');assert b['status']=='SUCCESSFUL'
 m.save(BACKUP/'cloud-backup.json',b);m.save(RUN/'cloud-backup.json',b);print('BACKUP',b['id'],b['status'],flush=True)

def upload():
 data,pin=final_plan();bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
 def one(im):
  dest=RUN/'uploads'/(im['artwork_id']+'.json')
  if dest.exists():
   rc=m.load(dest);assert rc['plan_sha256']==pin and rc['sha256']==im['sha256'];return
  raw=Path(im['local_path']).read_bytes();assert m.sha(raw)==im['sha256'];blob=bucket.blob(im['path'].lstrip('/'))
  blob.metadata={'sha256':im['sha256'],'operation':OP,'artwork-id':im['artwork_id'],'provider':im['provider']};blob.cache_control='public,max-age=31536000,immutable'
  try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
  except PreconditionFailed:blob.reload(timeout=30)
  assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
  response=m.requests.get('https://artlines.org'+im['path'],timeout=(15,45));response.raise_for_status();assert m.sha(response.content)==im['sha256']
  m.save(dest,dict(at=m.now(),artwork_id=im['artwork_id'],plan_sha256=pin,sha256=im['sha256'],generation=blob.generation,bytes=len(raw),public_http_status=response.status_code,public_bytes_verified=True))
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
  for n,_ in enumerate(pool.map(one,data['images'].values()),1):
   if n%100==0:print('UPLOADED AND VERIFIED',n,'/',len(data['images']),flush=True)

def source_id(provider):return m.uid('source/'+provider)
def slug(label,key):return (re.sub('[^a-z0-9]+','-',m.latin(label)).strip('-')[:105] or 'soviet-artwork')+'-'+key[:8]

def initialize(db,data,pin):
 dest=RUN/'applied-initialization.json'
 if dest.exists():return
 used={r['artist_id'] for r in data['rows']};profiles=collections.defaultdict(list)
 for ap in data['artists'].values():
  if ap.get('artist_id') in used:profiles[ap['artist_id']].append(ap)
 with db.transaction():
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  for provider,name,base in [('sovcom','SOVCOM — Soviet painting catalogue','https://sovcom.ru/'),('socrealizm','Kyiv collectors club Socrealizm — public catalogue','https://www.socrealizm.com.ua/'),('movement','WikiArt — Socialist Realism movement','https://www.wikiart.org/en/Artists-by-Art-Movement/socialist-realism')]:
   db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,%s,'collection_page',%s,%s) ON CONFLICT(id) DO NOTHING",(source_id(provider),OP+'-'+provider,name,base,OP))
  existing=db.execute("SELECT id::text FROM movements WHERE slug='soviet-realism'").fetchone();assert existing is None or existing['id']==MOVEMENT
  db.execute("INSERT INTO movements(id,slug,name,color_hex,summary_md,status) VALUES(%s,'soviet-realism','Soviet Realism','#A94B3B',%s,'review') ON CONFLICT(id) DO NOTHING",(MOVEMENT,'The Soviet tradition of Socialist Realism and related realist painting, including the Severe Style. Artists depicted work and everyday life, public history, portraits, landscapes and still lifes across the Soviet republics. This survey includes selected works created through 1970.'))
  db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'movement',%s,%s,'definition',%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",(m.uid('movement-definition'),MOVEMENT,source_id('movement'),'https://www.wikiart.org/en/Artists-by-Art-Movement/socialist-realism','User-requested Soviet regional tradition within Socialist Realism. Related but distinct Social Realism and non-Soviet traditions are not automatically included. Source-specific creator and artwork evidence accompanies the selections.',m.now(),ACTOR))
  created=[]
  actual_artists={r['id']:r for r in db.execute('SELECT id::text,display_name,birth_year,status FROM artists WHERE id=ANY(%s::uuid[]) FOR SHARE',(list(used),))}
  new_names=[m.norm(aps[0]['profile']['full_name']) for aps in profiles.values() if aps[0]['action']=='create']
  collisions_by_name=collections.defaultdict(set)
  for r in db.execute("SELECT id::text,normalized_name FROM artists WHERE normalized_name=ANY(%s) AND status<>'archived'",(new_names,)):collisions_by_name[r['normalized_name']].add(r['id'])
  with db.pipeline():
   for aid,aps in profiles.items():
    ap=aps[0];p=ap['profile'];works=[r for r in data['rows'] if r['artist_id']==aid];lo=min(r['date']['creation_year_start'] for r in works);hi=max(r['date']['creation_year_end'] for r in works)
    if ap['action']=='create':
     others=collisions_by_name[m.norm(p['full_name'])]-{aid};assert not others,'Concurrent duplicate creator'
     existing=actual_artists.get(aid)
     if existing:assert existing['display_name']==p['full_name']
     else:
      birth=p.get('birth_year');death=p.get('death_year');lifelabel=p.get('life_source_label','')
      if re.search(r'\?|около|ок\.',lifelabel,re.I):birth=death=None
      db.execute('''INSERT INTO artists(id,slug,display_name,sort_name,normalized_name,birth_year,death_year,birth_display,death_display,birth_precision,death_precision,active_start_year,active_end_year,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status,created_by,updated_by)
       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'activity','review',%s,%s)''',(aid,slug(p['full_name'],aid),p['full_name'],p['full_name'],m.norm(p['full_name']),birth,death,str(birth) if birth else None,str(death) if death else None,'exact' if birth else None,'exact' if death else None,lo,hi,lo,hi,f'Documented selected works: {lo}–{hi}',ACTOR,ACTOR));created.append(aid)
    else:
     actual=actual_artists.get(aid);expected=data['existing_artists'][aid]
     assert actual and actual['display_name']==expected['display_name'] and actual['birth_year']==expected['birth_year'] and actual['status']!='archived'
    for link in aps:
     p=link['profile'];provider=p.get('provider','socrealizm')
     db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id) VALUES(%s,'artist',%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",(m.uid('artist-source/'+p['url']),aid,provider+'-artist-profile',urlsplit(p['url']).path,p['url'],source_id(provider)))
     db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artist',%s,%s,'soviet_realism_creator_identity',%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",(m.uid('artist-citation/'+p['url']),aid,source_id(provider),p['url'],json.dumps(dict(profile=p,identity_basis=link['basis'],movement_basis='Editorial association supported by the source Soviet Realism collection and selected dated representational works; does not classify every work by this artist.'),ensure_ascii=False),p['receipt']['retrieved_at'],ACTOR))
    db.execute("INSERT INTO artist_movements(artist_id,movement_id,role) VALUES(%s,%s,'associated') ON CONFLICT DO NOTHING",(aid,MOVEMENT))
 m.save(dest,dict(at=m.now(),plan_sha256=pin,movement_id=MOVEMENT,new_artist_ids=created,associated_artist_ids=sorted(used)))

def apply():
 data,pin=final_plan();assert m.load(BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
 for aid,im in data['images'].items():
  upload=m.load(RUN/'uploads'/(aid+'.json'));assert upload['plan_sha256']==pin and upload['sha256']==im['sha256'] and upload['public_bytes_verified']
 with m.connect(True) as db:
  initialize(db,data,pin)
  for start in range(0,len(data['rows']),50):
   batch=data['rows'][start:start+50];ids=[r['artwork_id'] for r in batch];dest=RUN/'applied-batches'/f'{start//50:03d}.json'
   if dest.exists():continue
   with db.transaction():
    db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
    db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall();before=snapshot(db,ids)
    prior=db.execute("SELECT id FROM citations WHERE id=ANY(%s::uuid[])",([m.uid('work-citation/'+r['provider']+'/'+r['source_id']) for r in batch],)).fetchall()
    if prior:assert len(prior)==len(batch),'Partially committed batch'
    else:
     assert before=={aid:data['preimages'][aid] for aid in ids if aid in data['preimages']},'Concurrent artwork change'
     m.save(BACKUP/'batch-preimages'/f'{start//50:03d}.json.gz',dict(plan_sha256=pin,records=before))
     pos=min(99999,db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(m.COLLECTION,)).fetchone()['n'])
     # Bound duplicate checks to this batch's source IDs and creator/title pairs.
     native=collections.defaultdict(set)
     for e in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)",(list({r['scheme'] for r in batch}),[r['source_id'] for r in batch])):native[e['scheme'],e['external_id']].add(e['entity_id'])
     titles=collections.defaultdict(set)
     for c in db.execute("SELECT a.id::text,aa.artist_id::text,a.normalized_title FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.normalized_title=ANY(%s) AND a.status<>'archived'",(list({r['artist_id'] for r in batch}),list({m.norm(r['title']) for r in batch}))):titles[c['artist_id'],c['normalized_title']].add(c['id'])
     for r in batch:
      assert native[r['scheme'],r['source_id']]<={r['artwork_id']},'Concurrent native source identity'
      if r['action']=='create':
       allowed={rr['artwork_id'] for rr in data['rows'] if rr['artist_id']==r['artist_id'] and m.norm(rr['title'])==m.norm(r['title'])}
       assert titles[r['artist_id'],m.norm(r['title'])]<=allowed,'Concurrent title/version candidate'
     with db.pipeline():
      for r in batch:
       aid=r['artwork_id'];im=data['images'][aid];sid=source_id(r['provider']);date=r['date'];rc=r['receipt'];credit=r['creator_full_name']+'; reproduction via '+('SOVCOM' if r['provider']=='sovcom' else 'Kyiv collectors club Socrealizm')
       if r['action']=='create':
        db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,status,research_candidate,created_by,updated_by)
         VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)''',(aid,slug(r['title'],aid),r['title'],m.norm(r['title']),r.get('source_date_display') or date['date_display'],date['creation_year_start'],date['creation_year_end'],date['date_precision'],r['work_type'],r.get('medium_text'),r.get('dimensions_text'),ACTOR,ACTOR))
        db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(aid,r['artist_id'],'Native creator label: '+r['creator_label']+'. Source: '+r['source_url']))
       db.execute("INSERT INTO curated_collection_items(id,collection_id,artwork_id,position,reason,source_id,source_url,checked_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(collection_id,artwork_id) DO NOTHING",(m.uid('selection/'+aid),m.COLLECTION,aid,pos+1,'Personal editorial selection for the Soviet Realism survey: '+r['category']+', '+r['creator_full_name']+', '+date['date_display']+'. Selected for the breadth of Soviet realist themes and regional practice. Collector/auction provenance; no museum designation or current-display claim.',sid,r['source_url'],rc['retrieved_at']))
       db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id) VALUES(%s,'artwork',%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",(m.uid('work-native/'+r['provider']+'/'+r['source_id']),aid,r['scheme'],r['source_id'],r['source_url'],sid))
       note=dict(source_record=r,plan_sha256=pin,selection=data['selection'],movement_id=MOVEMENT,rights_approval=m.load(RUN/'authorization.json')['rights_approval'])
       db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'soviet_realism_source_identity',%s,%s,%s,%s,%s)",(m.uid('work-citation/'+r['provider']+'/'+r['source_id']),aid,sid,r['source_id'],r['source_url'],json.dumps(note,ensure_ascii=False),rc['retrieved_at'],ACTOR))
       db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
        VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)''',(im['media_id'],im['path'],r['source_url'],r['provider'],im['width'],im['height'],im['bytes'],im['sha256'],r['title']+' — '+r['creator_full_name'],r['rights_status'],r['source_rights_label'],r['source_url'],credit,credit+'. Full source frame, proportionally resized and JPEG compressed; no crop. Source rights: '+r['source_rights_label'],im['download']['at'],ACTOR))
       db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(im['media_id'],sid,r['source_id'],rc['sha256'],r['source_image_url'],'https://'+urlsplit(r['source_url']).netloc+'/',r['source_rights_label']+'; separate user approval for this selected Soviet Realism collection, 11 October 2026. No independent licence asserted.',OP,m.now(),Jsonb(dict(source_rights_label=r['source_rights_label'],user_approval=m.load(RUN/'authorization.json'),image=im,source_receipt=rc,plan_sha256=pin))))
       db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Full source reproduction')",(aid,im['media_id']))
       db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],aid))
    after=snapshot(db,ids)
    for r in batch:
     a=after[r['artwork_id']]['artwork'];assert a['primary_media_id']==data['images'][r['artwork_id']]['media_id']
     assert a['status']=='review' and a['published_at'] is None and a['current_institution_id'] is None
   m.save(dest,dict(at=m.now(),plan_sha256=pin,artwork_ids=ids,new_artworks=sum(r['action']=='create' for r in batch),images=len(batch)));print('COMMITTED',start+len(batch),'/',len(data['rows']),flush=True)

def primary_groups():
 data,pin=final_plan();ids=m.load(RUN/'applied-initialization.json')['new_artist_ids'];dest=RUN/'primary-movement-groups.json'
 if dest.exists():return
 with m.connect(True) as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='120s'")
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  artists=[dict(r) for r in db.execute("SELECT id::text,movement_review_state,status FROM artists WHERE id=ANY(%s::uuid[]) FOR UPDATE",(ids,))]
  links=[dict(r) for r in db.execute('SELECT artist_id::text,movement_id::text,role FROM artist_movements WHERE artist_id=ANY(%s::uuid[])',(ids,))]
  assert len(artists)==len(ids) and all(a['status']=='review' for a in artists)
  assert not any(l['role']=='primary' and l['movement_id']!=MOVEMENT for l in links),'A new artist acquired another primary movement'
  m.save(BACKUP/'primary-movement-preimages.json.gz',dict(artists=artists,links=links,plan_sha256=pin))
  db.execute("UPDATE artist_movements SET role='primary' WHERE movement_id=%s AND artist_id=ANY(%s::uuid[])",(MOVEMENT,ids))
  db.execute("UPDATE artists SET movement_review_state='classified',updated_by=%s WHERE id=ANY(%s::uuid[])",(ACTOR,ids))
  with db.pipeline():
   for aid in ids:
    db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artist',%s,%s,'primary_movement_editorial_group',%s,%s,now(),%s) ON CONFLICT(id) DO NOTHING",(m.uid('primary-movement/'+aid),aid,source_id('movement'),'https://www.wikiart.org/en/Artists-by-Art-Movement/socialist-realism','Primary catalogue grouping for this newly introduced artist in the broad Soviet Realism survey, based on the separately cited native creator profile, Soviet painting collection provenance and visually reviewed dated representational works. Editorial grouping includes related realist practice; it is not an exclusive classification of the entire career. Original source attribution and object-level evidence remain in their own citations. Plan '+pin,ACTOR))
 m.save(dest,dict(at=m.now(),plan_sha256=pin,primary_artist_ids=ids,existing_artist_primary_movements_changed=0))

def public_verify():
 data,pin=final_plan();base='https://artlines.org';used={r['artist_id'] for r in data['rows']};samples=[]
 for provider in ('sovcom','socrealizm'):
  rows=[r for r in data['rows'] if r['provider']==provider]
  samples.extend([rows[0],rows[len(rows)//2],rows[-1]])
 with m.connect() as db:
  slugs={r['id']:r['slug'] for r in db.execute('SELECT id::text,slug FROM artists WHERE id=ANY(%s::uuid[])',([r['artist_id'] for r in samples],))}
 facet_response=m.requests.get(base+'/api/backend/v1/timeline/facets',params=dict(popular='false'),timeout=30);facet_response.raise_for_status()
 facet=next(x for x in facet_response.json()['movements'] if x['slug']=='soviet-realism');assert facet['count']==len(used)
 directory=m.requests.get(base+'/api/backend/v1/artists',params=dict(movement='soviet-realism',limit=2),timeout=30);directory.raise_for_status();directory_data=directory.json();assert directory_data['total']==len(used) and len(directory_data['items'])==2
 checks=[]
 for r in samples:
  path='/api/backend/v1/artists/'+slugs[r['artist_id']]+'/works/'+r['artwork_id'];response=m.requests.get(base+path,timeout=30);response.raise_for_status();a=response.json();im=data['images'][r['artwork_id']]
  assert a['id']==r['artwork_id'] and a['title']==r['title'] and a['status']=='review' and a['media_url']==im['path']
  assert a['creation_year_start']==r['date']['creation_year_start'] and a['creation_year_end']==r['date']['creation_year_end'] and a['date_precision']==r['date']['date_precision']
  assert a['rights_status']==r['rights_status'] and a['source_page_url']==r['source_url'] and a['holding'] is None and a['display'] is None
  assert any(c['source_url']==r['source_url'] for c in a['citations'])
  checks.append(dict(artwork_id=r['artwork_id'],provider=r['provider'],url=base+path,status=response.status_code,review_status=a['status'],primary_image_verified=True,source_citation_verified=True))
  m.save(RUN/'public-samples'/(r['artwork_id']+'.json'),dict(url=base+path,at=m.now(),payload=a))
 page_url=base+'/artists?movement=soviet-realism';page=m.requests.get(page_url,timeout=45);page.raise_for_status();assert 'Soviet Realism' in page.text
 m.save(RUN/'public-verification.json',dict(at=m.now(),plan_sha256=pin,movement_facet=facet,directory_total=directory_data['total'],page_url=page_url,page_status=page.status_code,anonymous_artwork_checks=checks,all_image_checks='All 2500 public image URLs already fetched and SHA-256 verified; see uploads/.'))
 print('PUBLIC VERIFIED',len(used),'artists,',len(checks),'anonymous artwork pages, movement page and 2500 image receipts',flush=True)

def verify():
 data,pin=final_plan();ids=[r['artwork_id'] for r in data['rows']];errors=[]
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  states=snapshot(db,ids);media={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(m) v FROM media_assets m WHERE id=ANY(%s::uuid[])',([x['media_id'] for x in data['images'].values()],))}
  identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='soviet_realism_source_identity'",(ids,))]
  rights=[dict(x) for x in db.execute('SELECT media_id::text,source_checksum,source_image_url,rights_basis FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([x['media_id'] for x in data['images'].values()],))]
  links=[dict(x) for x in db.execute('SELECT artist_id::text,movement_id::text,role FROM artist_movements WHERE movement_id=%s',(MOVEMENT,))]
  new_artists=m.load(RUN/'applied-initialization.json')['new_artist_ids']
  assert {l['artist_id'] for l in links if l['role']=='primary'}==set(new_artists)
  eligibility=db.execute("SELECT count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)) n FROM artworks WHERE id=ANY(%s::uuid[])",(ids,)).fetchone()['n']
  movement=db.execute('SELECT to_jsonb(m) v FROM movements m WHERE id=%s',(MOVEMENT,)).fetchone()['v']
  for r in data['rows']:
   aid=r['artwork_id'];a=states[aid]['artwork'];im=data['images'][aid];med=media[im['media_id']]
   assert a['title']==r['title'] and a['creation_year_start']==r['date']['creation_year_start'] and a['creation_year_end']==r['date']['creation_year_end']
   assert a['status']=='review' and a['published_at'] is None and a['current_institution_id'] is None and a['primary_media_id']==im['media_id']
   assert any(c['artist_id']==r['artist_id'] for c in states[aid]['creators']) and any(c['artist_id']==r['artist_id'] for c in links)
   assert med['checksum_sha256']==im['sha256'] and med['byte_size']==im['bytes']<=100000 and med['rights_status']==r['rights_status']
   assert any(e['entity_id']==aid and e['scheme']==r['scheme'] and e['external_id']==r['source_id'] for e in identifiers)
   assert any(c['entity_id']==aid and c['source_url']==r['source_url'] for c in citations)
   assert any(e['media_id']==im['media_id'] and e['source_checksum']==r['receipt']['sha256'] and e['source_image_url']==r['source_image_url'] for e in rights)
  assert eligibility==len(ids)
 report=dict(at=m.now(),plan_sha256=pin,new_artworks=sum(r['action']=='create' for r in data['rows']),existing_enriched=sum(r['action']=='existing' for r in data['rows']),images=len(media),eligible_with_selection_evidence=eligibility,movement=movement,associated_artists=len({r['artist_id'] for r in data['rows']}),new_artists=len(new_artists),by_provider=dict(collections.Counter(r['provider'] for r in data['rows'])),errors=errors,local_database_connections=0,publication_changes=0,museum_or_display_claims=0)
 m.save(RUN/'production-verification.json',report);m.save(BACKUP/'verified-after.json.gz',dict(artworks=states,media=media,plan_sha256=pin));print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
