#!/usr/bin/env python3
"""Selected nineteenth-century French prints: public Yale evidence, production only."""
import collections,concurrent.futures,datetime,gzip,hashlib,importlib.util,json,re,sys,threading,time,unicodedata,uuid
from pathlib import Path
from urllib.parse import urlsplit
import requests

ROOT=Path(__file__).resolve().parents[1];OP='french-printmaking-20261011';RUN=ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
ACTOR='local-european-research';IID='127cc862-91c7-5c9b-af5e-03bfdfe33859'
GALLERY='https://lux.collections.yale.edu/data/group/41310ca5-8137-45fe-ac2c-a6a04e2235f1'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
dbutil=module('french_db','ops/india-300-delivery-20261011.py')
def connect(write=False):return dbutil.connect(write)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+key))
def norm(s):return ' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',str(s or '')).casefold() if not unicodedata.combining(c))))
def load(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(p,v):
 b=v if isinstance(v,bytes) else json.dumps(v,ensure_ascii=False,indent=2,default=str).encode()
 if p.suffix=='.gz':b=gzip.compress(b,mtime=0)
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,'Immutable evidence differs: '+str(p)
 else:p.write_bytes(b)
LOCKS=collections.defaultdict(threading.Lock);NEXT=collections.defaultdict(float);SESSIONS=threading.local()
def capture(url,kind='captures'):
 key=sha(url.encode());rp=RUN/kind/(key+'.json');bp=RUN/kind/(key+'.body.gz')
 if rp.exists():
  rc=load(rp);raw=gzip.decompress(bp.read_bytes());assert sha(raw)==rc['sha256']
  if rc['status']==200:return raw,rc
  if rc['status'] in (500,502,503,504) and kind.count('-retry')<2:return capture(url,kind+'-retry')
  raise RuntimeError('Captured provider HTTP '+str(rc['status'])+': '+url)
 host=urlsplit(url).hostname;hold=RUN/'access-holds'/(host+'.json')
 with LOCKS[host]:
  if hold.exists():raise RuntimeError('Provider access held: '+host)
  time.sleep(max(0,NEXT[host]-time.monotonic()));NEXT[host]=time.monotonic()+.5
 if not hasattr(SESSIONS,'session'):SESSIONS.session=requests.Session()
 response=SESSIONS.session.get(url,headers={'User-Agent':'ArtlineCatalogueResearch/1.0 (selected French printmaking survey)'},timeout=(15,45))
 raw=response.content;rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=now(),sha256=sha(raw),bytes=len(raw),body_path=str(bp.relative_to(ROOT)),content_type=response.headers.get('Content-Type'))
 save(bp,raw);save(rp,rc)
 if response.status_code in (401,403,429):
  with LOCKS[host]:
   if not hold.exists():save(hold,dict(rc,retry_after=response.headers.get('Retry-After')))
 if response.status_code in (500,502,503,504) and kind.count('-retry')<2:
  time.sleep(2);return capture(url,kind+'-retry')
 response.raise_for_status();return raw,rc
def getjson(url,kind='captures'):
 b,r=capture(url,kind);return json.loads(b),r
