import argparse,sys,json,gzip,collections,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import exhibitions_common as c
from psycopg import sql
R=c.ROOT;H=Path.home()/'Library/Application Support/Artline';OP='museum-all-profiles-20261030';E=R/'docs/research'/OP;D=H/'source-metadata'/OP;B=H/'backups'/OP
parser=argparse.ArgumentParser(description='Read-only verification of completed museum profile batches and the prior 91 profiles.')
parser.add_argument('--campaign-profiles',type=int,required=True)
parser.add_argument('--version',required=True)
args=parser.parse_args()
assert 0<args.campaign_profiles<=2574 and args.version.startswith('v') and args.version[1:].isdigit()
dest=E/('cumulative-database-verification-'+args.version+'.json');assert not dest.exists()
base=c.load(D/'baseline.json.gz');target={x['record']['slug']:x['record']for x in base['rows']}
profiles=[];deliveries=[];previous=[]
for op in ['museum-page-review-20261030','museum-guide-profiles-20261030']:
 profiles+=c.load(R/'docs/research'/op/'profiles-reviewed.json')
 previous.append(c.load(H/'backups'/op/'transaction-staged.json.gz'))
prior=len(profiles);assert prior==91
staged=list(previous)
for p in sorted((E/'batches').glob('*/applied.json')):
 a=c.load(p);batch=p.parent.name;assert all((p.parent/f).exists()for f in ['database-verification.json','preservation.json','repository-projection.json'])
 ps=c.load(p.parent/'profiles-reviewed.json');assert len(ps)==a['profiles'];profiles+=ps;staged.append(c.load(B/'batches'/batch/'transaction-staged.json.gz'));deliveries.append(dict(batch=batch,**a))
assert len(profiles)==prior+args.campaign_profiles and len({p['slug']for p in profiles})==len(profiles)
assert all(s['transaction']['held']==3 for s in staged)
expected={};auditids=[]
for s in staged:
 for x in s['changes']:
  assert x['table']in ['institutions','places','sources','citations']
  expected.setdefault(x['table'],{})[x['after']['id']]=x['after'];auditids.append(x['audit_id'])
checked=collections.Counter()
with c.connect()as db:
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 for table,rows in expected.items():
  ids=list(rows)
  for offset in range(0,len(ids),200):
   chunk=ids[offset:offset+200];actual={x['v']['id']:x['v']for x in db.execute(sql.SQL('SELECT to_jsonb(t)v FROM {} t WHERE id=ANY(%s::uuid[])').format(sql.Identifier(table)),(chunk,))};assert actual=={i:rows[i]for i in chunk},table;checked[table]+=len(chunk)
 current={x['record']['slug']:x for x in db.execute('SELECT to_jsonb(i)record,p.name city,trim(p.country_code)country FROM institutions i LEFT JOIN places p ON p.id=i.place_id WHERE i.slug=ANY(%s)',([p['slug']for p in profiles],))}
 for p in profiles:
  x=current[p['slug']];assert x['record']['description']==p['description']and x['city']==p['city']and x['country']==p['country'],p['slug']
  if p['slug']in target:assert {k:v for k,v in x['record'].items()if k not in ['description','place_id','updated_at']}=={k:v for k,v in target[p['slug']].items()if k not in ['description','place_id','updated_at']}
 audits={}
 for offset in range(0,len(auditids),200):
  audits.update({str(x['id']):x for x in db.execute('SELECT id,before_json,after_json FROM audit_log WHERE id=ANY(%s::uuid[])',(auditids[offset:offset+200],))})
 assert len(audits)==len(auditids)==len(set(auditids))
 for s in staged:
  for x in s['changes']:
   a=audits[x['audit_id']];assert a['before_json']==x['before']and a['after_json']==dict(record=x['after'],transaction=s['transaction'],plan_sha256=s['plan_sha256'])
c.save(dest,dict(at=c.now(),passed=True,target_total=2574,campaign_profiles=args.campaign_profiles,previous_profiles_preserved=prior,total_verified_profiles=len(profiles),remaining_target_profiles=2574-args.campaign_profiles,exact_city_country_and_descriptions=True,all_owned_atomic_postimages_verified=dict(checked),all_owned_explicit_audits_verified=len(auditids),campaign_identity_status_and_non_profile_fields_preserved=True,all_saved_write_transactions_retain_three_shared_locks=True,read_only=True,deliveries=deliveries))
print('CUMULATIVE VERIFIED',len(profiles),'profiles,',len(auditids),'atomic audits')
