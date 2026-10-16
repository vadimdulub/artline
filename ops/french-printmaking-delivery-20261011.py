#!/usr/bin/env python3
"""Reconciled Yale French prints, authentic image preparation and atomic delivery."""
import base64,collections,concurrent.futures,csv,gzip,hashlib,importlib.util,io,json,re,subprocess,sys,time
from pathlib import Path
from PIL import Image,ImageOps,ImageStat,ImageDraw,ImageFont
from psycopg.types.json import Jsonb
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
s=importlib.util.spec_from_file_location('french',Path(__file__).with_name('french-printmaking-20261011.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
core=m.module('french_images','ops/enrich-artwork-images.py')
RUN=m.RUN;ROOT=m.ROOT;BACKUP=m.BACKUP;OP=m.OP;ACTOR=m.ACTOR;IID=m.IID
SID=m.uid('source/yale');COLLECTION=m.uid('collection/french-printmaking')
def slug(title,aid):return (re.sub('[^a-z0-9]+','-',m.norm(title)).strip('-')[:100] or 'french-print')+'-'+aid[:8]
def baseline():
 dest=RUN/'production-baseline.json.gz'
 if dest.exists():return m.load(dest)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  ids=[r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s',(IID,IID))]
  data=dict(at=m.now(),artworks=m.dbutil.snapshot(db,ids),identifiers=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))],
   artists=[dict(r) for r in db.execute('SELECT id::text,slug,display_name,normalized_name,birth_year,death_year,status FROM artists')],
   aliases=[dict(r) for r in db.execute('SELECT artist_id::text,alias FROM artist_aliases')],
   artist_identifiers=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist'")])
  m.save(RUN/'museum-query-plan.json',db.execute('EXPLAIN (FORMAT JSON) SELECT id FROM artworks WHERE current_institution_id=%s',(IID,)).fetchone())
 m.save(dest,data);m.save(BACKUP/'initial-scope.json.gz',data);return data
def profile(url):
 dest=RUN/'creators'/(url.rsplit('/',1)[1]+'.json.gz')
 if dest.exists():return m.load(dest)
 p,rc=m.getjson(url,'creator-captures');assert p['id']==url and p['type']=='Person'
 out=dict(raw=p,receipt=rc,url=url)
 m.save(dest,out);return out
def artist_decision(row,base):
 url=row['creator']['id'];dest=RUN/'artist-decisions'/(url.rsplit('/',1)[1]+'.json')
 if dest.exists():return m.load(dest)
 pr=profile(url);p=pr['raw'];names={m.norm(row['creator_label'])}|{m.norm(v['content']) for v in p.get('identified_by',[]) if v.get('type')=='Name'}
 candidates=set();ids={a['id']:a for a in base['artists']};byname=collections.defaultdict(set)
 for a in base['artists']:
  for name in (a['display_name'],a['normalized_name']):byname[m.norm(name)].add(a['id'])
 for a in base['aliases']:byname[m.norm(a['alias'])].add(a['artist_id'])
 source_ids={v['id'] for v in p.get('equivalent',[])};qids={u.rsplit('/',1)[1] for u in source_ids if re.match('https?://www.wikidata.org/entity/Q',u)}
 for e in base['artist_identifiers']:
  if e['canonical_url'] in source_ids or (e['scheme']=='wikidata' and e['external_id'] in qids) or e['canonical_url']==url:candidates.add(e['entity_id'])
 life=re.search(r'\(French, (\d{4})[–-](\d{4})\)$',row['source_creator_label']);birth=int(life[1]) if life else None;death=int(life[2]) if life else None
 bynames=set().union(*(byname[n] for n in names));reason=None;basis='Exact source authority and concordant native names/lifespan'
 if candidates:
  if len(candidates)!=1:reason='Multiple production authority matches'
  elif not candidates&bynames:reason='Authority requires cross-language/name reconciliation'
 else:
  candidates={aid for aid in bynames if birth is not None and death is not None and ids[aid]['birth_year']==birth and ids[aid]['death_year']==death}
  basis='Exact source name/alias and matching explicit lifespan'
  if not candidates and bynames:reason='Existing creator name requires authority/lifespan reconciliation'
  elif len(candidates)>1:reason='Multiple same-name/lifespan creators'
 aid=next(iter(candidates)) if len(candidates)==1 else None
 if aid and not reason:
  a=ids[aid]
  if a['status']=='archived':reason='Archived creator'
  elif (birth and a['birth_year'] and birth!=a['birth_year']) or (death and a['death_year'] and death!=a['death_year']):reason='Creator lifespan conflict'
 out=dict(url=url,profile_reference=str((RUN/'creators'/(url.rsplit('/',1)[1]+'.json.gz')).relative_to(ROOT)),profile_sha256=m.sha((RUN/'creators'/(url.rsplit('/',1)[1]+'.json.gz')).read_bytes()),name=row['creator_label'],birth_year=birth,death_year=death,source_label=row['source_creator_label'],qid=next(iter(qids)) if len(qids)==1 else None)
 if reason:out.update(action='hold',hold=reason)
 elif aid:out.update(action='existing',artist_id=aid,basis=basis,existing=ids[aid])
 else:
  out.update(action='create',artist_id=m.uid('artist/'+url),basis='Distinct native Yale/LUX artist authority; no matching production native authority, name or alias; explicit source name retained')
  # A compact biography range can encode activity dates. Only create life
  # dates when the structured authority explicitly supplies birth/death events.
  if not p.get('born'):out['birth_year']=None
  if not p.get('died'):out['death_year']=None
  if out['birth_year']!=birth or out['death_year']!=death:out['date_interpretation']='Source compact date label retained as evidence; professional activity is not inferred to be birth/death.'
 m.save(dest,out);return out
def stage():
 base=baseline();done={p.stem for p in (RUN/'identity-rows').glob('*.json')};rows=[];counts=collections.Counter()
 pending=[];creator_urls=set()
 for path in sorted((RUN/'objects').glob('*.json.gz')):
  row=m.load(path)
  if row['outcome']=='candidate' and row['native_id'] not in done:
   pending.append((path,row));url=row['creator']['id']
   if not (RUN/'creators'/(url.rsplit('/',1)[1]+'.json.gz')).exists():creator_urls.add(url)
 # Independent public creator profiles share capture()'s per-host throttle.
 # Only creators of already selected, source-eligible objects are prefetched.
 def fetch_creator(url):
  try:profile(url)
  except Exception as exc:print('CREATOR PROFILE DEFERRED',url,type(exc).__name__,flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(fetch_creator,sorted(creator_urls)))
 known_native=collections.defaultdict(set)
 for e in base['identifiers']:
  for url in [e.get('canonical_url') or '']:
   match=re.search(r'(?:/collections/objects/|/yuag/obj/|/lux/obj/)(\d+)',url)
   if match:known_native[match[1]].add(e['entity_id'])
  if 'yale' in e['scheme'] and e['external_id'].isdigit():known_native[e['external_id']].add(e['entity_id'])
 accession=collections.defaultdict(set)
 for aid,a in base['artworks'].items():
  if a['artwork'].get('accession_number'):accession[m.norm(a['artwork']['accession_number'])].add(aid)
 for path,row in pending:
  native=row['native_id'];out={k:v for k,v in row.items() if k not in ('raw','manifest','index')};reason=None
  existing=known_native[native]|accession[m.norm(row['accession_number'])]
  if existing:reason='Already present Yale native identity or accession; not a new artwork'
  elif re.search(r'\b(unknown|anonymous|unidentified|school|workshop)\b',row['creator_label'],re.I):reason='Unresolved creator label needs a separate attribution review'
  elif re.search(r'restrike|posthum|facsimile|reprint|later printing',row['title']+' '+(row.get('medium') or ''),re.I):reason='Later print/version wording requires physical-impression date review'
  else:
   ap=artist_decision(row,base)
   if ap['action']=='hold':reason=ap['hold']
   elif ap.get('birth_year') and row['date']['creation_year_end']<ap['birth_year']:reason='Source creation interval precedes the identified creator birth'
   else:out.update(artist_id=ap['artist_id'],artist_identity=ap,artwork_id=m.uid('artwork/yale/'+native),action='create')
  out.update(source_record_reference=str(path.relative_to(ROOT)),source_record_sha256=m.sha(path.read_bytes()),provider='yale',source_id=native,scheme='yale-object')
  if reason:out.update(action='hold',hold=reason)
  else:
   out['rights_status']='restricted' if 'United States' in row['rights_label'] else ('public_domain' if row['rights_label'].lower() in ('public domain','no copyright') else 'unknown')
   rows.append(out)
  m.save(RUN/'identity-rows'/(native+'.json'),out);done.add(native);counts[out['action']]+=1
 wave=len(list((RUN/'identity-waves').glob('*.json')))+1
 m.save(RUN/'identity-waves'/f'{wave:03}.json',dict(at=m.now(),rows=[r['native_id'] for r in rows],counts=dict(counts),baseline_sha256=m.sha((RUN/'production-baseline.json.gz').read_bytes())))
 print('STAGED',dict(counts),'total decisions',len(done),flush=True)
def identity_rows():return [x for p in sorted((RUN/'identity-rows').glob('*.json')) if (x:=m.load(p))['action']=='create']
def download(url):
 assert url.startswith('https://images.collections.yale.edu/iiif/2/yuag:')
 key=m.sha(url.encode());rp=RUN/'image-downloads'/(key+'.json');path=m.ORIGINALS/(key+'.body')
 if rp.exists():
  rc=m.load(rp);raw=path.read_bytes();assert m.sha(raw)==rc['sha256'];return raw,rc
 host='images.collections.yale.edu';hold=RUN/'access-holds'/(host+'.json')
 with m.LOCKS[host]:
  if hold.exists():raise RuntimeError('Image provider access held')
  time.sleep(max(0,m.NEXT[host]-time.monotonic()));m.NEXT[host]=time.monotonic()+.5
 with m.requests.get(url,headers={'User-Agent':'ArtlineCatalogueResearch/1.0 (selected French printmaking survey)'},timeout=(15,60),stream=True) as response:
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
def prepare_one(row):
 dest=RUN/'prepared-images'/(row['artwork_id']+'.json')
 if dest.exists():return m.load(dest)
 out=dict(artwork_id=row['artwork_id'],artist_id=row['artist_id'],title=row['title'],creator=row['creator_label'],source_image_url=row['image_url'],provider='yale',outcome='held',native_id=row['native_id'])
 try:
  original,rc=download(row['image_url']);raw,w,h,quality=core.compress(original)
  with Image.open(io.BytesIO(original)) as im:ow,oh=ImageOps.exif_transpose(im).size
  assert min(w,h)>=100 and max(w,h)>=300 and abs(w/h-ow/oh)<.025
  with Image.open(io.BytesIO(raw)) as im:
   im.load();gray=im.convert('L').resize((17,16));pix=list(gray.getdata());bits=''.join('1' if pix[y*17+x]>pix[y*17+x+1] else '0' for y in range(16) for x in range(16));dhash=hex(int(bits,2))[2:].zfill(64);assert ImageStat.Stat(im.convert('L')).stddev[0]>2
  digest=m.sha(raw);urlpath='/assets/artworks/imported/'+OP+'/'+row['artwork_id']+'-'+digest[:16]+'.jpg';local=ROOT/'apps/web/public'/urlpath.lstrip('/');m.save(local,raw)
  out.update(outcome='prepared',path=urlpath,local_path=str(local),width=w,height=h,bytes=len(raw),sha256=digest,quality=quality,dhash=dhash,original_dimensions=[ow,oh],download=rc,media_id=m.uid('media/'+row['artwork_id']+'/'+digest))
 except Exception as exc:out['error']=(type(exc).__name__+': '+str(exc))[:400]
 m.save(dest,out);return out
def prepare():
 rows=identity_rows();counts=collections.Counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for n,r in enumerate(pool.map(prepare_one,rows),1):
   counts[r['outcome']]+=1
   if n%50==0:print('IMAGES',n,len(rows),dict(counts),flush=True)
 print('IMAGE PREPARATION',dict(counts),flush=True)

def cycle():
 # Research and image preparation overlap, but each individual image is selected
 # only after its own source, date, creator and production identity checks.
 for iteration in range(200):
  complete=(RUN/'objects-summary.json').exists() and (not (RUN/'extension-index-seed.json').exists() or ((RUN/'extension-summary.json').exists() and (RUN/'date-review-summary.json').exists()))
  stage();prepare();sheets()
  if complete:break
  time.sleep(30)

def sheets():
 old=list((RUN/'visual-sheets').glob('*.json'));indexed={im['artwork_id'] for path in old for im in m.load(path)['images']}
 ims=[x for p in sorted((RUN/'prepared-images').glob('*.json')) if (x:=m.load(p))['outcome']=='prepared' and x['artwork_id'] not in indexed]
 folder=m.ORIGINALS/'contact-sheets';folder.mkdir(parents=True,exist_ok=True);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
 for start in range(0,len(ims),30):
  group=ims[start:start+30];canvas=Image.new('RGB',(1600,1800),'#eeeae4');draw=ImageDraw.Draw(canvas)
  for i,im in enumerate(group):
   x=(i%5)*320;y=(i//5)*300
   with Image.open(im['local_path']) as pic:
    pic.thumbnail((306,250));canvas.paste(pic,(x+(320-pic.width)//2,y+(250-pic.height)//2))
   draw.text((x+5,y+253),str(i+1)+' / '+im['native_id']+' / '+im['title'][:29],font=font,fill='black');draw.text((x+5,y+274),im['creator'][:37],font=font,fill='black')
  name=f'{len(old)+start//30+1:03d}';path=folder/(name+'.jpg');canvas.save(path,quality=90)
  m.save(RUN/'visual-sheets'/(name+'.json'),dict(sheet=str(path),images=[dict(artwork_id=im['artwork_id'],sha256=im['sha256'],title=im['title'],creator=im['creator'],native_id=im['native_id']) for im in group]))
 print('VISUAL SHEETS',len(ims),'new images',flush=True)

def audit(required_reports=('objects-summary.json','extension-summary.json','date-review-summary.json','transport-review-summary.json')):
 assert all((RUN/name).exists() for name in required_reports),'Finish bounded source passes before final audit'
 assert all((RUN/'prepared-images'/(r['artwork_id']+'.json')).exists() for r in identity_rows()),'Finish image preparation before final audit'
 rows=identity_rows();byid={r['artwork_id']:r for r in rows};ready=[x for p in (RUN/'prepared-images').glob('*.json') if (x:=m.load(p))['outcome']=='prepared'];held={};groups=[];byartist=collections.defaultdict(list);bysha=collections.defaultdict(list)
 for im in ready:byartist[im['artist_id']].append(im);bysha[im['download']['sha256']].append(im)
 byaccession=collections.defaultdict(list)
 for r in rows:byaccession[m.norm(r['accession_number'])].append(r)
 for r in rows:
  if re.search(r'restrike|posthum|facsimile|reprint|later printing',r['title']+' '+(r.get('medium') or ''),re.I):held[r['artwork_id']]='Later print/version wording requires physical-impression date review; original design dates alone are insufficient'
 for group in byaccession.values():
  if len(group)>1:
   groups.append(dict(type='repeated-native-accession',artwork_ids=[r['artwork_id'] for r in group]))
   for r in group:held[r['artwork_id']]='Multiple native objects share the same accession; component/physical identity requires review'
 for group in bysha.values():
  if len(group)>1:
   groups.append(dict(type='identical-reproduction',artwork_ids=[im['artwork_id'] for im in group]))
   for im in group:held[im['artwork_id']]='Identical source image serves multiple native objects; separate impression/view reconciliation needed'
 for group in byartist.values():
  for i,a in enumerate(group):
   for b in group[i+1:]:
    distance=(int(a['dhash'],16)^int(b['dhash'],16)).bit_count()
    if distance<=8:
     groups.append(dict(type='near-identical-reproduction',artwork_ids=[a['artwork_id'],b['artwork_id']],distance=distance))
     for im in [a,b]:held[im['artwork_id']]='Near-identical reproduction; impression/state/composition review pending'
 with m.connect() as db:
  native_matches=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",([r['source_url'] for r in rows]+[r['receipt']['url'] for r in rows],))]
  byurl={url:r['artwork_id'] for r in rows for url in (r['source_url'],r['receipt']['url'])}
  for e in native_matches:held[byurl[e['canonical_url']]]='Existing catalogue identifier references the exact Yale/LUX object page, independently of its assigned holding'
  old=[dict(r) for r in db.execute('''SELECT aa.artist_id::text,a.id::text artwork_id,a.current_institution_id::text,a.accession_number,m.storage_path,m.checksum_sha256
   FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id JOIN media_assets m ON m.id=a.primary_media_id
   WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' ''',(list(byartist),))]
 matches=[];missing=[];checked=0
 for oldim in old:
  if not oldim.get('storage_path'):missing.append(dict(oldim,gap='Existing remote image has no local file'));continue
  p=ROOT/'apps/web/public'/oldim['storage_path'].lstrip('/')
  if not p.exists():missing.append(oldim);continue
  raw=p.read_bytes()
  if oldim['checksum_sha256']:assert m.sha(raw)==oldim['checksum_sha256']
  with Image.open(io.BytesIO(raw)) as im:
   gray=ImageOps.exif_transpose(im).convert('L').resize((17,16));pix=list(gray.getdata());dh=int(''.join('1' if pix[y*17+x]>pix[y*17+x+1] else '0' for y in range(16) for x in range(16)),2)
  checked+=1
  for candidate in byartist[oldim['artist_id']]:
   distance=(dh^int(candidate['dhash'],16)).bit_count()
   if distance<=8:
    matches.append(dict(existing=oldim,candidate=candidate['artwork_id'],distance=distance));held[candidate['artwork_id']]='Near-identical existing catalogue image; source impression/composition reconciliation pending'
 m.save(RUN/'image-audit.json',dict(at=m.now(),prepared=len(ready),groups=groups,existing_native_page_matches=native_matches,existing_image_checks=checked,existing_local_image_gaps=missing,existing_matches=matches,held_artwork_ids=held))
 print('AUDITED',len(ready),'images,',checked,'existing images,',len(held),'holds',flush=True)

def freeze():
 rows=identity_rows();held=dict(m.load(RUN/'image-audit.json')['held_artwork_ids']);approved=set()
 for path in (RUN/'visual-decisions').glob('*.json'):
  d=m.load(path);sheet=m.load(RUN/'visual-sheets'/path.name);assert d['sheet_sha256']==m.sha(Path(sheet['sheet']).read_bytes())
  assert set(d['approved'])|set(d['held'])=={x['artwork_id'] for x in sheet['images']} and not set(d['approved'])&set(d['held'])
  approved.update(d['approved']);held.update(d['held'])
 for path in (RUN/'cross-sheet-review').glob('*.json'):held.update(m.load(path)['held'])
 ready=[];images={};gaps={}
 for r in rows:
  aid=r['artwork_id'];p=RUN/'prepared-images'/(aid+'.json')
  if aid in held:continue
  if not p.exists():gaps[aid]='No prepared image';continue
  im=m.load(p)
  if im['outcome']!='prepared':gaps[aid]=im.get('error') or 'Source image failed preparation quality validation; see image-quality-followup.json';continue
  assert aid in approved,'Image awaits actual visual review'
  assert m.sha(Path(im['local_path']).read_bytes())==im['sha256'] and im['bytes']<=100000
  source=ROOT/r['source_record_reference'];assert m.sha(source.read_bytes())==r['source_record_sha256']
  native=m.load(source)
  for key,receipt_key in [('raw','receipt'),('manifest','manifest_receipt')]:
   rc=native[receipt_key];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert m.sha(raw)==rc['sha256'] and json.loads(raw)==native[key] and rc['status']==200
  assert native['manifest']['id']==r['manifest_receipt']['url'] and r['manifest_receipt']['url'].endswith('/'+r['native_id'])
  assert any(x['id']==r['source_url'] for x in native['manifest'].get('homepage',[]))
  assert r['date']['creation_year_end']>=r['artist_identity'].get('birth_year',0) if r['artist_identity'].get('birth_year') else True
  ready.append(r);images[aid]=im
 queues=collections.defaultdict(list)
 for r in ready:queues[r['artist_id']].append(r)
 for group in queues.values():group.sort(key=lambda r:(r['date']['creation_year_start'],int(r['native_id'])))
 chosen=[]
 while any(queues.values()) and len(chosen)<3000:
  for key in sorted(queues):
   if queues[key] and len(chosen)<3000:chosen.append(queues[key].pop(0))
 assert len(chosen)>=2500,'Continue research to a comparable 2500-work illustrated delivery'
 data=dict(at=m.now(),rows=chosen,images={r['artwork_id']:images[r['artwork_id']] for r in chosen},held=held,image_gaps=gaps,
  authorization_sha256=m.sha((RUN/'authorization.json').read_bytes()),baseline_sha256=m.sha((RUN/'production-baseline.json.gz').read_bytes()),
  selection='French printmaking, 1800–1970: a personal editorial survey of distinct, individually accessioned Yale museum prints, beginning with nineteenth-century prints and extending into the twentieth century. Includes individual impressions/states; does not assert a new movement, museum masterpiece designation or current display.',
  eligible_reserve=[r['artwork_id'] for r in ready if r['artwork_id'] not in {x['artwork_id'] for x in chosen}])
 m.save(RUN/'delivery-plan.json.gz',data);pin=m.sha((RUN/'delivery-plan.json.gz').read_bytes());m.save(RUN/'delivery-plan-pin.json',dict(sha256=pin))
 m.save(BACKUP/'delivery-preimages.json.gz',dict(plan_sha256=pin,artworks={},artists={r['artist_id']:r['artist_identity'].get('existing') for r in chosen}))
 print('FROZEN',len(chosen),'new artworks and images;',len({r['artist_id'] for r in chosen}),'artists',flush=True)

def final_plan():
 path=RUN/'delivery-plan.json.gz';pin=m.load(RUN/'delivery-plan-pin.json')['sha256'];assert m.sha(path.read_bytes())==pin
 d=m.load(path);assert d['authorization_sha256']==m.sha((RUN/'authorization.json').read_bytes());return d,pin

def backup():
 rows=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--limit=100','--format=json'],text=True))
 b=next(x for x in rows if x.get('description')=='Before French printmaking catalogue 20261011');assert b['status']=='SUCCESSFUL'
 m.save(BACKUP/'cloud-backup.json',b);m.save(RUN/'cloud-backup.json',b);print('BACKUP',b['id'],b['status'],flush=True)

def upload():
 data,pin=final_plan();credentials=core.GcloudCredentials();credentials.refresh(None)
 bucket=storage.Client(project='artline-508319',credentials=credentials).bucket('artline-508319-images')
 def one(im):
  path=RUN/'uploads'/(im['artwork_id']+'.json')
  if path.exists():
   rc=m.load(path);assert rc['plan_sha256']==pin and rc['sha256']==im['sha256'];return
  raw=Path(im['local_path']).read_bytes();assert m.sha(raw)==im['sha256'];blob=bucket.blob(im['path'].lstrip('/'))
  blob.metadata={'sha256':im['sha256'],'operation':OP,'artwork-id':im['artwork_id'],'provider':'yale'};blob.cache_control='public,max-age=31536000,immutable'
  try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
  except PreconditionFailed:blob.reload(timeout=30)
  assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
  response=m.requests.get('https://artlines.org'+im['path'],timeout=(15,45));response.raise_for_status();assert m.sha(response.content)==im['sha256']
  m.save(path,dict(at=m.now(),artwork_id=im['artwork_id'],plan_sha256=pin,sha256=im['sha256'],generation=blob.generation,bytes=len(raw),public_http_status=response.status_code,public_bytes_verified=True))
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
  for n,_ in enumerate(pool.map(one,data['images'].values()),1):
   if n%100==0:print('UPLOADED AND VERIFIED',n,len(data['images']),flush=True)

def initialize(db,data,pin):
 dest=RUN/'applied-initialization.json'
 if dest.exists():assert m.load(dest)['plan_sha256']==pin;return
 aps={r['artist_id']:r['artist_identity'] for r in data['rows']};new=[aid for aid,ap in aps.items() if ap['action']=='create']
 with db.transaction():
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  institution=db.execute('SELECT id,name,status FROM institutions WHERE id=%s',(IID,)).fetchone();assert institution and institution['status']!='archived'
  prior_collection=db.execute("SELECT id::text FROM curated_collections WHERE institution_id=%s AND curator_kind='owner'",(IID,)).fetchone();assert prior_collection is None or prior_collection['id']==COLLECTION,'Concurrent personal Yale selection; reconcile before writing'
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key,priority) VALUES(%s,%s,'Yale University Art Gallery — LUX records and IIIF image manifests','museum_api','https://lux.collections.yale.edu/',%s,10) ON CONFLICT(id) DO NOTHING",(SID,OP+'-yale',OP))
  db.execute("INSERT INTO curated_collections(id,institution_id,curator_kind,title,status) VALUES(%s,%s,'owner','French printmaking, 1800–1970','review') ON CONFLICT(id) DO NOTHING",(COLLECTION,IID))
  actual={r['id']:dict(r) for r in db.execute('SELECT id::text,display_name,birth_year,death_year,status FROM artists WHERE id=ANY(%s::uuid[]) FOR SHARE',(list(aps),))}
  collisions=collections.defaultdict(set)
  for r in db.execute("SELECT id::text,normalized_name FROM artists WHERE normalized_name=ANY(%s) AND status<>'archived'",([m.norm(ap['name']) for ap in aps.values() if ap['action']=='create'],)):collisions[r['normalized_name']].add(r['id'])
  with db.pipeline():
   for aid,ap in aps.items():
    if ap['action']=='existing':
     expected=ap['existing'];a=actual.get(aid);assert a and a['status']!='archived'
     assert all(a[k]==expected[k] for k in ('display_name','birth_year','death_year')),'Concurrent creator identity change'
    else:
     assert collisions[m.norm(ap['name'])]<={aid},'Concurrent new creator name'
     if aid in actual:assert actual[aid]['display_name']==ap['name']
     else:
      works=[r for r in data['rows'] if r['artist_id']==aid];lo=min(r['date']['creation_year_start'] for r in works);hi=max(r['date']['creation_year_end'] for r in works)
      birth=ap.get('birth_year');death=ap.get('death_year');basis='life' if birth and death else 'estimated';first=birth if birth and death else lo;last=death if birth and death else hi;label=f'{birth}–{death}' if basis=='life' else f'Documented selected works {lo}–{hi}; lifespan incomplete'
      db.execute('''INSERT INTO artists(id,slug,display_name,sort_name,normalized_name,birth_year,death_year,birth_display,death_display,birth_precision,death_precision,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status,created_by,updated_by)
       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',%s,%s)''',(aid,slug(ap['name'],aid),ap['name'],ap['name'],m.norm(ap['name']),birth,death,str(birth) if birth else None,str(death) if death else None,'exact' if birth else None,'exact' if death else None,first,last,label,basis,ACTOR,ACTOR))
    pr=m.load(ROOT/ap['profile_reference']);assert m.sha((ROOT/ap['profile_reference']).read_bytes())==ap['profile_sha256']
    db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id) VALUES(%s,'artist',%s,'yale-lux-person',%s,%s,%s) ON CONFLICT(id) DO NOTHING",(m.uid('artist-native/'+ap['url']),aid,ap['url'].rsplit('/',1)[1],ap['url'],SID))
    db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artist',%s,%s,'french_printmaking_creator_identity',%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",(m.uid('artist-citation/'+ap['url']),aid,SID,ap['url'],json.dumps(dict(identity=ap,native_profile=pr['raw'],source_receipt=pr['receipt'],plan_sha256=pin),ensure_ascii=False),pr['receipt']['retrieved_at'],ACTOR))
 m.save(dest,dict(at=m.now(),plan_sha256=pin,source_id=SID,collection_id=COLLECTION,new_artist_ids=new,existing_artist_ids=[aid for aid in aps if aid not in new],movement_changes=0))

def apply():
 data,pin=final_plan();assert m.load(BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
 for aid,im in data['images'].items():
  u=m.load(RUN/'uploads'/(aid+'.json'));assert u['plan_sha256']==pin and u['sha256']==im['sha256'] and u['public_bytes_verified']
 with m.connect(True) as db:
  initialize(db,data,pin)
  for start in range(0,len(data['rows']),50):
   batch=data['rows'][start:start+50];ids=[r['artwork_id'] for r in batch];dest=RUN/'applied-batches'/f'{start//50:03}.json'
   if dest.exists():assert m.load(dest)['plan_sha256']==pin;continue
   with db.transaction():
    db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
    before=m.dbutil.snapshot(db,ids);prior=db.execute('SELECT id FROM citations WHERE id=ANY(%s::uuid[])',([m.uid('work-citation/'+r['native_id']) for r in batch],)).fetchall()
    if prior:assert len(prior)==len(batch) and set(before)==set(ids),'Partially committed batch'
    else:
     assert not before,'Planned new IDs already exist without this operation receipt'
     native=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)",(['yale-object','museum-expansion-yale-object','yale-lux-object'],[r['native_id'] for r in batch]+[r['receipt']['url'].rsplit('/',1)[1] for r in batch]))]
     assert not native,'Concurrent native Yale object identity; reconcile before insertion'
     accessions=db.execute("SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s) AND status<>'archived'",(IID,[r['accession_number'] for r in batch])).fetchall();assert not accessions,'Concurrent Yale accession identity'
     preimage_path=BACKUP/'batch-preimages'/f'{start//50:03}.json.gz'
     if preimage_path.exists():
      prior_preimage=m.load(preimage_path);assert prior_preimage['plan_sha256']==pin and prior_preimage['artworks']==before and prior_preimage['native_identity_conflicts']==native
     else:m.save(preimage_path,dict(at=m.now(),plan_sha256=pin,artworks=before,native_identity_conflicts=native))
     with db.pipeline():
      for n,r in enumerate(batch,start+1+data.get('position_offset',0)):
       aid=r['artwork_id'];im=data['images'][aid];date=r['date'];rc=r['receipt'];mf=r['manifest_receipt'];credit=r['creator_label']+'; Yale University Art Gallery; '+r['credit_line'];roles='; '.join(r.get('all_creator_labels',[r['source_creator_label']]))
       db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,cultural_context,status,research_candidate,created_by,updated_by)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'print',%s,%s,%s,%s,'review',true,%s,%s)''',(aid,slug(r['title'],aid),r['title'],m.norm(r['title']),date['date_display'],date['creation_year_start'],date['creation_year_end'],date['date_precision'],r.get('medium'),r.get('dimensions_text'),r['accession_number'],'Nineteenth-century French printmaking' if date['creation_year_end']<=1900 else 'French printmaking through 1970',ACTOR,ACTOR))
       db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(aid,r['artist_id'],'Museum roles retained: '+roles+'. Primary link identifies the print artist, separately from printer, publisher and after/influence roles. Source: '+r['source_url']))
       db.execute("INSERT INTO curated_collection_items(id,collection_id,artwork_id,position,reason,source_id,source_url,checked_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(m.uid('selection/'+aid),COLLECTION,aid,n,'Personal editorial selection for French printmaking, 1800–1970: '+r['creator_label']+', '+date['date_display']+'. Exact Yale accession '+r['accession_number']+'; distinct physical print/impression, source frame preserved. This is not a museum masterpiece designation.',SID,r['source_url'],rc['retrieved_at']))
       for scheme,value,url in [('yale-object',r['native_id'],r['source_url']),('yale-lux-object',rc['url'].rsplit('/',1)[1],rc['url'])]:
        db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id) VALUES(%s,'artwork',%s,%s,%s,%s,%s)",(m.uid('work-native/'+scheme+'/'+value),aid,scheme,value,url,SID))
       db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'french_printmaking_source_identity',%s,%s,%s,%s,%s)",(m.uid('work-citation/'+r['native_id']),aid,SID,r['native_id'],r['source_url'],json.dumps(dict(source_record=r,selection=data['selection'],plan_sha256=pin,authorization=m.load(RUN/'authorization.json')),ensure_ascii=False),rc['retrieved_at'],ACTOR))
       db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(m.uid('holding/'+aid),aid,IID,SID,r['source_url'],json.dumps(dict(confidence=.99,basis='Concordant native owner/collection and official IIIF manifest institution, exact native ID and accession, explicit museum gift/acquisition credit without current-loan wording.',accession_number=r['accession_number'],source_checksum=rc['sha256'],manifest_checksum=mf['sha256'],scope='Documented holding only, not current display'),ensure_ascii=False),rc['retrieved_at']))
       db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
        VALUES(%s,'local',%s,%s,'Yale University Art Gallery','image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)''',(im['media_id'],im['path'],r['source_url'],im['width'],im['height'],im['bytes'],im['sha256'],r['title']+' — '+r['creator_label'],r['rights_status'],r['rights_label'],mf['url'],credit,credit+'. Full source frame, proportionally resized and JPEG compressed; no crop. Actual image rights: '+r['rights_label']+'. Object copyright statement: '+r['copyright_statement'],im['download']['at'],ACTOR))
       db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(im['media_id'],SID,r['native_id'],mf['sha256'],r['image_url'],mf['url'],r['rights_label']+'; separate user approval to continue selected topic/image delivery, 11 October 2026. Manifest metadata CC0 is not asserted as the image licence.',OP,m.now(),Jsonb(dict(source_rights_label=r['rights_label'],object_copyright_statement=r['copyright_statement'],native_image_url=r['native_image_url'],canvas_id=r['canvas_id'],manifest_receipt=mf,user_approval=m.load(RUN/'authorization.json'),image=im,plan_sha256=pin))))
       db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Full source print reproduction')",(aid,im['media_id']))
       db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],aid))
    after=m.dbutil.snapshot(db,ids)
    for r in batch:
     a=after[r['artwork_id']]['artwork'];assert a['primary_media_id']==data['images'][r['artwork_id']]['media_id'] and a['status']=='review' and a['published_at'] is None and a['current_institution_id']==IID
   m.save(dest,dict(at=m.now(),plan_sha256=pin,artwork_ids=ids,new_artworks=len(batch),images=len(batch)));print('COMMITTED',start+len(batch),len(data['rows']),flush=True)

