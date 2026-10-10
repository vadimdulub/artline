"""Atomic selected Royal Collection holding links; preserve all object metadata and unresolved versions."""
import argparse,csv,hashlib,importlib.util,json,types
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
r=module('r','museum-expansion-royal-review-20261009.py');i=module('i','museum-expansion-royal-identity-20261009.py');ts=module('ts','museum-expansion-ferens-timestamps-20261009.py');s=r.s;m=r.m;RUN=r.RUN;IIDS=s.IIDS;reference=r.ref;checked=r.checked
KEY='royal-existing-holdings-001';SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY;PLAN=RUN/(KEY+'-plan-001.json.gz');REVIEW=RUN/'editorial-reviewed-001.json.gz';CHECKPOINT=s.CP;HCOUNT=79;N=0
snapshot=s.snapshot;counts=s.counts;prior_state=s.prior_state
def records():
 x=m.load(REVIEW);checked(x['reviewer_reference'])
 for dep in x['dependencies']:checked(dep)
 r.raw_checked();assert x['decisions']==r.build();out=[]
 for d in x['decisions']:
  if d['state']!='approved_existing_holding':continue
  assert d['confidence']>=.8 and d['previous_institution_id'] is None;aid=d['existing_artwork_id'];out.append(dict(institution_id=d['institution_id'],artwork_id=aid,holding_id=m.uid(KEY+'/holding/'+aid),facts=d['facts'],decision=d,retrieved_at=d['retrieved_at']))
 assert len(out)==len({v['artwork_id'] for v in out})==HCOUNT;return out
def prior_ids():
 ids=[]
 for name in ['added-artworks','reconciled-artworks']:
  with(m.RUN/(name+'-after-wave-89.csv')).open(newline='') as fp:ids.extend(v['artwork_id'] for v in csv.DictReader(fp))
 assert len(ids)==len(set(ids))==13020;return sorted(ids)
def verify_baseline():
 assert reference(CHECKPOINT)['sha256']=='40e55394ef6bf9c536e0ca549d1f901bb388e17c3dad3c162014c374a0454456';cp=m.load(CHECKPOINT)
 for dep in cp['artifacts']:checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 return cp
def fresh_identity(db):
 initial=m.load(RUN/'initial-scope-001.json.gz');painterids=sorted(v['id'] for v in initial['painters']);authorities=[v['row'] for v in db.execute("SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(painterids,))];assert authorities==initial['creator_authorities']
 x=m.load(RUN/'identity-001.json.gz');state=i.queries(db,x['params']);assert state==x['state'],'Current bounded identity scope changed';cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))];assert cs==m.load(RUN/'identity-citations-001.json.gz')['citations']
 if db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='off':
  path=m.BACKUP/(KEY+'-transaction-identity-001.json.gz');assert not path.exists();m.save(path,dict(at=m.now(),state_equal=True,citations_equal=True,identity_reference=reference(RUN/'identity-001.json.gz'),artwork_count=len(state['artworks']),citation_count=len(cs)))
def preflight(db,p):
 assert snapshot(db,p['scoped_ids'])==p['before'];assert counts(db)==p['before_counts']==m.load(RUN/'initial-scope-001.json.gz')['counts'];assert prior_state(db,p['prior_ids'])==p['prior_state'];fresh_identity(db);assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone()
 for v in p['holdings']:
  a=next(a for a in p['before']['artworks'] if a['id']==v['artwork_id']);assert a['current_institution_id'] is None and a['status']=='review';hs=[h for h in p['before']['assertions'] if h['artwork_id']==a['id']];assert not any(h['review_state']=='accepted' and h['superseded_by'] is None for h in hs)
  expected=[h['id'] for h in hs if h['institution_id']==v['institution_id'] and h['review_state']=='review' and h['superseded_by'] is None and h['claim_type']=='holding'];assert expected==v['decision']['supersede_assertion_ids']
  assert expected==[v['decision']['pending_assertion_id']] and v['institution_id']==s.IID
