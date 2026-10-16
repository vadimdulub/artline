#!/usr/bin/env python3
"""Selected exact Greek object images via established native-image workflow."""
import importlib.util,sys,shutil,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
b=mod('greek','continuous-greek-batch-000015.py');h=b.h;E=b.E;i=mod('images','illustrated-300k-20261011.py');B='athens-000'
i.OP=h.OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/h.OP;i.BACKUP=h.BACKUP
IID='052007aa-11f7-4d57-90e6-d3b62bb0bf4b'
i.CFG['athens']=dict(mid=IID,scheme='continuous-athens-object',name=b.MUSEUM,rights='restricted',license='Museum reproduction; no independent copyright-holder licence asserted',policy='https://www.nationalgallery.gr/en/terms-of-use/',host='www.nationalgallery.gr',limit=3)
def connect(write=False,local=False):
 assert not local;db=h.connect(write);db.autocommit=False;return db
i.m.m.connect=connect
old=i.m.uid;i.m.uid=lambda key:h.uid('source/athens/'+b.MUSEUM) if key=='source/athens' else old(key)
def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return
 plan,pin=h.pinned(b.PHASE);rows=[]
 for r in plan['records']:
  if r['date_decision']!='eligible' or (r['before'] and r['before']['artwork']['primary_media_id']):continue
  assert r['last']<=1955
  rows.append(dict(artwork_id=r['artwork_id'],provider='athens',native_id=r['source_id'],title=r['title'],creator_label=r['creator_label'],source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type=r['source_type'],plan_sha256=pin,expected_primary_artist_id=r['artist_id'],image=dict(image_url=r['raw']['image_url'],source=r,receipt=r['evidence']),rights_basis='Selected Greek museum source reproduction under docs/ARTLINE_IMAGE_USE.md Greek museum extension; explicit ca 1800/1803 creation before 1955. Actual museum restriction retained separately from user approval, which is not a copyright-holder licence.'))
 i.saved(i.folder(B)/'selection.json.gz',dict(provider='athens',batch=B,rows=rows));i.saved(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 i.ORIG.mkdir(parents=True,exist_ok=True)
 for r in rows:print(i.prepare_one(r,B)['state'])
 i.audit(B)
 h.save(E/'image-authorization.json',dict(at=h.now(),policy='docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026',scope='Three explicitly dated 1800/1803 official Koutouzis reproductions; one undated object excluded',user_approval='Selected authentic Greek museum reproductions directly delivered under existing scope',copyright_holder_license='Not independently obtained',rights_status='restricted'))
def deliver():
 checked=b.target();shutil.copyfile(E/'cloud-sql-backup.json',E/'cloud-backup.json');i.upload(B)
 if not(i.folder(B)/'applied/000.json').exists():h.save(E/'production-target-before-image-write.json',b.target());i.apply(B)
if __name__=='__main__':
 with (b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);dict(prepare=prepare,deliver=deliver)[sys.argv[1]]()
