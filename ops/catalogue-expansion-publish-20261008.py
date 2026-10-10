#!/usr/bin/env python3
"""Selected museum metadata, production INSERTs only; immutable plan and receipts."""
import argparse, collections, copy, csv, gzip, importlib.util, json, re
from pathlib import Path
from psycopg import sql
from psycopg.types.json import Jsonb

spec=importlib.util.spec_from_file_location('research',Path(__file__).with_name('catalogue-expansion-20261008.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
DRAFT=m.RUN/'publication-plan.json.gz'
PLAN=m.RUN/'publication-plan-final.json.gz'
QUALIFIED=r'\b(?:after|workshop|studio|circle|school|follower|formerly|possibly|probably|attributed|copy|style of|manner of)\b'

def safe(value):return json.loads(json.dumps(value,default=str))
def records(db,table,ids,column='id'):
 return [r['r'] for r in db.execute(sql.SQL('SELECT to_jsonb(t) r FROM {} t WHERE {}=ANY(%s::uuid[]) ORDER BY {}').format(sql.Identifier(table),sql.Identifier(column),sql.Identifier('artwork_id' if table in ['artwork_artists','artwork_media'] else 'id')),(ids,))]
def receipt_raw(receipt):
 assert receipt['status']==200
 raw=gzip.decompress((m.ROOT/receipt['body_path']).read_bytes());assert m.sha(raw)==receipt['sha256'],'Source capture changed'
 return raw
def qids(w):
 return list(dict.fromkeys(u.rsplit('/',1)[-1] for u in w['raw_fields'].get('external_resources',{}).get('wikidata',[]) if re.fullmatch(r'Q\d+',u.rsplit('/',1)[-1]))) if w['source_kind']=='cma' else []
def keys(w):
 schemes={'aic':m.AIC_SCHEMES,'cma':m.CMA_SCHEMES,'villa':['morocco-africa-object','morocco-africa-object-20261008']}[w['source_kind']]
 return [(s,w['external_id']) for s in schemes]+[('wikidata',q) for q in qids(w)]
def duplicate_audit(db,works):
 requested=list(dict.fromkeys((s,v) for w in works for s,v in keys(w)))
 external=[]
 for part in m.chunks(requested,500):
  external+=safe(db.execute('''SELECT e.entity_id::text,e.scheme,e.external_id,e.canonical_url FROM jsonb_to_recordset(%s) AS p(scheme text,external_id text)
   JOIN external_identifiers e USING(scheme,external_id) WHERE e.entity_type='artwork' ''',(Jsonb([dict(scheme=s,external_id=v) for s,v in part]),)).fetchall())
 urls=list(dict.fromkeys(u for w in works for u in [w['source_url'],w['source_url'].replace('https:','http:')]))
 citations=[]
 for part in m.chunks(urls,500):
  citations+=safe(db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(part,)).fetchall())
  external+=safe(db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(part,)).fetchall())
 institutions=sorted({w['institution_id'] for w in works})
 scoped=safe(db.execute('SELECT id::text,current_institution_id::text,title,accession_number FROM artworks WHERE current_institution_id=ANY(%s::uuid[])',(institutions,)).fetchall())
 bykey=collections.defaultdict(set);byurl=collections.defaultdict(set);byacc=collections.defaultdict(set);bytitle=collections.defaultdict(set)
 for e in external:
  bykey[(e['scheme'],e['external_id'])].add(e['entity_id'])
  if e.get('canonical_url'):byurl[e['canonical_url'].replace('http:','https:').rstrip('/')].add(e['entity_id'])
 for e in citations:byurl[e['source_url'].replace('http:','https:').rstrip('/')].add(e['entity_id'])
 for e in scoped:
  if e['accession_number']:byacc[(e['current_institution_id'],m.norm(e['accession_number']))].add(e['id'])
  else:bytitle[(e['current_institution_id'],m.norm(e['title']))].add(e['id'])
 found={}
 for w in works:
  matches=set().union(*(bykey[k] for k in keys(w)))|byurl[w['source_url'].rstrip('/')]|byacc[(w['institution_id'],m.norm(w['accession']))]|bytitle[(w['institution_id'],m.norm(w['title']))]
  if matches:found[w['key']]=sorted(matches)
 return dict(at=m.now(),matches=found,external_matches=external,citation_matches=citations,scoped_existing_count=len(scoped))

