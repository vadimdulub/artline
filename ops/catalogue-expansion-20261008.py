#!/usr/bin/env python3
"""Bounded, source-pinned catalogue expansion; reads by default, explicit apply only."""
import argparse,collections,datetime,gzip,hashlib,html,json,os,re,subprocess,time,unicodedata,uuid
from pathlib import Path
from urllib.parse import urljoin
import psycopg,requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/catalogue-expansion-20261008'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/catalogue-expansion-20261008';ACTOR='local-european-research'
AIC_SCHEMES=['aic-object','european-chicago-art-institute-of-chicago-object'];FIELD='catalogue_expansion_20261008'
LAST={};SESSION=requests.Session();SESSION.headers['User-Agent']='ArtlineCatalogue/1.0 (selected source-backed museum records; metadata only)'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def norm(v):return ' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',html.unescape(str(v or '')).casefold()) if not unicodedata.combining(c))))
def uid(v):return str(uuid.uuid5(uuid.NAMESPACE_URL,'artline/catalogue-expansion-20261008/'+v))
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True);b=json.dumps(obj,ensure_ascii=False,indent=2,default=str).encode();b=gzip.compress(b,mtime=0) if p.suffix=='.gz' else b
 if p.exists():assert p.read_bytes()==b,'Preserve evidence '+str(p)
 else:p.write_bytes(b)
def chunks(xs,n=500):
 for i in range(0,len(xs),n):yield xs[i:i+n]
def connect(write=False):
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319'],text=True).strip();kw=psycopg.conninfo.conninfo_to_dict(secret);kw.update(host='127.0.0.1',port='55519',sslmode='disable',connect_timeout=20)
 return psycopg.connect(**kw,autocommit=True,row_factory=dict_row,options='-c timezone=UTC -c statement_timeout=120000 -c lock_timeout=15000'+('' if write else ' -c default_transaction_read_only=on'))
def capture(url,params=None,pace=1.1):
 request=requests.Request('GET',url,params=params).prepare();url=request.url;key=sha(url.encode());p=RUN/'captures'/(key+'.json');body=p.with_suffix('.body.gz')
 if p.exists():
  receipt=load(p);raw=gzip.decompress(body.read_bytes());assert sha(raw)==receipt['sha256'];return raw,receipt
 host=url.split('/')[2];time.sleep(max(0,LAST.get(host,0)+pace-time.monotonic()));LAST[host]=time.monotonic()
 response=SESSION.get(url,timeout=(15,60));raw=response.content;assert len(raw)<15_000_000
 receipt=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=now(),bytes=len(raw),sha256=sha(raw),body_path=str(body.relative_to(ROOT)))
 body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(raw,mtime=0));save(p,receipt)
 if response.status_code in [403,429]:raise RuntimeError('Source access restriction; stop this source: '+str(response.status_code))
 return raw,receipt

def snapshot():
 path=RUN/'production-baseline.json.gz'
 if path.exists():print('Baseline already pinned');return
 with connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
  inst=[x['r'] for x in db.execute("SELECT to_jsonb(i) r FROM institutions i WHERE slug=ANY(%s)",(['art-institute-of-chicago','africa-almada'],))];assert len(inst)==2
  iids=[x['id'] for x in inst]
  works=[x['r'] for x in db.execute("SELECT to_jsonb(a) r FROM artworks a WHERE current_institution_id=ANY(%s::uuid[]) OR id IN (SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s))",(iids,AIC_SCHEMES))];ids=[x['id'] for x in works]
  relations={}
  for t,col in [('artwork_artists','artwork_id'),('artwork_media','artwork_id'),('artwork_location_assertions','artwork_id'),('citations','entity_id'),('external_identifiers','entity_id')]:
   relations[t]=[x['r'] for x in db.execute(f'SELECT to_jsonb(t) r FROM {t} t WHERE {col}=ANY(%s::uuid[])',(ids,))]
  artists=[x['r'] for x in db.execute('SELECT to_jsonb(a) r FROM artists a')]
  aliases=[dict(x) for x in db.execute('SELECT artist_id::text,alias,normalized_alias FROM artist_aliases')]
  artist_external=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist'")]
  sources=[x['r'] for x in db.execute("SELECT to_jsonb(s) r FROM sources s WHERE base_url ILIKE ANY(%s) OR name ILIKE ANY(%s)",(['%artic.edu%','%villadesarts.ma%'],['%Chicago%','%Al Mada%']))]
 result=dict(at=now(),institutions=inst,artworks=works,relations=relations,artists=artists,artist_aliases=aliases,artist_external=artist_external,sources=sources)
 save(path,result);BACKUP.mkdir(parents=True,exist_ok=True);BACKUP.chmod(0o700);save(BACKUP/'production-baseline.json.gz',result)
 print('Pinned baseline:',len(works),'scoped artworks;',len(artists),'artist authorities;',len(aliases),'aliases',flush=True)

