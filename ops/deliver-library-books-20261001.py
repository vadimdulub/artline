#!/usr/bin/env python3
"""Deliver only the two explicitly reviewed book selections; require exact preimages and plan SHA."""
import json,subprocess,os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/research/production-library-20261001'
BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/production-library-20261001')
def connect(target,readonly=True):
 dsn='postgres://localhost/artline'
 if target=='cloud':
  raw=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
  fields=psycopg.conninfo.conninfo_to_dict(raw);fields.update(host='127.0.0.1',port='55434',sslmode='disable',connect_timeout='15');dsn=psycopg.conninfo.make_conninfo(**fields)
 return psycopg.connect(dsn,row_factory=dict_row,options='-c statement_timeout=180000'+(' -c default_transaction_read_only=on' if readonly else ''))
def norm(x):return json.loads(json.dumps(x,default=str))
def save(path,data):path.write_text(json.dumps(data,indent=2,default=str)+'\n')

import hashlib,datetime,sys
os.umask(0o077)
RESEARCH=ROOT/'docs/research/production-library-20261001';RESEARCH.mkdir(parents=True,exist_ok=True)
PLAN=RESEARCH/'books-plan.json'
CAMPAIGNS=['byzantine-books-20261001','pre1850-books-20261001']
CLOUD_BACKUP_ID='1790869347953'
KEYS={'book_records':['id'],'book_creators':['id'],'book_creator_links':['book_id','position'],'book_discovery':['book_id'],'book_discovery_terms':['kind','key']}
COLS={'book_records':['id','source_id','status','record','source_checksum'],'book_creators':['id','name','record','source_checksum'],'book_creator_links':['book_id','creator_id','position','credit'],'book_discovery_terms':['kind','key','name','evidence']}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def rows(d,t,ids,field='id'):
 return norm(d.execute('select * from '+t+' where '+field+'=ANY(%s) order by '+','.join(KEYS[t]),(ids,)).fetchall())
def state(d,ids,creators,terms):
 x={t:rows(d,t,ids,'id' if t=='book_records' else 'book_id')for t in ['book_records','book_creator_links','book_discovery']};x['book_creators']=rows(d,'book_creators',creators)
 x['book_discovery_terms']=norm([r for r in d.execute('select * from book_discovery_terms order by kind,key')if [r['kind'],r['key']]in terms]);return x
def summary(d):return norm(d.execute("select count(*) books,count(*) filter(where b.status='published') published,count(*) filter(where b.end_year<1850) pre1850,count(*) filter(where d.top100 and d.book_checksum=b.source_checksum) highlights from book_records b left join book_discovery d on b.id=d.book_id").fetchone())
def key(t,r):return tuple(r[k]for k in KEYS[t])
def fingerprint(d,ids):
 return norm(d.execute("select (select md5(string_agg(row_to_json(b)::text,'|' order by id)) from book_records b where not(id=ANY(%s))) books,(select md5(string_agg(row_to_json(d)::text,'|' order by book_id)) from book_discovery d where not(book_id=ANY(%s))) discovery,(select md5(string_agg(row_to_json(c)::text,'|' order by id)) from book_creators c) creators",(ids,ids)).fetchone())
def prepare():
 assert not PLAN.exists(),'Preserve original delivery plan'
 sourceplans=[json.load(open(ROOT/'docs/research'/c/'plan.json'))for c in CAMPAIGNS];ids=[c['id']for p in sourceplans for c in p['changes']]
 assert ids and len(ids)==len(set(ids))
 with connect('local')as l,connect('cloud')as p:
  links=rows(l,'book_creator_links',ids,'book_id');creators=sorted({r['creator_id']for r in links});discovery=rows(l,'book_discovery',ids,'book_id')
  terms=sorted({(kind,q)for d in discovery for kind,col in [('language','languages'),('country','countries'),('region','regions')]for q in d[col]});terms=[list(x)for x in terms]
  desired=state(l,ids,creators,terms);before=state(p,ids,creators,terms)
  byid={r['id']:r for r in before['book_records']}
  for old in [c for plan in sourceplans for c in plan['changes']]:
   if old['new']:assert old['id']not in byid,'Unexpected production record'
   else:assert byid[old['id']]['source_checksum']==old['before']['source_checksum'] and byid[old['id']]['status']==old['before']['status']
  for table in ['book_creators','book_discovery_terms','book_creator_links']:
   existing={key(table,r):r for r in before[table]}
   for r in desired[table]:
    if key(table,r)in existing:
     cols=COLS[table] if table!='book_discovery_terms' else ['kind','key','name']
     assert all(r[c]==existing[key(table,r)][c] for c in cols),'Existing dependency differs: '+table+str(key(table,r))
  plan={'ids':ids,'creators':creators,'terms':terms,'before':before,'desired':desired,'beforeTotals':summary(p),'sourcePlans':[{'path':'docs/research/'+c+'/plan.json','sha256':hashlib.sha256((ROOT/'docs/research'/c/'plan.json').read_bytes()).hexdigest()}for c in CAMPAIGNS],'cloudBackupId':CLOUD_BACKUP_ID}
  save(PLAN,plan);print(json.dumps({'selected':len(ids),'newBooks':len(desired['book_records'])-len(before['book_records']),'newCreators':len(desired['book_creators'])-len(before['book_creators']),'sha256':digest(plan),'before':plan['beforeTotals']}))
