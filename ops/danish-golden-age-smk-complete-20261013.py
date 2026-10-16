#!/usr/bin/env python3
"""Complete SMK object scan for the closed Danish Golden Age authority set."""
import argparse, collections, datetime, gzip, hashlib, importlib.util, json, re, time
from pathlib import Path
from urllib.parse import urlencode
import requests

ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/danish-golden-age-20261013';BATCH=RUN/'smk-complete-batch-v2'
spec=importlib.util.spec_from_file_location('dga',ROOT/'ops/danish-golden-age-20261013.py');dga=importlib.util.module_from_spec(spec);spec.loader.exec_module(dga)
ROSTER=set(dga.ROSTER);SESSION=requests.Session();SESSION.headers['User-Agent']='ArtlineCatalogue/1.0 (source-backed SMK metadata research)'
SCHEME='european-smk-statens-museum-for-kunst-object'
UNCERTAIN=re.compile(r'udateret|virkeår|levetid|baseret på kunstnerens årstal|tilgået museet|unknown|undated|after|before|efter|før|muligvis|tilskrevet',re.I)

def save(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(obj,ensure_ascii=False,indent=2,default=str).encode();raw=gzip.compress(raw,mtime=0) if path.suffix=='.gz' else raw
 if path.exists():assert path.read_bytes()==raw,'Preserve evidence '+str(path)
 else:path.write_bytes(raw)
def load(path):return json.loads(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def creator(r):
 p=r.get('production',[])
 if len(p)!=1:return None
 x=p[0]
 return x if x.get('creator_lref') in ROSTER and x.get('creator_qualifier','')=='' and x.get('creator_role','') in ('','artist','Painter') and 'Danish' in [v.strip() for v in x.get('creator_nationality','').split(',')] else None
def date(r):
 ds=r.get('production_date',[]);notes='; '.join(r.get('production_dates_notes',[]));display='; '.join(x.get('period','') for x in ds).strip() or notes or 'Date not established by museum record'
 if len(ds)!=1:return {'first':None,'last':None,'precision':'unknown'},display
 x=ds[0];first=int(x['start'][:4]) if re.match(r'^\d{4}-',x.get('start','')) else None;last=int(x['end'][:4]) if re.match(r'^\d{4}-',x.get('end','')) else None
 if first and first>1970:return None,display
 if not first or not last or first<1100 or first>last or last>1970 or UNCERTAIN.search(notes+' '+display):return {'first':None,'last':None,'precision':'unknown'},display
 circa=bool(re.search(r'\bca\.?|circa|\bc\.',notes+' '+display,re.I));return {'first':first,'last':last,'precision':('circa' if circa else 'exact') if first==last else ('circa_range' if circa else 'range')},display
def life(person,kind):
 a=person.get(kind+'_date_start',[]);b=person.get(kind+'_date_end',[]);p=person.get(kind+'_date_prec',[])
 if len(a)!=1 or len(b)!=1 or len(p)!=1 or not re.fullmatch(r'(?:\d{1,2}-\d{1,2}-)?\d{4}',p[0]) or a[0][:4]!=b[0][:4] or not re.match(r'^\d{4}-',a[0]):return None
 return int(a[0][:4])

def scan():
 with dga.c.connect() as db:
  existing={r['external_id'] for r in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s",(SCHEME,))}
  selected=[];stats={};painting={};seen_source=collections.defaultdict(set);duplicates=collections.Counter();all_candidates={};receipts=[]
 for typ in ('Painting','Drawing','Print'):
  total=None;matched=missing=0
  for offset in range(0,200000,500):
   params=dict(keys='*',filters=f'[creator_nationality:Danish],[object_names:{typ}]',rows=500,offset=offset,lang='en',sort='object_number',sort_type='asc');url='https://api.smk.dk/api/v1/art/search/?'+urlencode(params)
   response=SESSION.get(url,timeout=(15,90));response.raise_for_status();raw=response.content;data=response.json();total=data['found'] if total is None else total;assert data['found']==total and data['offset']==offset
   receipts.append(dict(type=typ,offset=offset,url=url,status=response.status_code,bytes=len(raw),sha256=sha(raw),retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
   for r in data['items']:
    assert r['id'] not in seen_source[typ];seen_source[typ].add(r['id']);c=creator(r)
    if not c:continue
    matched+=1;oid=r.get('object_number','')
    if r['id'] not in all_candidates:duplicates[oid]+=1;all_candidates[r['id']]=(typ,r,c)
    if typ=='Painting':painting.setdefault(c['creator_lref'],r)
   if offset+len(data['items'])>=total:break
   assert len(data['items'])==500
   if offset%5000==0:print(typ,offset+len(data['items']),'/',total,'matched',matched,flush=True)
   time.sleep(.04)
  stats[typ]=dict(total=total,matched=matched)
 for typ,r,c in all_candidates.values():
  oid=r.get('object_number','');reason=None
  if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ./_-]{0,160}',oid or '') or '..' in oid:reason='source_identity_review'
  elif duplicates[oid]>1:reason='duplicate_source_accession'
  elif oid in existing:reason='already_in_catalogue'
  d,display=date(r)
  if d is None:reason=reason or 'post_1970'
  titles=[x['title'] for x in r.get('titles',[]) if x.get('title')]
  if not titles:reason=reason or 'missing_title'
  if r.get('frontend_url')!='https://open.smk.dk/artwork/image/'+oid:reason=reason or 'source_url_review'
  if reason:
   selected.append(dict(decision=reason,object_number=oid,person=c['creator_lref'],source_id=r.get('id'),source_url=r.get('frontend_url'),title=(next((x.get('title') for x in r.get('titles',[]) if x.get('title')),None)),exhibitions=r.get('exhibitions',[])))
   continue
  title=next((x['title'] for x in r['titles'] if x.get('language')=='engelsk' and x.get('title')),titles[0])
  selected.append(dict(decision='import',object_number=oid,person=c['creator_lref'],type=typ.lower(),title=title,date=d,date_display=display,raw=r,exhibitions=r.get('exhibitions',[])))
 save(RUN/'smk-complete-scan-v3.json.gz',dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),stats=stats,receipts=receipts,records=selected,painting_evidence=painting))
 print('scan',stats,'decisions',dict(collections.Counter(x['decision'] for x in selected)),flush=True)

def plan():
 data=load(RUN/'smk-complete-scan-v2.json.gz');candidates=[x for x in data['records'] if x['decision']=='import']
 with dga.c.connect() as db:
  museum=db.execute("SELECT id::text FROM institutions WHERE slug='statens-museum-for-kunst'").fetchone()['id']
  ids={r['external_id'] for r in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s",(SCHEME,))}
  urls={r['url'] for r in db.execute("SELECT canonical_url url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url IS NOT NULL UNION SELECT source_url FROM citations WHERE entity_type='artwork'")}
  accessions={r['accession_number'] for r in db.execute("SELECT accession_number FROM artworks WHERE current_institution_id=%s AND accession_number IS NOT NULL",(museum,))}
 imports=[];collisions=[]
 for x in candidates:
  raw=x['raw'];oid=x['object_number'];url=raw.get('frontend_url');basis=[]
  if oid in ids:basis.append('native_id')
  if oid in accessions:basis.append('museum_accession')
  if url in urls:basis.append('canonical_or_citation_url')
  (collisions if basis else imports).append(dict(x,collision_basis=basis) if basis else x)
 save(RUN/'smk-complete-production-collisions.json.gz',dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),count=len(collisions),records=collisions));authors={}
 for pid in sorted({x['person'] for x in imports}):
  url='https://api.smk.dk/api/v1/person/?id='+pid+'&lang=en';response=SESSION.get(url,timeout=(15,60));response.raise_for_status();items=response.json().get('items',[]);person=items[0] if len(items)==1 else {};assert person.get('id')==pid
  raw=data['painting_evidence'].get(pid);assert raw and creator(raw)
  c=creator(raw);years=[v for x in imports if x['person']==pid for v in (x['date']['first'],x['date']['last']) if v is not None]
  authors[pid]=dict(id=pid,name=' '.join(v for v in (c.get('creator_forename'),c.get('creator_surname')) if v),sort_name=c['creator'],nationality=c['creator_nationality'],source_url=url,birth=life(person,'birth'),death=life(person,'death'),start=min(years,default=0),end=max(years,default=0),painting_raw=raw,person_raw=person)
 works=[]
 for x in imports:
  r=x['raw'];titles=[v['title'] for v in r.get('titles',[]) if v.get('title')];medium='; '.join(dict.fromkeys(r.get('techniques',[])+r.get('materials',[])));dims='; '.join(' '.join(str(v.get(k,'')) for k in ('part','type','value','unit')).strip() for v in r.get('dimensions',[]))
  works.append(dict(painter=x['person'],title=x['title'],institution='smk-statens-museum-for-kunst',url=r['frontend_url'],accession=x['object_number'],source_object_id=x['object_number'],date_display=x['date_display'],creation_date=x['date'],attribution_role='primary',work_type=x['type'],medium=medium,dimensions=dims,aliases=list(dict.fromkeys(t for t in titles if t!=x['title'])),notes='Official SMK object record. Creation-date notes: '+'; '.join(r.get('production_dates_notes',[]))+'. The museum holding is separate from current display.',raw=r))
 BATCH.mkdir(parents=True,exist_ok=True);chunks=[]
 for i in range(0,len(works),250):
  rows=works[i:i+250];payload=dict(source='danish-painters-20260913',accessed_on='2026-10-13',authors={p:authors[p] for p in sorted({x['painter'] for x in rows})},works=rows);path=BATCH/f'chunk-{i//250+1:03d}.json';save(path,payload);chunks.append(dict(file=path.name,sha256=sha(path.read_bytes()),works=len(rows)))
 imported_ids={x['object_number'] for x in imports};held=[x for x in data['records'] if x['decision']!='already_in_catalogue' and x['object_number'] not in imported_ids]
 manifest=dict(source='danish-golden-age-smk-complete-20261013',works=len(works),artists=len(authors),unknown_dates=sum(x['creation_date']['precision']=='unknown' for x in works),types=dict(collections.Counter(x['work_type'] for x in works)),chunks=chunks);save(BATCH/'manifest.json',manifest);save(RUN/'smk-complete-held.json',dict(counts=dict(collections.Counter(x['decision'] for x in held)),records=held))
 print(manifest|{'chunks':len(chunks),'manifest_sha256':sha((BATCH/'manifest.json').read_bytes())},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['scan','plan']);a=p.parse_args();globals()[a.phase]()