def validate(plan):
 works=plan['artworks'];artists=plan['artists']
 assert 2000<=len(works)<=5000
 assert len({w['id'] for w in works})==len(works)==len({w['key'] for w in works})
 assert len({(w['external_scheme'],w['external_id']) for w in works})==len(works)
 assert len({a['id'] for a in artists})==len(artists)
 source_map={s['id']:s for s in plan['sources']};inst={i['id']:i for i in plan['institutions']}
 parsed={}
 for r in works+artists:
  rc=r['receipt'];k=rc['sha256']
  if k not in parsed:
   raw=receipt_raw(rc)
   if r['source_kind']=='villa':
    position=raw.find(b'artwork-content');assert position>=0
    parsed[k]=m.BeautifulSoup(raw[position:position+12000],'html.parser')
   else:parsed[k]={str(x['id']):x for x in json.loads(raw)['data']}
  raw=parsed[k]
  if r in artists:
   a=raw[r['source_artist_id']];assert a==r['source_record'] and a['agent_type_title']=='Individual'
   assert r['display_name']==a['title'] and r['birth_year']==a['birth_date'] and r['death_year']==a['death_date']
   assert r['timeline_start_year']==r['birth_year']<r['death_year']==r['timeline_end_year']
   continue
  w=r
  assert w['source_database_id'] in source_map and source_map[w['source_database_id']]['is_active']
  assert w['institution_id'] in inst and inst[w['institution_id']]['status']!='archived'
  assert isinstance(w['first'],int) and isinstance(w['last'],int) and -10000<=w['first']<=w['last']<=1970
  assert w['date_precision'] not in ['unknown','after'] and not (w['date_precision'] in ['circa','circa_range'] and w['last']==1970)
  assert w['title'] and w['date_display'] and w['accession'] and w['work_type']!='unknown'
  assert w['source_url'].startswith('https://') and w['confidence']>=.8
  assert not w.get('display_state') and not w.get('venue_id')
  if w['source_kind']=='villa':
   assert any(m.norm(h.get_text(' ',strip=True))==m.norm(w['title']) for h in raw.select('h1,h2'))
   text=raw.get_text('\n',strip=True)
   for label,value in w['raw_fields'].items():
    found=re.search(re.escape(label)+r'\s*:\s*\n([^\n]+)',text)
    assert found and found[1].strip()==value,('Foundation field',label)
   assert w['raw_fields']['Référence']==w['accession'] and int(w['raw_fields']["Année d'exécution"])==w['first']==w['last']
   assert w['creator_label']==w['raw_fields']['Artiste'] and w['date_display']==str(w['first'])
  else:
   a=raw[w['source_id']];assert a==w['raw_fields'] and a['title']==w['title']
   if w['source_kind']=='aic':
    assert w['first']==a['date_start'] and w['last']==a['date_end'] and w['accession']==a['main_reference_number']
    assert w['date_display']==a['date_display'] and w['medium']==a.get('medium_display') and w['dimensions']==a.get('dimensions')
    assert w['creator_label']==a['artist_display'] or w['creator_label'] is None and w['cultural_context']==a['artist_display'] or w.get('creator_label_source_line')==0 and w['creator_label']==a['artist_display'].splitlines()[0]
    assert a.get('date_qualifier_title') not in ['Original',"Artist's working dates",'Found'] and not a.get('fiscal_year_deaccession')
    assert not re.search(r'\b(?:loan|lent|deposit|courtesy)\b',a.get('credit_line') or '',re.I)
    if w['artist_id'] and w['attribution_role']=='primary':assert not re.search(QUALIFIED,w['creator_label'] or '',re.I)
   else:
    assert w['first']==a['creation_date_earliest'] and w['last']==a['creation_date_latest'] and w['accession']==a['accession_number']
    assert w['date_display']==a['creation_date'] and w['medium']==a.get('technique') and w['dimensions']==a.get('measurements')
    assert a['legal_status']=='accessioned' and a['record_type']=='object' and not a['cover_accession_number']
    if w['artist_id']:
     assert len(a['creators'])==1 and not a['creators'][0]['qualifier'] and a['creators'][0].get('role') in ['artist','painter','carver','weaver','potter','calligrapher','calligraphy by']
 return dict(artworks=len(works),artists=len(artists),verified_source_captures=len(parsed))

