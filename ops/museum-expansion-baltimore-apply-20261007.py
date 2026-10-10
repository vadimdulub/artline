#!/usr/bin/env python3
"""Atomic local delivery of the21 completed and individually reviewed BMA objects."""
import argparse,csv,hashlib,importlib.util,json,types
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
r=module('review','museum-expansion-baltimore-review-20261007.py');prior=module('prior','museum-expansion-detroit-final-apply-20261007.py')
m=r.m;RUN=r.RUN;IID=r.IID;reference=r.ref;checked=r.checked
KEY='baltimore-reviewed-additions-001';SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY;COUNT=21
PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'editorial-reviewed-001.json.gz';CHECKPOINT=m.RUN/'native/detroit-followup/delivery-checkpoint-001.json'
def records():
 x=m.load(REVIEW);checked(x['reviewer_reference']);assert x['decisions']==r.build()
 for dep in x['supplement_references']:checked(dep)
 out=[]
 for d in x['decisions']:
  if d['state']=='editorial_hold':continue
  assert d['state']=='approved_review_only_addition' and d['confidence']>=.8
  f=d['facts'];key=f['source_id'];out.append(dict(artwork_id=m.uid(KEY+'/'+key),slug='museum-expansion-'+KEY+'-'+hashlib.sha256(key.encode()).hexdigest()[:16],institution_id=IID,provider='baltimore',scheme='baltimore-object',facts=f,decision=d,retrieved_at=d['retrieved_at']))
 assert len(out)==len({x['facts']['inventory'] for x in out})==COUNT;return out
def snapshot(db,ids):
 out=prior.old.old.snapshot(db,ids,IID);mids=sorted({x['media_id'] for x in out['media']}|{x['primary_media_id'] for x in out['artworks'] if x['primary_media_id']})
 out['media_assets']=[x['row'] for x in db.execute('SELECT to_jsonb(x) row FROM media_assets x WHERE id=ANY(%s::uuid[]) ORDER BY id',(mids,))];return out
def counts(db):return prior.old.old.counts(db,IID)
def expected_art(v):return prior.old.old.expected_art(v)
def prior_ids():
 ids=[]
 for prefix in ['added-artworks','reconciled-artworks']:
  with (m.RUN/(prefix+'-after-wave-52.csv')).open(newline='') as fp:ids += [x['artwork_id'] for x in csv.DictReader(fp)]
 assert len(ids)==len(set(ids))==6193;return sorted(ids)
def prior_state(db,ids):return {k:prior.digest_rows(v if isinstance(v,list) else [v]) for k,v in snapshot(db,ids).items()}
def fresh_identity(db):
 x=m.load(r.IDENTITY);assert r.identity.base.queries(db,x['params'])==x['state'],'Identity scope changed'
 c=m.load(r.CITATIONS);actual=[x['row'] for x in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(c['selected_ids'],))];assert actual==c['citations'],'Version citation scope changed'
def verify_baseline():
 assert reference(CHECKPOINT)['sha256']=='f7044ae5292b085019ba840d4c75ca9a5c2dd45b53af403774e25ae64d88616c'
 cp=m.load(CHECKPOINT)
 for dep in cp['artifacts']:prior.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==prior.old.h.OLD else checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 return cp
def preflight(db,p):
 assert snapshot(db,p['scoped_ids'])==p['before'] and counts(db)==dict(linked=1,eligible=1)
 assert prior_state(db,p['prior_ids'])==p['prior_state'];fresh_identity(db)
 assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone()
 assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[])',([x['artwork_id'] for x in p['records']],)).fetchone()
