#!/usr/bin/env python3
"""Source-backed Polish artists and museum/gallery catalogue imports, review only.

Plans are immutable, production comparisons are scoped, and writes are atomic.
No publication, invented dates, current-display claims or local DB writes.
"""
import argparse, collections, datetime, gzip, hashlib, json, os, re, subprocess, unicodedata, uuid
from pathlib import Path
from urllib.parse import urlsplit
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg import sql

ROOT=Path(__file__).resolve().parents[1]
OP='poland-collections-20261008'
RUN=ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ACTOR='local-european-research'
DESCRIPTION='Before Polish artists and galleries import 20261008'
SCHEMES={'warsaw':['mnw-current-object-2026'],'krakow':['mnk-current-object'],'wroclaw':['mnwr-digital-object'],'zacheta':['zacheta-collection-object'],'lodz':['msl-collection-object'],'royal-warsaw':['royal-warsaw-object'],'poland-highlights':['poland-museum-highlight'],'szczecin':['szczecin-collection-caption'],'silesian':['silesian-object'],'cleveland':['cleveland-object','european-cleveland-cleveland-museum-of-art-object'],
 'chicago':['aic-object','european-chicago-art-institute-of-chicago-object'],
 'mia':['mia-object'],'met':['met-object'],'npm':['npm-painting-object'],
 'namoc':['namoc-object'],'hkmoa':['hkmoa-caption'],'ashmolean':['ashmolean-object'],
 'selected-highlights':['asian-museum-highlight'],'dunhuang':['dunhuang-scene'],
 'ota':['ota-collection-object'],'emuseum':['nich-emuseum-object'],'japan-highlights':['japan-museum-highlight'],
 'manila-highlights':['manila-museum-highlight'],'lopez':['lopez-collection-caption'],'ayala':['ayala-collection-object'],'national-philippines':['national-philippines-collection-feature'],'ncca':['ncca-talapamana-caption']}

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def uid(k):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+k))
def norm(s):return ' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',str(s or '')).casefold() if not unicodedata.combining(c))))
def safe(v):return json.loads(json.dumps(v,default=str))
def load(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(p,v):
 b=json.dumps(v,ensure_ascii=False,indent=2,default=str).encode()
 if p.suffix=='.gz':b=gzip.compress(b,mtime=0)
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,'Immutable evidence differs: '+str(p)
 else:p.write_bytes(b)
def connect(write=False):
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
 kw=psycopg.conninfo.conninfo_to_dict(secret);kw.update(host='127.0.0.1',port=os.environ.get('ARTLINE_ASIAN_PROXY_PORT','55528'),sslmode='disable',connect_timeout=20)
 return psycopg.connect(**kw,autocommit=True,row_factory=dict_row,options='-c timezone=UTC -c statement_timeout=180000 -c lock_timeout=15000'+('' if write else ' -c default_transaction_read_only=on'))
def batch_insert(db,table,rows):
 if not rows:return
 keys=list(rows[0]);assert all(list(r)==keys for r in rows)
 query=sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,keys)),sql.SQL(',').join(sql.Placeholder() for k in keys))
 with db.cursor() as cur:cur.executemany(query,[[r[k] for k in keys] for r in rows])
def snapshot(db,ids):
 result={r['v']['id']:dict(artwork=r['v'],holdings=[],creators=[],attachments=[]) for r in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,))}
 for table,key in [('artwork_location_assertions','holdings'),('artwork_artists','creators'),('artwork_media','attachments')]:
  for r in db.execute(sql.SQL('SELECT artwork_id::text,to_jsonb(t) v FROM {} t WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,to_jsonb(t)::text').format(sql.Identifier(table)),(ids,)):result[r['artwork_id']][key].append(r['v'])
 return result
def backup():
 rows=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--limit=80','--format=json'],text=True))
 r=next(x for x in rows if x.get('description')==DESCRIPTION)
 assert r['status']=='SUCCESSFUL',r['status']
 save(BACKUP/'cloud-sql-backup.json',r);save(RUN/'cloud-sql-backup.json',r)
 print('Verified production backup',r['id'],flush=True)
