#!/usr/bin/env python3
"""Resume audited image delivery; visual decisions are supplied independently.

Each mode has one process lock. Audit only prepares evidence/contact sheets.
Delivery only runs batches with an explicit, checksum-bound visual decision.
"""
import argparse,fcntl,importlib.util,os,subprocess,sys,time
from pathlib import Path
s=importlib.util.spec_from_file_location('images',Path(__file__).with_name('illustrated-300k-20261011.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
def run(action,batch):
 subprocess.run([sys.executable,str(Path(__file__).with_name('illustrated-300k-20261011.py')),action,'--batch',batch],check=True)
def main(mode,start):
 i.DATA.mkdir(parents=True,exist_ok=True)
 with (i.DATA/(mode+'-controller.lock')).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if Path('/usr/bin/caffeinate').exists():subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  if mode=='wikiart':
   for index in range(start,18):
    if (i.RUN/'stop-prefetch.json').exists():return
    batch='wikiart-'+str(index).zfill(3)
    while len([p for p in (i.RUN/'batches').glob('wikiart-*/preparation-summary.json') if not (p.parent/'verification.json').exists()])>=3:
     if (i.RUN/'stop-prefetch.json').exists():return
     time.sleep(20)
    with i.m.m.connect() as db:count=i.coverage(db)['qualifying_illustrated']
    if count>=i.TARGET:return
    subprocess.run([sys.executable,str(Path(__file__).with_name('illustrated-300k-wikiart-20261011.py')),'--index',str(index)],check=True)
    if not (i.folder(batch)/'preparation-summary.json').exists():run('prepare',batch)
   return
  while True:
   if (i.RUN/('stop-'+mode+'.json')).exists():return
   pending=[p.parent for p in sorted((i.RUN/'batches').glob('*/preparation-summary.json')) if not (p.parent/'verification.json').exists()]
   progressed=False
   for folder in pending:
    batch=folder.name
    if mode=='audit':
     if not (folder/'quality-audit.json').exists():run('audit',batch);progressed=True
     continue
    if not (folder/'visual-review.json').exists():continue
    images,_,_=i.accepted(batch)
    with i.m.m.connect() as db:count=i.coverage(db)['qualifying_illustrated']
    # Always finish verification of an already-started batch.
    if count>=i.TARGET and not any((folder/'applied').glob('*.json')):
     if not (i.RUN/'stop-prefetch.json').exists():i.saved(i.RUN/'stop-prefetch.json',dict(at=i.m.now(),reason='Production qualifying illustration target reached; root final verification pending.'))
     return
    print('Delivering reviewed batch',batch,'accepted',len(images),'qualifying illustrated',count,flush=True)
    run('upload',batch);run('apply',batch);run('verify',batch);progressed=True
   if not progressed:time.sleep(20)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['audit','deliver','wikiart']);p.add_argument('--start',type=int,default=2);a=p.parse_args();main(a.mode,a.start)