def dependencies():
 paths={Path(__file__).resolve()};seen=set()
 def visit(mod):
  if id(mod) in seen:return
  seen.add(id(mod));file=getattr(mod,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  paths.add(Path(file).resolve())
  for v in vars(mod).values():
   if isinstance(v,types.ModuleType):visit(v)
 for mod in [r,prior]:visit(mod)
 return paths
def prepare():
 assert not PLAN.exists();rs=records();verify_baseline();initial=m.load(RUN/'initial-scope-001.json.gz');pids=prior_ids()
 # Complete preimages for the existing BMA object and all top comparison leads;
 # additional prior campaign rows are independently protected by content digests.
 decisions=m.load(REVIEW)['decisions'];ids=sorted(set(initial['scoped_ids'])|{a['id'] for d in decisions for a in d['comparison']['leads']})
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert prior.old.old.snapshot(db,initial['scoped_ids'],IID)==initial['snapshot']
  p=dict(at=m.now(),records=rs,scoped_ids=ids,before=snapshot(db,ids),prior_ids=pids,prior_state=prior_state(db,pids),baseline_reference=reference(CHECKPOINT),policy='21 review additions to local Baltimore Museum of Art. Preserve all existing records and all earlier campaign objects. Two captured holds and221 uncaptured leads excluded. No image attachments, painter authorities/links, publication, display or custody claims. Source challenge respected; no retry scheduled.')
  preflight(db,p)
 backup=m.BACKUP/(KEY+'-before.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),scoped_ids=ids,before=p['before'],prior_ids=pids,prior_state=p['prior_state']))
 p.update(backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest())
 paths=dependencies()|{CHECKPOINT,m.ROOT/'AGENTS.md',Path(__file__).with_name('test_museum_expansion_baltimore_20261007.py')}
 paths|={x for x in RUN.rglob('*') if x.is_file() and x.name!='README.md'}
 p['evidence']=[reference(x) for x in sorted(paths)];m.save(PLAN,p);print(json.dumps(dict(new=COUNT,protected_existing=len(ids),protected_prior=len(pids),sha256=reference(PLAN)['sha256'])),flush=True)
def validate_plan():
 p=m.load(PLAN)
 for dep in p['evidence']:checked(dep)
 assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256'];assert p['records']==records();return p,reference(PLAN)['sha256']
def citation_note(v,digest):return json.dumps(dict(plan_sha256=digest,source_record=v,policy='Complete native object and index capture chain, original creator roles and individual physical-version decision retained. Public AIC comparison API and web-tool primary/approved comparison excerpts identified separately. Literal source unknowns remain. Review only; no image/display claim.'),ensure_ascii=False)
def holding_note(v,digest):return v['decision']['basis']+' '+v['decision']['limitation']+' Plan SHA-256 '+digest
def verify(db,p,digest):
 assert snapshot(db,p['scoped_ids'])==p['before'],'Existing scoped records changed'
 assert prior_state(db,p['prior_ids'])==p['prior_state'],'Prior campaign records changed'
 ids=[v['artwork_id'] for v in p['records']];s=snapshot(db,ids)
 assert all(len(s[k])==COUNT for k in ['artworks','identifiers','citations','assertions']) and not s['artists'] and not s['media'] and not s['media_assets']
 for v in p['records']:
  f=v['facts'];aid=v['artwork_id'];art=next(x for x in s['artworks'] if x['id']==aid);assert all(art[k]==value for k,value in expected_art(v).items())
  for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None
  e=next(x for x in s['identifiers'] if x['entity_id']==aid);assert(e['scheme'],e['external_id'],e['canonical_url'],e['source_id'])==(v['scheme'],f['source_id'],f['source_url'],SID)
  c=next(x for x in s['citations'] if x['entity_id']==aid);assert(c['source_id'],c['field_name'],c['source_record_id'],c['source_url'],c['evidence_note'])==(SID,'museum_expansion_reviewed_metadata',f['source_id'],f['source_url'],citation_note(v,digest))
  h=next(x for x in s['assertions'] if x['artwork_id']==aid);assert h['source_id']==SID and h['claim_type']=='holding' and h['institution_id']==IID and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==f['source_url'] and h['evidence_note']==holding_note(v,digest)
  assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
 assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n']==COUNT
 assert counts(db)==dict(linked=22,eligible=22)
 return dict(verified_new_records=COUNT,existing_artworks_linked=0,current_counts=counts(db),protected_existing_records=len(p['scoped_ids']),prior_campaign_records_preserved=len(p['prior_ids']),prior_campaign_table_digests=p['prior_state'],new_media_links=0,new_artist_links=0,new_published=0,new_display_claims=0)
def apply(expected_sha):
 p,digest=validate_plan();assert digest==expected_sha
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay:21 additions;zero writes',flush=True);return
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(p['scoped_ids'],));db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(IID,));preflight(db,p)
  backup=m.BACKUP/(KEY+'-reviewed-plan.json.gz');assert not backup.exists();m.save(backup,p)
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SLUG,'Baltimore Museum of Art selected native collection records, reviewed 8 October 2026','collection_page','https://artbma.org/artworks/'))
  for v in p['records']:
   f=v['facts'];aid=v['artwork_id'];at=v['retrieved_at']
   db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s)""",(aid,v['slug'],f['title'],m.norm(f['title']),f['date_display'],f['first'],f['last'],f['date_precision'],f['work_type'],f['medium'],f['dimensions_text'],f['inventory'],f['creator_label'],f['object_form'],m.ACTOR,m.ACTOR))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,v['scheme'],f['source_id'],f['source_url'],SID,at))
   db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_reviewed_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,f['source_id'],f['source_url'],citation_note(v,digest),at,m.ACTOR))
   db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(m.uid(KEY+'/holding/'+aid),aid,IID,SID,f['source_url'],holding_note(v,digest),at))
  result=verify(db,p,digest)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=COUNT,existing_links=0,local_only=True,verification=result));print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');v=p.parse_args()
 if v.command=='prepare':prepare()
 elif v.command=='apply':assert v.plan_sha;apply(v.plan_sha)
 else:
  p,d=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,p,d)),flush=True)
