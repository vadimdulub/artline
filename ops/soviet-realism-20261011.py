#!/usr/bin/env python3
"""Bounded Soviet Realism research; immutable evidence, production-only delivery.

The source is a collector catalogue, not a museum. Selected objects are personal
editorial selections; source classifications never establish museum ownership.
"""
import collections, concurrent.futures, datetime, gzip, hashlib, importlib.util
import json, re, sys, threading, time, unicodedata, uuid
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OP='soviet-realism-20261011';RUN=ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
BASE='https://www.socrealizm.com.ua'
ACTOR='local-european-research'
COLLECTION='42c83e94-d1f2-539a-accb-b4e9ded61f06'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
dbutil=module('soviet_db','ops/india-300-delivery-20261011.py')
def connect(write=False):return dbutil.connect(write)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+key))
def norm(s):return ' '.join(re.findall(r'[^\W_]+',unicodedata.normalize('NFKC',str(s or '')).casefold().replace('ё','е')))
def load(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(p,v):
 raw=v if isinstance(v,bytes) else json.dumps(v,ensure_ascii=False,indent=2,default=str).encode()
 if p.suffix=='.gz':raw=gzip.compress(raw,mtime=0)
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw,'Immutable evidence differs: '+str(p)
 else:p.write_bytes(raw)
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
 response=SESSIONS.session.get(url,headers={'User-Agent':'ArtlineCatalogueResearch/1.0 (selected Soviet Realism collection)'},timeout=(15,45))
 raw=response.content;rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=now(),sha256=sha(raw),bytes=len(raw),body_path=str(bp.relative_to(ROOT)),content_type=response.headers.get('Content-Type'))
 save(bp,raw);save(rp,rc)
 if response.status_code in (401,403,429):
  with LOCKS[host]:
   if not hold.exists():save(hold,dict(rc,retry_after=response.headers.get('Retry-After')))
 if response.status_code in (500,502,503,504) and kind.count('-retry')<2:
  time.sleep(2);return capture(url,kind+'-retry')
 response.raise_for_status();return raw,rc

DIM=re.compile(r'\b\d{1,3}(?:[.,]\d+)?\s*[-xх×*]\s*\d{1,3}(?:[.,]\d+)?\b',re.I)
def date_tail(text):
 text=text.strip(' .,;');m=re.search(r'(?<!\d)((?:18|19|20)\d{2})(\s*[-–]\s*((?:18|19|20)?\d{2}))?\s*([-–]?\s*[еы]е?\s*(?:г(?:оды|од|г)?\.?)?|(?:г(?:од(?:а|у|ы)?|г)?\.?)?)$',text,re.I)
 if not m:return None
 if re.search(r'(?:18|19|20)\d{2}|около|примерно|circa|\?|~|\bок\.',text[:m.start()],re.I):return None
 lo=int(m[1]);hi=lo;precision='exact'
 if m[3]:
  hi=int(m[3]);hi=lo//100*100+hi if hi<100 else hi;precision='range'
 if re.search('[еы]',m[4] or '',re.I):
  if m[3]:return None
  if lo%10:return None
  hi=lo+9;precision='decade'
 if not 1800<=lo<=hi<=2100:return None
 return dict(creation_year_start=lo,creation_year_end=hi,date_precision=precision,date_display=m[0].strip())

def card(li,category,receipt):
 a=li.select_one('a.caregory-li-title');creator=li.select_one('.frame-item-brand a');im=li.select_one('img');native=li.select_one('[data-id]')
 if not a or not creator or not native:return None
 text=a.get_text(' ',strip=True);dimension=DIM.search(text);date=date_tail(text[dimension.end():] if dimension else '')
 label=creator.get_text(' ',strip=True);reason=None
 if not dimension:reason='No unambiguous title/dimensions boundary'
 elif not date:reason='No explicit unambiguous creation date after dimensions'
 elif date['creation_year_start']<1917:reason='Pre-Soviet creation; no automatic retrospective movement attribution'
 elif date['creation_year_end']>1970:reason='Creation date extends after 1970'
 elif 'неизвест' in label.casefold():reason='Unresolved creator label in this collector-source selection'
 elif not text[:dimension.start()].strip(' ,.-'):reason='Missing individual artwork title'
 url=a['href'];slug=urlsplit(url).path.rsplit('/',1)[-1]
 if date and date['date_precision']=='exact' and re.search(r'(?:^|-)'+str(date['creation_year_start'])[-2:]+r'-?e(?:-|$)',slug):reason='Title date conflicts with decade wording in native object URL'
 return dict(provider='socrealizm',source_id=native['data-id'],source_url=url,source_title=text,title=text[:dimension.start()].strip(' ,.') if dimension else text,
  creator_label=re.sub(r'\s+(?:18|19|20)\d{2}\s*$', '',label).strip(),creator_source_label=label,creator_url=creator['href'],
  dimensions_text=dimension[0] if dimension else None,date=date,category=category,index_receipt=receipt,
  index_image_url=urljoin(BASE,im['src']) if im else None,hold=reason)

