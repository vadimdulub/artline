#!/usr/bin/env python3
"""Apply a pinned editorial selection of Courtauld objects to the local review catalogue."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-courtauld-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);w=i.w;d=w.d;m=w.m;RUN=w.RUN;IID=d.IID
KEY='courtauld-native-additions-001';SID=m.uid('source/'+KEY);SOURCE_SLUG='museum-expansion-20261006-'+KEY;SCHEME='courtauld-native-object'
PLAN=RUN/(KEY+'-plan.json.gz');IDENTITY=RUN/'native-identity-002.json.gz';CANDIDATES=RUN/'native-candidates-002.json.gz';COMPARISONS=RUN/'native-comparisons-002.json.gz'
reference=w.ref
REVIEWS=[RUN/'editorial-reviewed-001.json.gz']

def checked_reference(ref):
 p=m.ROOT/ref['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256'];return p

def snapshot(db,ids):
 qs=dict(artworks='SELECT to_jsonb(x) row FROM artworks x WHERE id=ANY(%s::uuid[]) ORDER BY id',artists='SELECT to_jsonb(x) row FROM artwork_artists x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id,attribution_role',media='SELECT to_jsonb(x) row FROM artwork_media x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',identifiers="SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",citations="SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",assertions='SELECT to_jsonb(x) row FROM artwork_location_assertions x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,id')
 out={k:[r['row'] for r in db.execute(q,(ids,))] for k,q in qs.items()};out['museum']=db.execute('SELECT to_jsonb(x) row FROM institutions x WHERE id=%s',(IID,)).fetchone()['row'];return out
def counts(db):return db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()

def decisions():
 return [x for p in REVIEWS for x in m.load(p)['decisions']]

def records():
 cs={x['source_id']:x for x in m.load(CANDIDATES)['rows'] if x['state']=='candidate'};cm={x['source_id']:x for x in m.load(COMPARISONS)['records']};out=[];seen=set()
 for decision in decisions():
  assert decision['source_id'] not in seen;seen.add(decision['source_id'])
  assert decision['state']=='approved_review_only_addition'
  row=cs[decision['source_id']];path=checked_reference(row['source_reference']);native,parsed=w.checked_record(path);facts=w.facts(native,parsed)
  assert facts==row['facts']==decision['facts'] and native['index_row']==row['index']==decision['index']
  assert row['grouping']==decision['grouping'] and not row['grouping']['component_number']
  assert row['source_reference']==decision['source_reference'] and cm[row['source_id']]==decision['comparison']
  assert decision['confidence']==.95 and len(decision['basis'])>60 and decision['limitation']
  assert not decision['comparison']['source_hits'] and not [x for x in decision['comparison']['inventory_hits'] if x['relevant']]
  assert facts['date_issue'] is None and facts['first'] is not None and 100<=facts['first']<=facts['last']<=1970
  assert facts['inventory'].startswith('P.') and facts['creator_label'] and facts['credit'].startswith('Courtauld Gallery, London')
  assert 'missing' not in str([facts['inventory'],facts['provenance']]).casefold()
  out.append(dict(artwork_id=m.uid(KEY+'/'+row['source_id']),slug='museum-expansion-'+KEY+'-'+row['source_id'],facts=facts,decision=decision,retrieved_at=native['capture']['receipt']['retrieved_at'],source_format='Retained official native HTML and HTTP receipts, with bounded index-to-object chain and full native metadata/rights/provenance.'))
 assert len(out)==len({x['artwork_id'] for x in out})==len({x['facts']['inventory'] for x in out})==90
 inventories={x['facts']['inventory'] for x in out}
 assert not any(set(x['decision']['grouping']['child_inventories'])&inventories for x in out)
 return out

def fresh_identity(db):
 v=m.load(IDENTITY);assert i.queries(db,v['params'])==v['state'],'Identity review scope changed'

def preflight(db,plan):
 assert snapshot(db,plan['scoped_ids'])==plan['before'],'Existing museum records changed'
 assert counts(db)==plan['before_counts']==dict(linked=16,eligible=15)
 fresh_identity(db)
 ids=[r['artwork_id'] for r in plan['records']];urls=[r['facts']['source_url'] for r in plan['records']]
 assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone()
 assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SOURCE_SLUG)).fetchone()
 assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) LIMIT 1",(urls,)).fetchone()

def prepare():
 assert not PLAN.exists();selected=records();initial=m.load(RUN/'initial-scope-001.json.gz');ids=initial['scoped_ids']
 with m.connect() as db:
  before=snapshot(db,ids);assert before==initial['snapshot'],'Museum changed since initial source scope'
  preflight(db,dict(records=selected,scoped_ids=ids,before=before,before_counts=counts(db)))
  backup=m.BACKUP/(KEY+'-before.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),institution_id=IID,scoped_ids=ids,before=before,policy='Preimage of real local catalogue scope; not a test database.'))
  paths=[p for p in RUN.rglob('*') if p.is_file() and p.name!='README.md']
  paths += [Path(x.__file__).resolve() for x in [i,w,w.c,d,d.n,m,w.dates,w.dates.d]]
  paths += [Path(__file__).resolve(),Path(__file__).with_name('museum-expansion-courtauld-facts-initial-20261007.py').resolve(),Path(__file__).with_name('test_museum_expansion_courtauld_20261007.py').resolve(),m.ROOT/'AGENTS.md']
  plan=dict(at=m.now(),records=selected,scoped_ids=ids,before=before,before_counts=counts(db),backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),evidence=[reference(p) for p in sorted(set(paths))],policy='Selected official Courtauld catalogue objects created by1970. Review only; qualified creators and unknown fields retained. Original HTML/HTTP evidence retained separately from discovery web-tool text. Museum connection does not establish current display, custody or legal ownership. No images, artist links, existing metadata edits or publication.')
 m.save(PLAN,plan);print('Prepared',len(selected),hashlib.sha256(PLAN.read_bytes()).hexdigest(),flush=True)

def validate_plan():
 plan=m.load(PLAN)
 for ref in plan['evidence']:checked_reference(ref)
 assert hashlib.sha256(Path(plan['backup_path']).read_bytes()).hexdigest()==plan['backup_sha256']
 assert plan['records']==records();return plan,hashlib.sha256(PLAN.read_bytes()).hexdigest()
def citation_note(r,digest):return json.dumps(dict(plan_sha256=digest,source_record=r,policy='Official native HTML and HTTP receipts retained with hashed source chain. Creation/acquisition, qualified creators, native narrative and source limitations preserved. No image or display assertion.'),ensure_ascii=False)
def holding_note(r,digest):return 'Official Courtauld collection object page, explicit collection credit and bounded painting index; exact accession and object identity. Native production dates, qualified makers, provenance, rights and grouping retained. Editorial confidence 0.95, not calibrated. '+r['decision']['basis']+' '+r['decision']['limitation']+' Plan SHA-256 '+digest

def expected_art(r):
 v=r['facts'];return dict(id=r['artwork_id'],slug=r['slug'],title=v['title'],normalized_title=m.norm(v['title']),date_display=v['date_display'],creation_year_start=v['first'],creation_year_end=v['last'],date_precision=v['date_precision'],work_type=v['work_type'],medium_text=v['medium'],dimensions_text=v['dimensions_text'],accession_number=v['inventory'],status='review',research_candidate=True,unlinked_creator_label=v['creator_label'],current_institution_id=IID,object_form=v['object_form'],created_by=m.ACTOR,updated_by=m.ACTOR)
def verify(db,plan,digest):
 rs=plan['records'];ids=[r['artwork_id'] for r in rs];count=len(rs);snap=snapshot(db,ids)
 assert len(snap['artworks'])==len(snap['identifiers'])==len(snap['citations'])==len(snap['assertions'])==count
 assert not snap['artists'] and not snap['media'];assert snapshot(db,plan['scoped_ids'])==plan['before']
 for r in rs:
  aid=r['artwork_id'];v=r['facts'];art=next(x for x in snap['artworks'] if x['id']==aid);assert all(art[k]==val for k,val in expected_art(r).items()),v['source_id']
  for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None,(v['source_id'],k)
  ident=next(x for x in snap['identifiers'] if x['entity_id']==aid);assert (ident['scheme'],ident['external_id'],ident['canonical_url'],ident['source_id'])==(SCHEME,v['source_id'],v['source_url'],SID)
  c=next(x for x in snap['citations'] if x['entity_id']==aid);assert c['source_id']==SID and c['field_name']=='museum_expansion_native_metadata' and c['source_record_id']==v['source_id'] and c['source_url']==v['source_url'] and c['evidence_note']==citation_note(r,digest)
  a=next(x for x in snap['assertions'] if x['artwork_id']==aid);assert a['claim_type']=='holding' and a['institution_id']==IID and a['context']=='collection' and a['review_state']=='accepted' and a['superseded_by'] is None and a['source_id']==SID and a['source_url']==v['source_url'] and a['evidence_note']==holding_note(r,digest)
  assert not any(a.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
 assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n']==count
 current=counts(db);assert current==dict(linked=16+count,eligible=15+count)
 return dict(verified_new_records=count,source_inventory_count=count,existing_artworks_unchanged=len(plan['before']['artworks']),old_citations_unchanged=len(plan['before']['citations']),new_artist_links=0,new_media_links=0,new_published=0,new_display_claims=0,new_identifiers=count,new_citations=count,new_accepted_holdings=count,current_counts=current,verified_all_metadata_and_citations=True)

def apply(expected_sha):
 plan,digest=validate_plan();assert digest==expected_sha;rs=plan['records'];ids=[r['artwork_id'] for r in rs]
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  old=db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
  if old:
   assert len(old)==len(rs);verify(db,plan,digest);print('Unchanged replay:',len(rs),'records;zero inserts',flush=True);return
  preflight(db,plan);db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(IID,));m.save(m.BACKUP/(KEY+'-reviewed-plan.json.gz'),plan)
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SOURCE_SLUG,'Courtauld selected native artworks,7 October2026','collection_page',d.BASE))
  for r in rs:
   v=r['facts'];aid=r['artwork_id'];retrieved=r['retrieved_at']
   db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s)''',(aid,r['slug'],v['title'],m.norm(v['title']),v['date_display'],v['first'],v['last'],v['date_precision'],v['work_type'],v['medium'],v['dimensions_text'],v['inventory'],v['creator_label'],v['object_form'],m.ACTOR,m.ACTOR))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,SCHEME,v['source_id'],v['source_url'],SID,retrieved))
   db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_native_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,v['source_id'],v['source_url'],citation_note(r,digest),retrieved,m.ACTOR))
   db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,IID,SID,v['source_url'],holding_note(r,digest),retrieved))
  result=verify(db,plan,digest)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=len(rs),local_only=True,verification=result));print(json.dumps(result),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');a=p.parse_args()
 if a.command=='prepare':prepare()
 elif a.command=='apply':assert a.plan_sha;apply(a.plan_sha)
 else:
  plan,digest=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
