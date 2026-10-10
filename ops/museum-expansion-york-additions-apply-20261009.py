"""Atomic selected160 York painting review additions with all existing records preserved."""
import argparse,csv,hashlib,importlib.util,json,types
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
r=module('r','museum-expansion-york-additions-review-20261009.py');i=module('i','museum-expansion-york-additions-identity-20261009.py');s=module('s','museum-expansion-york-additions-common-20261009.py');ts=module('ts','museum-expansion-ferens-timestamps-20261009.py');m=r.m;RUN=r.RUN;IID=s.IID;reference=r.ref;checked=r.checked;snapshot=s.snapshot;counts=s.counts;prior_state=s.prior_state;IIDS=s.IIDS
KEY='york-native-paintings-001';SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY;SCHEME='york-museums-object';PLAN=RUN/(KEY+'-plan-001.json.gz');REVIEW=RUN/'editorial-reviewed-001.json.gz';CHECKPOINT=s.CP;N=160;HCOUNT=0
def records():
 x=m.load(REVIEW);checked(x['reviewer_reference'])
 for dep in x['dependencies']:checked(dep)
 assert x['decisions']==r.build();news=[];holds=[]
 for d in x['decisions']:
  if d['state'] not in ['approved_review_only_addition','approved_existing_holding']:continue
  f=d['facts'];assert 100<=f['first']<=f['last']<=1970;assert not d['comparison']['source_hits'];new=d['state']=='approved_review_only_addition';aid=m.uid(KEY+'/'+f['source_id']) if new else d['existing_artwork_id'];v=dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+f['native_id'],institution_id=IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=f,decision=d,retrieved_at=d['retrieved_at']);(news if new else holds).append(v)
 assert len(news)==N and len(holds)==HCOUNT and len({v['artwork_id'] for v in news+holds})==N+HCOUNT;return news,holds
def prior_ids():
 ids=[]
 for name in ['added-artworks','reconciled-artworks']:
  with(m.RUN/(name+'-after-wave-95.csv')).open(newline='') as fp:ids.extend(v['artwork_id'] for v in csv.DictReader(fp))
 assert len(ids)==len(set(ids))==13658;return sorted(ids)
def verify_baseline():
 assert reference(CHECKPOINT)['sha256']=='b18514150f7dd97550b6bb1309177f695764a55c6f1f81b0cf3544d556b4a11c';cp=m.load(CHECKPOINT)
 for dep in cp['artifacts']:checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 return cp
def fresh_identity(db):
 x=m.load(RUN/'identity-001.json.gz');state=i.queries(db,x['params']);assert state==x['state'],'Current bounded identity scope changed';cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))];assert cs==m.load(RUN/'identity-citations-001.json.gz')['citations']
 if db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='off':
  path=m.BACKUP/(KEY+'-transaction-identity-001.json.gz');assert not path.exists();m.save(path,dict(at=m.now(),state_equal=True,citations_equal=True,identity_reference=reference(RUN/'identity-001.json.gz'),artwork_count=len(state['artworks']),citation_count=len(cs)))
def preflight(db,p):
 constraints={v['conname']:v['definition'] for v in db.execute("SELECT conname,pg_get_constraintdef(oid) definition FROM pg_constraint WHERE conrelid='artworks'::regclass AND conname=ANY(%s)",(['artwork_object_form','artworks_work_type_check'],))};assert len(constraints)==2 and 'painting' in constraints['artworks_work_type_check'] and "'icon'" in constraints['artwork_object_form'];assert all(v['facts']['work_type'] == 'painting' and v['facts']['object_form'] is None for v in p['records'])
 assert snapshot(db,p['scoped_ids'])==p['before'];assert counts(db)==p['before_counts']=={IID:dict(linked=90,eligible=68)};assert prior_state(db,p['prior_ids'])==p['prior_state'];fresh_identity(db)
 assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone();assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s)',([v['artwork_id'] for v in p['records']],[v['slug'] for v in p['records']])).fetchone()
 for v in p['holdings']:
  art=next(a for a in p['before']['artworks'] if a['id']==v['artwork_id']);assert art['current_institution_id'] is None and art['status']=='review';assert not [a for a in p['before']['assertions'] if a['artwork_id']==v['artwork_id']];assert (art['creation_year_start'],art['creation_year_end'])==(v['facts']['first'],v['facts']['last'])
