#!/usr/bin/env python3
"""Retire only pinned campaign images whose original provenance is unresolved.

Source bytes/evidence are preserved in the user's backup area. Database artwork
records remain intact; public copies are removed only after exact checks.
"""
import argparse,base64,concurrent.futures,hashlib,importlib.util,json,shutil
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=module('withdraw','withdraw-overnight-source-image-conflict.py');audit=module('audit','audit-overnight-local-images.py');core=w.core
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--retire-public-only',action='store_true');a=p.parse_args();r=a.run.resolve();assert r==w.RUN
 plan=json.loads((r/'commons-origin-withdrawal-plan.json').read_text());records=plan['records']
 for target in ('local','cloud'):assert json.loads((r/('commons-origin-'+target+'-withdrawal-preflight.json')).read_text())['count']==len(records)
 backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915/unverified-image-origins';backup.mkdir(parents=True,exist_ok=True)
 for row in records:
  im=row['image'];source=(ROOT/'apps/web/public'/im['path'].lstrip('/')).resolve();assert source.is_relative_to(ROOT/'apps/web/public/assets/artworks/open-museums')
  dest=backup/'images'/(im['artwork_id']+'-'+im['sha256']+'.jpg');dest.parent.mkdir(exist_ok=True)
  if not dest.exists():
   raw=source.read_bytes();assert len(raw)==im['bytes'] and core.sha(raw)==im['sha256'];dest.write_bytes(raw)
  assert core.sha(dest.read_bytes())==im['sha256']
 manifest=backup/'origin-review-plan.json'
 if not manifest.exists():core.save_new(manifest,plan)
 dsn=core.cloud_dsn();core.cloud_dsn=lambda:dsn
 for n,row in enumerate([] if a.retire_public_only else records,1):
  im=row['image'];note='Artline provenance audit: '+row['reason']+'. The Commons file supplied an allowed licence label, but that alone does not independently establish the original image provenance. Withhold this image association and public copy; retain the artwork metadata, rights evidence and exact source bytes in the backup area. A separately verified reproduction is still needed.'
  w.withdraw(im,note,'origin-hold-'+im['artwork_id'],receipt=row['receipt'])
  if n%25==0:print(core.now(),'Origin associations withheld',n,'of',len(records),flush=True)
 # One bounded reference-count query per database, never one catalogue scan
 # per image. Removing a public copy must not break another artwork's image.
 for target,connection in [('local','postgres://localhost/artline'),('cloud',dsn)]:
  with psycopg.connect(connection,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=60000') as db:
   assert not db.execute('SELECT id FROM artworks WHERE primary_media_id=ANY(%s::uuid[]) LIMIT 1',([x['image']['media_id'] for x in records],)).fetchone(),'A public image still has an artwork reference'
 client=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials());out=[]
 def retire(row):
  im=row['image'];source=ROOT/'apps/web/public'/im['path'].lstrip('/');dest=backup/'images'/(im['artwork_id']+'-'+im['sha256']+'.jpg');raw=dest.read_bytes();assert core.sha(raw)==im['sha256'];blob=client.bucket(core.BUCKET).get_blob(im['path'].lstrip('/'),timeout=30)
  if blob:
   expected=dict(im,md5=base64.b64encode(hashlib.md5(raw).digest()).decode(),local_artwork_id=im['artwork_id']);audit.verify_blob(blob,expected);blob.delete(if_generation_match=blob.generation,timeout=30)
  if source.exists():assert core.sha(source.read_bytes())==im['sha256'];source.unlink()
  return {'artwork_id':im['artwork_id'],'source_image_sha256':im['sha256'],'local_public_copy_removed':True,'production_public_copy_removed':True,'private_backup_verified':True}
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for n,result in enumerate(pool.map(retire,records),1):
   out.append(result)
   if n%50==0:print(core.now(),'Public copies retired with backup',n,'of',len(records),flush=True)
 core.save_new(r/'commons-origin-withdrawal-completed.json',{'at':core.now(),'count':len(out),'artworks_preserved':True,'both_database_associations_withheld':True,'records':out,'policy':'Only campaign images in the pinned unresolved-origin plan; exact source bytes and metadata preserved privately before removal. Google Storage generation, checksum, source identifier and artwork metadata checked before deleting the public copy.'})
if __name__=='__main__':main()