def classified(v,aat):return any(x.get('id')=='http://vocab.getty.edu/aat/'+aat or any(e.get('id')=='http://vocab.getty.edu/aat/'+aat for e in x.get('equivalent',[])) for x in v.get('classified_as',[]))
def statements(v,aat):return [x['content'] for x in v.get('referred_to_by',[]) if classified(x,aat) and x.get('content')]
def one(v):return v[0] if len(v)==1 else None
def dates(label,last=1900):
 t=(label or '').strip().replace('–','-').replace('—','-')
 t=re.sub(r'^(?:published|printed|issued)\s+','',t,flags=re.I)
 match=re.fullmatch(r'(?:(ca?\.?|circa|about)\s*)?(\d{4})(?:\s*[-/]\s*(\d{2,4}))?',t,re.I)
 if match:
  lo=int(match[2]);hi=int(match[3] or match[2]);hi=lo//100*100+hi if hi<100 else hi
  if match[1] and hi==1970:return None # Backend retains circa-1970 dates for review.
  if 1800<=lo<=hi<=last:return dict(creation_year_start=lo,creation_year_end=hi,date_precision=('circa' if lo==hi else 'circa_range') if match[1] else ('exact' if lo==hi else 'range'),date_display=label)
 match=re.fullmatch(r'(?:(?:early|mid|late)\s+)?((?:18|19)\d)0s',t,re.I)
 if match:
  lo=int(match[1])*10
  if lo+9<=last:return dict(creation_year_start=lo,creation_year_end=lo+9,date_precision='decade',date_display=label)
 if re.fullmatch(r'(?:(?:early|mid|late)[ -]+)?19th(?:[ -]+(?:(?:early|mid|late)[ -]+)?19th)? century',t,re.I):return dict(creation_year_start=1801,creation_year_end=1900,date_precision='century',date_display=label)
 # Fully stated day/month is retained without mistaking a subject/event year.
 match=re.fullmatch(r'(?:\d{1,2}\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(?:\d{1,2},?\s+)?((?:18|19)\d{2})',t,re.I)
 if match and int(match[1])<=last:return dict(creation_year_start=int(match[1]),creation_year_end=int(match[1]),date_precision='exact',date_display=label)
 return None
def indexes():
 seed=load(RUN/'french-index-seed-v4.json');data=seed['data'];rc=seed['receipt'];rows={};refs=[]
 for page in range(1,61):
  path=RUN/'indexes'/f'{page:03}.json.gz'
  save(path,dict(data=data,receipt=rc));refs.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path.read_bytes())))
  for row in data['orderedItems']:
   assert row['type']=='HumanMadeObject';rows.setdefault(row['id'],dict(**row,index_page=page))
  print('INDEX',page,len(rows),flush=True)
  nxt=data.get('next',{}).get('id')
  if not nxt:break
  data,rc=getjson(nxt)
 save(RUN/'discovered.json.gz',dict(at=now(),query=seed['query'],selected=list(rows.values()),index_references=refs,policy='Bounded French print survey: at most 60 pages of 100 metadata identities, actual literal dates and native identity reviewed before any image selection. Search estimates never establish date eligibility.'))
