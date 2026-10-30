"""Owner-authorized review of the frozen 2,574 remaining institution profiles.

Finite foreground batches only. Never replay a dispatched transaction. All
institution identities, statuses, venues, artworks, holdings and images remain
outside the write scope. Original review operations remain immutable.
"""
import argparse,collections,hashlib,importlib.util,json,shutil,sys,uuid
from pathlib import Path
from psycopg import sql
from psycopg.types.json import Jsonb
sys.path.insert(0,str(Path(__file__).parent))
import exhibitions_common as c
ROOT=c.ROOT;H=Path.home()/'Library/Application Support/Artline';OP='museum-all-profiles-20261030'
E=ROOT/'docs/research'/OP;D=H/'source-metadata'/OP;B=H/'backups'/OP

def pin(p):
 p=Path(p);r=p.read_bytes();return dict(path=str(p),bytes=len(r),sha256=hashlib.sha256(r).hexdigest())
def setup():
 for p in [E,D,B]:p.mkdir(parents=True,exist_ok=True)
 B.chmod(0o700);assert shutil.disk_usage(H).free>30*1024**3

def census():
 setup();assert not(D/'baseline.json.gz').exists()
 prior=[]
 for op in ['museum-page-review-20261030','museum-guide-profiles-20261030']:prior+=c.load(ROOT/'docs/research'/op/'profiles-reviewed.json')
 assert len(prior)==91
 previous=c.load(H/'source-metadata/museum-guide-profiles-20261030/baseline.json.gz')['rows'];done={p['slug']for p in prior};targets=[r['record']for r in previous if r['record']['slug']not in done];assert len(targets)==2574
 ids=[r['id']for r in targets]
 with c.connect()as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  rows=list(db.execute('''SELECT to_jsonb(i)record,p.name city,trim(p.country_code)country,
  co.name country_name FROM institutions i LEFT JOIN places p ON p.id=i.place_id LEFT JOIN countries co ON co.code=p.country_code WHERE i.id=ANY(%s::uuid[]) ORDER BY lower(i.name),i.id''',(ids,)))
  citations=[r['v']for r in db.execute("SELECT to_jsonb(t)v FROM citations t WHERE entity_type='institution' AND entity_id=ANY(%s::uuid[])",(ids,))]
  venues=[r['v']for r in db.execute('SELECT to_jsonb(t)v FROM institution_venues t WHERE institution_id=ANY(%s::uuid[])',(ids,))]
  countries=[dict(r)for r in db.execute('SELECT code,name,region_code FROM countries')]
 assert len(rows)==2574
 c.save(D/'baseline.json.gz',dict(at=c.now(),rows=rows,citations=citations,venues=venues,countries=countries,prior_91=prior))
 c.save(E/'target-manifest.json',dict(at=c.now(),total=2574,targets=[dict(id=r['record']['id'],slug=r['record']['slug'],name=r['record']['name'],kind=r['record']['kind'],initial_city=r['city'],initial_country=r['country'])for r in rows],prior_91_excluded=True,baseline=pin(D/'baseline.json.gz')))
 c.save(E/'authorization.json',dict(user_request='2,574 profiles remain - go ahead, cover all of them',all_2574_authorized=True,production_profile_description_location_citations_and_audits_only=True,previous_deploy_commit_push_authorization_retained=True,no_artworks_images_holdings_status_or_identity_changes=True,no_agents_jobs_or_schedules=True))
 print('FROZEN',len(rows),'remaining institution records')

def paths(batch):return E/'batches'/batch,D/'batches'/batch,B/'batches'/batch