def museums():
 return {
 'National Museum in Warsaw':('wikimedia-museum-q153306','https://www.mnw.art.pl/'),
 'National Museum in Kraków':('wikimedia-museum-q195311','https://mnk.pl/'),
 'National Museum in Wrocław':('national-museum-wroclaw','https://mnwr.pl/'),
 'Zachęta — National Gallery of Art':('zacheta-national-gallery-of-art','https://zacheta.art.pl/'),
 'Muzeum Sztuki in Łódź':('muzeum-sztuki-lodz','https://msl.org.pl/'),
 'Royal Castle in Warsaw':('royal-castle-warsaw','https://www.zamek-krolewski.pl/'),
 'National Museum in Poznań':('museum-source-123009ee4d4a070c0feb','https://mnp.art.pl/'),
 'National Museum, Gdańsk, Poland':('museum-source-30a140b55edbbc8a3205','https://www.mng.gda.pl/'),
 'National Museum in Lublin':('national-museum-lublin','https://zamek-lublin.pl/'),
 'National Museum in Szczecin':('national-museum-szczecin','https://muzeum.szczecin.pl/'),
 'Silesian Museum, Katowice':('silesian-museum-katowice','https://muzeumslaskie.pl/'),
 }
def keys(r):
 k=[(s,r['source_id']) for s in SCHEMES[r['provider']]]
 if r['provider']=='cleveland':k += [('wikidata',u.rsplit('/',1)[-1]) for u in r['raw'].get('external_resources',{}).get('wikidata',[])]
 if r['provider']=='met' and r['raw'].get('objectWikidata_URL'):k.append(('wikidata',r['raw']['objectWikidata_URL'].rsplit('/',1)[-1]))
 return k
def dates(r):
 lo,hi=r.get('year_start'),r.get('year_end');text=r.get('date_display') or ''
 if r['date_decision']=='date_review' or lo==0 or hi==0 or not isinstance(lo,int) or not isinstance(hi,int):return None,None,'unknown'
 assert -10000<=lo<=hi<=1970
 approx=bool(re.search(r'\b(circa|about|around|ca\.|c\.|ok\.|około)',text,re.I))
 return lo,hi,('circa' if approx else 'exact') if lo==hi else ('circa_range' if approx else 'range')
def worktype(r):
 t=(r.get('source_type') or '').lower()
 if 'sculpture' in t:return 'sculpture'
 if 'calligraphy' in t:return 'calligraphy'
 if 'print' in t:return 'print'
 if 'watercolor' in t and 'drawing' not in t:return 'watercolor'
 if 'drawing' in t:return 'drawing'
 if 'paint' in t or '繪畫' in t or '绘画' in t or 'mural' in t:return 'painting'
 return 'unknown'
def source_records(phase):
 if phase=='china':
  data=load(ROOT/'docs/research/chinese-art-20261008/in-scope-or-review.json.gz')
  for x in load(ROOT/'docs/research/chinese-art-20261008/priority-mural-scenes.json'):
   data.append(dict(provider='dunhuang',source_id=str(x['cave'])+'/'+urlsplit(x['source_url']).fragment,title=x['title']+' — Mogao Cave '+str(x['cave'])+', '+x['surface'].split('\xa0')[-1],museum='Mogao Caves, Dunhuang Academy',source_url=x['source_url'],creator_label=None,date_display=None,year_start=None,year_end=None,date_decision='date_review',source_type='mural painting',medium=None,accession_number=None,raw=x,evidence=x['evidence'],decision='research_candidate',image_url=None,image_license_url=None,identity_note='Exact named scene within a specified cave surface; no whole-cave, whole-wall or individual-figure inflation. Paint layers remain in source description.'))
  return data
 rows=load(RUN/phase/'source-records.json.gz')
 corrections=load(RUN/phase/'source-field-corrections.json.gz')
 for r in rows:r.update(corrections.get(r['provider']+'/'+r['source_id'],{}))
 cross=load(RUN/phase/'source-identity-crosswalk.json.gz')
 for r in rows:r.update(cross.get(r['provider']+'/'+r['source_id'],{}))
 return rows