def object_one(row):
 key=row['id'].rsplit('/',1)[1];dest=RUN/'objects'/(key+'.json.gz')
 if dest.exists():return load(dest)
 out=dict(index=row)
 try:
  p,rc=getjson(row['id']);assert p['id']==row['id'];out.update(raw=p,receipt=rc)
  ids=[x['id'].rsplit('/',1)[1][:-5] for x in p.get('equivalent',[]) if re.fullmatch(r'https://media\.art\.yale\.edu/content/lux/obj/\d+\.json',x['id'])]
  native=one(ids);assert native,'No unique native Yale identity'
  out['native_id']=native;out['source_url']='https://artgallery.yale.edu/collections/objects/'+native
  if p.get('type')!='HumanMadeObject' or not classified(p,'300041273'):raise ValueError('Not a physical print')
  if [x['id'] for x in p.get('current_owner',[])]!=[GALLERY]:raise ValueError('Not uniquely held by Yale University Art Gallery')
  if not all('Yale University Art Gallery' in x.get('_label','') for x in p.get('member_of',[])):raise ValueError('Mixed collection context')
  parts=[]
  def walk(v):
   if classified(v,'300025103'):parts.append(v)
   for child in v.get('part',[]):walk(child)
  walk(p.get('produced_by',{}));part=one(parts)
  if not part or len(part.get('carried_out_by',[]))!=1 or part.get('influenced_by'):raise ValueError('Qualified or multiple primary artist roles need individual review')
  desc=one(statements(part,'300435446'))
  if not desc or not re.match(r'^Artist: .+ \(French, ',desc):raise ValueError('No unqualified French artist statement')
  artist=part['carried_out_by'][0]
  if artist.get('type')!='Person':raise ValueError('Not a reconciled individual creator')
  out.update(creator=artist,creator_label=re.sub(r'^Artist:\s*','',desc).rsplit(' (French, ',1)[0],source_creator_label=desc)
  manifests=[a['id'] for s in p.get('subject_of',[]) for d in s.get('digitally_carried_by',[]) if d.get('format')=='application/ld+json' for a in d.get('access_point',[]) if a['id'].startswith('https://manifests.collections.yale.edu/yuag/obj/')]
  manifest_url=one(manifests)
  if not manifest_url:raise ValueError('No unique official image manifest')
  mf,mrc=getjson(manifest_url,'manifests');out.update(manifest=mf,manifest_receipt=mrc)
  fields={one(v['label'].get('en',[])):v['value'].get('en',[]) for v in mf.get('metadata',[])}
  last=1970 if row.get('topic_period')=='modern_extension' else 1900
  title=one(fields.get('Title',[]));date=one(fields.get('Date',[]));dt=dates(date,last)
  if not dt:raise ValueError('Literal creation date missing, uncertain, complex or outside 1800-'+str(last))
  if norm(title)!=norm(p.get('_label')):raise ValueError('Manifest and native title disagree')
  if fields.get('Classification')!=['Prints'] or fields.get('Institution')!=['Yale University Art Gallery']:raise ValueError('Manifest object type/institution conflict')
  manifest_roles=[role.strip() for field in fields.get('Creator(s)',[]) for role in field.split(';')]
  if desc not in manifest_roles:raise ValueError('Manifest and native creator disagree')
  out['all_creator_labels']=fields.get('Creator(s)',[])
  inv=one(fields.get('Object Number',[]));native_inv=one([x['content'] for x in p.get('identified_by',[]) if x.get('type')=='Identifier' and classified(x,'300312355')])
  if not inv or inv!=native_inv:raise ValueError('Native accession and manifest conflict')
  credit=one(fields.get('Creditline',[]))
  if not credit or re.search(r'\b(lent|loan|promised|deaccession|returned|restitut|private collection)',credit,re.I):raise ValueError('Credit needs loan/ownership review')
  ts=p.get('produced_by',{}).get('timespan',{});literal=one([x['content'] for x in ts.get('identified_by',[]) if x.get('type')=='Name']);ld=dates(literal,last)
  if ld and (ld['creation_year_end']<dt['creation_year_start'] or ld['creation_year_start']>dt['creation_year_end']):raise ValueError('Literal dates conflict')
  if ts.get('begin_of_the_begin') and ts.get('end_of_the_end'):
   lo=int(ts['begin_of_the_begin'][:4]);hi=int(ts['end_of_the_end'][:4])
   if hi<dt['creation_year_start'] or lo>dt['creation_year_end']:raise ValueError('Merged production bounds contradict literal date')
  canvases=mf.get('items',[])
  if not canvases:raise ValueError('No image canvas')
  canvas=canvases[0];annotations=[a for page in canvas.get('items',[]) for a in page.get('items',[]) if a.get('motivation')=='painting'];an=one(annotations)
  if not an or not isinstance(an.get('body'),dict):raise ValueError('No unambiguous first canvas image')
  im=an['body'];services=im.get('service',[]);service=one([x.get('id',x.get('@id')) for x in services])
  if not service or not service.startswith('https://images.collections.yale.edu/iiif/2/yuag:'):raise ValueError('Unsupported image source')
  rights=[x['value'].get('en',[]) for x in canvas.get('metadata',[]) if x['label'].get('en')==['Image Use Rights']]
  out.update(title=title,date=dt,accession_number=inv,medium=one(fields.get('Medium',[])),dimensions_text='; '.join(fields.get('Dimensions',[])),credit_line=credit,
    rights_label='; '.join(x for values in rights for x in values) or 'Unspecified image rights',copyright_statement='; '.join(fields.get('Copyright Statement',[])),
    image_url=service+'/full/!1200,1200/0/default.jpg',native_image_url=im['id'],canvas_id=canvas['id'],canvas_count=len(canvases),work_type='print',outcome='candidate',topic_period=row.get('topic_period','nineteenth_century'))
 except Exception as exc:out.update(outcome='hold',hold=type(exc).__name__+': '+str(exc))
 save(dest,out);return out