def plan(batch):
 setup();e,d,b=paths(batch)
 for p in [e,d,b]:p.mkdir(parents=True,exist_ok=True)
 assert not(b/'plan.json.gz').exists();profiles=c.load(e/'profiles-reviewed.json');assert len({p['slug']for p in profiles})==len(profiles)
 target={r['record']['slug']:r for r in c.load(D/'baseline.json.gz')['rows']}
 completed=set()
 for f in (E/'batches').glob('*/applied.json'):
  completed.update(c.load(f)['slugs'])
 assert not completed&{p['slug']for p in profiles}
 assert all(p['slug']in target and p['sources']and len(p['description'].split('\n\n'))==2 and 25<=len(p['description'].split())<=170 for p in profiles)
 with c.connect()as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  rows={r['v']['slug']:r['v']for r in db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE slug=ANY(%s)',([p['slug']for p in profiles],))}
  places=[r['v']for r in db.execute('SELECT to_jsonb(p)v FROM places p')]
  countries={r['code'].strip()for r in db.execute('SELECT code FROM countries')}
  ids=[r['id']for r in rows.values()]
  old_venues=[r['v']for r in db.execute('SELECT to_jsonb(t)v FROM institution_venues t WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(ids,))]
  old_citations=[r['v']for r in db.execute("SELECT to_jsonb(t)v FROM citations t WHERE entity_type='institution' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,))]
 changes=[];new={};key=OP+'/'+batch
 def uid(k):return str(uuid.uuid5(uuid.NAMESPACE_URL,key+'/'+k))
 for p in profiles:
  before=rows[p['slug']];original=target[p['slug']]['record']
  assert before['id']==original['id']and before['status']!='archived'and before['canonical_institution_id']is None
  assert {k:v for k,v in before.items()if k not in ['description','place_id','updated_at']}=={k:v for k,v in original.items()if k not in ['description','place_id','updated_at']},'Identity/status changed; reconcile target'
  assert before['description']==original['description']and before['place_id']==original['place_id'],'Profile changed since census; reconcile before update'
  assert p['country']in countries and p['city']
  old_place=next((x for x in places if x['id']==before['place_id']),None)
  if old_place and c.norm(old_place['name'])==c.norm(p['city'])and(old_place['country_code']or'').strip()==p['country']:place_id=old_place['id']
  else:
   if old_place:assert p.get('reviewed_location_replacement'),p['slug']+' requires explicit location correction rationale'
   matches=[x for x in places if c.norm(x['name'])==c.norm(p['city'])and(x['country_code']or'').strip()==p['country']]
   assert len(matches)<=1,'Ambiguous city: '+p['city']
   if matches:place_id=matches[0]['id']
   else:
    k=p['city']+'/'+p['country'];place_id=uid('place/'+k);new[k]=dict(id=place_id,name=p['city'],normalized_name=c.norm(p['city']),country_code=p['country'])
  changes.append(dict(before=before,place_id=place_id,description=p['description'],sources=p['sources'],reviewed_city=p['city'],reviewed_country=p['country'],research_note=p.get('research_note'),location_correction=p.get('reviewed_location_replacement')))
 value=dict(at=c.now(),request_id=key,content=pin(e/'profiles-reviewed.json'),instructions=pin(ROOT/'AGENTS.md'),changes=changes,new_places=list(new.values()),source=dict(id=uid('source'),slug=OP+'-'+batch+'-references',name='Institution profile references reviewed 30 October 2026, batch '+batch,source_type='collection_page',priority=80,is_active=True),old_venues=old_venues,old_citations=old_citations)
 (b/'AGENTS-before-write.md').write_bytes((ROOT/'AGENTS.md').read_bytes());c.save(b/'plan.json.gz',value);c.save(e/'plan-pin.json',pin(b/'plan.json.gz'));print('PLANNED',batch,len(changes),'profiles;',sum(x['before']['place_id']!=x['place_id']for x in changes),'location links;',len(new),'new cities')

def module(batch):
 spec=importlib.util.spec_from_file_location('museum_review_writer',ROOT/'ops/museum-page-review-20261030.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OP=OP+'/'+batch;m.E,m.D,m.B=paths(batch);m.CONTENT=m.E/'profiles-reviewed.json';return m

def apply(batch):
 m=module(batch);e,d,b=paths(batch);v=c.load(b/'plan.json.gz');assert not(e/'applied.json').exists()and not(b/'transaction-staged.json.gz').exists(),'Reconcile dispatched writer; never replay'
 assert pin(b/'plan.json.gz')==c.load(e/'plan-pin.json')and pin(m.CONTENT)==v['content']and pin(ROOT/'AGENTS.md')==v['instructions']
 changes=[];digest=pin(b/'plan.json.gz')['sha256']
 with c.connect(write=True)as db:
  assert db.execute("SELECT current_database()db,current_setting('transaction_read_only')ro").fetchone()==dict(db='artline',ro='off')
  db.execute("SET LOCAL application_name='artline-all-museum-profile-review'");db.execute("SET LOCAL statement_timeout='60s'");db.execute("SET LOCAL lock_timeout='45s'")
  for q in ["SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))",'SELECT pg_advisory_xact_lock(2026101201)','SELECT pg_advisory_xact_lock(202610053)']:db.execute(q)
  proof=m.locks_held(db);assert pin(ROOT/'AGENTS.md')==v['instructions'];assert not db.execute('SELECT id FROM audit_log WHERE request_id=%s LIMIT 1',(m.OP,)).fetchone()
  for change in v['changes']:assert db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE id=%s FOR UPDATE',(change['before']['id'],)).fetchone()['v']==change['before']
  db.execute("SELECT set_config('artline.actor_user_id',%s,true),set_config('artline.request_id',%s,true)",(m.ACTOR,m.OP))
  for row in v['new_places']:changes.append(dict(table='places',before=None,after=m.insert(db,'places',row)))
  changes.append(dict(table='sources',before=None,after=m.insert(db,'sources',v['source'])))
  for change in v['changes']:
   before=change['before'];after=db.execute('UPDATE institutions SET place_id=%s,description=%s,updated_at=now() WHERE id=%s RETURNING to_jsonb(institutions)v',(change['place_id'],change['description'],before['id'])).fetchone()['v'];changes.append(dict(table='institutions',before=before,after=after))
   row=dict(id=m.uid('citation/'+after['id']),entity_type='institution',entity_id=after['id'],field_name='description_and_location',source_id=v['source']['id'],source_record_id=after['slug'],source_url=change['sources'][0],evidence_note=json.dumps(dict(sources=change['sources'],city=change['reviewed_city'],country=change['reviewed_country'],original_English_summary=True,research_note=change['research_note'],location_correction=change['location_correction'],plan_sha256=digest)),retrieved_at=v['at'],created_by=m.ACTOR)
   changes.append(dict(table='citations',before=None,after=m.insert(db,'citations',row)))
  for index,change in enumerate(changes):
   row=dict(id=m.uid('audit/'+str(index)),actor_user_id=m.ACTOR,action='review_museum_description_and_location',entity_type=change['table'],entity_id=change['after']['id'],request_id=m.OP,before_json=Jsonb(change['before']),after_json=Jsonb(dict(record=change['after'],transaction=proof,plan_sha256=digest)));m.insert(db,'audit_log',row);change['audit_id']=row['id']
  assert m.locks_held(db)==proof and pin(ROOT/'AGENTS.md')==v['instructions']
  c.save(b/'transaction-staged.json.gz',dict(at=c.now(),transaction=proof,changes=changes,plan_sha256=digest))
 c.save(e/'applied.json',dict(at=c.now(),transaction=proof,explicit_audits=len(changes),profiles=len(v['changes']),slugs=[x['before']['slug']for x in v['changes']],location_links=sum(x['before']['place_id']!=x['place_id']for x in v['changes']),new_cities=len(v['new_places']),three_shared_locks_retained=True));print('COMMITTED',batch,len(changes),'atomic changes',proof)

def verify(batch):
 m=module(batch);m.verify();e,d,b=paths(batch);v=c.load(b/'plan.json.gz')
 with c.connect()as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  for table in ['institution_venues','citations']:
   rows=v['old_venues'if table=='institution_venues'else'old_citations'];ids=[x['id']for x in rows];current=[x['v']for x in db.execute(sql.SQL('SELECT to_jsonb(t)v FROM {} t WHERE id=ANY(%s::uuid[]) ORDER BY id').format(sql.Identifier(table)),(ids,))];assert current==rows
 c.save(e/'preservation.json',dict(passed=True,existing_venues=len(v['old_venues']),existing_citations=len(v['old_citations']),identities_statuses_and_non_profile_fields_unchanged=True));print('PRESERVED existing venues/citations')

def projection(batch):
 import os,subprocess
 e,d,b=paths(batch);dest=e/'repository-projection.json'
 assert(e/'database-verification.json').exists()and not dest.exists()
 with c.connect():pass
 env=dict(os.environ,ARTLINE_READONLY_DATABASE_URL=c._db_base._dsn)
 subprocess.run([str(H/'runtime/museum-profile-projection-20261030'),str(e/'profiles-reviewed.json'),str(dest)],env=env,check=True)

def public(batch):
 import concurrent.futures,gzip,urllib.request,urllib.error
 e,d,b=paths(batch);assert(e/'database-verification.json').exists();expected={x['slug']:x for x in c.load(e/'repository-projection.json')['profiles']};dest=d/'public';dest.mkdir(parents=True,exist_ok=True)
 def fetch(p):
  receipt=dest/(p['slug']+'.receipt.json');body=dest/(p['slug']+'.json.gz')
  if receipt.exists():
   rc=c.load(receipt);raw=gzip.decompress(body.read_bytes());assert c.sha(raw)==rc['sha256']
  else:
   u='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/museums/'+p['slug']
   try:r=urllib.request.urlopen(u,timeout=60)
   except urllib.error.HTTPError as ex:r=ex
   raw=r.read(2*1024**2+1);assert len(raw)<=2*1024**2
   body.write_bytes(gzip.compress(raw,mtime=0));rc=dict(at=c.now(),url=u,status=r.status,bytes=len(raw),sha256=c.sha(raw),body=str(body));c.save(receipt,rc)
  assert rc['status']==expected[p['slug']]['status'],p['slug']+' HTTP '+str(rc['status'])
  if rc['status']==404:return dict(slug=p['slug'],status=404,sha256=rc['sha256'],reason=expected[p['slug']]['reason'],profile_metadata_verified_in_database=True)
  v=json.loads(raw);assert v['slug']==p['slug']and v['description']==p['description']and v['city']==p['city']and v['country']==p['country'],p['slug']
  return dict(slug=p['slug'],status=200,sha256=rc['sha256'])
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:checks=list(pool.map(fetch,c.load(e/'profiles-reviewed.json')))
 c.save(e/'public-verification.json',dict(at=c.now(),passed=True,profiles=len(checks),available_profiles=sum(x['status']==200 for x in checks),not_browsable_empty_collections=sum(x['status']==404 for x in checks),exact_descriptions_and_city_country_on_available_profiles=True,all_profile_metadata_verified_in_database=True,checks=checks));print('PUBLIC VERIFIED',batch,len(checks),'museum profiles')


if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['census','plan','apply','verify','projection','public']);a.add_argument('batch',nargs='?');v=a.parse_args();census()if v.action=='census'else globals()[v.action](v.batch)
