#!/usr/bin/env python3
"""Source-configured, pinned, physical-object imports with bounded production writes."""
import argparse,collections,importlib.util,json,re,time
from psycopg import OperationalError
from psycopg.errors import LockNotAvailable,DeadlockDetected,SerializationFailure
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));x=importlib.util.module_from_spec(s);s.loader.exec_module(x);return x
n=module('nga','million-nga-20261010.py');m=n.m
CONFIG={
 'aic':dict(module='million-aic-20261011.py',name='Art Institute of Chicago',url='https://www.artic.edu/',docs='https://api.artic.edu/docs/',native='aic-artist',schemes=['aic-object','european-chicago-art-institute-of-chicago-object']),
 'moma':dict(module='million-moma-20261011.py',name='Museum of Modern Art',url='https://www.moma.org/',docs='https://github.com/MuseumofModernArt/collection',native='moma-artist',schemes=['moma-object']),
 'met':dict(module='million-met-20261010.py',name='The Metropolitan Museum of Art',url='https://www.metmuseum.org/',docs='https://metmuseum.github.io/',native='met-creator-evidence',schemes=['met-object','european-met-the-met-object']),
 'rijks':dict(module='million-rijks-20261010.py',name='Rijksmuseum',url='https://www.rijksmuseum.nl/',docs='https://data.rijksmuseum.nl/docs/oai-pmh/',native='rijks-person',schemes=['european-rijks-rijksmuseum-object','rijks-object','european-rijks-object'])}
def setup(provider,phase):
 cfg=dict(CONFIG[provider]);adapter=module('adapter',cfg['module']);selection=getattr(adapter,'SELECTION','selection.json.gz')
 if provider=='rijks':
  assert re.fullmatch(r'\d{5}-\d{5}',phase),'Rijks phase must identify its immutable page window'
  selection='selection-'+phase+'-v3.json.gz'
 cfg.update(provider=provider,mid=adapter.MID,sid=m.uid('source/'+provider),run=m.RUN/provider/phase,input=m.RUN/provider/selection);return cfg
def execution_exclusions(folder):
 path=folder/'execution-exclusions-v2.json'
 return path if path.exists() else folder/'execution-exclusions.json'
def is_physical_view(provider,accession):
 return provider=='rijks' and bool(re.search(r'\((?:V|VERSO)\)\s*$',accession,re.I))
def source_chronology_conflicts(row):
 conflicts=[]
 for creator in row['creators']:
  if creator.get('prefix') or creator.get('suffix'):continue
  life=n.life.literal_life(creator['displaydate']) or {};birth=life.get('birth');death=life.get('death')
  if birth and row['last']<birth['year']:conflicts.append(dict(creator=creator,reason='Object date wholly precedes explicit source birth'))
  elif death and row['work_type'] in ['painting','drawing','watercolor','calligraphy'] and row['first']>death['year']:conflicts.append(dict(creator=creator,reason='Original painting/drawing date wholly follows explicit source death; attribution or date review required'))
 return conflicts
def matched_chronology_conflicts(row,artists):
 conflicts=[]
 for link in row['links']:
  if link['attribution_role']!='primary':continue
  artist=artists[link['artist_id']];birth=artist['birth_year'];death=artist['death_year']
  if birth is not None and row['last']<birth:conflicts.append(dict(artist_id=link['artist_id'],reason='Object date wholly precedes the matched catalogue person birth'))
  elif death is not None and row['work_type'] in ['painting','drawing','watercolor','calligraphy'] and row['first']>death:conflicts.append(dict(artist_id=link['artist_id'],reason='Original artwork date wholly follows the matched catalogue person death'))
 return conflicts