def dependencies():
 paths=set();seen=set()
 def visit(mod):
  if id(mod) in seen:return
  seen.add(id(mod));file=getattr(mod,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  paths.add(Path(file).resolve())
  for v in vars(mod).values():
   if isinstance(v,types.ModuleType):visit(v)
 for mod in [r,i,ts]:visit(mod)
 paths.add(Path(__file__).resolve());return paths
def prepare():
 assert not PLAN.exists();holds=records();verify_baseline();initial=m.load(RUN/'initial-scope-001.json.gz');identity=m.load(RUN/'identity-001.json.gz');ids=sorted(set(initial['scoped_ids'])|{h['id'] for c in identity['comparisons'] for h in c['hits']});pids=prior_ids();assert set(pids).isdisjoint(v['artwork_id'] for v in holds)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert snapshot(db,initial['scoped_ids'])==initial['snapshot'];p=dict(at=m.now(),holdings=holds,records=[],scoped_ids=ids,before=snapshot(db,ids),prior_ids=pids,prior_state=prior_state(db,pids),before_counts=counts(db),baseline_reference=reference(CHECKPOINT),policy='79 selected existing-object links:76 date-eligible and3 undated. Preserve12 unresolved Royal candidates and82 existing holdings. Supersede only the79 reviewed same-object,same-target pending assertions. No metadata,images,artist links,status,display,custody or ownership change.');preflight(db,p)
 backup=m.BACKUP/(KEY+'-before-001.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),scoped_ids=ids,before=p['before'],prior_ids=pids,prior_state=p['prior_state']));p.update(backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest());paths=dependencies()|{CHECKPOINT,m.ROOT/'AGENTS.md',Path(__file__).with_name('test_museum_expansion_royal_20261009.py').resolve()};paths|={v for v in RUN.rglob('*') if v.is_file() and v.name!='README.md'}
 for name in ['source-context-001.json.gz','comparison-source-context-001.json.gz']:
  for dep in m.load(RUN/name)['body_references']:paths.add(checked(dep))
 p['evidence']=[reference(v) for v in sorted(paths)];m.save(PLAN,p);print(json.dumps(dict(holdings=HCOUNT,protected_existing=len(ids),protected_prior=len(pids),sha256=reference(PLAN)['sha256'])),flush=True)
def validate_plan():
 p=m.load(PLAN)
 for dep in p['evidence']:checked(dep)
 assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256'];assert p['holdings']==records();return p,reference(PLAN)['sha256']
def citation_note(v,digest):return json.dumps(dict(plan_sha256=digest,source_record=v,review_reference=reference(REVIEW),institution_context_reference=reference(RUN/'royal-household-context-001.json'),access_hold_reference=reference(RUN/'native-probes-001.json'),policy='Exact retained Wikidata object evidence with Royal Collection references. Native RCT access returned403 and was stopped; Royal Household overview supplies institution context only. Correlated references are not independent confirmations. Selected maker,pendant and derivative distinctions are recorded in the review. Retained primary Walters evidence distinguishes the Byron replica. No legal ownership,current custody,palace location or current display claim. Source dates and existing metadata retained.'),ensure_ascii=False)
def holding_note(v,digest):return v['decision']['basis']+' '+v['decision']['limitation']+' Plan SHA-256 '+digest
def assert_delta(before,after,holds,digest):
 targets={v['artwork_id']:v for v in holds};old={a['id']:a for a in before['artworks']};new={a['id']:a for a in after['artworks']};assert set(old)==set(new)
 for aid,a in old.items():
  ignore={'current_institution_id','updated_at'} if aid in targets else set();assert {k:v for k,v in a.items() if k not in ignore}=={k:v for k,v in new[aid].items() if k not in ignore}
  if aid in targets:assert a['current_institution_id'] is None and new[aid]['current_institution_id']==targets[aid]['institution_id']
 for key in ['artists','media','media_assets','identifiers','museums']:assert before[key]==after[key]
 assert [v for v in after['citations'] if v['source_id']!=SID]==before['citations'];newc=[v for v in after['citations'] if v['source_id']==SID];newh=[v for v in after['assertions'] if v['source_id']==SID];assert len(newc)==len(newh)==len(holds)
 allowed={hid:v['holding_id'] for v in holds for hid in v['decision']['supersede_assertion_ids']};expected=[dict(v,superseded_by=allowed[v['id']]) if v['id'] in allowed else v for v in before['assertions']];assert [v for v in after['assertions'] if v['source_id']!=SID]==expected
 for v in holds:
  c=next(c for c in newc if c['entity_id']==v['artwork_id']);h=next(h for h in newh if h['artwork_id']==v['artwork_id']);f=v['facts'];assert(c['source_id'],c['field_name'],c['source_record_id'],c['source_url'],c['evidence_note'])==(SID,'museum_expansion_holding_reconciliation',f['source_id'],f['source_url'],citation_note(v,digest));assert ts.same_instant(c['retrieved_at'],v['retrieved_at']);assert h['id']==v['holding_id'] and h['source_id']==SID and h['claim_type']=='holding' and h['institution_id']==v['institution_id'] and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==f['source_url'] and h['evidence_note']==holding_note(v,digest) and ts.same_instant(h['checked_at'],v['retrieved_at']);assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
def verify(db,p,digest):
 assert_delta(p['before'],snapshot(db,p['scoped_ids']),p['holdings'],digest);assert prior_state(db,p['prior_ids'])==p['prior_state'];expected={iid:dict(linked=p['before_counts'][iid]['linked']+sum(v['institution_id']==iid for v in p['holdings']),eligible=p['before_counts'][iid]['eligible']+sum(v['institution_id']==iid and v['facts']['date_precision']!='unknown' for v in p['holdings'])) for iid in IIDS};assert counts(db)==expected
 assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",([v['artwork_id'] for v in p['holdings']],)).fetchone()['n']==76
 return dict(verified_new_records=0,existing_artworks_linked=79,previously_unlinked=79,current_counts=expected,protected_existing_records=len(p['scoped_ids']),prior_campaign_records_preserved=len(p['prior_ids']),prior_campaign_table_digests=p['prior_state'],prior_pending_assertions_superseded=sum(len(v['decision']['supersede_assertion_ids']) for v in p['holdings']),existing_royal_holdings_preserved=82,editorial_holds=12,unknown_date_records_preserved=3,date_eligible_links=76,new_media_links=0,new_artist_links=0,new_published=0,new_display_claims=0)
def apply(expected_sha):
 p,digest=validate_plan();assert digest==expected_sha
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay: zero writes',flush=True);return
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(p['scoped_ids'],));db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(s.PROTECT_IIDS,));preflight(db,p);backup=m.BACKUP/(KEY+'-reviewed-plan-001.json.gz');assert not backup.exists();m.save(backup,p);db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SLUG,'Royal Collection reviewed object holdings with explicitly referenced secondary evidence,9 October2026','collection_page','https://www.wikidata.org/wiki/Q1459037'))
  for v in p['holdings']:
   f=v['facts'];aid=v['artwork_id'];hid=v['holding_id'];db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_holding_reconciliation',%s,%s,%s,%s,%s,%s)",(aid,SID,f['source_id'],f['source_url'],citation_note(v,digest),v['retrieved_at'],m.ACTOR));db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'review')",(hid,aid,v['institution_id'],SID,f['source_url'],holding_note(v,digest),v['retrieved_at']));db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=ANY(%s::uuid[])',(hid,v['decision']['supersede_assertion_ids']));db.execute("UPDATE artwork_location_assertions SET review_state='accepted' WHERE id=%s AND review_state='review'",(hid,))
  result=verify(db,p,digest)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=0,existing_links=79,local_only=True,verification=result));print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');v=p.parse_args()
 if v.command=='prepare':prepare()
 elif v.command=='apply':assert v.plan_sha;apply(v.plan_sha)
 else:
  p,d=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,p,d)),flush=True)