def verify():
 data,pin=final_plan();ids=[r['artwork_id'] for r in data['rows']];init=m.load(RUN/'applied-initialization.json')
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  states=m.dbutil.snapshot(db,ids);media={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(m) v FROM media_assets m WHERE id=ANY(%s::uuid[])',([im['media_id'] for im in data['images'].values()],))}
  native=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  citations=[dict(r) for r in db.execute("SELECT entity_id::text,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
  rights=[dict(r) for r in db.execute('SELECT media_id::text,source_checksum,source_image_url FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([im['media_id'] for im in data['images'].values()],))]
  scope_rows=[dict(r) for r in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,artline_has_selection_evidence(id) evidence FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))]
  boundary_path=RUN/'boundary-date-review.json';expected_review=set(m.load(boundary_path)['review_artwork_ids']) if boundary_path.exists() else set()
  assert all(r['evidence'] and r['scope'] in ('eligible','review') for r in scope_rows)
  assert {r['id'] for r in scope_rows if r['scope']=='review'}==expected_review
  eligible=sum(r['scope']=='eligible' for r in scope_rows)
  for r in data['rows']:
   aid=r['artwork_id'];state=states[aid];a=state['artwork'];im=data['images'][aid];med=media[im['media_id']]
   assert all(a[k]==r['date'][k] for k in ('creation_year_start','creation_year_end','date_precision','date_display'))
   assert a['title']==r['title'] and a['accession_number']==r['accession_number'] and a['status']=='review' and a['published_at'] is None and a['current_institution_id']==IID and a['primary_media_id']==im['media_id']
   assert len(state['creators'])==1 and state['creators'][0]['artist_id']==r['artist_id']
   assert len(state['holdings'])==1 and state['holdings'][0]['claim_type']=='holding' and state['holdings'][0]['review_state']=='accepted'
   assert med['checksum_sha256']==im['sha256'] and med['byte_size']==im['bytes']<=100000 and med['rights_status']==r['rights_status'] and med['license_label']==r['rights_label']
   assert any(e['entity_id']==aid and e['scheme']=='yale-object' and e['external_id']==r['native_id'] for e in native)
   assert any(c['entity_id']==aid and c['source_url']==r['source_url'] for c in citations)
   assert any(e['media_id']==im['media_id'] and e['source_checksum']==r['manifest_receipt']['sha256'] and e['source_image_url']==r['image_url'] for e in rights)
  collection=db.execute('SELECT to_jsonb(c) v FROM curated_collections c WHERE id=%s',(COLLECTION,)).fetchone()['v']
  selected={r['artwork_id'] for r in db.execute('SELECT artwork_id::text FROM curated_collection_items WHERE collection_id=%s',(COLLECTION,))};assert selected==set(data.get('collection_expected_ids',ids))
  creator_plans={r['artist_id']:r['artist_identity'] for r in data['rows']}
  creator_states={r['id']:dict(r) for r in db.execute('SELECT id::text,display_name,birth_year,death_year,status FROM artists WHERE id=ANY(%s::uuid[])',(list(creator_plans),))};assert set(creator_states)==set(creator_plans)
  for aid,ap in creator_plans.items():
   a=creator_states[aid]
   if ap['action']=='create':assert a['display_name']==ap['name'] and a['birth_year']==ap.get('birth_year') and a['death_year']==ap.get('death_year') and a['status']=='review'
   else:assert all(a[k]==ap['existing'][k] for k in ('display_name','birth_year','death_year','status'))
 report=dict(at=m.now(),plan_sha256=pin,new_artworks=len(ids),images=len(media),eligible_with_selection_evidence=eligible,creation_scope_review_ids=sorted(expected_review),artists=len(creator_states),new_artists=len(init['new_artist_ids']),museum='Yale University Art Gallery',holding_assertions=len(ids),collection=collection,collection_items_verified=len(selected),artist_identities_verified=len(creator_states),date_min=min(r['date']['creation_year_start'] for r in data['rows']),date_max=max(r['date']['creation_year_end'] for r in data['rows']),date_precisions=dict(collections.Counter(r['date']['date_precision'] for r in data['rows'])),image_bytes=sum(im['bytes'] for im in data['images'].values()),errors=[],local_database_connections=0,publication_changes=0,current_display_claims=0,movement_changes=0)
 m.save(RUN/'production-verification.json',report);m.save(BACKUP/'verified-after.json.gz',dict(artworks=states,media=media,plan_sha256=pin));print(json.dumps(report,ensure_ascii=False),flush=True)

def public_verify():
 data,pin=final_plan();samples=[data['rows'][i] for i in sorted({min(2,len(data['rows'])-1),0,min(1,len(data['rows'])-1),len(data['rows'])//3,len(data['rows'])//2,2*len(data['rows'])//3,len(data['rows'])-1})]
 with m.connect() as db:slugs={r['id']:r['slug'] for r in db.execute('SELECT id::text,slug FROM artists WHERE id=ANY(%s::uuid[])',([r['artist_id'] for r in samples],))}
 checks=[]
 for r in samples:
  url='https://artlines.org/api/backend/v1/artists/'+slugs[r['artist_id']]+'/works/'+r['artwork_id'];response=m.requests.get(url,timeout=45);response.raise_for_status();a=response.json();im=data['images'][r['artwork_id']]
  assert a['id']==r['artwork_id'] and a['title']==r['title'] and a['status']=='review' and a['media_url']==im['path'] and a['display'] is None
  assert a['creation_year_start']==r['date']['creation_year_start'] and a['creation_year_end']==r['date']['creation_year_end'] and a['rights_status']==r['rights_status'] and a['source_page_url']==r['source_url']
  assert a['holding'] and 'Yale' in json.dumps(a['holding'])
  assert any(c['source_url']==r['source_url'] for c in a['citations'])
  listing=m.requests.get(url.rsplit('/',1)[0],params={'q':r['accession_number'],'limit':3,'work_type':'print','image_only':'true'},timeout=45);listing.raise_for_status();page=listing.json()
  assert any(item['id']==r['artwork_id'] and item['media_url']==im['path'] for item in page['items']),'Selected review artwork absent from public artist browsing'
  checks.append(dict(artwork_id=r['artwork_id'],url=url,status=response.status_code,source_citation_verified=True,holding_verified=True,display_claim=False,listing_url=listing.url,listing_status=listing.status_code,public_browsing_verified=True))
  path=RUN/'public-samples'/(r['artwork_id']+'.json')
  if not path.exists():m.save(path,dict(at=m.now(),url=url,payload=a,listing_url=listing.url,listing_payload=page))
 m.save(RUN/'public-verification.json',dict(at=m.now(),plan_sha256=pin,anonymous_artwork_checks=checks,all_public_images_verified=len(data['images'])));print('PUBLIC VERIFIED',len(checks),'anonymous artwork samples and',len(data['images']),'image receipts',flush=True)

def manifest():
 data,pin=final_plan();dest=RUN/'delivery-manifest.csv';fields=['artwork_id','native_id','accession_number','title','creator','date_display','creation_year_start','creation_year_end','date_precision','medium','source_url','image_url','public_image_url','sha256','bytes','rights_label','plan_sha256'];out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=fields);w.writeheader()
 for r in data['rows']:
  im=data['images'][r['artwork_id']];w.writerow(dict(artwork_id=r['artwork_id'],native_id=r['native_id'],accession_number=r['accession_number'],title=r['title'],creator=r['creator_label'],**r['date'],medium=r.get('medium'),source_url=r['source_url'],image_url=r['image_url'],public_image_url='https://artlines.org'+im['path'],sha256=im['sha256'],bytes=im['bytes'],rights_label=r['rights_label'],plan_sha256=pin))
 m.save(dest,out.getvalue().encode('utf-8-sig'));print('MANIFEST',len(data['rows']),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
