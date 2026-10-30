"""Bounded exact-key writer preflight and read-only verification for profile batches.

The original runner and receipts remain immutable. This version avoids an
unindexed audit request-id scan while preserving all deterministic audit keys,
exact preimages, atomic writes and all three shared locks.
"""
import argparse,collections,importlib.util,sys
from pathlib import Path
from psycopg import sql
from psycopg.types.json import Jsonb
sys.path.insert(0,str(Path(__file__).parent))
import exhibitions_common as c
spec=importlib.util.spec_from_file_location('museum_profiles_original',Path(__file__).with_name('museum-all-profiles-20261030.py'))
v1=importlib.util.module_from_spec(spec);spec.loader.exec_module(v1)

def audit_keys(batch,plan):
 m=v1.module(batch)
 count=len(plan['new_places'])+1+2*len(plan['changes'])
 return [m.uid('audit/'+str(i))for i in range(count)]

def check_keys(db,batch,plan):
 keys=audit_keys(batch,plan)
 rows=list(db.execute('SELECT id,request_id FROM audit_log WHERE id=ANY(%s::uuid[])',(keys,)))
 assert not rows,'Previously dispatched deterministic audit keys exist; reconcile instead of replaying'
 return len(keys)

def reconcile_zero(batch):
 e,d,b=v1.paths(batch);plan=c.load(b/'plan.json.gz')
 assert not(e/'applied.json').exists()and not(b/'transaction-staged.json.gz').exists()
 with c.connect()as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  keys=check_keys(db,batch,plan)
  ids=[x['before']['id']for x in plan['changes']]
  actual={r['v']['id']:r['v']for r in db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE id=ANY(%s::uuid[])',(ids,))}
  assert all(actual[x['before']['id']]==x['before']for x in plan['changes'])
  assert not db.execute('SELECT id FROM sources WHERE id=%s',(plan['source']['id'],)).fetchone()
  assert not db.execute('SELECT id FROM citations WHERE source_id=%s',(plan['source']['id'],)).fetchone()
  assert not list(db.execute('SELECT id FROM places WHERE id=ANY(%s::uuid[])',([p['id']for p in plan['new_places']],)))
  places=[dict(r)for r in db.execute('SELECT id,name,trim(country_code)country FROM places')]
  for p in plan['new_places']:
   assert not any(x['country']==p['country_code']and c.norm(x['name'])==c.norm(p['name'])for x in places),'New city appeared since planning; reconcile plan'
 c.save(e/'prewrite-timeout-zero-reconciliation.json',dict(at=c.now(),read_only=True,all_exact_institution_preimages_unchanged=len(ids),deterministic_audit_keys_absent=keys,new_owned_city_source_citation_rows_absent=True,no_new_same_name_country_city_since_plan=True,staged_and_applied_files_absent=True,original_failure='Statement timeout in SELECT id FROM audit_log WHERE request_id=... LIMIT 1 before first mutation. Transaction rolled back.',original_plan_retained=v1.pin(b/'plan.json.gz'),original_runner_retained=v1.pin(Path(__file__).with_name('museum-all-profiles-20261030.py')),no_committed_writer_replay=True))
 print('POSITIVELY RECONCILED ZERO WRITES',batch,len(ids),'preimages and',keys,'absent atomic audit keys',flush=True)

def apply(batch):
 m=v1.module(batch);e,d,b=v1.paths(batch);v=c.load(b/'plan.json.gz')
 assert not(e/'applied.json').exists()and not(b/'transaction-staged.json.gz').exists(),'Reconcile dispatched writer; never replay'
 assert v1.pin(b/'plan.json.gz')==c.load(e/'plan-pin.json')and v1.pin(m.CONTENT)==v['content']and v1.pin(v1.ROOT/'AGENTS.md')==v['instructions']
 changes=[];digest=v1.pin(b/'plan.json.gz')['sha256']
 with c.connect(write=True)as db:
  assert db.execute("SELECT current_database()db,current_setting('transaction_read_only')ro").fetchone()==dict(db='artline',ro='off')
  db.execute("SET LOCAL application_name='artline-all-museum-profile-review-v2'")
  db.execute("SET LOCAL statement_timeout='60s'");db.execute("SET LOCAL lock_timeout='45s'")
  for q in ["SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))",'SELECT pg_advisory_xact_lock(2026101201)','SELECT pg_advisory_xact_lock(202610053)']:db.execute(q)
  proof=m.locks_held(db);assert v1.pin(v1.ROOT/'AGENTS.md')==v['instructions'];checked_keys=check_keys(db,batch,v)
  for change in v['changes']:assert db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE id=%s FOR UPDATE',(change['before']['id'],)).fetchone()['v']==change['before']
  db.execute("SELECT set_config('artline.actor_user_id',%s,true),set_config('artline.request_id',%s,true)",(m.ACTOR,m.OP))
  for row in v['new_places']:changes.append(dict(table='places',before=None,after=m.insert(db,'places',row)))
  changes.append(dict(table='sources',before=None,after=m.insert(db,'sources',v['source'])))
  for change in v['changes']:
   before=change['before'];after=db.execute('UPDATE institutions SET place_id=%s,description=%s,updated_at=now() WHERE id=%s RETURNING to_jsonb(institutions)v',(change['place_id'],change['description'],before['id'])).fetchone()['v'];changes.append(dict(table='institutions',before=before,after=after))
   row=dict(id=m.uid('citation/'+after['id']),entity_type='institution',entity_id=after['id'],field_name='description_and_location',source_id=v['source']['id'],source_record_id=after['slug'],source_url=change['sources'][0],evidence_note=__import__('json').dumps(dict(sources=change['sources'],city=change['reviewed_city'],country=change['reviewed_country'],original_English_summary=True,research_note=change['research_note'],location_correction=change['location_correction'],plan_sha256=digest)),retrieved_at=v['at'],created_by=m.ACTOR)
   changes.append(dict(table='citations',before=None,after=m.insert(db,'citations',row)))
  assert len(changes)==checked_keys
  for index,change in enumerate(changes):
   row=dict(id=m.uid('audit/'+str(index)),actor_user_id=m.ACTOR,action='review_museum_description_and_location',entity_type=change['table'],entity_id=change['after']['id'],request_id=m.OP,before_json=Jsonb(change['before']),after_json=Jsonb(dict(record=change['after'],transaction=proof,plan_sha256=digest)));m.insert(db,'audit_log',row);change['audit_id']=row['id']
  assert m.locks_held(db)==proof and v1.pin(v1.ROOT/'AGENTS.md')==v['instructions']
  c.save(b/'transaction-staged.json.gz',dict(at=c.now(),transaction=proof,changes=changes,plan_sha256=digest))
 c.save(e/'applied.json',dict(at=c.now(),transaction=proof,explicit_audits=len(changes),profiles=len(v['changes']),slugs=[x['before']['slug']for x in v['changes']],location_links=sum(x['before']['place_id']!=x['place_id']for x in v['changes']),new_cities=len(v['new_places']),three_shared_locks_retained=True,bounded_exact_audit_key_preflight=checked_keys))
 print('COMMITTED',batch,len(changes),'atomic changes',proof,flush=True)

def verify(batch):
 e,d,b=v1.paths(batch);assert not(e/'database-verification.json').exists()and not(e/'preservation.json').exists()
 staged=c.load(b/'transaction-staged.json.gz');plan=c.load(b/'plan.json.gz');m=v1.module(batch)
 expected=collections.defaultdict(dict)
 for x in staged['changes']:expected[x['table']][x['after']['id']]=x
 keys=audit_keys(batch,plan);assert keys==[x['audit_id']for x in staged['changes']]and staged['transaction']['held']==3
 with c.connect()as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  for table,rows in expected.items():
   actual={r['v']['id']:r['v']for r in db.execute(sql.SQL('SELECT to_jsonb(t)v FROM {} t WHERE id=ANY(%s::uuid[])').format(sql.Identifier(table)),(list(rows),))}
   assert actual=={k:x['after']for k,x in rows.items()}
  audits={str(r['id']):dict(r)for r in db.execute('SELECT id,request_id,before_json,after_json FROM audit_log WHERE id=ANY(%s::uuid[])',(keys,))}
  assert len(audits)==len(keys)
  for x in staged['changes']:
   a=audits[x['audit_id']];assert a['request_id']==m.OP and a['before_json']==x['before']and a['after_json']==dict(record=x['after'],transaction=staged['transaction'],plan_sha256=staged['plan_sha256'])
   if x['before']:assert {k:v for k,v in x['before'].items()if k not in ['place_id','description','updated_at']}=={k:v for k,v in x['after'].items()if k not in ['place_id','description','updated_at']}
  for table,key in [('institution_venues','old_venues'),('citations','old_citations')]:
   rows=plan[key];current=[r['v']for r in db.execute(sql.SQL('SELECT to_jsonb(t)v FROM {} t WHERE id=ANY(%s::uuid[]) ORDER BY id').format(sql.Identifier(table)),([r['id']for r in rows],))];assert current==rows
  armenia=db.execute("SELECT i.slug,p.name city,trim(p.country_code)country FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.slug='national-gallery-armenia'").fetchone();assert armenia==dict(slug='national-gallery-armenia',city='Yerevan',country='AM')
 c.save(e/'database-verification.json',dict(at=c.now(),read_only=True,checked=[dict(table=x['table'],id=x['after']['id'],audit_id=x['audit_id'])for x in staged['changes']],Armenia=armenia,exact_rows_and_audits=True,institution_identity_status_and_other_fields_preserved=True,bounded_exact_audit_keys=len(keys)))
 c.save(e/'preservation.json',dict(passed=True,existing_venues=len(plan['old_venues']),existing_citations=len(plan['old_citations']),identities_statuses_and_non_profile_fields_unchanged=True))
 print('VERIFIED',batch,len(keys),'exact atomic rows/audits and preserved old venues/citations',flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['reconcile_zero','apply','verify','plan','projection','public']);parser.add_argument('batch');args=parser.parse_args()
 (globals()[args.action]if args.action in ['reconcile_zero','apply','verify']else getattr(v1,args.action))(args.batch)