def indexes():
 limits={'lenin':30,'war':50,'kolkhoz':60,'sport':25,'children':60,'celebration':35,'portrait':240,'landscape':320,'still-life':160}
 def one_category(pair):
  category,limit=pair;rows={};maxpage=limit
  for page in range(limit):
   if page>=maxpage:break
   dest=RUN/'indexes'/category/f'{page:04d}.json.gz'
   if dest.exists():data=load(dest)
   else:
    url=BASE+'/gallery/category/'+category+('?per_page='+str(page*20) if page else '')
    try:raw,rc=capture(url,'index-captures')
    except Exception as exc:
     gap=RUN/'index-gaps'/category/f'{page:04d}.json'
     if not gap.exists():save(gap,dict(at=now(),url=url,error=str(exc)))
     print('INDEX GAP',category,page,str(exc)[:100],flush=True);continue
    soup=BeautifulSoup(raw,'html.parser')
    items=[card(li,category,rc) for li in soup.select('#items-catalog-main > li')];items=[x for x in items if x]
    offsets=[int(parse_qs(urlsplit(a['href']).query)['per_page'][0]) for a in soup.select('a[href*="per_page="]') if '/category/'+category in a['href']]
    data=dict(category=category,page=page,receipt=rc,items=items,maxpage=max(offsets+[0])//20+1)
    save(dest,data)
   maxpage=min(limit,data['maxpage'])
   if not data['items']:break
   for row in data['items']:rows[row['source_id']]=row
   if (page+1)%20==0:print(category,page+1,'pages',sum(not x['hold'] for x in rows.values()),'eligible leads',flush=True)
  print('INDEX',category,len(rows),'records;',sum(not x['hold'] for x in rows.values()),'eligible leads',flush=True)
  return list(rows.values())
 allrows={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for rows in pool.map(one_category,limits.items()):
   for r in rows:
    if r['source_id'] in allrows:allrows[r['source_id']]['categories'].append(r['category'])
    else:allrows[r['source_id']]=dict(r,categories=[r['category']])
 save(RUN/'index-records.json.gz',list(allrows.values()))
 print('TOTAL',len(allrows),'unique source objects;',sum(not x['hold'] for x in allrows.values()),'eligible leads',flush=True)

def page(row):
 path=RUN/'objects'/(row['source_id']+'.json.gz')
 if path.exists():return load(path)
 result=dict(row)
 try:
  raw,rc=capture(row['source_url'],'object-captures');s=BeautifulSoup(raw,'html.parser')
  h=s.select_one('h1');title=h.get_text(' ',strip=True) if h else None
  if norm(title)!=norm(row['source_title']):raise ValueError('Object title differs from selected index')
  result['receipt']=rc
  # Only the main product image: related-item images are never substituted.
  images=[(im,im.parent) for im in s.select('img') if norm(im.get('alt'))==norm(title) and '/uploads/gallery/paintings/' in im.get('src','')]
  main=[(im,parent) for im,parent in images if not im.find_parent('li',class_='globalFrameProduct')]
  candidates=[]
  for im,parent in main:
   href=parent.get('href','')
   candidates.append(urljoin(BASE,href if re.search(r'\.(?:jpg|jpeg|png)$',href,re.I) else im.get('src')))
  candidates=list(dict.fromkeys(candidates));assert len(candidates)==1,('Ambiguous main source image',candidates)
  result['source_image_url']=candidates[0]
  result['source_rights_label']='No reproduction licence stated on the object page'
  result['rights_status']='unknown'
  dimension=DIM.search(title);suffix=title[dimension.end():];date=date_tail(suffix)
  assert date==row['date']
  medium=re.sub(r'^\s*см\.?\s*[,.;]?','',suffix[:suffix.rfind(date['date_display'])],flags=re.I).strip(' .,;')
  result['medium_text']=medium or None
  result['work_type']='watercolor' if 'акварел' in medium.lower() else 'drawing' if re.search('карандаш|тушь|пастел',medium,re.I) else 'painting' if re.search('масл|гуашь|темпер',medium,re.I) else 'unknown'
  # Titles explicitly identifying reproductions/copies require separate identity review.
  if re.search(r'\b(копия|репродукция|по мотивам|литограф|эскиз памятника)\b',title,re.I):result['hold']='Copy, reproduction or different object type requires individual review'
  result['outcome']='captured'
 except Exception as e:result.update(outcome='held',hold=str(e)[:500])
 save(path,result);return result

def pages():
 rows=[r for r in load(RUN/'index-records.json.gz') if not r['hold']]
 # A bounded reserve supports image/version holds; no entire-source image download.
 rows=rows[:700];save(RUN/'object-selection.json.gz',rows)
 counts=collections.Counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for n,r in enumerate(pool.map(page,rows),1):
   counts['held' if r.get('hold') else 'ready']+=1
   if n%50==0:print('OBJECTS',n,'/',len(rows),dict(counts),flush=True)
 save(RUN/'objects-summary.json',dict(at=now(),counts=counts,selected=len(rows)))

def profiles():
 rows=load(RUN/'object-selection.json.gz');urls={r['creator_url']:r for r in rows}
 def one(pair):
  url,row=pair;dest=RUN/'artists'/(sha(url.encode())+'.json.gz')
  if dest.exists():return load(dest)
  data=dict(url=url,label=row['creator_label'],source_label=row['creator_source_label'])
  try:
   raw,rc=capture(url,'artist-captures');s=BeautifulSoup(raw,'html.parser');h=s.select_one('main h1') or s.select_one('h1')
   label=h.get_text(' ',strip=True) if h else ''
   name=re.sub(r'^.*?\b(?:художник|художница|живописец|скульптор|график)\s+','',label,flags=re.I).strip()
   desc=s.select_one('main .description');bio=desc.get_text(' ',strip=True) if desc else ''
   birth=re.search(r'((?:18|19)\d{2})\s*$',row['creator_source_label'])
   data.update(full_name=name if len(name.split())>=2 and norm(row['creator_label'].split()[0]) in norm(name) and not re.search(r'[!?\d]',name) else None,
    title=label,birth_year=int(birth[1]) if birth else None,biography_source_text=bio,receipt=rc,outcome='captured')
  except Exception as exc:data.update(outcome='held',error=str(exc)[:400])
  save(dest,data);return data
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for n,_ in enumerate(pool.map(one,urls.items()),1):
   if n%25==0:print('ARTIST PROFILES',n,'/',len(urls),flush=True)

TRANSLIT=dict(zip('абвгдежзийклмнопрстуфхцчшщьыэюя',['a','b','v','g','d','e','zh','z','i','i','k','l','m','n','o','p','r','s','t','u','f','kh','ts','ch','sh','shch','','y','e','yu','ya']))
def latin(value):
 value=''.join(TRANSLIT.get(c,c) for c in norm(value));return ''.join(c for c in unicodedata.normalize('NFKD',value) if not unicodedata.combining(c))
def artist_plan():
 import difflib
 baseline=load(RUN/'production-artists-baseline.json.gz');names=collections.defaultdict(set);byid={a['id']:a for a in baseline['artists']};namevariants=collections.defaultdict(set)
 for a in baseline['artists']:names[norm(a['display_name'])].add(a['id']);namevariants[a['id']].add(a['display_name'])
 for a in baseline['aliases']:names[norm(a['alias'])].add(a['artist_id']);namevariants[a['artist_id']].add(a['alias'])
 latin_names=collections.defaultdict(set);token_names=collections.defaultdict(set)
 for aid,variants in namevariants.items():
  for name in variants:
   latin_names[latin(name)].add(aid)
   for token in latin(name).split():
    if len(token)>=5:token_names[token].add(aid)
 birthmap=collections.defaultdict(list)
 for a in baseline['artists']:birthmap[a.get('birth_year')].append(a['id'])
 profiles=[load(p) for p in (RUN/'artists').glob('*.json.gz')];plans={};newidentities={}
 facts=load(RUN/'artist-profile-facts.json.gz') if (RUN/'artist-profile-facts.json.gz').exists() else {}
 for p in profiles:
  p=dict(p,**facts.get(p['url'],{}))
  source=p['url'];name=p.get('full_name');birth=p.get('birth_year');exact=set()
  if name:
   words=name.split();variants=[name,' '.join(words[1:]+words[:1])]
   if len(words)>=3:variants+=[' '.join(words[:2]),' '.join([words[1],words[0]])]
   for n in variants:exact.update(names[norm(n)]);exact.update(latin_names[latin(n)])
  rawexact=set(exact);exact={a for a in exact if byid[a]['birth_year'] in (None,birth) or birth is None}
  possible=set(rawexact)
  if name:
   surname=latin(name.split()[0]);first=latin(name.split()[1])[:1]
   for aid in token_names[surname]:
    if any(any(t.startswith(first) for t in latin(n).split() if t!=surname) for n in namevariants[aid]):possible.add(aid)
  if name and birth:
   surname=latin(name.split()[0]);first=latin(name.split()[1])[:1]
   for aid in birthmap[birth]:
    for n in namevariants[aid]:
     tokens=latin(n).split()
     if any(difflib.SequenceMatcher(None,surname,t).ratio()>=.72 for t in tokens) and any(t.startswith(first) for t in tokens):possible.add(aid)
  if len(exact)==1:
   aid=next(iter(exact));plans[source]=dict(action='existing',artist_id=aid,profile=p,basis='Unique exact full native name or surname/given-name alias with concordant source birth year',possible=list(possible))
  elif possible:plans[source]=dict(action='hold',profile=p,possible=sorted(possible),reason='Cross-language or duplicate creator identity requires individual reconciliation')
  elif not name:plans[source]=dict(action='hold',profile=p,reason='No complete individual name in native profile')
  else:
   key=(norm(name),birth);aid=newidentities.setdefault(key,uid('artist/'+source));plans[source]=dict(action='create',artist_id=aid,profile=p,basis='Named native creator profile; no matching full-name alias or concordant-birth transliteration candidate in production inventory')
 grouped=collections.defaultdict(list)
 for url,p in plans.items():
  if p['action'] in ('create','existing'):grouped[' '.join(sorted(norm(p['profile']['full_name']).split()))].append((url,p))
 for key,group in grouped.items():
  births={p['profile'].get('birth_year') for _,p in group}-{None};existing={p['artist_id'] for _,p in group if p['action']=='existing'}
  if len(births)>1 or len(existing)>1:
   for _,p in group:p.update(action='hold',reason='Conflicting cross-source full-name creator identities')
  else:
   canonical=next(iter(existing)) if existing else uid('artist/native-name/'+key+'/'+str(next(iter(births)) if births else 'unknown'))
   for _,p in group:
    if p['action']=='create' and existing:p.update(action='existing',basis=p['basis']+'; exact complete native-name tokens match an independently reconciled source profile')
    p['artist_id']=canonical
 save(RUN/'artist-plan.json.gz',plans)
 print('ARTIST PLAN',dict(collections.Counter(p['action'] for p in plans.values())),flush=True)

def profile_facts():
 facts={}
 for path in (RUN/'artists').glob('*.json.gz'):
  p=load(path)
  if p.get('provider')!='sovcom':continue
  rc=p['receipt'];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert sha(raw)==rc['sha256']
  soup=BeautifulSoup(raw,'html.parser');bio=soup.select_one('.biografy')
  if not bio:continue
  heading=bio.find_previous_sibling('h3');label=heading.get_text(' ',strip=True) if heading else ''
  parenthetical=re.search(r'\((.*)\)',label);years=re.findall(r'(?<!\d)(?:18|19|20)\d{2}(?!\d)',parenthetical[1] if parenthetical else '')
  birth=int(years[0]) if years else None;death=int(years[1]) if len(years)==2 else None
  if birth and death and birth>death:birth=death=None
  facts[p['url']]=dict(birth_year=birth,death_year=death,biography_source_text=bio.get_text(' ',strip=True),life_source_label=label)
 save(RUN/'artist-profile-facts.json.gz',facts);print('PROFILE FACTS',len(facts),flush=True)

def bootstrap():
 RUN.mkdir(parents=True,exist_ok=True)
 save(RUN/'authorization.json',dict(at=now(),instruction='try to cover "soviet realism" add this movement, I expect at least 2000-3000 artworks that meet the criteria, u can add all images don\'t think about rights! this is ok',target='production',local_database_connected=False,minimum_new_artworks=2000,target_new_artworks=2500,creation_cutoff=1970,image_cutoff=1970,rights_approval='User-approved selected authentic reproductions; retain actual labels and credits separately',selection='Personal editorial selection for Soviet Realism; no museum holding or current-display inference'))
 capture(BASE+'/')
 capture('https://www.wikiart.org/en/Artists-by-Art-Movement/socialist-realism','movement-captures')
 with connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  artists=[x['v'] for x in db.execute("SELECT to_jsonb(a) v FROM artists a WHERE status<>'archived'")]
  aliases=[dict(x) for x in db.execute('SELECT artist_id::text,alias FROM artist_aliases')]
  movements=[x['v'] for x in db.execute('SELECT to_jsonb(m) v FROM movements m')]
  ids=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist'")]
  save(RUN/'production-artists-baseline.json.gz',dict(at=now(),artists=artists,aliases=aliases,identifiers=ids,movements=movements))
 print('Production identity inventory',len(artists),'artists',flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
