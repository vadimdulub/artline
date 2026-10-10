"""Atomic local addition of22 reviewed museum-published Guildhall objects, without legacy edits."""
import argparse,csv,hashlib,importlib.util,json,types
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
r=module('r','museum-expansion-guildhall-review-20261009.py');i=module('i','museum-expansion-guildhall-identity-v3-20261009.py');s=module('s','museum-expansion-guildhall-source-20261009.py');m=r.m;RUN=r.RUN;IID=s.IID;reference=r.ref;checked=r.checked;prior=s.prior;snapshot=s.snapshot;counts=s.counts;prior_state=prior.prior_state
KEY='guildhall-native-additions-001';SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY;SCHEME='google-arts-culture-guildhall-object';PLAN=RUN/(KEY+'-plan-001.json.gz');REVIEW=RUN/'editorial-reviewed-001.json.gz';CHECKPOINT=s.CP;N=22
ts=module('ts','museum-expansion-ferens-timestamps-20261009.py')
def records():
 x=m.load(REVIEW);checked(x['reviewer_reference'])
 for dep in x['dependencies']:checked(dep)
 assert x['decisions']==r.build();out=[]
 for d in x['decisions']:
  if d['state']!='approved_review_only_addition':continue
  f=d['facts'];assert d['confidence']==.95 and d['basis'] and d['limitation'];assert 100<=f['first']<=f['last']<=1970;assert not d['comparison']['source_hits'] and not d['comparison']['presentation_alias_hits']
  out.append(dict(artwork_id=m.uid(KEY+'/'+f['source_id']),slug='museum-expansion-'+KEY+'-'+f['source_id'],facts=f,decision=d,retrieved_at=d['retrieved_at']))
 assert len(out)==len({x['artwork_id'] for x in out})==len({x['facts']['source_id'] for x in out})==N;return out
def prior_ids():
 ids=[]
 for name in ['added-artworks','reconciled-artworks']:
  with(m.RUN/(name+'-after-wave-85.csv')).open(newline='') as fp:ids.extend(v['artwork_id'] for v in csv.DictReader(fp))
 assert len(ids)==len(set(ids))==12692;return sorted(ids)
def verify_baseline():
 assert reference(CHECKPOINT)['sha256']=='1064b93d392810edd5276f43c30dcfcfa6fd03776d1f66eaddec63fc200c9b31';x=m.load(CHECKPOINT)
 for dep in x['artifacts']:checked(dep)
 for dep in x['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 return x
def fresh_identity(db):
 x=m.load(RUN/'native-identity-003.json.gz');state=i.queries(db,x['params']);assert state==x['state'],'Current bounded identity scope changed'
 cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))];assert cs==m.load(RUN/'identity-citations-003.json.gz')['citations']
 if db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='off':
  path=m.BACKUP/(KEY+'-transaction-identity-001.json.gz');assert not path.exists();m.save(path,dict(at=m.now(),state_equal=True,citations_equal=True,identity_reference=reference(RUN/'native-identity-003.json.gz'),artwork_count=len(state['artworks']),citation_count=len(cs)))
def preflight(db,p):
 assert snapshot(db,p['scoped_ids'])==p['before'];assert counts(db)==p['before_counts']==dict(linked=93,eligible=64);assert prior_state(db,p['prior_ids'])==p['prior_state'];fresh_identity(db)
 assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone();assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s)',([v['artwork_id'] for v in p['records']],[v['slug'] for v in p['records']])).fetchone()
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
 assert not PLAN.exists();rs=records();verify_baseline();initial=m.load(RUN/'initial-scope-001.json.gz');identity=m.load(RUN/'native-identity-003.json.gz');ids=sorted(set(initial['scoped_ids'])|set(identity['state']['artwork_ids']));pids=prior_ids()
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert snapshot(db,initial['scoped_ids'])==initial['snapshot'];p=dict(at=m.now(),records=rs,scoped_ids=ids,before=snapshot(db,ids),prior_ids=pids,prior_state=prior_state(db,pids),before_counts=counts(db),baseline_reference=reference(CHECKPOINT),policy='Selected22 museum-published Guildhall objects in review. No existing artwork fields,images,painter links,statuses or institution metadata changed. Anonymous,school and attributed makers preserved as labels. Holdings do not establish current display,custody or legal ownership.');preflight(db,p)
 backup=m.BACKUP/(KEY+'-before-001.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),scoped_ids=ids,before=p['before'],prior_ids=pids,prior_state=p['prior_state']));p.update(backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest())
 paths=dependencies()|{CHECKPOINT,m.ROOT/'AGENTS.md',Path(__file__).with_name('test_museum_expansion_guildhall_20261009.py').resolve()};paths|={v for v in RUN.rglob('*') if v.is_file() and v.name!='README.md'};p['evidence']=[reference(v) for v in sorted(paths)];m.save(PLAN,p);print(json.dumps(dict(records=N,protected_existing=len(ids),protected_prior=len(pids),sha256=reference(PLAN)['sha256'])),flush=True)
def validate_plan():
 p=m.load(PLAN)
 for dep in p['evidence']:checked(dep)
 assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256'];assert p['records']==records();return p,reference(PLAN)['sha256']
def citation_note(v,digest):return json.dumps(dict(plan_sha256=digest,source_record=v,review_reference=reference(REVIEW),policy='Retained exact museum-published object metadata,source HTTP hashes,loan/version comparisons and scholarly accession evidence. Original creator/date conflicts and literal qualifications retained. No images or current-display claim.'),ensure_ascii=False)
def holding_note(v,digest):return 'Museum-published object and collection evidence. Editorial confidence0.95,not calibrated. '+v['decision']['basis']+' '+v['decision']['limitation']+' Plan SHA-256 '+digest
def expected_art(v):
 f=v['facts'];return dict(id=v['artwork_id'],slug=v['slug'],title=f['title'],normalized_title=m.norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],medium_text=f['medium'],dimensions_text=f['dimensions_text'],accession_number=f['inventory'],status='review',research_candidate=True,unlinked_creator_label=f['creator_label'],current_institution_id=IID,object_form=f['object_form'],created_by=m.ACTOR,updated_by=m.ACTOR)