def prepare():
 plan=m.load(m.RUN/'candidate-plan.json.gz');baseline=m.load(m.RUN/'production-baseline.json.gz')
 decisions=[];retained=[]
 # Retain source labels when the museum's own authority and object biographies
 # disagree, contain activity dates, or overlap an existing transliterated identity.
 potential_existing={'34942','34969','57671','52271','40415','36665','42692'}
 for a in plan['artists']:
  labels=[w['creator_label'] or '' for w in plan['artworks'] if w['artist_id']==a['id']]
  consistent=all(re.search(r'(?<!\d)'+str(a['birth_year'])+r'\s*[-–—]\s*'+str(a['death_year'])+r'(?!\d)',s) and not re.search(r'\bactive\b|\bc\.|\bca\.|\?',s) for s in labels)
  if not consistent or a['source_artist_id'] in potential_existing or a['source_artist_id']=='35180':
   decisions.append(dict(source_artist_id=a['source_artist_id'],name=a['display_name'],reason='Conflicting/qualified or activity dates, or possible existing transliteration/name identity; retain object labels without new authority.'))
   for w in plan['artworks']:
    if w['artist_id']==a['id']:w['artist_id']=None;w['creator_basis']='Original museum creator label retained. New authority deferred due to uncertain lifespan or possible existing identity; evidence recorded in the publication plan.'
  else:retained.append(a)
 plan['artists']=retained;plan['authority_holds']=decisions
 for w in plan['artworks']:
  if w['source_kind']=='cma' and w['artist_id'] and w['raw_fields']['creators'][0].get('role') not in ['artist','painter','carver','weaver','potter','calligrapher','calligraphy by']:
   w['artist_id']=None;w['creator_basis']='Source contributor role preserved at object level, without converting a publisher or contributor into a primary creator.'
  if w['source_kind']=='villa':w['external_scheme']='morocco-africa-object-20261008'
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
  audit=duplicate_audit(db,plan['artworks']);m.save(m.RUN/'publication-duplicate-audit.json.gz',audit)
  seen=set();works=[]
  for w in plan['artworks']:
   if w['key'] in audit['matches']:plan['held'].append(dict(key=w['key'],reason='Existing catalogue identity or unresolved duplicate',existing_ids=audit['matches'][w['key']]));continue
   if set(keys(w))&seen:plan['held'].append(dict(key=w['key'],reason='Repeated native or Wikidata identity within batch'));continue
   works.append(w);seen.update(keys(w))
  plan['artworks']=works;used={w['artist_id'] for w in works if w['artist_id']};plan['artists']=[a for a in plan['artists'] if a['id'] in used]
  existing_ids=sorted(used-{a['id'] for a in plan['artists']})
  protected=dict(artists=records(db,'artists',existing_ids),institutions=records(db,'institutions',[i['id'] for i in plan['institutions']]),sources=records(db,'sources',[s['id'] for s in plan['sources']]))
  # Identity checks use the current directory, not only an earlier snapshot.
  known=list(db.execute('SELECT display_name,normalized_name FROM artists'))
  known_aliases={m.norm(r['alias']) for r in db.execute('SELECT alias FROM artist_aliases')}
  for a in plan['artists']:
   assert m.norm(a['display_name']) not in {m.norm(x['display_name']) for x in known}|known_aliases
  assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s) LIMIT 1',([w['id'] for w in works],[w['slug'] for w in works])).fetchone()
  assert not db.execute('SELECT 1 FROM artists WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s) LIMIT 1',([a['id'] for a in plan['artists']],[a['slug'] for a in plan['artists']])).fetchone()
 plan['at']=m.now();plan['authorization']='User requests 2,000–5,000 added records, more painters if needed, Africa first then worldwide, direct production publication; retain entries and show known information only.'
 plan['protected']=protected;plan['validation']=validate(plan)
 m.save(DRAFT,plan);m.BACKUP.mkdir(parents=True,exist_ok=True);m.BACKUP.chmod(0o700);m.save(m.BACKUP/DRAFT.name,plan)
 print('Publication plan',plan['validation'],'by source',dict(collections.Counter(w['source_kind'] for w in plan['artworks'])),'SHA256',m.sha(DRAFT.read_bytes()),flush=True)

