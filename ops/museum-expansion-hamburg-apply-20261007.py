#!/usr/bin/env python3
"""Pinned, loopback-only application of84explicitly reviewed Hamburg artworks."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-hamburg-review-20261007.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r);m=r.m;f=r.f;x=r.x;RUN=r.RUN;IID=f.d.IID
s=importlib.util.spec_from_file_location('y',Path(__file__).with_name('museum-expansion-yale-apply-20261007.py'));y=importlib.util.module_from_spec(s);s.loader.exec_module(y);y.IID=IID
snapshot=y.snapshot;counts=y.counts;expected_art=y.expected_art;checked_reference=r.checked_reference;reference=f.ref
KEY='hamburg-reviewed-additions-001';SID=m.uid('source/'+KEY);SOURCE_SLUG='museum-expansion-20261006-'+KEY;SCHEME='wikidata';PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'editorial-reviewed-001.json.gz'

def records():
 review=m.load(REVIEW);checked_reference(review['reviewer_reference']);checked_reference(review['candidate_reference'])
 ds,_=r.build();assert ds==review['decisions'];out=[]
 for d in ds:
  v=d['facts'];assert d['confidence']>=.8 and d['state']=='approved_review_only_addition'
  assert 100<=v['first']<=v['last']<=1970 and v['source_url']=='https://www.wikidata.org/wiki/'+v['source_id']
  assert not d['comparison']['source_hits'] and not d['comparison']['native_url_hits'] and not any(a['relevant'] for a in d['comparison']['inventory_hits'])
  batch=m.load(checked_reference(d['source_reference']));assert batch['entities'][v['source_id']]==d['source_entity']
  decision={k:d[k] for k in ['source_id','state','confidence','basis','limitation','supplement_references']}
  decision['full_editorial_review_reference']=reference(REVIEW)
  out.append(dict(artwork_id=m.uid(KEY+'/'+v['source_id']),slug='museum-expansion-'+KEY+'-'+v['source_id'].lower(),facts=v,source_facts=d['source_facts'],source_entity=d['source_entity'],source_reference=d['source_reference'],decision=decision,retrieved_at=batch['capture']['receipt']['retrieved_at'],source_format='Selected Wikidata raw entity JSON and HTTP receipt; original claims,ranks,qualifiers,references retained. Independently captured public source supplements where recorded. Unfetched native catalogue references are not native verification.'))
 assert len(out)==len({a['artwork_id'] for a in out})==len({a['facts']['source_id'] for a in out})==84
 return out

def fresh_identity(db):
 scope=m.load(RUN/'identity-scope-001.json.gz');assert x.i.queries(db,scope['params'])==scope['state'],'Reviewed identity scope changed'

def preflight(db,plan):
 assert snapshot(db,plan['scoped_ids'])==plan['before'],'Existing Hamburg scope changed'
 assert counts(db)==plan['before_counts']==dict(linked=24,eligible=24)
 fresh_identity(db)
 ids=[a['artwork_id'] for a in plan['records']];qids=[a['facts']['source_id'] for a in plan['records']];urls=[a['facts']['source_url'] for a in plan['records']]
 assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone()
 assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SOURCE_SLUG)).fetchone()
 assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='wikidata' AND external_id=ANY(%s)) OR canonical_url=ANY(%s)) LIMIT 1",(qids,urls)).fetchone()

def prepare():
 assert not PLAN.exists();selected=records();initial=m.load(RUN/'initial-scope-001.json.gz');ids=initial['scoped_ids']
 with m.connect() as db:
  before=snapshot(db,ids);assert before==initial['snapshot'];before_counts=counts(db)
  preflight(db,dict(records=selected,scoped_ids=ids,before=before,before_counts=before_counts))
  backup=m.BACKUP/(KEY+'-before.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),institution_id=IID,scoped_ids=ids,before=before,policy='Preimage of real local catalogue, no test fixtures.'))
 paths=[p for root in (m.RUN/'native').glob('hamburg*') if root.is_dir() for p in root.rglob('*') if p.is_file() and p.name!='README.md']
 paths+=list((m.ROOT/'ops').glob('*hamburg*20261007.py'))
 paths+=[Path(v.__file__).resolve() for v in [y,y.i,y.w,y.d,y.d.n,m,x.i,x.i.w,x.i.w.c,x.i.w.dates,x.i.w.dates.c,x.i.w.dates.d,x.i.w.dates.dates,x.i.w.dates.dates.d]]+[m.ROOT/'AGENTS.md']
 plan=dict(at=m.now(),records=selected,scoped_ids=ids,before=before,before_counts=before_counts,backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),evidence=[reference(p) for p in sorted(set(paths))],policy='84individually reviewed pre1971painting records with documentedHamburg connection; local review only. Explicit unknowns and source conflicts retained. No images,publication,artist links or existing catalogue edits.')
 m.save(PLAN,plan);print('Prepared',len(selected),hashlib.sha256(PLAN.read_bytes()).hexdigest(),flush=True)

def validate_plan():
 p=m.load(PLAN)
 for ref in p['evidence']:checked_reference(ref)
 assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256']
 assert p['records']==records();return p,hashlib.sha256(PLAN.read_bytes()).hexdigest()

def citation_note(v,digest):return json.dumps(dict(plan_sha256=digest,source_record=v,policy='Selected Wikidata secondary metadata; original claims and explicit independent-source resolutions retained. No silent source repair, image or display assertion.'),ensure_ascii=False)
def holding_note(v,digest):return v['decision']['basis']+' '+v['decision']['limitation']+' Plan SHA-256 '+digest

def verify(db,p,digest):
 rs=p['records'];ids=[v['artwork_id'] for v in rs];n=len(rs);snap=snapshot(db,ids)
 assert len(snap['artworks'])==len(snap['identifiers'])==len(snap['citations'])==len(snap['assertions'])==n
 assert not snap['artists'] and not snap['media'] and snapshot(db,p['scoped_ids'])==p['before']
 for v in rs:
  aid=v['artwork_id'];fv=v['facts'];art=next(a for a in snap['artworks'] if a['id']==aid)
  assert all(art[k]==value for k,value in expected_art(v).items()),fv['source_id']
  for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None,(fv['source_id'],k)
  ident=next(a for a in snap['identifiers'] if a['entity_id']==aid);assert (ident['scheme'],ident['external_id'],ident['canonical_url'],ident['source_id'])==(SCHEME,fv['source_id'],fv['source_url'],SID)
  c=next(a for a in snap['citations'] if a['entity_id']==aid);assert (c['source_id'],c['field_name'],c['source_record_id'],c['source_url'],c['evidence_note'])==(SID,'museum_expansion_reviewed_metadata',fv['source_id'],fv['source_url'],citation_note(v,digest))
  a=next(a for a in snap['assertions'] if a['artwork_id']==aid);assert a['claim_type']=='holding' and a['institution_id']==IID and a['context']=='collection' and a['review_state']=='accepted' and a['superseded_by'] is None and a['source_id']==SID and a['source_url']==fv['source_url'] and a['evidence_note']==holding_note(v,digest)
  assert not any(a.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
 assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n']==n
 assert counts(db)==dict(linked=p['before_counts']['linked']+n,eligible=p['before_counts']['eligible']+n)
 return dict(verified_new_records=n,known_inventories=sum(bool(v['facts']['inventory']) for v in rs),existing_artworks_unchanged=len(p['before']['artworks']),old_citations_unchanged=len(p['before']['citations']),new_artist_links=0,new_media_links=0,new_published=0,new_display_claims=0,new_identifiers=n,new_citations=n,new_accepted_holdings=n,current_counts=counts(db),verified_all_metadata_and_citations=True)

def apply(expected_sha):
 p,digest=validate_plan();assert digest==expected_sha;rs=p['records'];ids=[v['artwork_id'] for v in rs]
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  old=db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
  if old:
   assert len(old)==len(rs);verify(db,p,digest);print('Unchanged replay:',len(rs),'records;zero inserts',flush=True);return
  preflight(db,p);db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(IID,));m.save(m.BACKUP/(KEY+'-reviewed-plan.json.gz'),p)
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SOURCE_SLUG,'Hamburger Kunsthalle selected reviewed Wikidata artworks,7 October2026','collection_page','https://www.wikidata.org'))
  for v in rs:
   fv=v['facts'];aid=v['artwork_id'];retrieved=v['retrieved_at']
   db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s)''',(aid,v['slug'],fv['title'],m.norm(fv['title']),fv['date_display'],fv['first'],fv['last'],fv['date_precision'],fv['work_type'],fv['medium'],fv['dimensions_text'],fv['inventory'],fv['creator_label'],fv['object_form'],m.ACTOR,m.ACTOR))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,SCHEME,fv['source_id'],fv['source_url'],SID,retrieved))
   db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_reviewed_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,fv['source_id'],fv['source_url'],citation_note(v,digest),retrieved,m.ACTOR))
   db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,IID,SID,fv['source_url'],holding_note(v,digest),retrieved))
  result=verify(db,p,digest)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=len(rs),local_only=True,verification=result));print(json.dumps(result),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');arg=p.parse_args()
 if arg.command=='prepare':prepare()
 elif arg.command=='apply':assert arg.plan_sha;apply(arg.plan_sha)
 else:
  plan,digest=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
