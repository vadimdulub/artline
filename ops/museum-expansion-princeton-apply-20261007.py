#!/usr/bin/env python3
"""Atomic local Princeton review additions and exact existing holding reconciliations."""
import argparse,csv,hashlib,importlib.util,json,types
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
r=module('review','museum-expansion-princeton-review-20261007.py');b=module('b','museum-expansion-baltimore-apply-20261007.py');base=b.prior.old.old
m=r.m;RUN=r.RUN;IID=r.IID;reference=r.ref;checked=r.checked
KEY='princeton-reviewed-additions-001';SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY
PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'editorial-reviewed-001.json.gz';CHECKPOINT=m.RUN/'native/baltimore/delivery-checkpoint-001.json'
COUNT=146;HCOUNT=18
def records():
 x=m.load(REVIEW);checked(x['reviewer_reference']);assert x['decisions']==r.build()
 for dep in x['supplement_references']:checked(dep)
 new=[];holds=[]
 for d in x['decisions']:
  if d['state']=='editorial_hold':continue
  assert d['confidence']>=.8;f=d['facts'];v=dict(institution_id=IID,provider='princeton',scheme='princeton-object',facts=f,decision=d,retrieved_at=d['retrieved_at'])
  if d['state']=='approved_existing_holding':
   aid=d['existing_artwork_id'];v.update(artwork_id=aid,holding_id=m.uid(KEY+'/holding/'+aid));holds.append(v)
  else:
   assert d['state']=='approved_review_only_addition';v.update(artwork_id=m.uid(KEY+'/'+f['source_id']),slug='museum-expansion-'+KEY+'-'+f['source_id']);new.append(v)
 assert len(new)==COUNT and len(holds)==HCOUNT and len({v['facts']['inventory'] for v in new+holds})==COUNT+HCOUNT;return new,holds
def snapshot(db,ids):
 out=base.snapshot(db,ids,IID);mids=sorted({v['media_id'] for v in out['media']}|{v['primary_media_id'] for v in out['artworks'] if v['primary_media_id']})
 out['media_assets']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM media_assets x WHERE id=ANY(%s::uuid[]) ORDER BY id',(mids,))];return out
def counts(db):return base.counts(db,IID)
def expected_art(v):return base.expected_art(v)
def prior_ids():
 ids=[]
 for name in ['added-artworks','reconciled-artworks']:
  with (m.RUN/(name+'-after-wave-53.csv')).open(newline='') as fp:ids += [v['artwork_id'] for v in csv.DictReader(fp)]
 assert len(ids)==len(set(ids))==6214;return sorted(ids)
def prior_state(db,ids):return {k:b.prior.digest_rows(v if isinstance(v,list) else [v]) for k,v in snapshot(db,ids).items()}
def verify_baseline():
 assert reference(CHECKPOINT)['sha256']=='fc614030b57207533a2540b4a0b5cdb03eaa525f3199fc7f00dbc886a01a2a81'
 cp=m.load(CHECKPOINT)
 for dep in cp['artifacts']:b.prior.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==b.prior.old.h.OLD else checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 return cp
def fresh_identity(db):
 assert r.aliases.query(db)==m.load(RUN/'latin-creator-aliases-001.json.gz')['state'],'Latin maker alias scope changed'
 x=m.load(r.IDENTITY);assert r.identity.queries(db,x['params'])==x['state'],'Identity scope changed'
 c=m.load(r.CITATIONS);actual=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(c['selected_ids'],))];assert actual==c['citations'],'Comparison citations changed'
def preflight(db,p):
 assert snapshot(db,p['scoped_ids'])==p['before'] and counts(db)==dict(linked=0,eligible=0)
 assert prior_state(db,p['prior_ids'])==p['prior_state'];fresh_identity(db)
 assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone()
 assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[])',([v['artwork_id'] for v in p['records']],)).fetchone()
 for v in p['holdings']:
  art=next(x for x in p['before']['artworks'] if x['id']==v['artwork_id']);assert art['current_institution_id'] is None and art['status']=='review' and art['accession_number']==v['facts']['inventory']
  hs=[h for h in p['before']['assertions'] if h['artwork_id']==v['artwork_id']];assert hs and all(h['claim_type']=='holding' and h['institution_id']==IID and h['review_state']=='review' and h['superseded_by'] is None for h in hs)