def finalize():
 plan=m.load(DRAFT);sources=[]
 for url,year in [('https://www.musee-orsay.fr/en/ressources/artists-personalities-catalog/georges-hanna-sabbagh-114891',1877),('https://www.centrepompidou.fr/en/ressources/oeuvre/cR548Xy',1887)]:
  sources.append(dict(url=url,birth_year_in_public_search_excerpt=year,retrieved_at=m.now(),use='Negative evidence only: defer painter lifespan. Orsay direct HTTP fetch returned 403 and was not retried or bypassed.'))
 plan['authority_conflict_sources']=sources
 removed={a['id']:a for a in plan['artists'] if a['source_artist_id'] in ['42280','32937']}
 for a in removed.values():
  reason='Sabbagh birth conflict: Chicago/Orsay 1877 versus Pompidou 1887; retain only object creator name, original dated label in citation.' if a['source_artist_id']=='42280' else 'Museum authority aliases name Alexander Tillander, while object label names Alfred Tillander; retain object label without merging people.'
  plan['authority_holds'].append(dict(source_artist_id=a['source_artist_id'],name=a['display_name'],reason=reason))
  for w in plan['artworks']:
   if w['artist_id']!=a['id']:continue
   w['artist_id']=None;w['creator_basis']=reason
   if a['source_artist_id']=='42280':w['creator_label']=w['raw_fields']['artist_display'].splitlines()[0];w['creator_label_source_line']=0
 plan['artists']=[a for a in plan['artists'] if a['id'] not in removed]
 plan['supersedes_sha256']=m.sha(DRAFT.read_bytes());plan['at']=m.now();plan['validation']=validate(plan)
 m.save(PLAN,plan);m.save(m.BACKUP/PLAN.name,plan)
 print('Final plan',plan['validation'],'SHA256',m.sha(PLAN.read_bytes()),flush=True)

def insert(db,table,rows):
 if not rows:return
 cols=list(rows[0]);assert all(list(r)==cols for r in rows)
 command=sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,cols)),sql.SQL(',').join(sql.Placeholder() for _ in cols))
 # Psycopg pipeline sends bounded groups without one WAN round-trip per row.
 with db.cursor() as cur:
  for part in m.chunks(rows,250):cur.executemany(command,[[r[c] for c in cols] for r in part])

def protected_unchanged(db,plan,lock=False):
 for table,expected in plan['protected'].items():
  ids=[r['id'] for r in expected]
  if lock:db.execute(sql.SQL('SELECT id FROM {} WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE').format(sql.Identifier(table)),(ids,)).fetchall()
  assert records(db,table,ids)==expected,'Protected '+table+' changed'

