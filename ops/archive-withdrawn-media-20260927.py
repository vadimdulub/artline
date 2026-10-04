#!/usr/bin/env python3
"""Reconcile withdrawn media as private archives; never re-publish held images."""
import argparse,base64,concurrent.futures,hashlib,importlib.util,json,subprocess
from pathlib import Path
import requests
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('release',Path(__file__).with_name('audit-production-release.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
RUN=r.ROOT/'docs/research/production-followup-20260927'
BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/production-followup-20260927')
def save(path,data):
 raw=json.dumps(data,indent=2,default=str).encode();path.write_bytes(raw);path.chmod(0o600)
def plan():
 source=json.loads((RUN/'missing-media-before.json').read_text());recovery={x['media_id']:x for x in json.loads((RUN/'missing-media-private-recovery.json').read_text())};entries=[]
 for row in source:
  m=row['media'];ev=row['rights']['evidence_json'];old=recovery[m['id']];assert not row['artworks'] and not row['artists']
  review=ev.get('image_identity_review') or ev.get('subsequent_rights_hold')
  if m['id']=='56cdd96a-7069-56f4-ad77-f14b1dfb9b1d':review=json.loads((r.ROOT/'docs/research/wikipedia-painter-by-painter-20260914/withdrawals/ad9bb5fa-e4e6-473f-9a44-8c9549fde899/result.json').read_text())
  assert review and old['private_copies']
  entries.append({'media_id':m['id'],'path':m['storage_path'],'sha256':m['checksum_sha256'],'bytes':m['byte_size'],'private_file':old['private_copies'][0], 'archive_key':'research-holds/withdrawn-media/'+m['id']+'/'+m['checksum_sha256']+'.jpg','withdrawal':review})
 assert len(entries)==590;save(RUN/'withdrawn-archive-plan.json',entries)
 for target in ['local','cloud']:
  with r.connect(target) as db:
   db.execute("SET LOCAL timezone='UTC'");rows=db.execute('SELECT to_jsonb(m),to_jsonb(e) FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[]) ORDER BY m.id',([e['media_id'] for e in entries],)).fetchall()
   assert len(rows)==590
   for m,e in rows:
    p=next(p for p in entries if p['media_id']==m['id']);assert m['storage_path']==p['path'] and m['checksum_sha256']==p['sha256'] and m['byte_size']==p['bytes']
   save(BACKUP/('withdrawn-'+target+'-before.json'),rows)
 print('Pinned 590 withdrawn records and exact private recovery bytes.')
def upload():
 entries=json.loads((RUN/'withdrawn-archive-plan.json').read_text());bucket=r.core.storage.Client(project='artline-508319',credentials=r.core.GcloudCredentials()).bucket(r.core.BUCKET)
 policy=bucket.get_iam_policy(requested_policy_version=3)
 assert not any(m in {'allUsers','allAuthenticatedUsers'} for b in policy.bindings for m in b['members'])
 def one(p):
  raw=Path(p['private_file']).read_bytes();assert len(raw)==p['bytes'] and hashlib.sha256(raw).hexdigest()==p['sha256'];md5=base64.b64encode(hashlib.md5(raw).digest()).decode()
  blob=bucket.get_blob(p['archive_key'])
  if blob is None:
   blob=bucket.blob(p['archive_key']);blob.metadata={'media_id':p['media_id'],'sha256':p['sha256'],'delivery_state':'withdrawn','original_public_path':p['path']};blob.cache_control='private, no-store';blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60);blob.reload()
  assert blob.size==p['bytes'] and blob.md5_hash==md5 and blob.metadata['sha256']==p['sha256']
  return {'media_id':p['media_id'],'key':p['archive_key'],'generation':blob.generation,'bytes':blob.size,'md5':blob.md5_hash,'sha256':p['sha256']}
 out=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for value in pool.map(one,entries):
   out.append(value)
   if len(out)%50==0:print('Private archive verified',len(out),flush=True)
 # Anonymous access must fail; the app route only serves the separate assets/ namespace.
 response=requests.get('https://storage.googleapis.com/'+r.core.BUCKET+'/'+out[0]['key'],timeout=20);assert response.status_code in (401,403)
 save(RUN/'withdrawn-archive-upload.json',{'at':r.core.now(),'private_iam':True,'anonymous_status':response.status_code,'objects':out})
def apply():
 entries=json.loads((RUN/'withdrawn-archive-plan.json').read_text());receipt=json.loads((RUN/'withdrawn-archive-upload.json').read_text());assert len(receipt['objects'])==590 and receipt['private_iam']
 backup=json.loads(subprocess.check_output(['/Users/vadimdulub/Documents/google-cloud-sdk/bin/gcloud','sql','backups','describe','1790533520479','--instance=artline-postgres','--project=artline-508319','--format=json']));assert backup['status']=='SUCCESSFUL'
 ids=[p['media_id'] for p in entries];objects={p['media_id']:p for p in receipt['objects']};out={}
 for target in ['local','cloud']:
  expected={m['id']:(m,e) for m,e in json.loads((BACKUP/('withdrawn-'+target+'-before.json')).read_text())}
  with r.connect(target,readonly=False) as db:
   db.execute("SET LOCAL timezone='UTC'");db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(559220260915)')
   assert not db.execute('SELECT 1 FROM artworks WHERE primary_media_id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone()
   assert not db.execute('SELECT 1 FROM artists WHERE portrait_media_id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone()
   assert not db.execute('SELECT 1 FROM artwork_media WHERE media_id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone()
   rows=db.execute('SELECT to_jsonb(m),to_jsonb(e) FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[]) ORDER BY m.id FOR UPDATE OF m,e',(ids,)).fetchall();assert len(rows)==590
   actual={m['id']:(m,e) for m,e in rows}
   for p in entries:
    m,e=actual[p['media_id']];review={'state':'withheld','at':r.core.now(),'former_public_path':p['path'],'archive_bucket':r.core.BUCKET,'archive_key':p['archive_key'],'archive_generation':objects[p['media_id']]['generation'],'sha256':p['sha256'],'reason':'Public reproduction was previously withdrawn; exact bytes and original review retained privately. This is not a missing public upload.','withdrawal':p['withdrawal']}
    if m['storage_kind']=='placeholder' and m['storage_path'] is None and e['evidence_json'].get('delivery_review',{}).get('archive_key')==p['archive_key']:continue
    assert (m,e)==expected[m['id']],'Changed preimage '+m['id']
    db.execute("UPDATE media_assets SET storage_kind='placeholder',storage_path=NULL,updated_at=now() WHERE id=%s",(m['id'],))
    db.execute("UPDATE media_rights_evidence SET evidence_json=evidence_json||%s WHERE media_id=%s",(Jsonb({'delivery_review':review}),m['id']))
    db.execute("INSERT INTO audit_log(actor_user_id,action,entity_type,entity_id,before_json,after_json) VALUES(%s,'media.archive_withdrawn','media',%s,%s,%s)",(r.core.ACTOR,m['id'],Jsonb(m),Jsonb({'storage_kind':'placeholder','storage_path':None,'delivery_review':review})))
   verified=db.execute("SELECT count(*) FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[]) AND m.storage_kind='placeholder' AND m.storage_path IS NULL AND e.evidence_json->'delivery_review'->>'state'='withheld'",(ids,)).fetchone()[0];assert verified==590
   out[target]={'archived':verified,'artwork_records_changed':0,'rights_labels_preserved':True,'private_bytes_verified':True}
  save(RUN/('withdrawn-archive-'+target+'-applied.json'),{'at':r.core.now(),**out[target]});print(target,'stale public paths reconciled',verified,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','upload','apply']);a=p.parse_args();globals()[a.phase]()
