#!/usr/bin/env python3
"""Atomic loopback-only application of two reviewed museum records."""
import argparse,hashlib,importlib.util,json,types
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-next-samples-review-20261007.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r);f=r.f;m=r.m;RUN=r.RUN;reference=r.ref;checked_reference=r.checked
y=f.module('y','museum-expansion-yale-apply-20261007.py')
h=f.module('history','museum-expansion-policy-history-20261007.py')
KEY='next-samples-reviewed-additions-001';SID=m.uid('source/'+KEY);SOURCE_SLUG='museum-expansion-20261006-'+KEY;PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'editorial-reviewed-001.json.gz';MODS={'ago':f.a,'detroit':f.d}
def records():
 review=m.load(REVIEW);checked_reference(review['reviewer_reference']);decisions=r.build();assert decisions==review['decisions'];out=[]
 for decision in decisions:
  v=decision['facts'];assert decision['confidence']>=.8 and decision['state']=='approved_review_only_addition';assert v['date_issue'] is None and 100<=v['first']<=v['last']<=1970 and v['inventory'] and v['credit_line'] and v['object_form'] is None
  key=decision['provider']+'/'+v['source_id'];out.append(dict(artwork_id=m.uid(KEY+'/'+key),slug='museum-expansion-'+KEY+'-'+hashlib.sha256(key.encode()).hexdigest()[:16],institution_id=decision['institution_id'],provider=decision['provider'],scheme=decision['provider']+'-object',facts=v,decision=decision,retrieved_at=decision['retrieved_at']))
 assert len(out)==len({v['artwork_id'] for v in out})==2;return out
def snapshot(db,ids,iid):y.IID=iid;return y.snapshot(db,ids)
def counts(db,iid):y.IID=iid;return y.counts(db)
def expected_art(v):y.IID=v['institution_id'];return y.expected_art(v)
def fresh_identity(db):
 for key,mod in MODS.items():
  x=m.load(mod.RUN/'complete-sample-identity-001.json.gz');f.i.RUN=mod.RUN;f.i.IID=mod.IID;assert f.i.queries(db,x['params'])==x['state'],'Identity scope changed'
  hit=db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND external_id=%s AND (scheme ILIKE %s OR scheme ILIKE %s) LIMIT 1",(x['row']['source_id'],'%'+key+'%','%dia%' if key=='detroit' else '%ontario%')).fetchone();assert not hit
  x=m.load(mod.RUN/'complete-sample-citations-001.json.gz');actual=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(x['selected_ids'],))];assert actual==x['citations'],'Version citations changed'
def preflight(db,p):
 for key,initial in p['before'].items():
  iid=MODS[key].IID;assert snapshot(db,initial['scoped_ids'],iid)==initial['snapshot'];assert counts(db,iid)==initial['counts']==dict(linked=0,eligible=0)
 fresh_identity(db);assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SOURCE_SLUG)).fetchone();assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[])',([v['artwork_id'] for v in p['records']],)).fetchone()
