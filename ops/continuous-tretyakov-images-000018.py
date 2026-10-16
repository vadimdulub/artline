#!/usr/bin/env python3
"""Selected exact Greek object images via established native-image workflow."""
import importlib.util,sys,shutil,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
b=mod('greek','continuous-tretyakov-batch-000018.py');h=b.h;E=b.E;i=mod('images','illustrated-300k-20261011.py');B='tretyakov-000'
i.OP=h.OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/h.OP;i.BACKUP=h.BACKUP
IID=b.IID
i.CFG['tretyakov']=dict(mid=IID,scheme='museum-native-tretyakov-object',name=b.MUSEUM,rights='restricted',license='Museum reproduction; no independent copyright-holder licence asserted',policy='https://www.tretyakovgallery.ru/about/copirith/',host='cdn.tretyakov.ru',limit=3)
def connect(write=False,local=False):
 assert not local;db=h.connect(write);db.autocommit=False;return db
i.m.m.connect=connect
old=i.m.uid;i.m.uid=lambda key:h.uid('source/tretyakov/'+b.MUSEUM) if key=='source/tretyakov' else old(key)
def source_image(r):
 import re,json
 from bs4 import BeautifulSoup
 raw=(ROOT/r['evidence_file']).read_text();soup=BeautifulSoup(raw,'html.parser');thumb=soup.select_one('img[alt="'+r['title']+'"]')['src'];name=thumb.rsplit('/',1)[-1].split('_x')[0]+'.jpg'
 candidates=[json.loads('"'+x+'"') for x in re.findall(r'"(https:[^"\n]+)"',raw) if name in x and '\\u002Fthumb\\u002F' not in x]
 candidates=list(dict.fromkeys(candidates));assert len(candidates)==1 and candidates[0].endswith('/'+name)
 prior=h.load(E.parent/'000017/tretyakov-route-verification.json');lead=next(x for x in prior['icon_related_metadata_leads'] if x['source_id']==r['source_id']);assert candidates[0].replace('/','\\u002F') in lead['evidence_excerpt']
 h.save(E/'native-image-identity.json',dict(at=h.now(),source_id=r['source_id'],accession=r['accession_number'],title=r['title'],thumbnail_url=thumb,primary_original_url=candidates[0],source_sha256=r['evidence']['sha256'],basis='Exact official object SSR contains this original URL; prior official collection record explicitly assigns it as pictureBig. Thumbnail not substituted.'))
 return candidates[0]

def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return
 plan,pin=h.pinned(b.PHASE);rows=[]
 for r in plan['records']:
  if r['date_decision']!='eligible' or (r['before'] and r['before']['artwork']['primary_media_id']):continue
  assert r['last']<=1955
  rows.append(dict(artwork_id=r['artwork_id'],provider='tretyakov',native_id=r['source_id'],title=r['title'],creator_label=r['creator_label'] or 'Anonymous / maker not supplied by source',source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type=r['source_type'],plan_sha256=pin,expected_primary_artist_id=r['artist_id'],image=dict(image_url=source_image(r),source=r,receipt=r['evidence']),rights_basis='Selected official Russian museum reproduction under docs/ARTLINE_IMAGE_USE.md Russian museum extension; explicit XVII century creation before 1955. Actual museum restriction retained separately from user approval, which is not a copyright-holder licence.'))
 i.saved(i.folder(B)/'selection.json.gz',dict(provider='tretyakov',batch=B,rows=rows));i.saved(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 i.ORIG.mkdir(parents=True,exist_ok=True)
 for r in rows:print(i.prepare_one(r,B)['state'])
 i.audit(B)
 h.save(E/'image-authorization.json',dict(at=h.now(),policy='docs/ARTLINE_IMAGE_USE.md#explicit-russian-museum-extension--21-september-2026',scope='One anonymous XVII century official icon, inventory ДР-305',user_approval='Selected authentic Russian museum reproductions directly delivered under existing scope',copyright_holder_license='Not independently obtained',rights_status='restricted'))
def deliver():
 checked=b.prior.target();shutil.copyfile(E/'cloud-sql-backup.json',E/'cloud-backup.json');i.upload(B)
 if not(i.folder(B)/'applied/000.json').exists():h.save(E/'production-target-before-image-write.json',b.prior.target());i.apply(B)
if __name__=='__main__':
 with (b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);dict(prepare=prepare,deliver=deliver)[sys.argv[1]]()
