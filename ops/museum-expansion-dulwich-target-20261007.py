#!/usr/bin/env python3
"""Apply the second individually reviewed Dulwich selection to local Artline."""
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-dulwich-apply-20261007.py'));prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
i=prior.i;w=prior.w;m=prior.m;RUN=prior.RUN;IID=prior.IID
KEY='dulwich-target-200-001';SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY;COUNT=70;HCOUNT=2
PLAN=RUN/(KEY+'-plan.json.gz');reference=prior.reference;checked_reference=prior.checked_reference
HOLDINGS={'DPG258':'77a6b959-60d2-5237-9410-777a5aca597e','DPG632':'7caa6481-a584-5385-b11c-30a51705d6ba'}

def decisions():
 out={}
 for p in sorted(RUN.glob('target-reviewed-*.json.gz')):
  for d in m.load(p)['decisions']:
   assert d['inventory'] not in out;out[d['inventory']]=d
 for d in m.load(RUN/'target-reconsidered-001.json.gz')['decisions']:
  old=out[d['inventory']];assert old['state']==d['previous_state']=='editorial_hold'
  assert old in m.load(checked_reference(d['previous_decision_reference']))['decisions']
  for ref in d['followup_evidence']:checked_reference(ref)
  out[d['inventory']]=d
 assert len(out)==130
 return out

def records():
 cs={r['source_id']:r for r in m.load(prior.CANDIDATES)['rows']};comps={r['source_id']:r for r in m.load(RUN/'supplemental-comparisons-002.json.gz')['records']}
 parsed={r['facts']['source_id']:r for r in w.review()['rows']};new=[];holds=[]
 for decision in decisions().values():
  if not decision['state'].startswith('approved_'):continue
  sid=decision['source_id'];r=cs[sid];native=parsed[sid];facts=dict(native['facts']);facts.update(w.creation(facts['date_display']))
  facts.update(work_type='painting' if (facts['medium'] or '').casefold().startswith('oil on ') else ('drawing' if (facts['medium'] or '').casefold().startswith('pastel on ') else 'unknown'),titles=[facts['title']],object_form=None,date_basis='Literal creation Date field, not acquisition/sitter/artist life. Century/decade search bounds retain the whole named period; no narrower early/mid/late or half-century boundaries invented.')
  assert r['state']=='candidate' and facts==r['facts']==decision['facts'] and native['index']==r['index']==decision['index'] and native['source_reference']==r['source_reference']==decision['source_reference']
  assert decision['comparison']==comps[sid] and decision['confidence']==.95 and decision['basis'] and decision['limitation']
  assert facts['date_issue'] is None and facts['last']<=1970 and (facts['first'] is not None or facts['date_precision']=='before')
  if facts['first'] is not None:assert 100<=facts['first']<=facts['last']
  capture=m.load(checked_reference(r['source_reference']));assert capture['at'] and capture['provider']=='web.run'
  record=dict(facts=facts,decision=decision,retrieved_at=capture['at'],source_format='Official-page web-tool text extraction, not original HTTP bytes')
  if decision['state']=='approved_existing_holding':
   aid=HOLDINGS[facts['inventory']];record.update(artwork_id=aid,holding_id=m.uid(KEY+'/holding/'+aid));holds.append(record)
  else:
   assert not decision['comparison']['source_hits'] and not [x for x in decision['comparison']['inventory_hits'] if x['relevant']]
   record.update(artwork_id=m.uid(KEY+'/'+sid),slug='museum-expansion-'+KEY+'-'+sid);new.append(record)
 override=m.load(RUN/'target-creator-overrides-001.json.gz')['overrides'];assert len(override)==1
 for spec in override:
  r=next(r for r in new if r['facts']['inventory']==spec['inventory']);assert spec['field']=='unlinked_creator_label' and r['facts']['creator_label']==spec['source_heading'] and r['facts']['detail_creator_label']==spec['selected_literal_detail'];checked_reference(spec['review_reference']);r['creator_override']=spec
 assert len(new)==len({r['artwork_id'] for r in new})==COUNT and len(holds)==HCOUNT
 assert len({r['facts']['inventory'] for r in new+holds})==COUNT+HCOUNT
 return new,holds