def payloads(plan,digest):
 out=collections.defaultdict(list);published=m.now();source={s['slug']:s['id'] for s in plan['sources']}
 artistcols='id slug display_name sort_name normalized_name entity_type birth_year death_year birth_display death_display birth_precision death_precision timeline_start_year timeline_end_year timeline_display timeline_basis'.split()
 for a in plan['artists']:
  row={k:a[k] for k in artistcols};row.update(status='published',created_by=m.ACTOR,updated_by=m.ACTOR,published_at=published);out['artists'].append(row)
  unique=set()
  for label in a['aliases']:
   n=m.norm(label)
   if not n or n in unique or n==m.norm(a['display_name']):continue
   unique.add(n);out['artist_aliases'].append(dict(id=m.uid('alias/'+a['id']+'/'+n),artist_id=a['id'],alias=label,normalized_alias=n,alias_type='alternate'))
  out['external_identifiers'].append(dict(id=m.uid('artist-external/'+a['id']),entity_type='artist',entity_id=a['id'],scheme='aic-artist',external_id=a['source_artist_id'],canonical_url=a['source_url'],source_id=source['art-institute-of-chicago'],retrieved_at=a['receipt']['retrieved_at']))
  out['citations'].append(dict(id=m.uid('artist-citation/'+a['id']),entity_type='artist',entity_id=a['id'],field_name=m.FIELD,source_id=source['art-institute-of-chicago'],source_record_id=a['source_artist_id'],source_url=a['source_url'],evidence_note=json.dumps(dict(plan_sha256=digest,decision=a,policy='Official museum person authority; explicit lifespan corroborated in selected object labels. No invented biography.'),ensure_ascii=False),retrieved_at=a['receipt']['retrieved_at'],created_by=m.ACTOR))
 mapping=dict(title='title',date_display='date_display',creation_year_start='first',creation_year_end='last',date_precision='date_precision',work_type='work_type',medium_text='medium',dimensions_text='dimensions',description_md='description',creation_place_display='creation_place',accession_number='accession',unlinked_creator_label='creator_label',cultural_context='cultural_context',object_form='object_form')
 for w in plan['artworks']:
  row=dict(id=w['id'],slug=w['slug'],normalized_title=m.norm(w['title']));row.update({k:w[v] for k,v in mapping.items()});row.update(status='published',research_candidate=False,created_by=m.ACTOR,updated_by=m.ACTOR,published_at=published);out['artworks'].append(row)
  if w['artist_id']:out['artwork_artists'].append(dict(artwork_id=w['id'],artist_id=w['artist_id'],attribution_role=w['attribution_role'],attribution_note=w['creator_basis']+' Original source: '+(w['creator_label'] or '')))
  out['external_identifiers'].append(dict(id=m.uid('artwork-external/'+w['key']),entity_type='artwork',entity_id=w['id'],scheme=w['external_scheme'],external_id=w['external_id'],canonical_url=w['source_url'],source_id=w['source_database_id'],retrieved_at=w['receipt']['retrieved_at']))
  for q in qids(w):out['external_identifiers'].append(dict(id=m.uid('wikidata/'+q),entity_type='artwork',entity_id=w['id'],scheme='wikidata',external_id=q,canonical_url='https://www.wikidata.org/wiki/'+q,source_id=w['source_database_id'],retrieved_at=w['receipt']['retrieved_at']))
  out['citations'].append(dict(id=m.uid('artwork-citation/'+w['key']),entity_type='artwork',entity_id=w['id'],field_name=m.FIELD,source_id=w['source_database_id'],source_record_id=w['source_id'],source_url=w['source_url'],evidence_note=json.dumps(dict(plan_sha256=digest,decision=w,policy='Selected published museum holding, creation no later than 1970. Original culture/creator qualifications and catalogue facts retained. No current-display claim or downloaded image.'),ensure_ascii=False),retrieved_at=w['receipt']['retrieved_at'],created_by=m.ACTOR))
  out['artwork_location_assertions'].append(dict(id=m.uid('holding/'+w['key']),artwork_id=w['id'],claim_type='holding',institution_id=w['institution_id'],context='collection',source_id=w['source_database_id'],source_url=w['source_url'],evidence_note=w['identity_basis']+' '+w['confidence_basis'],checked_at=w['receipt']['retrieved_at'],review_state='accepted'))
 return out