def apply(pin):
 plan=json.load(open(PLAN));assert pin==digest(plan)
 for proof in plan['sourcePlans']:assert hashlib.sha256((ROOT/proof['path']).read_bytes()).hexdigest()==proof['sha256']
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe',plan['cloudBackupId'],'--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(BACKUP/'cloud-backup.json',backup)
 with connect('cloud',False)as d,d.transaction():
  d.execute('select pg_advisory_xact_lock(202610010004)');d.execute('lock table book_records,book_creators,book_creator_links,book_discovery,book_discovery_terms in share row exclusive mode')
  assert state(d,plan['ids'],plan['creators'],plan['terms'])==plan['before'],'Production changed since review'
  untouched=fingerprint(d,plan['ids']);before=summary(d);save(BACKUP/'book-preimages.json',{'planSha256':pin,'before':plan['before'],'unselectedFingerprint':untouched})
  for t in ['book_creators','book_discovery_terms','book_records','book_creator_links','book_discovery']:
   prior={key(t,r):r for r in plan['before'][t]}
   for r in plan['desired'][t]:
    present=key(t,r)in prior
    if present and t in ['book_creators','book_discovery_terms','book_creator_links']:continue
    if t=='book_records':assert r['status']=='review'
    if present and t=='book_records':
     d.execute('update book_records set record=%s,source_checksum=%s where id=%s',(Jsonb(r['record']),r['source_checksum'],r['id']));continue
    if t=='book_discovery':d.execute('delete from book_discovery where book_id=%s',(r['book_id'],))
    cols=COLS.get(t,list(r));values=[Jsonb(r[c])if isinstance(r[c],dict)else r[c]for c in cols]
    d.execute('insert into '+t+'('+','.join(cols)+') values('+','.join(['%s']*len(cols))+')',values)
  after=summary(d)
  added_books=len(plan['desired']['book_records'])-len(plan['before']['book_records'])
  added_highlights=sum(bool(r['top100']) for r in plan['desired']['book_discovery'])-sum(bool(r['top100']) for r in plan['before']['book_discovery'])
  assert after['books']==before['books']+added_books and after['highlights']==before['highlights']+added_highlights and after['published']==before['published']
  untouched_after=fingerprint(d,plan['ids']);assert untouched_after['books']==untouched['books'] and untouched_after['discovery']==untouched['discovery']
  # Every pre-existing creator is preserved, including those outside this batch.
  old_creator_ids=[r['id']for r in plan['before']['book_creators']]
  assert rows(d,'book_creators',old_creator_ids)==plan['before']['book_creators']
  result=state(d,plan['ids'],plan['creators'],plan['terms'])
  for t in ['book_records','book_creator_links','book_discovery']:
   actual={key(t,r):r for r in result[t]}
   cols=COLS.get(t,[c for c in result[t][0]if c not in ['checked_at']])
   for r in plan['desired'][t]:assert all(r[c]==actual[key(t,r)][c]for c in cols),t+' verification failed'
 receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'planSha256':pin,'cloudBackupId':plan['cloudBackupId'],'before':before,'after':after,'newBooks':added_books,'dateCorrections':len(plan['before']['book_records']),'newCreators':len(plan['desired']['book_creators'])-len(plan['before']['book_creators']),'unselectedBooksAndDiscoveryUnchanged':True,'existingSelectedCreatorsUnchanged':True,'allNewBooksStatus':'review'};save(RESEARCH/'books-apply-receipt.json',receipt);print(json.dumps(receipt,indent=2))
if __name__=='__main__':prepare()if sys.argv[1]=='prepare'else apply(sys.argv[2])