def expected_art(r):
 art=prior.expected_art(r)
 if 'creator_override' in r:art['unlinked_creator_label']=r['creator_override']['selected_literal_detail']
 return art

def identity_preflight(db):
 for check in m.load(RUN/'target-preflight-identities-001.json.gz')['checks']:
  checked_reference(check['reference']);assert i.queries(db,check['params'])==check['state'],'Reviewed identity scope changed'
 x=m.load(RUN/'target-extra-preflight-001.json.gz');assert prior.snapshot(db,x['ids'])==x['snapshot']
 rows=db.execute('SELECT '+i.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) OR a.normalized_title LIKE ANY(%s) ORDER BY a.id LIMIT 2001',(x['query_ids'],x['title_patterns'])).fetchall();assert rows==x['artworks']
 assert not db.execute('SELECT id FROM artworks WHERE normalized_title=ANY(%s) LIMIT 1',(x['absent_index_title_keys'],)).fetchone()

def preflight(db,p):
 assert prior.snapshot(db,p['scoped_ids'])==p['before'],'Existing Dulwich preimage changed'
 assert prior.counts(db)==dict(linked=128,eligible=127)
 pp,pd=prior.validate_plan();assert pd==p['prior_plan_sha256'];prior.verify(db,pp,pd);identity_preflight(db)
 assert prior.snapshot(db,list(HOLDINGS.values()))==m.load(RUN/'existing-identity-followup-001.json.gz')['snapshot']
 ids=[r['artwork_id'] for r in p['records']];urls=[r['facts']['source_url'] for r in p['records']+p['holdings']]
 assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone()
 assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone()
 assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) LIMIT 1",(urls,)).fetchone()
 old={r['id']:r for r in p['before']['artworks']}
 assert all(old[aid]['current_institution_id'] is None for aid in HOLDINGS.values())
 piero=old[HOLDINGS['DPG258']];assert (piero['creation_year_start'],piero['creation_year_end'],piero['date_precision'])==(1500,1500,'exact')
 brodie=old[HOLDINGS['DPG632']];assert (brodie['accession_number'],brodie['creation_year_start'],brodie['creation_year_end'])==('DPG632',1891,1900)
 assert len([h for h in p['before']['assertions'] if h['artwork_id'] in HOLDINGS.values()])==1
 for h in p['before']['assertions']:
  if h['artwork_id'] in HOLDINGS.values():assert h['artwork_id']==HOLDINGS['DPG632'] and h['review_state']=='review' and h['claim_type']=='holding' and h['institution_id']==IID and h['superseded_by'] is None