def verify(db,plan,digest):
 protected_unchanged(db,plan)
 ids=[w['id'] for w in plan['artworks']];aids=[a['id'] for a in plan['artists']];expected=payloads(plan,digest)
 rows={t:records(db,t,ids,'artwork_id' if t in ['artwork_artists','artwork_location_assertions','artwork_media'] else 'id') for t in ['artworks','artwork_artists','artwork_location_assertions','artwork_media']}
 rows['artists']=records(db,'artists',aids)
 rows['artist_aliases']=records(db,'artist_aliases',aids,'artist_id')
 rows['external_identifiers']=records(db,'external_identifiers',ids+aids,'entity_id')
 rows['citations']=records(db,'citations',ids+aids,'entity_id')
 for table,wanted in expected.items():
  key=(lambda r:(r['artwork_id'],r['artist_id'],r['attribution_role'])) if table=='artwork_artists' else (lambda r:r['id'])
  actual={key(r):r for r in rows[table]};assert len(actual)==len(wanted),(table,len(actual),len(wanted))
  for r in wanted:
   a=actual[key(r)]
   for col,val in r.items():
    if col in ['published_at','retrieved_at','checked_at']:assert a[col] is not None;continue
    assert a[col]==val,(table,col,key(r))
 inst={w['id']:w['institution_id'] for w in plan['artworks']}
 assert all(r['current_institution_id']==inst[r['id']] and r['primary_media_id'] is None and r['location_checked_at'] is None for r in rows['artworks'])
 assert not rows['artwork_media']
 assert all(r['claim_type']=='holding' and r['display_state'] is None and r['venue_id'] is None and r['review_state']=='accepted' for r in rows['artwork_location_assertions'])
 scope=safe(db.execute("SELECT artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,count(*) n,bool_and(artline_has_selection_evidence(id)) supported FROM artworks WHERE id=ANY(%s::uuid[]) GROUP BY 1",(ids,)).fetchall())
 assert scope==[dict(scope='eligible',n=len(ids),supported=True)],scope
 return dict(at=m.now(),scope=scope,rows=rows)

def apply():
 plan=m.load(PLAN);validate(plan);digest=m.sha(PLAN.read_bytes());path=m.RUN/'production-publication-receipt.json'
 if path.exists():
  assert m.load(path)['plan_sha256']==digest;print('Already published; use verify_live');return
 data=payloads(plan,digest)
 with m.connect(write=True) as db,db.transaction():
  db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  db.execute("SELECT set_config('artline.user_id',%s,true)",(m.ACTOR,))
  protected_unchanged(db,plan,lock=True)
  assert not duplicate_audit(db,plan['artworks'])['matches'],'New conflicting artwork identity appeared'
  assert not db.execute('SELECT 1 FROM artists WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s) OR normalized_name=ANY(%s) LIMIT 1',([a['id'] for a in plan['artists']],[a['slug'] for a in plan['artists']],[a['normalized_name'] for a in plan['artists']])).fetchone()
  for t in ['artists','artist_aliases','artworks','artwork_artists','external_identifiers','citations','artwork_location_assertions']:
   insert(db,t,data[t]);print('Inserted',t,len(data[t]),flush=True)
  for w in {w['institution_id']:w for w in plan['artworks']}.values():
   db.execute('INSERT INTO source_institutions(source_id,institution_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(w['source_database_id'],w['institution_id']))
  verified=verify(db,plan,digest);m.save(m.BACKUP/'production-postimages.json.gz',verified)
  print('Transactional readback passed; committing',flush=True)
 receipt=dict(at=m.now(),plan_sha256=digest,production=True,artworks_added=len(plan['artworks']),artists_added=len(plan['artists']),by_source=dict(collections.Counter(w['institution_name'] for w in plan['artworks'])),table_inserts={t:len(r) for t,r in data.items()},scope=verified['scope'],existing_profiles_preserved=True,images_downloaded=0,current_display_claims=0,backup=str(m.BACKUP),site='https://artlines.org')
 m.save(path,receipt);print(json.dumps(receipt,ensure_ascii=False,indent=2),flush=True)

def verify_live():
 plan=m.load(PLAN);digest=m.sha(PLAN.read_bytes())
 with m.connect() as db:result=verify(db,plan,digest)
 m.save(m.RUN/'production-readback.json.gz',dict(at=result['at'],scope=result['scope'],counts={t:len(r) for t,r in result['rows'].items()},plan_sha256=digest))
 print('Production readback:',result['scope'],flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','finalize','apply','verify_live']);args=p.parse_args();globals()[args.action]()