def plan(phase):
 folder=RUN/phase;dest=folder/'plan.json.gz';assert not dest.exists()
 rows=source_records(phase);save(folder/'input-records.json.gz',rows)
 # All successful captured pages are retained as immutable source evidence.
 valid_hashes=set()
 for base in [ROOT/'docs/research/chinese-art-20261008/captures',folder/'captures']:
  for p in base.glob('*.json'):
   rc=load(p);body=p.with_suffix('.body.gz')
   if body.exists():assert sha(gzip.decompress(body.read_bytes()))==rc['sha256'];valid_hashes.add(rc['sha256'])
 for x in rows:
  if x.get('evidence_file'):
   p=ROOT/x['evidence_file'];assert sha(p.read_bytes())==x['evidence']['sha256'];valid_hashes.add(x['evidence']['sha256'])
  assert x['evidence']['status']==200 and x['evidence']['sha256'] in valid_hashes,(x['provider'],x['source_id'])
  assert len(x.get('accession_number') or '')<=150,('Unbounded inventory field',x['provider'],x['source_id'])
  x['key']=x['provider']+'/'+x['source_id'];x['scheme']=SCHEMES[x['provider']][0]
 assert len({r['key'] for r in rows})==len(rows)
 with connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  allinst=[x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i')]
  byslug={i['slug']:i for i in allinst};instmap={};newinst=[]
  for name in sorted({r['museum'] for r in rows}):
   slug,website=museums()[name]
   existing=[i for i in allinst if i['slug']==slug or norm(i['name'])==norm(name)]
   assert len(existing)<=1,('Institution ambiguity',name)
   if existing:
    i=existing[0]
    while i['canonical_institution_id']:i=next(v for v in allinst if v['id']==i['canonical_institution_id'])
    assert i['status']!='archived'
   else:
    host=urlsplit(website).netloc.removeprefix('www.')
    possible=[i for i in allinst if i['website_url'] and urlsplit(i['website_url']).netloc.removeprefix('www.')==host]
    assert not possible,('Institution website ambiguity',name,possible)
    i=dict(id=uid('museum/'+slug),name=name,normalized_name=norm(name),slug=slug,website_url=website,status='review',kind='museum',description='')
    newinst.append(i)
   instmap[name]=i
  for r in rows:r['institution_id']=instmap[r['museum']]['id']
  scoped=[r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE current_institution_id=ANY(%s::uuid[])',([i['id'] for i in instmap.values()],))]
  byacc=collections.defaultdict(set);bytitle=collections.defaultdict(set)
  for a in scoped:
   if a['accession_number']:byacc[a['current_institution_id'],norm(a['accession_number'])].add(a['id'])
   bytitle[a['current_institution_id'],norm(a['title'])].add(a['id'])
  lookups=list({(s,v) for r in rows for s,v in keys(r)})
  bykey=collections.defaultdict(set)
  for offset in range(0,len(lookups),500):
   for e in db.execute("SELECT e.entity_id::text,e.scheme,e.external_id FROM jsonb_to_recordset(%s) p(scheme text,external_id text) JOIN external_identifiers e USING(scheme,external_id) WHERE e.entity_type='artwork'",(Jsonb([dict(scheme=s,external_id=v) for s,v in lookups[offset:offset+500]]),)):
    bykey[e['scheme'],e['external_id']].add(e['entity_id'])
  # Shared collection index URLs identify a caption only together with its title.
  urls=list({r['source_url'] for r in rows});byurl=collections.defaultdict(set)
  for offset in range(0,len(urls),500):
   for e in db.execute("SELECT entity_id::text,source_url url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls[offset:offset+500],urls[offset:offset+500])):byurl[e['url']].add(e['entity_id'])
  urlcounts=collections.Counter(r['source_url'] for r in rows)
  possible={}
  for r in rows:
   exact=set().union(*(bykey[k] for k in keys(r)))
   if r.get('verified_existing_id'):exact.add(r['verified_existing_id'])
   if r.get('accession_number'):exact|=byacc[r['institution_id'],norm(r['accession_number'])]
   if urlcounts[r['source_url']]==1 and r['provider'] not in ['hkmoa','manila-highlights','japan-highlights']:exact|=byurl[r['source_url']]
   titlematches=bytitle[r['institution_id'],norm(r['title'])]
   possible[r['key']]=dict(exact=sorted(exact),title=sorted(titlematches))
  foundids=sorted(set().union(*(set(x['exact'])|set(x['title']) for x in possible.values())))
  states=snapshot(db,foundids)
  artist_names=collections.defaultdict(set)
  for a in db.execute("SELECT id::text,display_name name FROM artists WHERE status<>'archived' UNION SELECT a.id::text,al.alias FROM artist_aliases al JOIN artists a ON a.id=al.artist_id WHERE a.status<>'archived'"):
   artist_names[norm(a['name'])].add(a['id'])
  artistnative=collections.defaultdict(set)
  for e in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artist' AND (scheme ~ 'cleveland|aic|chicago|mia|met-')"):
   artistnative[e['scheme'],e['external_id']].add(e['entity_id'])
  selected=[];held=[];claimed={};batchacc={}
  for r in rows:
   matches=possible[r['key']];exact=matches['exact'];reason=r.get('editorial_hold')
   if not r.get('title'):reason='Missing source title; blank catalogue title not invented'
   elif r['date_decision']=='after_cutoff':reason='Explicit creation after 1970'
   elif re.search(r'\b(?:on loan|loan from|lent by|deaccessioned)\b',r.get('credit') or '',re.I):reason='Museum ownership not established by loan record'
   elif len(exact)>1:reason='Multiple existing physical-object identities'
   aid=exact[0] if len(exact)==1 else None
   if not aid and matches['title']:
    # A new inventory cannot silently overwrite another impression or version.
    concordant=[a for a in matches['title'] if states[a]['artwork']['accession_number'] is None and dates(r)[:2]==(states[a]['artwork']['creation_year_start'],states[a]['artwork']['creation_year_end']) and norm(states[a]['artwork'].get('unlinked_creator_label'))==norm(r.get('creator_label'))]
    if len(concordant)==1:aid=concordant[0]
    elif not r.get('accession_number'):reason='Same-museum title candidates require object/version separation'
   if aid:
    a=states[aid]['artwork']
    if a['status']=='archived' or a['current_institution_id'] not in [None,r['institution_id']]:reason='Existing archived record or different holding'
    holding=[v for v in states[aid]['holdings'] if v['claim_type']=='holding' and v['review_state']=='accepted' and not v['superseded_by']]
    if any(v['institution_id']!=r['institution_id'] for v in holding):reason='Existing accepted holding conflicts'
   batchkey=(r['institution_id'],norm(r.get('accession_number'))) if r.get('accession_number') else None
   if batchkey and batchkey in batchacc:reason='Source records share one accession; preserve in reconciliation evidence'
   if aid and aid in claimed:reason='Second source record resolves to already selected artwork'
   if reason:held.append(dict(record=r,reason=reason,matches=matches));continue
   if batchkey:batchacc[batchkey]=r['key']
   r['artwork_id']=aid or uid('artwork/'+r['key']);r['before']=states.get(aid);claimed[r['artwork_id']]=r['key']
   r['add_holding']=not aid or not any(v['claim_type']=='holding' and v['review_state']=='accepted' and not v['superseded_by'] for v in states[aid]['holdings'])
   r['first'],r['last'],r['precision']=dates(r)
   r['artist_id']=None
   label=(r.get('creator_label') or '').strip()
   # Source-qualified makers remain object-level wording, not false primary links.
   if label and ';' not in label and not re.search(r'\b(qualified|master|pracownia|kręgu|monogramista|bracia|attributed|after|copy|school|workshop|formerly|possibly|probably|follower|circle|unknown|anonymous)\b|傳|传|款|仿',label,re.I):
    simple=re.sub(r'^(Artist|Painter):\s*','',label).split('\n')[0].split(';')[0]
    simple=re.sub(r'\s*\([^)]*\)\s*$','',simple).strip()
    candidates=artist_names[norm(simple)]
    if len(candidates)==1:r['artist_id']=next(iter(candidates))
   if r['provider']=='npm':r['artist_id']=None # Historical catalogue attribution, retained verbatim.
   r['dimensions']=r['raw'].get('measurements') or r['raw'].get('dimensions') or r.get('dimensions')
   if r['dimensions'] is not None and not isinstance(r['dimensions'],str):r['dimensions']=json.dumps(r['dimensions'],ensure_ascii=False)
   r['holding_confidence']=.98
   r['holding_basis']='Exact official collection object/caption and native identifier or inventory; archival metadata, not a display assertion.'
   selected.append(r)
  usedartists=sorted({r['artist_id'] for r in selected if r['artist_id'] and not r['before']})
  artists={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(usedartists,))}
  queryplan=db.execute('EXPLAIN (FORMAT JSON) SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>%s ORDER BY id LIMIT 100',([i['id'] for i in instmap.values()],'archived')).fetchone()
 p=dict(at=now(),phase=phase,authorization='User: ok, import all data, I am not goint to verify them; then add Poland artists and galleries.',records=selected,held=held,institutions=instmap,new_institutions=newinst,artists=artists,existing_scope=len(scoped),query_plan=queryplan,source_capture_hashes=sorted({r['evidence']['sha256'] for r in rows}),input_sha256=sha((folder/'input-records.json.gz').read_bytes()))
 save(dest,p);save(folder/'plan-pin.json',dict(sha256=sha(dest.read_bytes())));save(BACKUP/phase/'plan-preimages.json.gz',p)
 print(json.dumps(dict(phase=phase,selected=len(selected),new=sum(not r['before'] for r in selected),existing=sum(bool(r['before']) for r in selected),new_institutions=len(newinst),linked_creators=sum(bool(r['artist_id']) and not r['before'] for r in selected),held=collections.Counter(x['reason'] for x in held))),flush=True)

def pinned(phase):
 p=RUN/phase/'plan.json.gz';digest=load(RUN/phase/'plan-pin.json')['sha256'];assert sha(p.read_bytes())==digest
 return load(p),digest
def apply(phase):
 p,digest=pinned(phase);folder=RUN/phase;assert not(folder/'applied.json').exists();assert load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'
 rows=p['records'];ids=[r['artwork_id'] for r in rows];sources={};data=collections.defaultdict(list)
 for r in rows:
  sk=r['provider']+'/'+r['museum'];sid=uid('source/'+sk)
  sources[sid]=dict(id=sid,slug=OP+'-'+sha(sk.encode())[:14],name=r.get('source_provider_name') or r['museum']+' — official catalogue',source_type='museum_api' if r['provider'] in ['cleveland','chicago','mia','met'] else 'collection_page',base_url='https://'+urlsplit(r['source_url']).netloc,adapter_key=OP)
  r['database_source_id']=sid
 with connect(True) as db,db.transaction():
  db.execute("SET LOCAL artline.actor_user_id=%s",(ACTOR,)) if False else None
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
  before=snapshot(db,ids);assert before=={r['artwork_id']:r['before'] for r in rows if r['before']},'Concurrent artwork drift'
  oldinst={i['id']:i for i in p['institutions'].values() if i['id'] not in {n['id'] for n in p['new_institutions']}}
  actual={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(list(oldinst),))};assert actual==oldinst
  actualartists={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(list(p['artists']),))};assert actualartists==p['artists']
  locked=dict(plan_sha256=digest,artworks=before,institutions=actual,artists=actualartists)
  bp=BACKUP/phase/'locked-before.json.gz'
  if bp.exists():assert {k:v for k,v in load(bp).items() if k!='at'}==locked
  else:save(bp,dict(at=now(),**locked))
  batch_insert(db,'institutions',p['new_institutions'])
  existing_sources={str(x['id']) for x in db.execute('SELECT id FROM sources WHERE id=ANY(%s::uuid[])',(list(sources),))}
  batch_insert(db,'sources',[s for sid,s in sources.items() if sid not in existing_sources])
  existing_keys={(e['scheme'],e['external_id']):str(e['entity_id']) for e in db.execute("SELECT scheme,external_id,entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s)",(list({r['scheme'] for r in rows}),))}
  for r in rows:
   aid=r['artwork_id'];sid=r['database_source_id'];label=r.get('creator_label');culture=r.get('culture')
   if isinstance(culture,list):culture='; '.join(culture)
   culture=(culture.strip() or None) if isinstance(culture,str) else None
   if culture and ('verification pending' in culture or 'individual attribution retained' in culture):culture=None
   if not r['before']:
    data['artworks'].append(dict(id=aid,slug=OP+'-'+sha(r['key'].encode())[:20],title=r['title'],alternate_title=r['raw'].get('original_title'),normalized_title=norm(r['title']),date_display=r.get('date_display') or 'Date unknown',creation_year_start=r['first'],creation_year_end=r['last'],date_precision=r['precision'],work_type=worktype(r),medium_text=r.get('medium'),dimensions_text=r.get('dimensions'),accession_number=r.get('accession_number'),status='review',research_candidate=True,unlinked_creator_label=None if r['artist_id'] else (label.strip() if label and label.strip() else None),cultural_context=culture,created_by=ACTOR,updated_by=ACTOR))
    if r['artist_id']:data['artwork_artists'].append(dict(artwork_id=aid,artist_id=r['artist_id'],attribution_role='primary',representative_order=1,attribution_note='Exact unique existing creator name/alias; original museum wording: '+label+'. '+r['source_url']))
   k=(r['scheme'],r['source_id'])
   if k in existing_keys:assert existing_keys[k]==aid
   else:data['external_identifiers'].append(dict(id=uid('identifier/'+r['key']),entity_type='artwork',entity_id=aid,scheme=r['scheme'],external_id=r['source_id'],canonical_url=r['source_url'],source_id=sid,retrieved_at=r['evidence']['retrieved_at']))
   note={k:v for k,v in r.items() if k not in ['before','local_matches']}
   note.update(plan_sha256=digest,confidence_interpretation='Editorial assessment, not a calibrated probability',publication='New record stays in review; existing state and fields preserved',date_policy='Unknown/review dates retained, no creator-life or excavation dates inferred',catalogue_unit='Source inventory record; cover/ensemble and component identifiers retained in raw evidence, not asserted as independent compositions')
   data['citations'].append(dict(id=uid('citation/'+phase+'/'+r['key']),entity_type='artwork',entity_id=aid,field_name='poland_collection_import_20261008',source_id=sid,source_record_id=r['source_id'],source_url=r['source_url'],evidence_note=json.dumps(note,ensure_ascii=False),retrieved_at=r['evidence']['retrieved_at'],created_by=ACTOR))
   if r['add_holding']:data['artwork_location_assertions'].append(dict(id=uid('holding/'+r['key']),artwork_id=aid,claim_type='holding',institution_id=r['institution_id'],context='collection',source_id=sid,source_url=r['source_url'],evidence_note=json.dumps(dict(confidence=r['holding_confidence'],basis=r['holding_basis'],source_sha256=r['evidence']['sha256'],inventory=r.get('accession_number'),scope='Documented collection record; no current display claim'),ensure_ascii=False),checked_at=r['evidence']['retrieved_at'],review_state='accepted'))
  for table in ['artworks','artwork_artists','external_identifiers','citations','artwork_location_assertions']:
   batch_insert(db,table,data[table]);print(phase,'inserted',table,len(data[table]),flush=True)
  after=snapshot(db,ids)
  for r in rows:
   a=after[r['artwork_id']]['artwork'];assert a['current_institution_id']==r['institution_id']
   if r['before']:
    old=r['before']['artwork'];assert {k:v for k,v in a.items() if k!='current_institution_id'}=={k:v for k,v in old.items() if k!='current_institution_id'}
    assert after[r['artwork_id']]['creators']==r['before']['creators'] and after[r['artwork_id']]['attachments']==r['before']['attachments']
   else:assert a['status']=='review' and a['published_at'] is None and a['primary_media_id'] is None and a['research_candidate']
  save(BACKUP/phase/'transaction-after.json.gz',dict(at=now(),artworks=after,plan_sha256=digest))
 receipt=dict(at=now(),phase=phase,target='production',plan_sha256=digest,new_artworks=len(data['artworks']),existing_records_enriched=len(rows)-len(data['artworks']),new_institutions=len(p['new_institutions']),new_creator_links=len(data['artwork_artists']),holding_assertions=len(data['artwork_location_assertions']),source_citations=len(data['citations']),held=len(p['held']),by_museum=dict(collections.Counter(r['museum'] for r in rows)),publication_changes=0,current_display_claims=0,local_database_changes=0,artwork_ids=ids)
 save(folder/'applied.json',receipt);print(json.dumps({k:v for k,v in receipt.items() if k!='artwork_ids'}),flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['backup','plan','apply']);parser.add_argument('phase',nargs='?',choices=['poland']);args=parser.parse_args()
 if args.action=='backup':backup()
 else:globals()[args.action](args.phase)