def prepare():
 assert not PLAN.exists();rs,holds=records();pp,pd=prior.validate_plan();ids=sorted(set(pp['scoped_ids'])|{r['artwork_id'] for r in pp['records']}|set(HOLDINGS.values()));assert len(ids)==139
 with m.connect() as db:
  p=dict(at=m.now(),records=rs,holdings=holds,scoped_ids=ids,before=prior.snapshot(db,ids),prior_plan_sha256=pd,policy='70 new individually reviewed records and two existing holding links, local only. Existing dates, metadata, images, creator links and publication unchanged. One pending Brodie holding superseded. Native Piero circa1500 retained as evidence without changing existing exact1500. New records keep source qualifiers and remain review; no display assertions.')
  preflight(db,p);backup=m.BACKUP/(KEY+'-before.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),scoped_ids=ids,before=p['before']));p.update(backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest())
 paths=[Path(__file__).resolve(),Path(prior.__file__).resolve(),prior.PLAN,RUN/(prior.KEY+'-applied.json'),m.ROOT/'AGENTS.md',RUN/'supplemental-identity-002.json.gz',RUN/'supplemental-comparisons-002.json.gz',RUN/'existing-identity-followup-001.json.gz',RUN/'existing-source-web-001.json.gz',RUN/'piero-source-web-002.json.gz',RUN/'piero-image-link-web-001.json.gz',Path(__file__).with_name('museum-expansion-dulwich-target-review-20261007.py').resolve(),Path(__file__).with_name('test_museum_expansion_dulwich_target_20261007.py').resolve()]
 paths += list(RUN.glob('target-*.json.gz'))+list((RUN/'identity-images-001').glob('*'))
 paths += [checked_reference(r['decision']['source_reference']) for r in rs+holds]+[checked_reference(r['decision']['index']['index_capture_reference']) for r in rs+holds]
 paths += [checked_reference(r) for r in pp['evidence']]
 p['evidence']=[reference(p) for p in sorted(set(paths))];m.save(PLAN,p);print(json.dumps(dict(new=COUNT,holdings=HCOUNT,sha256=hashlib.sha256(PLAN.read_bytes()).hexdigest())),flush=True)

def validate_plan():
 p=m.load(PLAN)
 for ref in p['evidence']:checked_reference(ref)
 assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256']
 assert prior.validate_plan()[1]==p['prior_plan_sha256'];rs,hs=records();assert p['records']==rs and p['holdings']==hs
 return p,hashlib.sha256(PLAN.read_bytes()).hexdigest()

def citation_note(r,digest):return json.dumps(dict(plan_sha256=digest,source_record=r,policy='Official source web-tool text, not original HTTP bytes. Source qualifiers, attributions and uncertainties retained. Existing catalogue metadata unchanged; new records remain review. No image or display assertion.'),ensure_ascii=False)
def holding_note(r,digest):return 'Official Dulwich collection object and complete index. Editorial confidence0.95, not calibrated. '+r['decision']['basis']+' '+r['decision']['limitation']+' Plan SHA-256 '+digest

def assert_delta(before,after,holdings,digest):
 targets={r['artwork_id'] for r in holdings};oldby={r['id']:r for r in before['artworks']};newby={r['id']:r for r in after['artworks']};assert set(oldby)==set(newby)
 for aid,old in oldby.items():
  ignored={'current_institution_id','updated_at'} if aid in targets else set();assert {k:v for k,v in old.items() if k not in ignored}=={k:v for k,v in newby[aid].items() if k not in ignored},aid
  if aid in targets:assert old['current_institution_id'] is None and newby[aid]['current_institution_id']==IID
 for key in ['artists','media','identifiers','museum']:assert before[key]==after[key],key
 assert [r for r in after['citations'] if r['source_id']!=SID]==before['citations']
 newc=[r for r in after['citations'] if r['source_id']==SID];newh=[r for r in after['assertions'] if r['source_id']==SID];assert len(newc)==len(newh)==HCOUNT
 expected=[]
 for old in before['assertions']:
  if old['artwork_id'] in targets:
   assert old['artwork_id']==HOLDINGS['DPG632'] and old['review_state']=='review' and old['claim_type']=='holding' and old['institution_id']==IID and old['superseded_by'] is None
   r=next(r for r in holdings if r['artwork_id']==old['artwork_id']);expected.append(dict(old,superseded_by=r['holding_id']))
  else:expected.append(old)
 assert [r for r in after['assertions'] if r['source_id']!=SID]==expected
 for r in holdings:
  c=next(x for x in newc if x['entity_id']==r['artwork_id']);h=next(x for x in newh if x['artwork_id']==r['artwork_id']);v=r['facts']
  assert c['source_record_id']==v['source_id'] and c['source_url']==v['source_url'] and c['evidence_note']==citation_note(r,digest) and c['field_name']=='museum_expansion_holding_reconciliation'
  assert h['id']==r['holding_id'] and h['claim_type']=='holding' and h['institution_id']==IID and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==v['source_url'] and h['evidence_note']==holding_note(r,digest)
  assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])

