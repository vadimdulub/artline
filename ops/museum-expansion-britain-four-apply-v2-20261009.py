"""Atomic local reviewed Brighton and Ulster links, including explicit branch refinements."""
import argparse,csv,gzip,hashlib,importlib.util,json,types
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
r=module('r','museum-expansion-britain-four-review-v2-20261009.py');m=r.m;s=r.s;RUN=r.RUN;IIDS=s.IIDS;reference=r.ref;checked=r.checked;prior=s.prior;i=r.i
KEY='britain-four-existing-holdings-001';SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY;PLAN=RUN/(KEY+'-plan-002.json.gz');REVIEW=RUN/'editorial-reviewed-002.json.gz';CHECKPOINT=prior.RUN/'delivery-checkpoint-001.json';HCOUNT=218
def network_current(db):
 return dict(institution=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(s.NETWORK,)).fetchone()['row'],counts=s.BASE.counts(db,s.NETWORK))
def ulster_parsed(raw):
 from bs4 import BeautifulSoup
 soup=BeautifulSoup(raw,'html.parser');dl=soup.select_one('dl.full_record_data');assert dl;fields={}
 for dt in dl.select('dt'):
  dd=dt.find_next_sibling('dd');assert dd;key=dt.get_text(' ',strip=True);assert key not in fields;fields[key]=dd.get_text('\n',strip=True).split('\n')
 return dict(fields=fields,headings=[v.get_text(' ',strip=True) for v in soup.select('h1,h2,h3')],text=soup.get_text(' ',strip=True))
snapshot=s.snapshot;counts=s.counts;prior_state=prior.prior_state

def records():
 x=m.load(REVIEW);checked(x['reviewer_reference'])
 for dep in x['dependencies']:checked(dep)
 for row in r.native_rows().values():
  if row['state']=='captured_exact_inventory':
   cap=row.get('object_capture') or row['search_capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256']
   parsed=ulster_parsed(raw) if row.get('object_capture') else next(v for v in json.loads(raw)['data'] if v['accessionId']==row['inventory']);assert parsed==row['parsed']
 bodies={}
 for row in m.load(RUN/'source-context-001.json.gz')['rows']:
  path=checked(row['body_reference']);key=str(path)
  if key not in bodies:
   raw=gzip.decompress(path.read_bytes());bodies[key]=(hashlib.sha256(raw).hexdigest(),json.loads(raw))
  sha,data=bodies[key];assert sha==row['raw_sha256'] and data['entities'][row['source_id']]==row['entity']
 assert x['decisions']==r.build();out=[]
 for d in x['decisions']:
  if d['state']!='approved_existing_holding':continue
  assert d['confidence']>=.8;aid=d['existing_artwork_id'];out.append(dict(institution_id=d['institution_id'],artwork_id=aid,holding_id=m.uid(KEY+'/holding/'+aid),facts=d['facts'],decision=d,retrieved_at=d['retrieved_at']))
 assert len(out)==len({v['artwork_id'] for v in out})==HCOUNT;return out

def prior_ids():
 ids=[]
 for name in ['added-artworks','reconciled-artworks']:
  with (m.RUN/(name+'-after-wave-80.csv')).open(newline='') as fp:ids.extend(v['artwork_id'] for v in csv.DictReader(fp))
 assert len(ids)==len(set(ids))==11709;return sorted(ids)

def verify_baseline():
 assert reference(CHECKPOINT)['sha256']=='0b94a0b9f931b610f55905140ab5fa85e7909a90f9523ba75c7158e543463fa4';cp=m.load(CHECKPOINT)
 for dep in cp['artifacts']:checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 return cp

def fresh_identity(db):
 initial=m.load(RUN/'initial-scope-001.json.gz');painterids=sorted(v['id'] for v in initial['painters']);authorities=[v['row'] for v in db.execute("SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(painterids,))];assert authorities==initial['creator_authorities'],'Creator authorities changed'
 x=m.load(RUN/'identity-001.json.gz');state=i.queries(db,x['params']);actual=i.comparisons(i.rows(),state);strip=lambda v:{k:x for k,x in v.items() if k!='creator_pool_ids'};assert [strip(v) for v in actual]==[strip(v) for v in x['comparisons']],'Relevant identity changed'
 ids=x['state']['artwork_ids'];cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(ids,))];assert cs==m.load(RUN/'identity-citations-001.json.gz')['citations']
 if db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='off':
  path=m.BACKUP/(KEY+'-transaction-identity-002.json.gz');assert not path.exists();m.save(path,dict(at=m.now(),params=x['params'],state=state,comparisons=actual,comparisons_equal=True))

