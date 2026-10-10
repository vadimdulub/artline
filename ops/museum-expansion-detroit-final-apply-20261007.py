#!/usr/bin/env python3
"""Atomic, replay-safe local delivery of the individually reviewed Detroit objects."""
import argparse,csv,hashlib,importlib.util,json,types
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
r=module('r','museum-expansion-detroit-final-review-20261007.py');old=module('old','museum-expansion-detroit-priority-apply-20261007.py')
m=r.m;f=r.f;RUN=r.RUN;IID=r.IID;reference=r.ref;checked=r.checked
KEY='detroit-reviewed-followup-001';SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY
PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'editorial-reviewed-002.json.gz';CHECKPOINT=m.RUN/'native/detroit-priority/delivery-checkpoint-001.json'
COUNT=92;HCOUNT=2;HOLDINGS=r.HOLDINGS
def records():
 review=m.load(REVIEW);checked(review['reviewer_reference']);assert review['decisions']==r.build()
 for dep in review['supplement_references']:checked(dep)
 new=[];holds=[]
 for d in review['decisions']:
  if d['state']=='editorial_hold':continue
  assert d['confidence']>=.8 and d['basis'] and d['limitation'];v=d['facts'];n=d['number']
  row=dict(institution_id=IID,provider='detroit',scheme='detroit-object',facts=v,decision=d,retrieved_at=d['retrieved_at'])
  if d['state']=='approved_existing_holding':
   aid=HOLDINGS[n];row.update(artwork_id=aid,holding_id=m.uid(KEY+'/holding/'+aid));holds.append(row)
  else:
   assert d['state']=='approved_review_only_addition';row.update(artwork_id=m.uid(KEY+'/'+v['source_id']),slug='museum-expansion-'+KEY+'-'+v['source_id']);new.append(row)
 assert len(new)==COUNT and len(holds)==HCOUNT and len({x['facts']['inventory'] for x in new+holds})==COUNT+HCOUNT
 return new,holds
def snapshot(db,ids):
 out=old.snapshot(db,ids)
 mids=sorted({x['media_id'] for x in out['media']}|{x['primary_media_id'] for x in out['artworks'] if x['primary_media_id']})
 out['media_assets']=[x['row'] for x in db.execute('SELECT to_jsonb(x) row FROM media_assets x WHERE id=ANY(%s::uuid[]) ORDER BY id',(mids,))]
 return out
def counts(db):return old.counts(db)
def expected_art(v):return old.expected_art(v)
def prior_ids():
 ids=[]
 for prefix in ['added-artworks','reconciled-artworks']:
  with (m.RUN/(prefix+'-after-wave-51.csv')).open(newline='') as fp:ids += [x['artwork_id'] for x in csv.DictReader(fp)]
 assert len(ids)==len(set(ids))==6099 and set(ids).isdisjoint(HOLDINGS.values());return sorted(ids)
def digest_rows(rows):
 h=hashlib.sha256();count=0
 for row in rows:h.update(json.dumps(row,sort_keys=True,ensure_ascii=False,separators=(',',':'),default=str).encode()+b'\n');count+=1
 return dict(rows=count,sha256=h.hexdigest())
def prior_state(db,ids):
 # All prior campaign objects and their associated metadata are protected by
 # content digests; full existing Detroit and comparison rows have preimages.
 out=snapshot(db,ids);return {k:digest_rows(v if isinstance(v,list) else [v]) for k,v in out.items()}
def fresh_identity(db):
 x=m.load(r.IDENTITY);assert f.i.queries(db,x['params'])==x['state'],'Final identity scope changed'
 c=m.load(r.CITATIONS);actual=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(c['selected_ids'],))];assert actual==c['citations'],'Version citations changed'
def preflight(db,p):
 assert snapshot(db,p['scoped_ids'])==p['before'],'Protected Detroit/comparison preimage changed'
 assert counts(db)==dict(linked=6,eligible=6)
 assert prior_state(db,p['prior_ids'])==p['prior_state'],'Earlier campaign records changed'
 fresh_identity(db)
 assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone()
 assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[])',([x['artwork_id'] for x in p['records']],)).fetchone()
 for aid in HOLDINGS.values():
  art=next(x for x in p['before']['artworks'] if x['id']==aid);assert art['current_institution_id'] is None and (art['creation_year_start'],art['creation_year_end'],art['date_precision'])==(1715,1715,'exact') and art['status']=='review' and art['primary_media_id']
  hs=[h for h in p['before']['assertions'] if h['artwork_id']==aid]
  assert len(hs)==1 and hs[0]['institution_id']==IID and hs[0]['claim_type']=='holding' and hs[0]['review_state']=='review' and hs[0]['superseded_by'] is None