def verify(db,p,digest):
 assert_delta(p['before'],prior.snapshot(db,p['scoped_ids']),p['holdings'],digest)
 rs=p['records'];ids=[r['artwork_id'] for r in rs];snap=prior.snapshot(db,ids)
 assert len(snap['artworks'])==len(snap['identifiers'])==len(snap['citations'])==len(snap['assertions'])==COUNT and not snap['artists'] and not snap['media']
 for r in rs:
  aid=r['artwork_id'];v=r['facts'];art=next(x for x in snap['artworks'] if x['id']==aid);assert all(art[k]==val for k,val in expected_art(r).items()),v['inventory']
  for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None
  ident=next(x for x in snap['identifiers'] if x['entity_id']==aid);assert (ident['scheme'],ident['external_id'],ident['canonical_url'],ident['source_id'])==(prior.SCHEME,v['source_id'],v['source_url'],SID)
  c=next(x for x in snap['citations'] if x['entity_id']==aid);assert c['source_id']==SID and c['field_name']=='museum_expansion_native_metadata' and c['source_record_id']==v['source_id'] and c['source_url']==v['source_url'] and c['evidence_note']==citation_note(r,digest)
  h=next(x for x in snap['assertions'] if x['artwork_id']==aid);assert h['source_id']==SID and h['claim_type']=='holding' and h['institution_id']==IID and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==v['source_url'] and h['evidence_note']==holding_note(r,digest)
  assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
 allids=ids+list(HOLDINGS.values());assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(allids,)).fetchone()['n']==COUNT+HCOUNT
 counts=prior.counts(db);assert counts==dict(linked=200,eligible=199)
 return dict(verified_new_records=COUNT,existing_artworks_linked=HCOUNT,previous_native_additions_preserved=125,scoped_artwork_metadata_preserved=len(p['before']['artworks']),old_citations_preserved=len(p['before']['citations']),artist_links_preserved=len(p['before']['artists']),media_links_preserved=len(p['before']['media']),identifiers_preserved=len(p['before']['identifiers']),prior_pending_assertions_superseded=1,new_citations=COUNT+HCOUNT,new_identifiers=COUNT,new_accepted_holdings=COUNT+HCOUNT,new_images=0,new_publications=0,new_display_claims=0,current_counts=counts)

def apply(expected_sha):
 p,digest=validate_plan();assert digest==expected_sha
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay:70 additions and2 holdings;zero writes',flush=True);return
  preflight(db,p);db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(list(HOLDINGS.values()),));m.save(m.BACKUP/(KEY+'-reviewed-plan.json.gz'),p)
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SLUG,'Dulwich selected additions and reconciled holdings,7 October2026','collection_page',prior.d.BASE))
  for r in p['records']:
   v=r['facts'];aid=r['artwork_id'];label=expected_art(r)['unlinked_creator_label']
   db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s)""",(aid,r['slug'],v['title'],m.norm(v['title']),v['date_display'],v['first'],v['last'],v['date_precision'],v['work_type'],v['medium'],v['dimensions_text'],v['inventory'],label,v['object_form'],m.ACTOR,m.ACTOR))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,prior.SCHEME,v['source_id'],v['source_url'],SID,r['retrieved_at']))
  for r in p['records']+p['holdings']:
   v=r['facts'];aid=r['artwork_id'];is_hold=r in p['holdings'];field='museum_expansion_holding_reconciliation' if is_hold else 'museum_expansion_native_metadata'
   db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,%s,%s,%s,%s,%s,%s)",(aid,field,SID,v['source_id'],v['source_url'],citation_note(r,digest),r['retrieved_at'],m.ACTOR))
   hid=r.get('holding_id',m.uid(KEY+'/holding/'+aid))
   db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(hid,aid,IID,SID,v['source_url'],holding_note(r,digest),r['retrieved_at']))
   if is_hold:
    for old in [x for x in p['before']['assertions'] if x['artwork_id']==aid]:db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s',(hid,old['id']))
  result=verify(db,p,digest)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=COUNT,existing_links=HCOUNT,local_only=True,verification=result));print(json.dumps(result),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');args=p.parse_args()
 if args.command=='prepare':prepare()
 elif args.command=='apply':assert args.plan_sha;apply(args.plan_sha)
 else:
  plan,digest=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