def morocco():
 out=[];held=[];leads=load(RUN/'morocco-leads.json')
 for n,lead in enumerate(leads,1):
  raw,rc=capture(lead['url'],pace=.6)
  if rc['status']!=200:held.append(dict(key=lead['reference'],reason='source_unavailable',receipt=rc));continue
  soup=BeautifulSoup(raw,'html.parser');main=soup.select_one('main') or soup;text=main.get_text('\n',strip=True);fields={}
  for label in ['Artiste','Technique','Dimensions',"Année d'exécution",'Type','Support','Référence']:
   hit=re.search(re.escape(label)+r'\s*:\s*\n([^\n]+)',text)
   if hit:fields[label]=hit[1].strip()
  if fields.get('Référence')!=lead['reference']:held.append(dict(key=lead['reference'],reason='reference_conflict',fields=fields,receipt=rc));continue
  date=fields.get("Année d'exécution",'');kind={'Peinture':'painting','Dessin':'drawing','Sculpture':'sculpture','Céramique':'ceramic'}.get(fields.get('Type'))
  if not re.fullmatch(r'\d{4}',date) or int(date)>1970 or not kind:held.append(dict(key=lead['reference'],reason='date_or_type_unresolved',fields=fields,receipt=rc));continue
  out.append(dict(key='villa/'+lead['reference'],title=lead['title'],creator_label=fields['Artiste'],source_id=lead['reference'],source_url=rc['final_url'].split('?')[0],source_kind='villa',date_display=date,first=int(date),last=int(date),date_precision='exact',work_type=kind,medium='; '.join(filter(None,[fields.get('Technique'),fields.get('Support')])),dimensions=fields.get('Dimensions'),accession=lead['reference'],creation_place=None,receipt=rc,raw_fields=fields,creator_index_label=lead['creator'],identity_basis='Exact individual foundation inventory and execution-year field. Inventory numbers were discovery hints only; source execution field independently verified. No branch or current display assignment.'))
  if n%20==0:print('Morocco source pages',n,'/',len(leads),'accepted',len(out),'held',len(held),flush=True)
 save(RUN/'morocco-selected.json.gz',out);save(RUN/'morocco-held.json.gz',held);print('Morocco selected',len(out),'held',len(held),flush=True)

FIELDS='id,title,alt_titles,main_reference_number,date_start,date_end,date_display,date_qualifier_title,artist_display,artist_title,artist_id,artist_ids,artist_titles,place_of_origin,dimensions,medium_display,credit_line,fiscal_year_deaccession,artwork_type_title,department_title,is_public_domain,copyright_notice,source_updated_at,classification_titles,term_titles,artist_pivots'
TYPES={'Painting':'painting','Miniature Painting':'painting','Print':'print','Drawing and Watercolor':'drawing','Architectural Drawing':'drawing','Sculpture':'sculpture','Ceramics':'ceramic','Metalwork':'metalwork','Textile':'textile','Photograph':'photograph'}