def objects():
 rows=load(RUN/'discovered.json.gz')['selected'];counts=collections.Counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:
  for i,r in enumerate(pool.map(object_one,rows),1):
   counts[r['outcome']]+=1
   if i%50==0:print('OBJECTS',i,len(rows),dict(counts),flush=True)
 save(RUN/'objects-summary.json',dict(at=now(),counts=dict(counts),selected=len(rows)));print('OBJECTS COMPLETE',dict(counts),flush=True)

def extension():
 seed=load(RUN/'extension-index-seed.json');data=seed['data'];rc=seed['receipt'];rows={}
 for page in range(1,11):
  save(RUN/'extension-indexes'/f'{page:03}.json.gz',dict(data=data,receipt=rc))
  for row in data['orderedItems']:rows.setdefault(row['id'],dict(**row,index_page=page,topic_period='modern_extension'))
  nxt=data.get('next',{}).get('id')
  if not nxt:break
  data,rc=getjson(nxt)
 save(RUN/'discovered-extension.json.gz',dict(at=now(),query=seed['query'],selected=list(rows.values()),scope='Selected extension into French printmaking 1901–1970; literal creation dates still decide eligibility.'))
 counts=collections.Counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:
  for i,r in enumerate(pool.map(object_one,list(rows.values())),1):
   counts[r['outcome']]+=1
   if i%50==0:print('EXTENSION',i,len(rows),dict(counts),flush=True)
 save(RUN/'extension-summary.json',dict(at=now(),counts=dict(counts),selected=len(rows)));print('EXTENSION COMPLETE',dict(counts),flush=True)
 recover_transport()
 recover_dates()

def recover_transport():
 dest=RUN/'transport-review-summary.json'
 if dest.exists():return
 rows=[]
 for path in sorted((RUN/'objects').glob('*.json.gz')):
  old=load(path)
  if not old.get('hold','').startswith(('ReadTimeout:','ConnectTimeout:','ConnectionError:')):continue
  history=RUN/'history-transport-review'/path.name;history.parent.mkdir(exist_ok=True);assert not history.exists();path.rename(history);rows.append(old['index'])
 outcomes=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for r in pool.map(object_one,rows):outcomes.append(dict(source_id=r['index']['id'],outcome=r['outcome'],hold=r.get('hold')))
 save(dest,dict(at=now(),records=outcomes,policy='One bounded retry of transport failures only, preserving original outcomes. Provider access holds remain binding.'))
 print('TRANSPORT REVIEW',len(outcomes),flush=True)

def recover_dates():
 dest=RUN/'date-review-summary.json'
 if dest.exists():return
 review=[]
 for path in sorted((RUN/'objects').glob('*.json.gz')):
  old=load(path)
  if not old.get('hold','').startswith('ValueError: Literal creation date'):continue
  label=one([text for item in old.get('manifest',{}).get('metadata',[]) if item['label'].get('en')==['Date'] for text in item['value'].get('en',[])])
  dt=dates(label,1970)
  if not dt:continue
  history=RUN/'history-date-review'/path.name;history.parent.mkdir(exist_ok=True);assert not history.exists();path.rename(history)
  row=dict(old['index'],topic_period='modern_extension' if dt['creation_year_end']>1900 else 'nineteenth_century')
  updated=object_one(row);review.append(dict(native_id=old['native_id'],literal_date=label,conservative_envelope=dt,outcome=updated['outcome'],previous_record=str(history.relative_to(ROOT))))
 save(dest,dict(at=now(),records=review,policy='Editorial source-date review: explicit early/mid/late nineteenth-century dates retain their literal wording and use the conservative whole-century envelope 1801–1900. Qualified decades use the whole stated decade. No invented narrow boundaries or artist-lifespan dates. The separately requested extension admits explicit ranges wholly through 1970, including ranges that cross 1900. Unknown and twentieth-century-wide ranges remain held.'))
 print('DATE REVIEW',len(review),'source statements reviewed',flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