def preflight(db,p):
 assert network_current(db)==m.load(RUN/'ulster-network-context-001.json.gz')['network_state']
 assert snapshot(db,p['scoped_ids'])==p['before'];assert counts(db)==p['before_counts']==m.load(RUN/'initial-scope-001.json.gz')['counts'];assert prior_state(db,p['prior_ids'])==p['prior_state'];fresh_identity(db)
 assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone()
 extra_history_ids={v['assertion']['id'] for v in m.load(RUN/'additional-network-review-context-001.json.gz')['rows']}
 for v in p['holdings']:
  art=next(a for a in p['before']['artworks'] if a['id']==v['artwork_id']);assert art['current_institution_id']==v['decision']['previous_institution_id'] and art['status']=='review'
  hs=[h for h in p['before']['assertions'] if h['artwork_id']==v['artwork_id']];expected={v['decision']['pending_assertion_id']}|({v['decision']['previous_network_assertion_id']} if v['decision']['previous_network_assertion_id'] else set());extras=[h for h in hs if h['id'] not in expected];assert expected<={h['id'] for h in hs} and all(h['superseded_by'] is None for h in hs);assert all(h['review_state']==('accepted' if h['id']==v['decision']['previous_network_assertion_id'] else 'review') for h in hs);assert all(h['institution_id']==s.NETWORK and h['id'] in extra_history_ids for h in extras)

def dependencies():
 paths=set();seen=set()
 def visit(mod):
  if id(mod) in seen:return
  seen.add(id(mod));file=getattr(mod,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  paths.add(Path(file).resolve())
  for v in vars(mod).values():
   if isinstance(v,types.ModuleType):visit(v)
 visit(r);paths.add(Path(__file__).resolve());return paths

def prepare():
 assert not PLAN.exists();holds=records();verify_baseline();initial=m.load(RUN/'initial-scope-001.json.gz');ids=sorted(set(initial['scoped_ids'])|{h['id'] for c in m.load(RUN/'identity-001.json.gz')['comparisons'] for h in c['hits']});assert set(initial['scoped_ids'])<=set(ids);pids=prior_ids();assert set(pids).isdisjoint(v['artwork_id'] for v in holds)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert snapshot(db,initial['scoped_ids'])==initial['snapshot'];p=dict(at=m.now(),holdings=holds,scoped_ids=ids,before=snapshot(db,ids),prior_ids=pids,prior_state=prior_state(db,pids),baseline_reference=reference(CHECKPOINT),before_counts=counts(db),policy='Holding reconciliation only. Existing object metadata, status, dates, creator labels, images and source citations preserved. Supersede original pending assertion; keep its evidence unchanged. No ownership or display claim.');preflight(db,p)
 backup=m.BACKUP/(KEY+'-before-002.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),scoped_ids=ids,before=p['before'],prior_ids=pids,prior_state=p['prior_state']));p.update(backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest())
 paths=dependencies()|{CHECKPOINT,m.ROOT/'AGENTS.md',Path(__file__).with_name('test_museum_expansion_britain_four_v2_20261009.py')};paths|={v for v in RUN.rglob('*') if v.is_file() and v.name!='README.md'}
 for name in ['source-context-001.json.gz','comparison-source-context-001.json.gz','ulster-network-context-001.json.gz','additional-network-review-context-001.json.gz']:
  for dep in m.load(RUN/name)['body_references']:paths.add(checked(dep))
 p['evidence']=[reference(v) for v in sorted(paths)];m.save(PLAN,p);print(json.dumps(dict(holdings=HCOUNT,protected_existing=len(ids),protected_prior=len(pids),sha256=reference(PLAN)['sha256'])),flush=True)

def validate_plan():
 p=m.load(PLAN)
 for dep in p['evidence']:checked(dep)
 assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256'];assert p['holdings']==records();return p,reference(PLAN)['sha256']

def citation_note(v,digest):
 d=v['decision'];return json.dumps(dict(plan_sha256=digest,facts=v['facts'],retrieved_at=v['retrieved_at'],reviewed_at=m.load(REVIEW)['at'],source_reference=d['source_reference'],source_raw_sha256=d['source_raw_sha256'],native_evidence_reference=d['native_evidence_reference'],previous_institution_id=d['previous_institution_id'],previous_network_assertion_id=d['previous_network_assertion_id'],network_context_reference=reference(RUN/'ulster-network-context-001.json.gz'),additional_network_review_context_reference=reference(RUN/'additional-network-review-context-001.json.gz'),creator_authority_reference=reference(RUN/'unlinked-creator-authorities-001.json.gz'),editorial_decision={k:d[k] for k in ['state','confidence','basis','limitation','existing_artwork_id','derived_fields']},review_reference=reference(REVIEW),identity_reference=reference(RUN/'identity-001.json.gz'),policy='Exact referenced Wikidata object statements with separately identified Brighton/NMNI native corroboration. Reviewed NMNI-to-Ulster branch refinements are editorial inferences from exact inventory,department,official collection policy and specific branch statements; old network evidence retained in audit history. Art UK references are not newly fetched; correlated secondary claims are not independent confirmation. No metadata, images, painter links, publication or display change.'),ensure_ascii=False)
def holding_note(v,digest):return v['decision']['basis']+' '+v['decision']['limitation']+' Plan SHA-256 '+digest

def assert_delta(before,after,holds,digest):
 targets={v['artwork_id']:v for v in holds};old={a['id']:a for a in before['artworks']};new={a['id']:a for a in after['artworks']};assert set(old)==set(new)
 for aid,art in old.items():
  ignored={'current_institution_id','updated_at'} if aid in targets else set();assert {k:v for k,v in art.items() if k not in ignored}=={k:v for k,v in new[aid].items() if k not in ignored}
  if aid in targets:assert art['current_institution_id']==targets[aid]['decision']['previous_institution_id'] and new[aid]['current_institution_id']==targets[aid]['institution_id']
 for key in ['artists','media','media_assets','identifiers','museums']:assert before[key]==after[key]
 assert [v for v in after['citations'] if v['source_id']!=SID]==before['citations'];newc=[v for v in after['citations'] if v['source_id']==SID];newh=[v for v in after['assertions'] if v['source_id']==SID];assert len(newc)==len(newh)==HCOUNT
 allowed={assertion:v['holding_id'] for v in holds for assertion in [v['decision']['pending_assertion_id'],v['decision']['previous_network_assertion_id']] if assertion};expected=[dict(v,superseded_by=allowed[v['id']]) if v['id'] in allowed else v for v in before['assertions']];assert [v for v in after['assertions'] if v['source_id']!=SID]==expected
 for v in holds:
  c=next(c for c in newc if c['entity_id']==v['artwork_id']);h=next(h for h in newh if h['artwork_id']==v['artwork_id']);f=v['facts'];assert(c['source_id'],c['field_name'],c['source_record_id'],c['source_url'],c['evidence_note'],c['retrieved_at'])==(SID,'museum_expansion_holding_reconciliation',f['source_id'],f['source_url'],citation_note(v,digest),v['retrieved_at'])
  assert h['id']==v['holding_id'] and h['source_id']==SID and h['claim_type']=='holding' and h['institution_id']==v['institution_id'] and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==f['source_url'] and h['evidence_note']==holding_note(v,digest) and h['checked_at']==v['retrieved_at'];assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])