def dependencies():
 paths=set();seen=set()
 def visit(mod):
  if id(mod) in seen:return
  seen.add(id(mod));file=getattr(mod,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  paths.add(Path(file).resolve())
  for v in vars(mod).values():
   if isinstance(v,types.ModuleType):visit(v)
 for mod in [r,i,s,ts]:visit(mod)
 paths.add(Path(__file__).resolve());return paths
def prepare():
 assert not PLAN.exists();news,holds=records();verify_baseline();initial=m.load(RUN/'initial-scope-001.json.gz');identity=m.load(RUN/'identity-001.json.gz');ids=sorted(set(initial['scoped_ids'])|set(m.load(RUN/'comparison-source-context-001.json.gz')['requested_ids']));pids=prior_ids();assert set(pids).isdisjoint(v['artwork_id'] for v in holds)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert snapshot(db,initial['scoped_ids'])==initial['snapshot'];p=dict(at=m.now(),records=news,holdings=holds,scoped_ids=ids,before=snapshot(db,ids),prior_ids=pids,prior_state=prior_state(db,pids),before_counts=counts(db),baseline_reference=reference(CHECKPOINT),policy='Selected160 native York physical paintings in review. Sixteen unresolved identity/version candidates and one conflicting source-date page are held. Unresolved source-maker relationships and two uncertain sitter titles remain explicit. Existing metadata,images,painter links,statuses and institution records unchanged. Holding does not establish current display or legal ownership.');preflight(db,p)
 backup=m.BACKUP/(KEY+'-before-001.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),scoped_ids=ids,before=p['before'],prior_ids=pids,prior_state=p['prior_state']));p.update(backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest())
 paths=dependencies()|{CHECKPOINT,m.ROOT/'AGENTS.md',Path(__file__).with_name('test_museum_expansion_york_additions_20261009.py').resolve()};paths|={v for v in RUN.rglob('*') if v.is_file() and v.name!='README.md'}
 for dep in m.load(RUN/'comparison-source-context-001.json.gz')['body_references']:paths.add(checked(dep))
 p['evidence']=[reference(v) for v in sorted(paths)];m.save(PLAN,p);print(json.dumps(dict(records=N,holdings=HCOUNT,protected_existing=len(ids),protected_prior=len(pids),sha256=reference(PLAN)['sha256'])),flush=True)
def validate_plan():
 p=m.load(PLAN)
 for dep in p['evidence']:checked(dep)
 assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256'];news,holds=records();assert p['records']==news and p['holdings']==holds;return p,reference(PLAN)['sha256']
def citation_note(v,digest):return json.dumps(dict(plan_sha256=digest,source_record=v,review_reference=reference(REVIEW),policy='Literal museum object metadata with retained raw source,identity and version evidence. Qualified and conflicting dates explicit. For existing-object links, source fields are evidence only and do not overwrite catalogue metadata. No image or display claim.'),ensure_ascii=False)
def holding_note(v,digest):return v['decision']['basis']+' '+v['decision']['limitation']+' Plan SHA-256 '+digest
def expected_art(v):
 f=v['facts'];return dict(id=v['artwork_id'],slug=v['slug'],title=f['title'],normalized_title=m.norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],medium_text=f['medium'],dimensions_text=f['dimensions_text'],accession_number=f['inventory'],status='review',research_candidate=True,unlinked_creator_label=f['creator_label'],current_institution_id=IID,object_form=f['object_form'],created_by=m.ACTOR,updated_by=m.ACTOR)
def verify_evidence_rows(snap,vs,digest,new):
 assert len(snap['citations'])==len(snap['assertions'])==len(vs)
 for v in vs:
  aid=v['artwork_id'];f=v['facts'];c=next(x for x in snap['citations'] if x['entity_id']==aid);h=next(x for x in snap['assertions'] if x['artwork_id']==aid);field='museum_expansion_native_metadata' if new else 'museum_expansion_holding_reconciliation';assert(c['source_id'],c['field_name'],c['source_record_id'],c['source_url'],c['evidence_note'])==(SID,field,f['source_id'],f['source_url'],citation_note(v,digest));assert ts.same_instant(c['retrieved_at'],v['retrieved_at']);assert h['id']==v['holding_id'] and h['source_id']==SID and h['claim_type']=='holding' and h['institution_id']==IID and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==f['source_url'] and h['evidence_note']==holding_note(v,digest) and ts.same_instant(h['checked_at'],v['retrieved_at']);assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
def assert_delta(before,after,holds,digest):
 target={v['artwork_id'] for v in holds};old={a['id']:a for a in before['artworks']};new={a['id']:a for a in after['artworks']};assert set(old)==set(new)
 for aid,art in old.items():
  ignore={'current_institution_id','updated_at'} if aid in target else set();assert {k:v for k,v in art.items() if k not in ignore}=={k:v for k,v in new[aid].items() if k not in ignore}
  if aid in target:assert art['current_institution_id'] is None and new[aid]['current_institution_id']==IID
 for key in ['artists','media','media_assets','identifiers','museums']:assert before[key]==after[key]
 for key in ['citations','assertions']:assert [v for v in after[key] if v['source_id']!=SID]==before[key]
 verify_evidence_rows({k:[v for v in after[k] if v['source_id']==SID] for k in ['citations','assertions']},holds,digest,False)
def verify(db,p,digest):
 ids=[v['artwork_id'] for v in p['records']];snap=snapshot(db,ids);assert len(snap['artworks'])==len(snap['identifiers'])==N;assert not snap['artists'] and not snap['media'] and not snap['media_assets'];assert_delta(p['before'],snapshot(db,p['scoped_ids']),p['holdings'],digest);assert prior_state(db,p['prior_ids'])==p['prior_state'];verify_evidence_rows(snap,p['records'],digest,True)
 for v in p['records']:
  aid=v['artwork_id'];f=v['facts'];art=next(x for x in snap['artworks'] if x['id']==aid);assert all(art[k]==val for k,val in expected_art(v).items()),f['source_id']
  for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None
  ex=next(x for x in snap['identifiers'] if x['entity_id']==aid);assert(ex['scheme'],ex['external_id'],ex['canonical_url'],ex['source_id'])==(SCHEME,f['source_id'],f['source_url'],SID)
 allids=ids+[v['artwork_id'] for v in p['holdings']];assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(allids,)).fetchone()['n']==N+HCOUNT;assert counts(db)=={IID:dict(linked=250,eligible=228)}
 return dict(verified_new_records=N,existing_artworks_linked=HCOUNT,current_counts=counts(db),protected_existing_records=len(p['scoped_ids']),prior_campaign_records_preserved=len(p['prior_ids']),prior_campaign_table_digests=p['prior_state'],new_identifiers=N,new_citations=N+HCOUNT,new_accepted_holdings=N+HCOUNT,new_media_links=0,new_artist_links=0,new_published=0,new_display_claims=0,editorial_holds=17,already_catalogued=0,distinct_source_object_ids=N+HCOUNT)
