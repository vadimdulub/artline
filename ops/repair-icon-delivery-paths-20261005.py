#!/usr/bin/env python3
"""Repair three existing icon delivery names; retain original blobs and evidence."""
import argparse,base64,hashlib,importlib.util,json,re
from pathlib import Path
import requests
from google.cloud import storage
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-artwork-locations-20261004.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r);r.PORT=55445
s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
RUN=r.ROOT/'docs/research/museum-gaps-20261005/icon-paths';BACKUP=Path.home()/'Library/Application Support/Artline/backups/museum-icon-paths-20261005'

def plan():
 targets={}
 for target in ['local','production']:
  with r.connect(target)as db:
   rows=db.execute("SELECT to_jsonb(m) media FROM media_assets m WHERE m.storage_path LIKE '/assets/artworks/reviewed-icons-20260920/%%' AND m.storage_path !~ '^/assets/[a-zA-Z0-9/_-]+\\.(jpg|jpeg|png|webp|avif)$' ORDER BY m.id").fetchall()
   assert len(rows)==3;targets[target]=[v['media']for v in rows]
 assert [(x['id'],x['storage_path'],x['checksum_sha256'])for x in targets['local']]==[(x['id'],x['storage_path'],x['checksum_sha256'])for x in targets['production']]
 changes=[]
 for m in targets['local']:
  path=Path(m['storage_path']);new=str(path.with_name(path.stem.replace('.','-')+path.suffix));assert re.fullmatch(r'/assets/[a-zA-Z0-9/_-]+\.jpg',new)
  response=requests.get('https://artlines.org'+m['storage_path'],timeout=30);response.raise_for_status();assert hashlib.sha256(response.content).hexdigest()==m['checksum_sha256'];assert len(response.content)==m['byte_size']<=100000
  changes.append({'id':m['id'],'old':m['storage_path'],'new':new,'sha256':m['checksum_sha256'],'bytes':m['byte_size']})
 r.save_gz(RUN/'plan.json.gz',{'changes':changes,'preimages':targets});print('Verified 3 existing icon files')

def apply(target):
 data=r.load(RUN/'plan.json.gz');BACKUP.mkdir(parents=True,exist_ok=True);r.save_gz(BACKUP/(target+'-before.json.gz'),data['preimages'][target])
 bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
 for c in data['changes']:
  old=bucket.blob(c['old'].lstrip('/'));old.reload();new=bucket.blob(c['new'].lstrip('/'))
  if not new.exists():bucket.copy_blob(old,bucket,new.name,if_generation_match=0)
  new.reload();assert new.md5_hash==old.md5_hash and new.size==c['bytes']
 with r.connect(target,readonly=False)as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='3s'");ids=[c['id']for c in data['changes']];db.execute('SELECT id FROM media_assets WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
  current=[v['media']for v in db.execute('SELECT to_jsonb(m) media FROM media_assets m WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()]
  if all(m['storage_path']==c['new']for m,c in zip(current,data['changes'])):print(target,'already repaired');return
  assert current==data['preimages'][target], 'Media changed after preflight'
  for c in data['changes']:db.execute('UPDATE media_assets SET storage_path=%s,updated_at=now() WHERE id=%s AND storage_path=%s',(c['new'],c['id'],c['old']))
 print(target,'3 icon delivery paths repaired; old assets retained')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['plan','apply']);p.add_argument('--target',choices=['local','production']);args=p.parse_args()
 if args.command=='plan':plan()
 else:assert args.target;apply(args.target)