def verify(db,p,digest):
 ids=[v['artwork_id'] for v in p['records']];snap=snapshot(db,ids);assert len(snap['artworks'])==len(snap['identifiers'])==len(snap['citations'])==len(snap['assertions'])==N;assert not snap['artists'] and not snap['media'] and not snap['media_assets'];assert snapshot(db,p['scoped_ids'])==p['before'];assert prior_state(db,p['prior_ids'])==p['prior_state']
 for v in p['records']:
  aid=v['artwork_id'];f=v['facts'];art=next(x for x in snap['artworks'] if x['id']==aid);assert all(art[k]==val for k,val in expected_art(v).items()),f['source_id']
  for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None
  ex=next(x for x in snap['identifiers'] if x['entity_id']==aid);assert(ex['scheme'],ex['external_id'],ex['canonical_url'],ex['source_id'])==(SCHEME,f['source_id'],f['source_url'],SID)
  c=next(x for x in snap['citations'] if x['entity_id']==aid);assert(c['source_id'],c['field_name'],c['source_record_id'],c['source_url'],c['evidence_note'],ts.instant(c['retrieved_at']))==(SID,'museum_expansion_native_metadata',f['source_id'],f['source_url'],citation_note(v,digest),ts.instant(v['retrieved_at']))
  h=next(x for x in snap['assertions'] if x['artwork_id']==aid);assert h['claim_type']=='holding' and h['institution_id']==IID and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_id']==SID and h['source_url']==f['source_url'] and h['evidence_note']==holding_note(v,digest) and ts.same_instant(h['checked_at'],v['retrieved_at']);assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
 assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n']==N;assert counts(db)==dict(linked=93+N,eligible=64+N)
 return dict(verified_new_records=N,existing_artworks_linked=0,current_counts=counts(db),protected_existing_records=len(p['scoped_ids']),prior_campaign_records_preserved=len(p['prior_ids']),prior_campaign_table_digests=p['prior_state'],new_identifiers=N,new_citations=N,new_accepted_holdings=N,new_media_links=0,new_artist_links=0,new_published=0,new_display_claims=0,editorial_holds=17,already_catalogued=1,distinct_source_object_ids=N,known_inventories=1)
def apply(expected_sha):
 p,digest=validate_plan();assert digest==expected_sha
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay: zero writes',flush=True);return
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(p['scoped_ids'],));db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(s.prior.s.PROTECT_IIDS,));preflight(db,p);backup=m.BACKUP/(KEY+'-reviewed-plan-001.json.gz');assert not backup.exists();m.save(backup,p)
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SLUG,'Guildhall selected museum-published artworks,9 October2026','collection_page','https://artsandculture.google.com/partner/guildhall-art-gallery'))
  for v in p['records']:
   f=v['facts'];aid=v['artwork_id'];retrieved=v['retrieved_at']
   db.execute("INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s)",(aid,v['slug'],f['title'],m.norm(f['title']),f['date_display'],f['first'],f['last'],f['date_precision'],f['work_type'],f['medium'],f['dimensions_text'],f['inventory'],f['creator_label'],f['object_form'],m.ACTOR,m.ACTOR))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,SCHEME,f['source_id'],f['source_url'],SID,retrieved));db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_native_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,f['source_id'],f['source_url'],citation_note(v,digest),retrieved,m.ACTOR));db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,IID,SID,f['source_url'],holding_note(v,digest),retrieved))
  result=verify(db,p,digest)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=N,existing_links=0,local_only=True,verification=result));print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');v=p.parse_args()
 if v.command=='prepare':prepare()
 elif v.command=='apply':assert v.plan_sha;apply(v.plan_sha)
 else:
  p,d=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,p,d)),flush=True)