def plan(provider,phase):
 cfg=setup(provider,phase);folder=cfg['run'];dest=folder/'plan.json.gz'
 if dest.exists():return
 data=m.load(cfg['input']);rows=data['selected'];qids=[r['wikidata_id'] for r in rows if r['wikidata_id']];creatorq=sorted({c['wikidataid'] for r in rows for c in r['creators'] if c['wikidataid']});creator_wrongtype=set()
 with m.m.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  artists={r['id']:r for r in db.execute('SELECT id::text,display_name,normalized_name,birth_year,death_year,status FROM artists')};byext=collections.defaultdict(set);bynames=collections.defaultdict(set)
  for a in artists.values():a['names']={m.norm(a['display_name']),m.norm(a['normalized_name'])}
  for e in db.execute('SELECT artist_id::text,alias FROM artist_aliases'):artists[e['artist_id']]['names'].add(m.norm(e['alias']))
  for aid,a in artists.items():
   for name in a['names']:bynames[name].add(aid)
  for e in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artist'"):byext[e['scheme'],e['external_id']].add(e['entity_id'])
  for chunk in m.chunks(creatorq,3000):creator_wrongtype.update(r['external_id'] for r in db.execute("SELECT external_id FROM external_identifiers WHERE scheme='wikidata' AND external_id=ANY(%s) AND entity_type<>'artist'",(chunk,)))
  existing=db.execute('SELECT id::text,title,accession_number FROM artworks WHERE current_institution_id=%s',(cfg['mid'],)).fetchall()
  external=db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s)",(cfg['schemes'],)).fetchall()
  for chunk in m.chunks(qids,3000):external+=db.execute("SELECT entity_type,entity_id::text,scheme,external_id FROM external_identifiers WHERE scheme='wikidata' AND external_id=ANY(%s)",(chunk,)).fetchall()
  queryplan=db.execute('EXPLAIN (FORMAT JSON) SELECT id FROM artworks WHERE current_institution_id=%s',(cfg['mid'],)).fetchone()
 bykey=collections.defaultdict(set);byacc=collections.defaultdict(set);bytitle=collections.defaultdict(list);wrongtype={e['external_id'] for e in external if e['scheme']=='wikidata' and e.get('entity_type','artwork')!='artwork'}
 for e in external:bykey[e['scheme'],e['external_id']].add(e['entity_id'])
 for r in existing:
  if r['accession_number']:byacc[m.norm(r['accession_number'])].add(r['id'])
  bytitle[m.norm(r['title'])].append(r)
 qcount=collections.Counter(r['wikidata_id'] for r in rows if r['wikidata_id']);acount=collections.Counter(m.norm(r['accession_number']) for r in rows);selected=[];held=[]
 for r in rows:
  matches=set().union(*(bykey.get((s,r['native_id']),set()) for s in cfg['schemes']),bykey.get(('wikidata',r['wikidata_id']),set()),byacc.get(m.norm(r['accession_number']),set()))
  reason=None
  if r['wikidata_id'] in wrongtype:reason='wikidata_identifies_other_entity_type'
  elif matches:reason='already_present' if len(matches)==1 else 'conflicting_existing_identity'
  elif is_physical_view(provider,r['accession_number']):reason='verso_same_physical_sheet_requires_review'
  elif source_chronology_conflicts(r):reason='literal_source_creation_and_lifetime_conflict'
  elif len(r['creator_label'])>500 or len(r.get('cultural_context',''))>500:reason='unbounded_source_attribution_requires_editorial_summary'
  elif r['wikidata_id'] and qcount[r['wikidata_id']]>1:reason='qid_covers_multiple_native_objects'
  elif acount[m.norm(r['accession_number'])]>1:reason='accession_repeats_in_export'
  elif any(not e['accession_number'] for e in bytitle.get(r['normalized_title'],[])):reason='same_title_unknown_inventory'
  if reason:held.append(dict(native_id=r['native_id'],reason=reason,existing_ids=sorted(matches)));continue
  r=dict(r,links=[]);selected.append(r)
 usable={'Artist','Artist and engraver','Painter','Sculptor','Engraver','Etcher','Photographer','Draftsman','Draftsman and engraver','Calligrapher','Printmaker','Lithographer','Maker'}
 groups=collections.defaultdict(list);authorities={};creatorholds=[]
 for r in selected:
  for c in r['creators']:
   if c['role'] in usable and c['prefix'].lower() in ['','attributed to','attributed to:'] and not c['suffix']:
    groups[c['constituentid']].append(r);authorities[c['constituentid']]=c
 newartists=[];decisions=[];amap={}
 for native,works in groups.items():
  variants={(c['forwarddisplayname'],c['displaydate'],c['wikidataid']) for c in data['people'][native]};person=authorities[native]
  if person['wikidataid'] in creator_wrongtype:creatorholds.append(dict(native_id=native,reason='creator_wikidata_identifies_other_entity_type'));continue
  if len(variants)>1:creatorholds.append(dict(native_id=native,reason='authority_fields_vary_across_objects',variants=sorted(variants)));continue
  if re.search(r'company|&|\band\b|sons|inc\.|workshop|manufactory|studio|press|brothers| et |family|firm',person['forwarddisplayname'],re.I):creatorholds.append(dict(native_id=native,reason='corporate_or_joint_creator_needs_review'));continue
  aid,reason,a=n.artist_plan(person,works,artists,byext,bynames,provider,cfg['native']);amap[native]=aid;decisions.append(dict(native_id=native,artist_id=aid,reason=reason,authority=person))
  if a and not n.life.literal_life(person['displaydate']) and a['timeline_basis']!='activity':
   amap[native]=None;decisions[-1].update(artist_id=None,reason='new_person_authority_requires_further_review');continue
  if a:
   if person.get('entity_type_hint')=='anonymous_master':a['entity_type']='anonymous_master'
   newartists.append(a);artists[aid]=dict(a,names={m.norm(a['display_name'])});bynames[a['normalized_name']].add(aid);byext[cfg['native'],native].add(aid)
   if person['wikidataid']:byext['wikidata',person['wikidataid']].add(aid)
 for r in selected:
  for c in r['creators']:
   aid=amap.get(c['constituentid'])
   if not aid or c['role'] not in usable or c['prefix'].lower() not in ['','attributed to','attributed to:'] or c['suffix']:continue
   role='attributed_to' if c['prefix'] else 'primary'
   if any(x['artist_id']==aid and x['attribution_role']==role for x in r['links']):continue
   r['links'].append(dict(artwork_id=r['artwork_id'],artist_id=aid,attribution_role=role,representative_order=min(10,len(r['links'])+1),attribution_note=cfg['name']+' creator evidence key '+c['constituentid']+'; source role: '+c['role']+'; prefix: '+c['prefix']))
 chronology_held=set()
 for row in selected:
  conflicts=matched_chronology_conflicts(row,artists)
  if conflicts:chronology_held.add(row['artwork_id']);held.append(dict(native_id=row['native_id'],reason='matched_creator_lifetime_conflict',conflicts=conflicts))
 selected=[r for r in selected if r['artwork_id'] not in chronology_held]
 cross=module('cross','million-cross-source-20261010.py')
 with m.m.connect() as db:crossholds=cross.find_candidates(db,selected)
 crossids={r['new_id'] for r in crossholds}
 held.extend(dict(native_id=r['native_id'],reason='unassigned_cross_source_creator_title_candidate',existing_ids=[r['existing']['id']]) for r in crossholds)
 selected=[r for r in selected if r['artwork_id'] not in crossids]
 linkedids={l['artist_id'] for r in selected for l in r['links']};newartists=[a for a in newartists if a['id'] in linkedids]
 for a in artists.values():a.pop('names',None)
 used={l['artist_id'] for r in selected for l in r['links']};newids={a['id'] for a in newartists}
 p=dict(at=m.now(),provider=provider,phase=phase,source_receipt=data['source_receipt'],selection_sha256=m.sha(cfg['input'].read_bytes()),new_artworks=selected,new_artists=newartists,artist_decisions=decisions,creator_holds=creatorholds,held=held,cross_source_candidates=crossholds,existing_artist_preconditions={aid:artists[aid] for aid in used-newids},query_plan=queryplan)
 m.save(dest,p);m.save(folder/'pin.json',dict(sha256=m.sha(dest.read_bytes())));m.save(m.BACKUP/provider/phase/'plan.json.gz',p)
 print(json.dumps(dict(provider=provider,new_artworks=len(selected),new_artists=len(newartists),creator_links=sum(len(r['links']) for r in selected),held=collections.Counter(r['reason'] for r in held),creator_holds=len(creatorholds))),flush=True)
