#!/usr/bin/env python3
"""Pinned production delivery for the explicitly accepted exhibition gallery.

Real local DB is never writable. Existing main artwork/artist rows, statuses and
original exhibition samples are preserved. New projections commit atomically.
"""
import argparse,base64,concurrent.futures,copy,hashlib,json,subprocess,threading
from pathlib import Path
from psycopg.types.json import Jsonb
import exhibitions_common as c
OP='exhibitions-gallery-20261012'
BASE=Path.home()/'Library/Application Support/Artline'
OUT=BASE/'backups'/OP
CORPUS=BASE/'source-metadata/exhibition-images-local-20261012/review-corpus.json'
MIGRATION=c.ROOT/'apps/server/db/migrations/0049_exhibition_research.sql'

def load():
 raise RuntimeError('Retired: the user replaced this 2020–2025 gallery with historical exhibitions from 1600–1989. Do not upload or import this corpus.')
 raw=CORPUS.read_bytes();d=json.loads(raw)
 assert len(d['records'])==700 and len(d['artworks'])==9936
 assert sum(len(r['entries'])for r in d['records'])==10506
 assert all(a['image']for a in d['artworks'])
 return d,hashlib.sha256(raw).hexdigest()

def plan():
 d,sha=load();ids=[r['id']for r in d['records']]
 with c.connect() as db:
  rows=db.execute('SELECT id,title,start_year,end_year,status FROM exhibitions WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
  sources=db.execute('SELECT id,exhibition_id,source_key,source_record_id FROM exhibition_source_records WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).fetchall()
  existing=db.execute("SELECT to_regclass('exhibition_research') name").fetchone()
 assert len(rows)==700 and all(r['status']!='archived'for r in rows)
 rm={str(r['id']):r for r in rows}
 assert all(r['title']==rm[r['id']]['title'] and r['startYear']==rm[r['id']]['start_year']for r in d['records'])
 sourcekeys={(str(s['exhibition_id']),s['source_key'])for s in sources}
 assert all((r['id'],e['provider'])in sourcekeys for r in d['records']for e in r['entries'])
 counts={'exhibitions':700,'objects':9936,'appearances':10506,'newImages':9928}
 manifest=dict(batch=OP,at=c.now(),corpusSHA256=sha,migrationSHA256=c.sha(MIGRATION.read_bytes()),counts=counts,sourceRecords=sources,existingExhibitions=rows,authorization='User: nice, deploy it (12 October 2026). Includes the accepted 700-exhibition gallery and prepared images.',localDatabaseWrites=False,mainCatalogueWrites=False)
 c.save(OUT/'plan.json',manifest);print(json.dumps(counts),flush=True)

def upload():
 from google.cloud import storage
 from google.auth.credentials import Credentials
 class GcloudCredentials(Credentials):
  def refresh(self,request):
   self.token=subprocess.check_output(['gcloud','auth','print-access-token'],text=True).strip()
 creds=GcloudCredentials();creds.refresh(None)
 bucket=storage.Client(project='artline-508319',credentials=creds).bucket('artline-508319-images')
 d,sha=load();p=c.load(OUT/'plan.json');assert sha==p['corpusSHA256']
 selected=[a for a in d['artworks']if a['image'].startswith('/assets/artworks/exhibitions-local/')];assert len(selected)==9928
 lock=threading.Lock();done=0
 def one(a):
  nonlocal done
  path=a['image'].lstrip('/');raw=(c.ROOT/'apps/web/public'/path).read_bytes();digest=c.sha(raw)
  assert len(raw)<=100000 and digest==a['localImageEvidence']['sha256']
  blob=bucket.get_blob(path);created=blob is None
  if created:
   blob=bucket.blob(path);blob.metadata={'sha256':digest,'source':a.get('imageSource')or a['sourceURL'],'license':a.get('imageLicense')or 'Not supplied','batch':OP,'source-object-id':a['sourceArtworkID']}
   blob.cache_control='public,max-age=31536000,immutable'
   blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60);blob.reload()
  assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
  receipt=dict(id=a['id'],path=path,sha256=digest,bytes=len(raw),generation=blob.generation)
  c.save(OUT/'images'/(a['id']+'.json'),receipt)
  with lock:
   done+=1
   if done%250==0:print('Verified production images',done,flush=True)
  return receipt
 with concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:receipts=list(pool.map(one,selected))
 # Retain all eight prior media attachments, verifying their stored bytes exist.
 preserved=[]
 for a in d['artworks']:
  if a['image'].startswith('/assets/artworks/exhibitions-local/'):continue
  b=bucket.get_blob(a['image'].lstrip('/'));assert b and b.size>0,a['image'];preserved.append(dict(id=a['id'],path=a['image'],generation=b.generation))
 c.save(OUT/'images-delivered.json',dict(corpusSHA256=sha,images=receipts,preserved=preserved));print('All images uploaded and verified',len(receipts),flush=True)

def apply():
 d,sha=load();p=c.load(OUT/'plan.json');assert sha==p['corpusSHA256'] and c.sha(MIGRATION.read_bytes())==p['migrationSHA256']
 images=c.load(OUT/'images-delivered.json');assert images['corpusSHA256']==sha and len(images['images'])==9928
 # Successful Cloud SQL backup must precede schema/data writes.
 backup=c.load(OUT/'cloud-backup.json');assert backup['status']=='SUCCESSFUL'
 objects={a['id']:a for a in d['artworks']}
 source={(str(s['exhibition_id']),s['source_key']):str(s['id'])for s in p['sourceRecords']}
 extra_keys=['entryCount','participantCount','participants','publications','research','participationCounts','localArtworkCount','illustratedArtworkCount','previewWorks']
 eventrows=[];peoplerows=[];objectrows=[];entryrows=[]
 for r in d['records']:
  detail={k:r[k]for k in extra_keys};detail['expandedStudy']=True
  summary=copy.deepcopy(detail);summary.pop('publications');summary['participants']=summary['participants'][:3]
  # Canonical event/venue facts are read live, never overwritten by the snapshot.
  eventrows.append((r['id'],OP,Jsonb(detail),Jsonb(summary),r['research']['concepts'],r['featured'],len(r['entries']),r['illustratedArtworkCount']))
  people={v['id']:v for v in r['participants']}
  for e in r['entries']:
   a=objects[e['localArtworkId']]
   for person in a['artists']:people.setdefault(person['id'],person)
   appearance=next(v for v in a['appearances']if v['id']==e['id']);assert appearance['exhibitionId']==r['id']
   entryrows.append((e['id'],r['id'],a['id'],source[(r['id'],e['provider'])],e['participation'],Jsonb(e),Jsonb(appearance)))
  peoplerows.extend((r['id'],v['id'],v.get('artist_id'))for v in people.values())
 for a in d['artworks']:
  detail={k:v for k,v in a.items()if k!='appearances'};detail['localStudy']=False;detail['deploymentEvidence']={'batch':OP,'authorization':p['authorization'],'corpusSHA256':sha}
  objectrows.append((a['id'],a['provider'],a['sourceArtworkID'],a.get('artworkId'),OP,Jsonb(detail)))
 with c.connect(write=True)as db:
  db.execute('SELECT pg_advisory_xact_lock(20250907001)')
  already=db.execute("SELECT 1 FROM schema_migrations WHERE filename=%s",(MIGRATION.name,)).fetchone()
  if not already:
   db.execute(MIGRATION.read_text());db.execute('INSERT INTO schema_migrations(filename) VALUES(%s)',(MIGRATION.name,))
  batch=db.execute('SELECT corpus_sha256 FROM exhibition_research_batches WHERE id=%s',(OP,)).fetchone()
  if batch:
   assert batch['corpus_sha256']==sha;print('Matching batch already committed');return
  current=db.execute('SELECT id,title,start_year,end_year,status FROM exhibitions WHERE id=ANY(%s::uuid[]) FOR SHARE',([r['id']for r in d['records']],)).fetchall()
  assert {str(r['id']):json.loads(json.dumps(r,default=str))for r in current}=={str(r['id']):r for r in p['existingExhibitions']},'Exhibitions changed during preparation'
  db.execute('INSERT INTO exhibition_research_batches(id,corpus_sha256,manifest)VALUES(%s,%s,%s)',(OP,sha,Jsonb({k:v for k,v in p.items()if k not in ['existingExhibitions','sourceRecords']})))
  with db.cursor()as cur:
   cur.executemany('INSERT INTO exhibition_research(exhibition_id,batch_id,detail,summary,concepts,featured,entry_count,illustrated_count)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',eventrows)
   cur.executemany('INSERT INTO exhibition_research_people(exhibition_id,person_id,artist_id)VALUES(%s,%s,%s)',peoplerows)
   cur.executemany('INSERT INTO exhibition_objects(id,provider,source_object_id,artwork_id,batch_id,detail)VALUES(%s,%s,%s,%s,%s,%s)',objectrows)
   cur.executemany('INSERT INTO exhibition_object_entries(id,exhibition_id,object_id,source_record_id,participation,detail,appearance)VALUES(%s,%s,%s,%s,%s,%s,%s)',entryrows)
  counts=db.execute('SELECT (SELECT count(*) FROM exhibition_research) exhibitions,(SELECT count(*) FROM exhibition_objects) objects,(SELECT count(*) FROM exhibition_object_entries) appearances').fetchone()
  assert counts==dict(exhibitions=700,objects=9936,appearances=10506)
  assert db.execute('SELECT count(*) n FROM exhibition_object_entries x JOIN exhibition_source_records s ON s.id=x.source_record_id WHERE x.exhibition_id<>s.exhibition_id').fetchone()['n']==0
  for table in ['exhibition_research','exhibition_research_people','exhibition_objects','exhibition_object_entries']:db.execute('ANALYZE '+table)
 c.save(OUT/'database-delivered.json',dict(at=c.now(),counts=counts,corpusSHA256=sha,realLocalDatabaseWrites=False,existingRecordsRewritten=False))
 print(json.dumps(counts),flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['plan','upload','apply']);args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True);OUT.chmod(0o700);globals()[args.action]()