def verify(db,p,digest):
 assert_delta(p['before'],snapshot(db,p['scoped_ids']),p['holdings'],digest);assert prior_state(db,p['prior_ids'])==p['prior_state'];expected={iid:dict(linked=p['before_counts'][iid]['linked']+sum(v['institution_id']==iid for v in p['holdings']),eligible=p['before_counts'][iid]['eligible']+sum(v['institution_id']==iid and v['facts']['date_precision']!='unknown' for v in p['holdings'])) for iid in IIDS};assert counts(db)==expected
 refinements=[v for v in p['holdings'] if v['decision']['previous_network_assertion_id']];old=m.load(RUN/'ulster-network-context-001.json.gz')['network_state'];new=network_current(db);assert old['institution']==new['institution'];assert new['counts']==dict(linked=old['counts']['linked']-len(refinements),eligible=old['counts']['eligible']-sum(v['facts']['date_precision']!='unknown' for v in refinements))
 return dict(verified_new_records=0,existing_artworks_linked=HCOUNT,previously_unlinked=HCOUNT-len(refinements),network_to_branch_refinements=len(refinements),current_counts=expected,network_counts=new['counts'],protected_existing_records=len(p['scoped_ids']),prior_campaign_records_preserved=len(p['prior_ids']),prior_campaign_table_digests=p['prior_state'],prior_pending_assertions_superseded=HCOUNT,prior_network_assertions_superseded=len(refinements),held_pending_records=239-HCOUNT,unknown_date_records_preserved=sum(v['facts']['date_precision']=='unknown' for v in p['holdings']),new_media_links=0,new_artist_links=0,new_published=0,new_display_claims=0)

def apply(expected_sha):
 p,digest=validate_plan();assert digest==expected_sha
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay: zero writes',flush=True);return
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(p['scoped_ids'],));db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(s.PROTECT_IIDS,));preflight(db,p);backup=m.BACKUP/(KEY+'-reviewed-plan-002.json.gz');assert not backup.exists();m.save(backup,p)
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SLUG,'Brighton and Ulster: referenced object evidence, native catalogue corroboration and reviewed branch refinements,9 October2026','collection_page','https://www.wikidata.org'))
  for v in p['holdings']:
   f=v['facts'];aid=v['artwork_id'];hid=v['holding_id'];db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_holding_reconciliation',%s,%s,%s,%s,%s,%s)",(aid,SID,f['source_id'],f['source_url'],citation_note(v,digest),v['retrieved_at'],m.ACTOR));db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'review')",(hid,aid,v['institution_id'],SID,f['source_url'],holding_note(v,digest),v['retrieved_at']));db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=ANY(%s::uuid[])',(hid,[v['decision']['pending_assertion_id']]+([v['decision']['previous_network_assertion_id']] if v['decision']['previous_network_assertion_id'] else [])));db.execute("UPDATE artwork_location_assertions SET review_state='accepted' WHERE id=%s AND review_state='review'",(hid,))
  result=verify(db,p,digest)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=0,existing_links=HCOUNT,local_only=True,verification=result));print(json.dumps(result),flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','apply','verify']);parser.add_argument('--plan-sha');v=parser.parse_args()
 if v.command=='prepare':prepare()
 elif v.command=='apply':assert v.plan_sha;apply(v.plan_sha)
 else:
  p,d=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,p,d)),flush=True)