def apply(provider,phase,limit=None):
 cfg=setup(provider,phase);folder=cfg['run'];path=folder/'plan.json.gz';digest=m.load(folder/'pin.json')['sha256'];assert m.sha(path.read_bytes())==digest;p=m.load(path);rc=p['source_receipt'];artists={a['id']:a for a in p['new_artists']};decisions={r['artist_id']:r for r in p['artist_decisions'] if r['reason']=='new_native_authority'}
 assert m.load(m.RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'
 exclusions_path=execution_exclusions(folder);exclusions=m.load(exclusions_path) if exclusions_path.exists() else {'rows':[]};excluded={r['artwork_id'] for r in exclusions['rows']};exclusion_sha=m.sha(exclusions_path.read_bytes()) if exclusions_path.exists() else None
 if excluded:assert exclusions['plan_sha256']==digest and all(r['artwork_id'] in {x['artwork_id'] for x in p['new_artworks']} for r in exclusions['rows'])
 for batch,rows in enumerate(m.chunks(p['new_artworks'],1000)):
  if limit is not None and batch>=limit:break
  rp=folder/'batches'/(str(batch).zfill(4)+'.json')
  if rp.exists():continue
  batch_excluded=[r['artwork_id'] for r in rows if r['artwork_id'] in excluded];rows=[r for r in rows if r['artwork_id'] not in excluded]
  ids=[r['artwork_id'] for r in rows];aids=sorted({l['artist_id'] for r in rows for l in r['links']});tables=collections.defaultdict(list)
  with m.m.connect(write=True) as db:
   db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
   done=db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
   if done:
    assert len(done)==len(ids)
    assert db.execute("SELECT count(*) n FROM citations WHERE entity_id=ANY(%s::uuid[]) AND field_name=%s AND evidence_note::jsonb->>'plan_sha256'=%s",(ids,'million_catalogue_'+provider,digest)).fetchone()['n']==len(ids)
    m.save(rp,dict(at=m.now(),artworks=len(ids),batch=batch,recovered_committed=True,artwork_ids=ids,plan_sha256=digest));continue
   current={a['id']:a for a in db.execute('SELECT id::text,display_name,normalized_name,birth_year,death_year,status FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(aids,))}
   for aid,a in current.items():
    if aid in p['existing_artist_preconditions']:assert a==p['existing_artist_preconditions'][aid],'Artist precondition changed'
   native=[r['native_id'] for r in rows];qids=[r['wikidata_id'] for r in rows if r['wikidata_id']]
   assert not db.execute("SELECT id FROM external_identifiers WHERE (scheme=ANY(%s) AND external_id=ANY(%s)) OR (scheme='wikidata' AND external_id=ANY(%s))",(cfg['schemes'],native,qids)).fetchall(),'Concurrent source identity conflict'
   assert not db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(cfg['mid'],[r['accession_number'] for r in rows])).fetchall(),'Concurrent inventory duplicate'
   newa=[artists[aid] for aid in aids if aid in artists and aid not in current]
   newq=[decisions[a['id']]['authority']['wikidataid'] for a in newa if decisions[a['id']]['authority']['wikidataid']]
   assert not db.execute("SELECT id FROM external_identifiers WHERE scheme='wikidata' AND external_id=ANY(%s)",(newq,)).fetchall(),'New artist identity appeared after plan'
   m.save(m.BACKUP/provider/phase/('before-'+str(batch).zfill(4)+('-filtered' if batch_excluded else '')+'.json.gz'),dict(artwork_ids_absent=ids,existing_artists=current,new_artist_ids=[a['id'] for a in newa],plan_sha256=digest))
   db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,api_docs_url,adapter_key) VALUES(%s,%s,%s,'museum_api',%s,%s,%s) ON CONFLICT(id) DO NOTHING",(cfg['sid'],m.OP+'-'+provider,cfg['name']+' official open data',cfg['url'],cfg['docs'],m.OP));n.copy_rows(db,'artists',newa)
   for a in newa:
    person=decisions[a['id']]['authority'];native=person['constituentid'];url=person.get('source_uri') or rc['url']
    tables['external_identifiers'].append(dict(id=m.uid('identifier/'+provider+'-artist/'+native),entity_type='artist',entity_id=a['id'],scheme=cfg['native'],external_id=native,canonical_url=url,source_id=cfg['sid'],retrieved_at=rc['retrieved_at']))
    if person['wikidataid']:tables['external_identifiers'].append(dict(id=m.uid('identifier/'+provider+'-artist-qid/'+native),entity_type='artist',entity_id=a['id'],scheme='wikidata',external_id=person['wikidataid'],canonical_url='https://www.wikidata.org/wiki/'+person['wikidataid'],source_id=cfg['sid'],retrieved_at=rc['retrieved_at']))
    tables['citations'].append(dict(id=m.uid('citation/'+provider+'-artist/'+native),entity_type='artist',entity_id=a['id'],field_name='million_catalogue_'+provider+'_artist',source_id=cfg['sid'],source_record_id=native,source_url=url,evidence_note=json.dumps(dict(authority=person,source_sha256=rc['sha256'],plan_sha256=digest,date_basis='Literal biography only for life; incomplete lifespan uses explicitly estimated source-work span.'),ensure_ascii=False),retrieved_at=rc['retrieved_at'],created_by=m.ACTOR))
   for r in rows:
    aid=r['artwork_id'];key=provider+'/'+r['native_id']
    tables['artworks'].append(dict(id=aid,slug=provider+'-object-'+r['native_id'],title=r['title'],normalized_title=r['normalized_title'],date_display=r['date_display'],creation_year_start=r['first'],creation_year_end=r['last'],date_precision=r['precision'],work_type=r['work_type'],medium_text=r['medium'] or None,dimensions_text=r['dimensions'] or None,accession_number=r['accession_number'],current_institution_id=cfg['mid'],status='review',research_candidate=True,unlinked_creator_label=r['creator_label'] or None,cultural_context=r.get('cultural_context') or None,created_by=m.ACTOR,updated_by=m.ACTOR))
    tables['artwork_artists']+=r['links']
    tables['external_identifiers'].append(dict(id=m.uid('identifier/'+key),entity_type='artwork',entity_id=aid,scheme=cfg['schemes'][0],external_id=r['native_id'],canonical_url=r['source_url'],source_id=cfg['sid'],retrieved_at=rc['retrieved_at']))
    if r['wikidata_id']:tables['external_identifiers'].append(dict(id=m.uid('identifier/qid/'+key),entity_type='artwork',entity_id=aid,scheme='wikidata',external_id=r['wikidata_id'],canonical_url='https://www.wikidata.org/wiki/'+r['wikidata_id'],source_id=cfg['sid'],retrieved_at=rc['retrieved_at']))
    note=dict(plan_sha256=digest,source_sha256=rc['sha256'],native_object=r['raw'],native_creators=r['creators'],identity='Native object ID and accession reconciled; same-export repeated accession/QID and ambiguous component records held.',date_basis='Literal creation date; numeric search bounds retained solely in source evidence',scope='Documented museum collection, no current display claim')
    tables['citations'].append(dict(id=m.uid('citation/'+key),entity_type='artwork',entity_id=aid,field_name='million_catalogue_'+provider,source_id=cfg['sid'],source_record_id=r['native_id'],source_url=r['source_url'],evidence_note=json.dumps(note,ensure_ascii=False),retrieved_at=rc['retrieved_at'],created_by=m.ACTOR))
    tables['artwork_location_assertions'].append(dict(id=m.uid('holding/'+key),artwork_id=aid,claim_type='holding',institution_id=cfg['mid'],context='collection',source_id=cfg['sid'],source_url=r['source_url'],evidence_note='Official museum collection inventory '+r['accession_number']+'. Source SHA256 '+rc['sha256']+'. High editorial confidence from native accession evidence. No current display claim.',checked_at=rc['retrieved_at'],review_state='accepted'))
   for table in ['artworks','artwork_artists','external_identifiers','citations','artwork_location_assertions']:n.copy_rows(db,table,tables[table])
   check=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND primary_media_id IS NULL AND current_institution_id=%s AND creation_year_end<=1970) valid FROM artworks WHERE id=ANY(%s::uuid[])",(cfg['mid'],ids)).fetchone();assert check['n']==check['valid']==len(ids);db.commit()
  receipt=dict(at=m.now(),batch=batch,artworks=len(ids),artists=len(newa),creator_links=len(tables['artwork_artists']),plan_sha256=digest,artwork_ids=ids,execution_exclusions_sha256=exclusion_sha,excluded_artwork_ids=batch_excluded);m.save(rp,receipt);print(json.dumps({k:v for k,v in receipt.items() if k!='artwork_ids'}),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['plan','apply']);ap.add_argument('provider',choices=CONFIG);ap.add_argument('--phase',default='001');ap.add_argument('--limit',type=int);a=ap.parse_args()
 for attempt in range(20):
  try:
   if a.action=='plan':plan(a.provider,a.phase)
   else:apply(a.provider,a.phase,a.limit)
   break
  except (LockNotAvailable,DeadlockDetected,SerializationFailure):
   if attempt==19:raise
   print('Concurrent import contention; transaction rolled back. Resuming from committed batch receipts.',flush=True);time.sleep(5)
  except OperationalError as error:
    # A disconnected transaction may have committed. apply() checks existing
    # object IDs and pinned citations before attempting any recovered batch.
   if attempt==19 or error.sqlstate is not None and not (error.sqlstate.startswith('08') or error.sqlstate in ['57P01','57P02','57P03']):raise
   print('Database connection interrupted. Reopening and checking committed batch identity before resuming.',flush=True);time.sleep(5)