def apply(expected_sha):
 p,digest=validate_plan();assert digest==expected_sha
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay: zero writes',flush=True);return
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(p['scoped_ids'],));db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(s.PROTECT_IIDS,));preflight(db,p);backup=m.BACKUP/(KEY+'-reviewed-plan-001.json.gz');assert not backup.exists();m.save(backup,p)
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SLUG,'York Art Gallery selected native paintings and source attribution evidence,9 October2026','collection_page','https://www.yorkmuseumstrust.org.uk/collections/'))
  for v in p['records']:
   f=v['facts'];a=expected_art(v);a.pop('current_institution_id');keys=list(a);db.execute('INSERT INTO artworks('+','.join(keys)+') VALUES('+','.join(['%s']*len(keys))+')',list(a.values()));db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(v['artwork_id'],SCHEME,f['source_id'],f['source_url'],SID,v['retrieved_at']))
  for isnew,vs in [(True,p['records']),(False,p['holdings'])]:
   for v in vs:
    f=v['facts'];field='museum_expansion_native_metadata' if isnew else 'museum_expansion_holding_reconciliation';db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,%s,%s,%s,%s,%s,%s)",(v['artwork_id'],field,SID,f['source_id'],f['source_url'],citation_note(v,digest),v['retrieved_at'],m.ACTOR));db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(v['holding_id'],v['artwork_id'],IID,SID,f['source_url'],holding_note(v,digest),v['retrieved_at']))
  result=verify(db,p,digest)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=N,existing_links=HCOUNT,local_only=True,verification=result));print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');v=p.parse_args()
 if v.command=='prepare':prepare()
 elif v.command=='apply':assert v.plan_sha;apply(v.plan_sha)
 else:
  p,d=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,p,d)),flush=True)