def dependencies():
 paths={Path(__file__).resolve()};seen=set()
 def visit(mod):
  if id(mod) in seen:return
  seen.add(id(mod));file=getattr(mod,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  paths.add(Path(file).resolve())
  for v in vars(mod).values():
   if isinstance(v,types.ModuleType):visit(v)
 for mod in [r,b]:visit(mod)
 return paths
def prepare():
 assert not PLAN.exists();new,holds=records();verify_baseline();initial=m.load(RUN/'initial-scope-001.json.gz');pids=prior_ids();ds=m.load(REVIEW)['decisions']
 ids=sorted(set(initial['scoped_ids'])|{a['id'] for d in ds for a in d['comparison']['leads']+d['comparison']['exact_title_hits']})
 assert set(pids).isdisjoint(v['artwork_id'] for v in holds)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert base.snapshot(db,initial['scoped_ids'],IID)==initial['snapshot']
  p=dict(at=m.now(),records=new,holdings=holds,scoped_ids=ids,before=snapshot(db,ids),prior_ids=pids,prior_state=prior_state(db,pids),baseline_reference=reference(CHECKPOINT),policy='Selected source-backed local Princeton additions remain review. Existing18 exact-object holding links preserve all metadata, dates, images, artist links and publication. Supersede only their pending Princeton holding assertions. No images, painter authorities, publication, current-display or production changes.')
  preflight(db,p)
 backup=m.BACKUP/(KEY+'-before.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),scoped_ids=ids,before=p['before'],prior_ids=pids,prior_state=p['prior_state']));p.update(backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest())
 paths=dependencies()|{CHECKPOINT,m.ROOT/'AGENTS.md',Path(__file__).with_name('test_museum_expansion_princeton_20261007.py')};paths|={v for v in RUN.rglob('*') if v.is_file() and v.name!='README.md'}
 p['evidence']=[reference(v) for v in sorted(paths)];m.save(PLAN,p);print(json.dumps(dict(new=COUNT,holdings=HCOUNT,protected_existing=len(ids),protected_prior=len(pids),sha256=reference(PLAN)['sha256'])),flush=True)
def validate_plan():
 p=m.load(PLAN)
 for dep in p['evidence']:checked(dep)
 assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256'];new,holds=records();assert p['records']==new and p['holdings']==holds;return p,reference(PLAN)['sha256']
def citation_note(v,digest):
 d=v['decision'];decision={k:d[k] for k in ['state','confidence','basis','limitation','existing_artwork_id','derived_fields']}
 return json.dumps(dict(plan_sha256=digest,facts=v['facts'],retrieved_at=v['retrieved_at'],native_capture_reference=d['source_reference'],editorial_decision=decision,review_reference=reference(REVIEW),identity_reference=reference(r.IDENTITY),discovery_queue_reference=reference(r.f.QUEUE),policy='Official public API facts retained in full. Hash-pinned review/identity artifacts retain the complete discovery and comparison rows without copying unrelated artworks into this citation. Museum/campus distinction preserved. Existing catalogue values unchanged; new additions review only. No image or current-display claim.'),ensure_ascii=False)
def holding_note(v,digest):return v['decision']['basis']+' '+v['decision']['limitation']+' Plan SHA-256 '+digest
def verify_citation(c,v,digest,field):
 f=v['facts'];assert(c['source_id'],c['field_name'],c['source_record_id'],c['source_url'],c['evidence_note'])==(SID,field,f['source_id'],f['source_url'],citation_note(v,digest))
def verify_holding(h,v,digest):
 assert h['source_id']==SID and h['claim_type']=='holding' and h['institution_id']==IID and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==v['facts']['source_url'] and h['evidence_note']==holding_note(v,digest)
 assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
def assert_delta(before,after,holds,digest):
 targets={v['artwork_id']:v for v in holds};old={a['id']:a for a in before['artworks']};new={a['id']:a for a in after['artworks']};assert set(old)==set(new)
 for aid,art in old.items():
  ignored={'current_institution_id','updated_at'} if aid in targets else set();assert {k:v for k,v in art.items() if k not in ignored}=={k:v for k,v in new[aid].items() if k not in ignored}
  if aid in targets:assert art['current_institution_id'] is None and new[aid]['current_institution_id']==IID
 for key in ['artists','media','media_assets','identifiers','museum']:assert before[key]==after[key]
 assert [v for v in after['citations'] if v['source_id']!=SID]==before['citations']
 newc=[v for v in after['citations'] if v['source_id']==SID];newh=[v for v in after['assertions'] if v['source_id']==SID];assert len(newc)==len(newh)==HCOUNT
 expected=[dict(v,superseded_by=targets[v['artwork_id']]['holding_id']) if v['artwork_id'] in targets else v for v in before['assertions']]
 assert [v for v in after['assertions'] if v['source_id']!=SID]==expected
 for v in holds:
  c=next(c for c in newc if c['entity_id']==v['artwork_id']);h=next(h for h in newh if h['artwork_id']==v['artwork_id']);verify_citation(c,v,digest,'museum_expansion_holding_reconciliation');verify_holding(h,v,digest);assert h['id']==v['holding_id']
def verify(db,p,digest):
 assert_delta(p['before'],snapshot(db,p['scoped_ids']),p['holdings'],digest);assert prior_state(db,p['prior_ids'])==p['prior_state']
 ids=[v['artwork_id'] for v in p['records']];snap=snapshot(db,ids);assert all(len(snap[k])==COUNT for k in ['artworks','identifiers','citations','assertions']) and not snap['artists'] and not snap['media'] and not snap['media_assets']
 for v in p['records']:
  f=v['facts'];aid=v['artwork_id'];art=next(x for x in snap['artworks'] if x['id']==aid);assert all(art[k]==value for k,value in expected_art(v).items())
  for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None
  e=next(x for x in snap['identifiers'] if x['entity_id']==aid);assert(e['scheme'],e['external_id'],e['canonical_url'],e['source_id'])==(v['scheme'],f['source_id'],f['source_url'],SID)
  verify_citation(next(x for x in snap['citations'] if x['entity_id']==aid),v,digest,'museum_expansion_reviewed_metadata');verify_holding(next(x for x in snap['assertions'] if x['artwork_id']==aid),v,digest)
 allids=ids+[v['artwork_id'] for v in p['holdings']];assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(allids,)).fetchone()['n']==COUNT+HCOUNT
 assert counts(db)==dict(linked=COUNT+HCOUNT,eligible=COUNT+HCOUNT)
 return dict(verified_new_records=COUNT,existing_artworks_linked=HCOUNT,current_counts=counts(db),protected_existing_records=len(p['scoped_ids']),prior_campaign_records_preserved=len(p['prior_ids']),prior_campaign_table_digests=p['prior_state'],prior_pending_assertions_superseded=sum(v['artwork_id'] in {a['artwork_id'] for a in p['holdings']} for v in p['before']['assertions']),new_media_links=0,new_artist_links=0,new_published=0,new_display_claims=0)
def apply(expected_sha):
 p,digest=validate_plan();assert digest==expected_sha
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay:zero writes',flush=True);return
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(p['scoped_ids'],));db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(IID,));preflight(db,p)
  backup=m.BACKUP/(KEY+'-reviewed-plan.json.gz');assert not backup.exists();m.save(backup,p)
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SLUG,'Princeton University Art Museum selected native API records, reviewed 8 October 2026','collection_page','https://data.artmuseum.princeton.edu'))
  for v in p['records']:
   f=v['facts'];aid=v['artwork_id'];db.execute("INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s)",(aid,v['slug'],f['title'],m.norm(f['title']),f['date_display'],f['first'],f['last'],f['date_precision'],f['work_type'],f['medium'],f['dimensions_text'],f['inventory'],f['creator_label'],f['object_form'],m.ACTOR,m.ACTOR))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,v['scheme'],f['source_id'],f['source_url'],SID,v['retrieved_at']))
  for v in p['records']+p['holdings']:
   f=v['facts'];aid=v['artwork_id'];hold=v in p['holdings'];hid=v.get('holding_id',m.uid(KEY+'/holding/'+aid));field='museum_expansion_holding_reconciliation' if hold else 'museum_expansion_reviewed_metadata'
   db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,%s,%s,%s,%s,%s,%s)",(aid,field,SID,f['source_id'],f['source_url'],citation_note(v,digest),v['retrieved_at'],m.ACTOR))
   db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(hid,aid,IID,SID,f['source_url'],holding_note(v,digest),v['retrieved_at']))
   if hold:
    for h in [x for x in p['before']['assertions'] if x['artwork_id']==aid]:db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s',(hid,h['id']))
  result=verify(db,p,digest)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=COUNT,existing_links=HCOUNT,local_only=True,verification=result));print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');v=p.parse_args()
 if v.command=='prepare':prepare()
 elif v.command=='apply':assert v.plan_sha;apply(v.plan_sha)
 else:
  p,d=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,p,d)),flush=True)