def aic():
 base=load(RUN/'production-baseline.json.gz');known_ids={x['external_id'] for x in base['relations']['external_identifiers'] if x['scheme'] in AIC_SCHEMES};known_acc={norm(x['accession_number']) for x in base['artworks'] if x['current_institution_id']==next(i['id'] for i in base['institutions'] if i['slug']=='art-institute-of-chicago') and x['accession_number']}
 selected={};held=[];blocked=False;groups=[('africa',{'term':{'department_title.keyword':'Arts of Africa'}},700),('egypt',{'match_phrase':{'place_of_origin':'Egypt'}},250),('greece-byzantium',{'term':{'department_title.keyword':'Arts of Greece, Rome, and Byzantium'}},300),('russia',{'match_phrase':{'place_of_origin':'Russia'}},200),('asia',{'term':{'department_title.keyword':'Arts of Asia'}},2200),('paintings',{'terms':{'artwork_type_title.keyword':['Painting','Miniature Painting']}},900),('drawings',{'term':{'artwork_type_title.keyword':'Drawing and Watercolor'}},2000),('prints',{'term':{'artwork_type_title.keyword':'Print'}},2500)]
 # Never more than 9,050 bounded index candidates, below the provider's 10k guidance.
 for group,extra,cap in groups:
  for page in range(1,cap//100+1):
   params={'query':{'bool':{'filter':[{'range':{'date_end':{'lte':1970}}},{'terms':{'artwork_type_title.keyword':list(TYPES)}},extra]}},'fields':FIELDS.split(','),'include':['artist_pivots'],'limit':100,'page':page}
   raw,rc=capture('https://api.artic.edu/api/v1/artworks/search',{'params':json.dumps(params,separators=(',',':'))})
   if rc['status']!=200:
    held.append(dict(group=group,reason='source_access_stopped',receipt=rc));blocked=True;break
   data=json.loads(raw);items=data['data']
   for w in items:
    key=str(w['id']);reason=None
    if key in known_ids or norm(w.get('main_reference_number')) in known_acc:reason='already_in_catalogue'
    elif key in selected:continue
    elif w.get('fiscal_year_deaccession'):reason='deaccessioned'
    elif re.search(r'\b(?:loan|lent|deposit|courtesy)\b',w.get('credit_line') or '',re.I):reason='loan_or_ownership_qualification'
    elif not w.get('main_reference_number') or not w.get('title') or not w.get('artist_display'):reason='identity_fields_incomplete'
    elif w.get('date_start') is None or w.get('date_end') is None or not -10000<=w['date_start']<=w['date_end']<=1970 or not w.get('date_display'):reason='date_scope_unresolved'
    elif re.search(r'\b(?:after|undated|unknown|n\.d\.|reprint|printed later|later print|later cast)\b',w['date_display'],re.I):reason='date_qualification_needs_individual_research'
    if reason:held.append(dict(key=key,group=group,reason=reason));continue
    selected[key]=dict(group=group,raw=w,receipt=rc,source_url='https://www.artic.edu/artworks/'+key)
   print('AIC',group,'page',page,'new selected',len(selected),flush=True)
   if len(selected)>=3600:break
   if len(items)<100:break
  if blocked or len(selected)>=3600:break
 save(RUN/'aic-candidates.json.gz',list(selected.values()));save(RUN/'aic-index-held.json.gz',held)
 print('AIC candidates',len(selected),dict(collections.Counter(x['group'] for x in selected.values())),flush=True)

CMA_SCHEMES=['cleveland-object','european-cleveland-cleveland-museum-of-art-object']
CMA_TYPES={'Painting':'painting','Portrait Miniature':'painting','Drawing':'drawing','Print':'print','Photograph':'photograph','Sculpture':'sculpture','Relief':'sculpture','Ceramic':'ceramic','Metalwork':'metalwork','Silver':'metalwork','Textile':'textile','Tapestry':'textile','Embroidery':'textile','Illumination':'manuscript_illumination','Calligraphy':'calligraphy'}

def cleveland():
 path=RUN/'cleveland-baseline.json.gz'
 if not path.exists():
  with connect() as db:
   museum=db.execute("SELECT to_jsonb(i) r FROM institutions i WHERE slug='cleveland-museum-of-art'").fetchone()['r']
   works=[x['r'] for x in db.execute('SELECT to_jsonb(a) r FROM artworks a WHERE current_institution_id=%s',(museum['id'],))]
   ids=[x['id'] for x in works]
   ext=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE (entity_type='artwork' AND scheme=ANY(%s)) OR entity_id=ANY(%s::uuid[])",(CMA_SCHEMES,ids))]
   sources=[x['r'] for x in db.execute("SELECT to_jsonb(s) r FROM sources s WHERE base_url ILIKE '%clevelandart.org%' OR name ILIKE '%Cleveland%'")]
  save(path,dict(at=now(),institution=museum,artworks=works,external=ext,sources=sources))
 b=load(path);known_ids={x['external_id'] for x in b['external'] if x['scheme'] in CMA_SCHEMES};known_acc={norm(x['accession_number']) for x in b['artworks'] if x['accession_number']};known_qids={x['external_id'] for x in b['external'] if x['scheme']=='wikidata'}
 fields='id,accession_number,title,creation_date,creation_date_earliest,creation_date_latest,culture,technique,type,measurements,creators,legal_status,record_type,cover_accession_number,creditline,url,external_resources,share_license_status,copyright,department,description,edition_of_the_work,state_of_the_work,updated_at'
 selected={};held=[]
 for department,cap in [('African Art',600),('Egyptian and Ancient Near Eastern Art',1200),('Greek and Roman Art',600),('Medieval Art',500),('Japanese Art',700),('Chinese Art',700),('Indian and South East Asian Art',700)]:
  for skip in range(0,cap,100):
   raw,rc=capture('https://openaccess-api.clevelandart.org/api/artworks/',dict(department=department,created_before=1971,limit=100,skip=skip,fields=fields))
   assert rc['status']==200;data=json.loads(raw);items=data['data']
   for w in items:
    key=str(w['id']);reason=None;first=w.get('creation_date_earliest');last=w.get('creation_date_latest');date=w.get('creation_date') or ''
    qids={u.rsplit('/',1)[-1] for u in (w.get('external_resources') or {}).get('wikidata',[])}
    if key in known_ids or norm(w.get('accession_number')) in known_acc or qids&known_qids:reason='already_in_catalogue'
    elif key in selected:continue
    elif w.get('legal_status')!='accessioned':reason='collection_status_not_accessioned'
    elif w.get('record_type')!='object' or w.get('cover_accession_number'):reason='part_or_ensemble_requires_individual_review'
    elif w.get('type') not in CMA_TYPES:reason='type_mapping_unresolved'
    elif not w.get('accession_number') or not w.get('title'):reason='identity_fields_incomplete'
    elif first is None or last is None or not -10000<=first<=last<=1970 or not date:reason='date_scope_unresolved'
    elif re.search(r'\b(?:after|undated|unknown|later print|later cast|printed later|reprint)\b',date,re.I):reason='date_qualification_requires_individual_research'
    if reason:held.append(dict(key=key,department=department,reason=reason));continue
    selected[key]=dict(raw=w,receipt=rc,source_url=w['url'].replace('http:','https:'),group=department)
   print('Cleveland',department,skip+len(items),'selected',len(selected),flush=True)
   if len(selected)>=1900 or len(items)<100:break
  if len(selected)>=1900:break
 save(RUN/'cleveland-candidates.json.gz',list(selected.values()));save(RUN/'cleveland-held.json.gz',held)
 print('Cleveland selected',len(selected),dict(collections.Counter(x['group'] for x in selected.values())),flush=True)

def aic_details():
 # The index returned a documented result-window error at offset 1000.
 # No access/authentication restriction occurred. Selected-ID detail reads are
 # bounded separate endpoints, recommended by the provider's documentation.
 candidates=load(RUN/'aic-candidates.json.gz');details={}
 for part in chunks([str(x['raw']['id']) for x in candidates],100):
  raw,rc=capture('https://api.artic.edu/api/v1/artworks',dict(ids=','.join(part),limit=100,fields=FIELDS,include='artist_pivots'))
  assert rc['status']==200;data=json.loads(raw)['data'];assert {str(w['id']) for w in data}==set(part)
  for w in data:details[str(w['id'])]=dict(raw=w,receipt=rc)
  print('Selected Chicago details',len(details),'/',len(candidates),flush=True)
 save(RUN/'aic-details.json.gz',details)
 ids=sorted({int(i) for d in details.values() for i in d['raw'].get('artist_ids',[])})
 artists={}
 for part in chunks(ids,100):
  raw,rc=capture('https://api.artic.edu/api/v1/artists',dict(ids=','.join(map(str,part)),limit=100,fields='id,title,sort_title,alt_titles,is_artist,agent_type_title,birth_date,death_date,wikidata_id,ulan_id,description,source_updated_at'))
  assert rc['status']==200;data=json.loads(raw)['data']
  for a in data:artists[str(a['id'])]=dict(raw=a,receipt=rc)
  print('Chicago creator authorities',len(artists),'/',len(ids),flush=True)
 save(RUN/'aic-artist-authorities.json.gz',artists)

def date_precision(text,first,last):
 if re.search(r'\bbefore\b',text,re.I):return 'before'
 if re.search(r'\bcentur(?:y|ies)\b',text,re.I):return 'century'
 uncertain=bool(re.search(r'(?:\bc\.|\bca\.|circa|about|approx|probably|early|mid|late|\?)',text,re.I))
 return ('circa' if first==last else 'circa_range') if uncertain else ('exact' if first==last else 'range')

def prepare():
 b=load(RUN/'production-baseline.json.gz');cma=load(RUN/'cleveland-baseline.json.gz');authorities=load(RUN/'aic-artist-authorities.json.gz')
 museums={x['slug']:x for x in b['institutions']+[cma['institution']]}
 sources={x['slug']:x for x in b['sources']+cma['sources']}
 cma_source=next((s for s in cma['sources'] if s['slug']=='cleveland-museum-of-art'),None)
 if cma_source is None:cma_source=next(s for s in cma['sources'] if s['source_type']=='museum_api' and s['is_active'])
 source_map={'aic':sources['art-institute-of-chicago'],'villa':sources['africa-research-20261008-villadesarts-ma'],'cma':cma_source}
 institution_map={'aic':museums['art-institute-of-chicago'],'villa':museums['africa-almada'],'cma':museums['cleveland-museum-of-art']}
 existing={a['id']:a for a in b['artists']};names=collections.defaultdict(set);qids=collections.defaultdict(set);source_artist_ids=collections.defaultdict(set)
 def namekey(s):return ' '.join(sorted(norm(s).split()))
 for a in b['artists']:names[namekey(a['display_name'])].add(a['id'])
 for a in b['artist_aliases']:names[namekey(a['alias'])].add(a['artist_id'])
 for e in b['artist_external']:
  if e['scheme']=='wikidata':qids[e['external_id']].add(e['entity_id'])
  source_artist_ids[(e['scheme'],e['external_id'])].add(e['entity_id'])
 decisions={};new_artists=[]
 for sid,entry in authorities.items():
  a=entry['raw'];result=dict(source_artist_id=sid,source_name=a['title'],source_record=entry)
  if a.get('agent_type_title')!='Individual':result.update(outcome='cultural_or_organizational_label',artist_id=None);decisions[sid]=result;continue
  exact=qids.get(a.get('wikidata_id'),set())|source_artist_ids.get(('aic-artist',sid),set())
  matches=set()
  for label in [a['title']]+(a.get('alt_titles') or []):
   key=namekey(label)
   if len(key.split())>=2 or label==a['title']:matches.update(names[key])
  possible={aid for aid in matches if existing[aid]['status']!='archived' and all(not a.get(k) or not existing[aid].get(field) or a[k]==existing[aid][field] for k,field in [('birth_date','birth_year'),('death_date','death_year')])}
  if exact:possible={i for i in exact if existing[i]['status']!='archived'}
  if len(possible)==1:
   result.update(outcome='matched_existing',artist_id=next(iter(possible)),basis='Exact source authority identifier or unique full-name/alias match with no conflicting supplied lifespan; source creator identity and original labels preserved.')
  elif possible or matches or exact:result.update(outcome='ambiguous_existing_identity',artist_id=None,possible_ids=sorted(possible or matches or exact))
  else:
   birth=a.get('birth_date');death=a.get('death_date');label=a['title']
   if birth is None or death is None or not -10000<birth<death<=2026 or not 5<=death-birth<=125 or re.search(r'\b(?:unknown|unidentified|anonymous|master|painter|school|workshop|kiln)\b',label,re.I):
    result.update(outcome='retain_object_creator_label',artist_id=None)
   else:
    aid=uid('artist/aic/'+sid);slug='aic-artist-'+sid+'-'+re.sub('[^a-z0-9]+','-',norm(label)).strip('-')[:100]
    row=dict(id=aid,slug=slug,display_name=label,sort_name=a.get('sort_title') or label,normalized_name=norm(label),birth_year=birth,death_year=death,birth_display=str(birth),death_display=str(death),birth_precision='exact',death_precision='exact',timeline_start_year=birth,timeline_end_year=death,timeline_display=f'{birth}–{death}',timeline_basis='life',entity_type='person',source_kind='aic',source_artist_id=sid,source_url='https://www.artic.edu/artists/'+sid,receipt=entry['receipt'],source_record=a,aliases=list(dict.fromkeys(a.get('alt_titles') or [])))
    new_artists.append(row);result.update(outcome='create_source_backed_artist',artist_id=aid,basis='Official museum Individual authority with explicit birth and death fields; no existing name/alias/identifier match. Biography, nationality and movement not invented.')
  decisions[sid]=result
 output=[];held=[]
 def common(w):
  w.update(id=uid('artwork/'+w['key']),slug='collection-expansion-'+sha(w['key'].encode())[:24],institution_id=institution_map[w['source_kind']]['id'],institution_name=institution_map[w['source_kind']]['name'],source_database_id=source_map[w['source_kind']]['id'],confidence=.98,confidence_basis='Individual museum catalogue identity with stable inventory number and dated collection record; editorial assessment, not a calibrated probability. Holdings do not assert current display.')
  w.setdefault('artist_id',None);w.setdefault('attribution_role','primary');w.setdefault('cultural_context',None);w.setdefault('object_form',None);w.setdefault('description',None);w.setdefault('creator_basis','Source creator or culture label retained without inventing a painter authority.')
  if w.get('creator_label') and len(w['creator_label'])>500:held.append(dict(key=w['key'],reason='creator_label_exceeds_schema'));return
  if w.get('cultural_context') and len(w['cultural_context'])>500:held.append(dict(key=w['key'],reason='culture_label_exceeds_schema'));return
  output.append(w)
 for w in load(RUN/'morocco-selected.json.gz'):
  candidates=names[namekey(w['creator_label'])];eligible=[i for i in candidates if existing[i]['status']!='archived']
  if len(eligible)==1:w.update(artist_id=eligible[0],creator_basis='Unique exact full-name tokens in the museum creator label and existing artist authority; original French surname-first label preserved.')
  w['external_scheme']='morocco-africa-object';w['external_id']=w['key'];common(w)
 details=load(RUN/'aic-details.json.gz')
 for x in load(RUN/'aic-candidates.json.gz'):
  sid=str(x['raw']['id']);detail=details[sid];a=detail['raw'];key='aic/'+sid
  if a.get('date_qualifier_title') in ['Original',"Artist's working dates",'Found']:
   held.append(dict(key=key,reason='date_is_original_model_artist_activity_or_discovery',qualifier=a['date_qualifier_title']));continue
  assert a['main_reference_number']==x['raw']['main_reference_number'] and a['date_start']==x['raw']['date_start'] and a['date_end']==x['raw']['date_end']
  creator=a.get('artist_display');culture=None;artist=None;basis=None;role='primary'
  pivots=[p for p in a.get('artist_pivots',[]) if p.get('role_title') in ['Artist','Carver','Engraver','Designer']]
  primary=next((p for p in pivots if p.get('is_preferred')),pivots[0] if len(pivots)==1 else None)
  if primary:
   d=decisions.get(str(primary['artist_id']),{});qualified=re.search(r'\b(?:after|workshop|studio|circle|school|follower|formerly|possibly|probably|attributed|copy|style of|manner of)\b',creator or '',re.I)
   if d.get('artist_id') and not qualified:artist=d['artist_id'];basis=d['basis']
   elif d.get('artist_id') and re.match(r'Attributed to\b',creator or '',re.I):artist=d['artist_id'];basis=d['basis']+' Explicit attributed-to qualification retained.';role='attributed_to'
  if not pivots and all(p.get('role_title')=='Culture' for p in a.get('artist_pivots',[])):
   culture=creator;creator=None
  kind=TYPES[a['artwork_type_title']]
  if kind=='drawing' and re.search(r'\bwatercolou?r\b',a.get('medium_display') or '',re.I):kind='watercolor'
  w=dict(key=key,source_kind='aic',source_id=sid,source_url=x['source_url'],receipt=detail['receipt'],raw_fields=a,title=a['title'],creator_label=creator,cultural_context=culture,artist_id=artist,attribution_role=role,creator_basis=basis or 'Unresolved or cultural creator identity retained exactly at object level; no unqualified painter assignment.',date_display=a['date_display'],first=a['date_start'],last=a['date_end'],date_precision=date_precision(a['date_display'],a['date_start'],a['date_end']),work_type=kind,medium=a.get('medium_display'),dimensions=a.get('dimensions'),accession=a['main_reference_number'],creation_place=a.get('place_of_origin'),external_scheme='aic-object',external_id=sid,group=x['group'],identity_basis='Official selected-ID API record confirms accession, type, date range and museum collection; deaccessioned and loan-qualified candidates excluded.',object_form='icon' if any(norm(t) in ['icon','icons'] for t in a.get('term_titles',[])) and kind=='painting' else None)
  common(w)
 for x in load(RUN/'cleveland-candidates.json.gz'):
  a=x['raw'];key='cma/'+str(a['id']);creators=a.get('creators') or [];labels=[];artist=None
  for creator in creators:
   text=' '.join(filter(None,[creator.get('qualifier'),creator.get('description')]))
   if creator.get('extent') and creator['extent'] not in text:text=creator['extent']+' '+text
   labels.append(text)
  if len(creators)==1 and not creators[0].get('qualifier'):
   c=creators[0];exact=source_artist_ids.get(('cleveland-creator',str(c['id'])),set());title=c.get('description','').split('(')[0].strip();matches=exact or names[namekey(title)]
   def compatible(i):
    return existing[i]['status']!='archived' and all(not str(c.get(k) or '').isdigit() or not existing[i].get(f) or int(c[k])==existing[i][f] for k,f in [('birth_year','birth_year'),('death_year','death_year')])
   matches={i for i in matches if compatible(i)}
   if len(matches)==1:artist=next(iter(matches))
  culture='; '.join(a.get('culture') or []) or None
  w=dict(key=key,source_kind='cma',source_id=str(a['id']),source_url=x['source_url'],receipt=x['receipt'],raw_fields=a,title=a['title'],creator_label='; '.join(labels) or None,cultural_context=culture,artist_id=artist,date_display=a['creation_date'],first=a['creation_date_earliest'],last=a['creation_date_latest'],date_precision=date_precision(a['creation_date'],a['creation_date_earliest'],a['creation_date_latest']),work_type=CMA_TYPES[a['type']],medium=a.get('technique'),dimensions=a.get('measurements'),accession=a['accession_number'],creation_place=None,external_scheme='cleveland-object',external_id=str(a['id']),group=x['group'],identity_basis='Museum API explicitly marks the individual inventory record accessioned and object-level; parts/components and loans excluded.',description=BeautifulSoup(a.get('description') or '', 'html.parser').get_text('\n',strip=True) or None)
  if artist:w['creator_basis']='Exact museum creator authority identifier or unique exact full name, with no supplied lifespan conflict. Unqualified source creator label retained.'
  common(w)
 # Only create painter records actually used by selected artworks.
 used={w['artist_id'] for w in output if w['artist_id']};new_artists=[a for a in new_artists if a['id'] in used]
 result=dict(at=now(),authorization='User: nice, add 2000-5000 records, you can add more painters if needed. Continues explicit production publication and keep-known-information-only preferences. Africa first, then worldwide museum connections.',artworks=output,artists=new_artists,creator_decisions=decisions,sources=list(source_map.values()),institutions=list(institution_map.values()),held=held)
 save(RUN/'candidate-plan.json.gz',result)
 print('Prepared',len(output),'artworks;',len(new_artists),'new artists;',len(held),'held',dict(collections.Counter(w['source_kind'] for w in output)),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['snapshot','morocco','aic','cleveland','aic_details','prepare']);args=p.parse_args();globals()[args.action]()
