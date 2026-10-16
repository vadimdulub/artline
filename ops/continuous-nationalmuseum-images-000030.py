#!/usr/bin/env python3
"""One selected Nationalmuseum public-media-portal reproduction; direct-source hold preserved."""
import importlib.util,inspect,json,gzip,sys,fcntl,shutil
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-nationalmuseum-batch-000030.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.base.i;E=b.E;B='nationalmuseum-000'
i.OP=h.OP+'-images';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
MID='3dd937e8-ac85-4b50-8b55-c45034c1a18e'
i.CFG['nationalmuseum']=dict(mid=MID,scheme='nationalmuseum-object',name='Nationalmuseum',rights='public_domain',license='Public Domain',policy='https://creativecommons.org/publicdomain/mark/1.0/',host='media.nationalmuseum.se')
old=i.m.uid;i.m.uid=lambda key:h.uid('source/nationalmuseum/Nationalmuseum') if key=='source/nationalmuseum' else old(key)
# Preserve exact photographer credit in addition to source label.
code=inspect.getsource(i.apply);needle="    credit=(r['creator_label']+'. ' if r['creator_label'] else '')+(credits.get(aid,'')+'. ' if credits.get(aid) else '')+cfg['name']+'. '+license+'.'";assert needle in code
code=code.replace(needle,"    credit=r['source_credit']+'. '+license+'.'");exec(compile(code,__file__,'exec'),i.__dict__)
def capture(name):
 rp=E/'source-captures'/(name+'.receipt.json');rc=h.load(rp);bp=rp.with_name(name+'.body.gz');raw=gzip.decompress(bp.read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256'];return json.loads(raw),dict(rc,body_path=str(bp.relative_to(b.ROOT)))
def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return
 plan,pin=h.pinned(b.PHASE);r=next(x for x in plan['records'] if x['source_id']=='26466');o=h.load(E/'objects/26466.json');m,rc=capture('media-102922');props=m['properties'];assert m['id']==102922
 assert props['inventarienummer']['value']==[o['ObjInventoryNumberTxt']]==['NMI 148']
 assert props['titel_en']['value']==[r['title']] and props['titel']['value']==[o['ObjTitleMainTxt_sv']] and props['konstnar']['value']==['Okänd']
 assert props['licens']['value']=='Public Domain' and props['photocreditline']['value']=='Foto: Heiko Arens / Nationalmuseum'
 fm=next(v for v in m['downloadables'] if v['templateName']=='Full JPEG');assert fm['dimensions']=='1644x2513 px'
 row=dict(artwork_id=r['artwork_id'],native_id=r['source_id'],title=r['title'],creator_label=r['creator_label'],source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type='painting',provider='nationalmuseum',image=dict(image_url='https://media.nationalmuseum.se'+fm['url'],source=m,receipt=rc),plan_sha256=pin,source_credit=props['photocreditline']['value'],rights_basis='Exact official media portal item 102922 explicitly labels this image Public Domain, credits Heiko Arens / Nationalmuseum, and matches museum inventory NMI 148, both titles and Unknown maker. Museum object separately assigns the same photographer and Public Domain. Direct collection-host image hold remains; this is the officially linked, unauthenticated separate media portal.')
 h.save(i.folder(B)/'selection.json.gz',dict(provider='nationalmuseum',batch=B,rows=[row],metadata_first=True));h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 im=i.prepare_one(row,B);assert im['state']=='prepared',im; i.audit(B);print(json.dumps(dict(path=im['path'],artwork_id=r['artwork_id'],sha256=im['sha256'],bytes=im['bytes'])))
def deliver():
 b.save('production-target-before-storage-write.json',b.base.target(True));shutil.copyfile(E/'cloud-sql-backup.json',E/'cloud-backup.json');i.upload(B)
 b.save('production-target-before-image-write.json',b.base.target(True));i.apply(B)
if __name__=='__main__':
 with (b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