def dependencies():
 paths=set();seen=set()
 def visit(mod):
  if id(mod) in seen:return
  seen.add(id(mod));file=getattr(mod,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  paths.add(Path(file).resolve())
  for value in vars(mod).values():
   if isinstance(value,types.ModuleType):visit(value)
 for mod in [r,old,m]:visit(mod)
 return paths
def verify_baseline():
 assert reference(CHECKPOINT)['sha256']=='1bb84ef12601ee2a933bd9724ebdece28bfb8108c25d9835f6cb8da106c817ae'
 cp=m.load(CHECKPOINT)
 for dep in cp['artifacts']:old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==old.h.OLD else checked(dep)
 return cp
def prepare():
 assert not PLAN.exists();new,holds=records();cp=verify_baseline();initial=m.load(RUN/'initial-scope-001.json.gz');version=m.load(RUN/'version-scope-001.json.gz');ids=sorted(set(initial['scoped_ids'])|set(version['selected_ids']));prior=prior_ids()
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
  assert old.snapshot(db,initial['scoped_ids'])==initial['snapshot']
  assert old.snapshot(db,version['selected_ids'])==version['snapshot']
  p=dict(at=m.now(),records=new,holdings=holds,scoped_ids=ids,before=snapshot(db,ids),prior_ids=prior,prior_state=prior_state(db,prior),baseline_reference=reference(CHECKPOINT),policy='Local only:92 review additions and2 existing holding reconciliations. Preserve all existing catalogue metadata, dates, images and publication state. Supersede exactly2 pending assertions. Source qualifications and unknown rights retained. No image attachments, new artist authorities or current-display claims.')
  preflight(db,p)
 backup=m.BACKUP/(KEY+'-before.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),scoped_ids=ids,before=p['before'],prior_ids=prior,prior_state=p['prior_state']));p.update(backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest())
 paths=dependencies()|{Path(__file__).resolve(),REVIEW,CHECKPOINT,m.ROOT/'AGENTS.md',Path(__file__).with_name('test_museum_expansion_detroit_final_20261007.py')}
 paths|={p for p in RUN.rglob('*') if p.is_file() and p.name!='README.md'}
 paths|={p for p in (m.RUN/'native/detroit-resume').rglob('*') if p.is_file() and p.name!='README.md'}
 visual=m.load(RUN/'judith-visual-comparison-002.json');image=m.load(RUN/'judith-visual-inspection-001.json');pdf=m.load(RUN/'judith-primary-pdf-receipt-001.json')
 p['external_evidence']=[visual['render'],image['preserved_reference'],dict(path=pdf['path'],sha256=pdf['sha256'])]
 for dep in p['external_evidence']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 p['evidence']=[reference(x) for x in sorted(paths)];m.save(PLAN,p);print(json.dumps(dict(new=COUNT,holdings=HCOUNT,protected_existing=len(ids),protected_prior=len(prior),sha256=hashlib.sha256(PLAN.read_bytes()).hexdigest())),flush=True)
def validate_plan():
 p=m.load(PLAN)
 for dep in p['evidence']:checked(dep)
 for dep in p['external_evidence']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256']
 new,holds=records();assert p['records']==new and p['holdings']==holds
 return p,hashlib.sha256(PLAN.read_bytes()).hexdigest()
def citation_note(v,digest):return json.dumps(dict(plan_sha256=digest,source_record=v,policy='Official native HTML and object/index capture chain retained with explicit individual version review. Comparison web extracts and actual Judith visual comparison are separately identified. Existing metadata unchanged. New records remain review; no image or display claim.'),ensure_ascii=False)
def holding_note(v,digest):return v['decision']['basis']+' '+v['decision']['limitation']+' Plan SHA-256 '+digest
def assert_delta(before,after,holds,digest):
 targets={v['artwork_id']:v for v in holds};oldby={a['id']:a for a in before['artworks']};newby={a['id']:a for a in after['artworks']};assert set(oldby)==set(newby)
 for aid,a in oldby.items():
  ignored={'current_institution_id','updated_at'} if aid in targets else set()
  assert {k:v for k,v in a.items() if k not in ignored}=={k:v for k,v in newby[aid].items() if k not in ignored},aid
  if aid in targets:assert a['current_institution_id'] is None and newby[aid]['current_institution_id']==IID
 for k in ['artists','media','media_assets','identifiers','museum']:assert before[k]==after[k],k
 assert [x for x in after['citations'] if x['source_id']!=SID]==before['citations']
 newc=[x for x in after['citations'] if x['source_id']==SID];newh=[x for x in after['assertions'] if x['source_id']==SID];assert len(newc)==len(newh)==HCOUNT
 expected=[]
 for a in before['assertions']:
  if a['artwork_id'] in targets:
   assert a['review_state']=='review' and a['claim_type']=='holding' and a['institution_id']==IID and a['superseded_by'] is None
   expected.append(dict(a,superseded_by=targets[a['artwork_id']]['holding_id']))
  else:expected.append(a)
 assert [x for x in after['assertions'] if x['source_id']!=SID]==expected
 for v in holds:
  aid=v['artwork_id'];c=next(x for x in newc if x['entity_id']==aid);h=next(x for x in newh if x['artwork_id']==aid)
  verify_citation(c,v,digest,'museum_expansion_holding_reconciliation');verify_holding(h,v,digest);assert h['id']==v['holding_id']
def verify_citation(c,v,digest,field):
 fv=v['facts'];assert (c['source_id'],c['field_name'],c['source_record_id'],c['source_url'],c['evidence_note'])==(SID,field,fv['source_id'],fv['source_url'],citation_note(v,digest))
def verify_holding(h,v,digest):
 assert h['source_id']==SID and h['claim_type']=='holding' and h['institution_id']==IID and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==v['facts']['source_url'] and h['evidence_note']==holding_note(v,digest)
 assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
def verify(db,p,digest):
 assert_delta(p['before'],snapshot(db,p['scoped_ids']),p['holdings'],digest)
 assert prior_state(db,p['prior_ids'])==p['prior_state'],'Prior campaign rows changed'
 ids=[v['artwork_id'] for v in p['records']];snap=snapshot(db,ids)
 assert all(len(snap[k])==COUNT for k in ['artworks','identifiers','citations','assertions']) and not snap['artists'] and not snap['media'] and not snap['media_assets']
 for v in p['records']:
  aid=v['artwork_id'];fv=v['facts'];a=next(x for x in snap['artworks'] if x['id']==aid)
  assert all(a[k]==value for k,value in expected_art(v).items()),fv['source_id']
  for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert a[k] is None
  e=next(x for x in snap['identifiers'] if x['entity_id']==aid);assert (e['scheme'],e['external_id'],e['canonical_url'],e['source_id'])==(v['scheme'],fv['source_id'],fv['source_url'],SID)
  verify_citation(next(x for x in snap['citations'] if x['entity_id']==aid),v,digest,'museum_expansion_reviewed_metadata')
  verify_holding(next(x for x in snap['assertions'] if x['artwork_id']==aid),v,digest)
 allids=ids+list(HOLDINGS.values());assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(allids,)).fetchone()['n']==COUNT+HCOUNT
 assert counts(db)==dict(linked=100,eligible=100)
 return dict(verified_new_records=COUNT,existing_artworks_linked=HCOUNT,current_counts=counts(db),protected_existing_records=len(p['scoped_ids']),prior_campaign_records_preserved=len(p['prior_ids']),prior_campaign_table_digests=p['prior_state'],prior_pending_assertions_superseded=2,new_media_links=0,new_artist_links=0,new_published=0,new_display_claims=0)
def apply(expected_sha):
 p,digest=validate_plan();assert digest==expected_sha
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay:92 additions and2 holdings;zero writes',flush=True);return
  preflight(db,p);db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(p['scoped_ids'],));db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(IID,))
  backup=m.BACKUP/(KEY+'-reviewed-plan.json.gz');assert not backup.exists();m.save(backup,p)
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SLUG,'Detroit Institute of Arts selected native catalogue records, reviewed 7 October 2026','collection_page','https://dia.org/collection'))
  for v in p['records']:
   fv=v['facts'];aid=v['artwork_id'];db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s)""",(aid,v['slug'],fv['title'],m.norm(fv['title']),fv['date_display'],fv['first'],fv['last'],fv['date_precision'],fv['work_type'],fv['medium'],fv['dimensions_text'],fv['inventory'],fv['creator_label'],fv['object_form'],m.ACTOR,m.ACTOR))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,v['scheme'],fv['source_id'],fv['source_url'],SID,v['retrieved_at']))
  for v in p['records']+p['holdings']:
   fv=v['facts'];aid=v['artwork_id'];is_hold=v in p['holdings'];field='museum_expansion_holding_reconciliation' if is_hold else 'museum_expansion_reviewed_metadata';hid=v.get('holding_id',m.uid(KEY+'/holding/'+aid))
   db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,%s,%s,%s,%s,%s,%s)",(aid,field,SID,fv['source_id'],fv['source_url'],citation_note(v,digest),v['retrieved_at'],m.ACTOR))
   db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(hid,aid,IID,SID,fv['source_url'],holding_note(v,digest),v['retrieved_at']))
   if is_hold:
    for a in [x for x in p['before']['assertions'] if x['artwork_id']==aid]:db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s',(hid,a['id']))
  result=verify(db,p,digest)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=COUNT,existing_links=HCOUNT,local_only=True,verification=result));print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');args=p.parse_args()
 if args.command=='prepare':prepare()
 elif args.command=='apply':assert args.plan_sha;apply(args.plan_sha)
 else:
  plan,digest=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