def prepare():
 assert not PLAN.exists();rs=records();before={key:m.load(mod.RUN/'initial-scope-001.json.gz') for key,mod in MODS.items()}
 with m.connect() as db:preflight(db,dict(records=rs,before=before))
 backup=m.BACKUP/(KEY+'-before.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),before=before,local_only=True))
 paths=[p for key in ['ago','detroit','slam','next-samples'] for p in (m.RUN/'native'/key).rglob('*') if p.is_file() and p.name!='README.md'];paths += [m.ROOT/'AGENTS.md'];paths+=list((m.ROOT/'ops').glob('*next_samples*20261007.py'))
 for row in rs:
  for ref in row['decision']['supplement_references']:paths.append(checked_reference(ref))
 visited=set()
 def deps(module):
  if id(module) in visited:return
  visited.add(id(module));file=getattr(module,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  paths.append(Path(file).resolve())
  for value in vars(module).values():
   if isinstance(value,types.ModuleType):deps(value)
 for module in [r,y,f,m,h]:deps(module)
 paths.append(Path(__file__).resolve())
 p=dict(at=m.now(),records=rs,before=before,backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),evidence=[reference(p) for p in sorted(set(paths))],policy='Two complete and individually reviewed source records, one each for AGO and DIA. All other discovered leads remain unapproved. Local review only; preserve source uncertainties and existing museum scopes. No images, artist authorities or links, publication or display claims.')
 m.save(PLAN,p);print('Prepared',len(rs),hashlib.sha256(PLAN.read_bytes()).hexdigest(),flush=True)
def validate_plan():
 p=m.load(PLAN)
 for ref in p['evidence']:checked_reference(ref)
 assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256'];assert p['records']==records();return p,hashlib.sha256(PLAN.read_bytes()).hexdigest()
def citation_note(v,digest):return json.dumps(dict(plan_sha256=digest,source_record=v,policy='Official source facts and complete capture chain preserved. AGO uses web extracts; DIA uses original HTML and linked JSON. Rights and attribution/accession discrepancies remain evidence. No current-display or image claim.'),ensure_ascii=False)
def holding_note(v,digest):return v['decision']['basis']+' '+v['decision']['limitation']+' Plan SHA-256 '+digest
def verify(db,p,digest):
 output={}
 for v in p['records']:
  iid=v['institution_id'];key=v['provider'];fv=v['facts'];aid=v['artwork_id'];initial=p['before'][key];snap=snapshot(db,[aid],iid)
  assert snapshot(db,initial['scoped_ids'],iid)==initial['snapshot'];assert counts(db,iid)==dict(linked=1,eligible=1)
  assert all(len(snap[k])==1 for k in ['artworks','identifiers','citations','assertions']);assert not snap['artists'] and not snap['media'];art=snap['artworks'][0];assert all(art[k]==value for k,value in expected_art(v).items())
  for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None
  ident=snap['identifiers'][0];assert (ident['scheme'],ident['external_id'],ident['canonical_url'],ident['source_id'])==(v['scheme'],fv['source_id'],fv['source_url'],SID)
  c=snap['citations'][0];assert (c['source_id'],c['field_name'],c['source_record_id'],c['source_url'],c['evidence_note'])==(SID,'museum_expansion_reviewed_metadata',fv['source_id'],fv['source_url'],citation_note(v,digest))
  a=snap['assertions'][0];assert a['claim_type']=='holding' and a['institution_id']==iid and a['context']=='collection' and a['review_state']=='accepted' and a['superseded_by'] is None and a['source_id']==SID and a['source_url']==fv['source_url'] and a['evidence_note']==holding_note(v,digest)
  assert not any(a.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
  assert db.execute("SELECT artline_has_selection_evidence(%s) ok",(aid,)).fetchone()['ok']
  output[key]=dict(added=1,current_counts=counts(db,iid),old_artworks_unchanged=len(initial['snapshot']['artworks']),old_citations_unchanged=len(initial['snapshot']['citations']))
 return dict(verified_new_records=2,museums=output,new_media_links=0,new_artist_links=0,new_published=0,new_display_claims=0)
def apply(expected_sha):
 p,digest=validate_plan();assert digest==expected_sha;rs=p['records'];ids=[v['artwork_id'] for v in rs]
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  old=db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
  if old:assert len(old)==2;verify(db,p,digest);print('Unchanged replay: 2 records; zero inserts',flush=True);return
  preflight(db,p);db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',([v['institution_id'] for v in rs],));backup=m.BACKUP/(KEY+'-reviewed-plan-'+digest+'.json.gz')
  if backup.exists():assert m.load(backup)==p
  else:m.save(backup,p)
  db.execute('INSERT INTO sources(id,slug,name,source_type) VALUES(%s,%s,%s,%s)',(SID,SOURCE_SLUG,'AGO and Detroit official collection records reviewed 7 October 2026','collection_page'))
  for v in rs:
   fv=v['facts'];aid=v['artwork_id'];at=v['retrieved_at'];db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s)''',(aid,v['slug'],fv['title'],m.norm(fv['title']),fv['date_display'],fv['first'],fv['last'],fv['date_precision'],fv['work_type'],fv['medium'],fv['dimensions_text'],fv['inventory'],fv['creator_label'],fv['object_form'],m.ACTOR,m.ACTOR))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,v['scheme'],fv['source_id'],fv['source_url'],SID,at))
   db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_reviewed_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,fv['source_id'],fv['source_url'],citation_note(v,digest),at,m.ACTOR))
   db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,v['institution_id'],SID,fv['source_url'],holding_note(v,digest),at))
  result=verify(db,p,digest)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=2,local_only=True,verification=result));print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');v=p.parse_args()
 if v.command=='prepare':prepare()
 elif v.command=='apply':assert v.plan_sha;apply(v.plan_sha)
 else:
  plan,digest=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
