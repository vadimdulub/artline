#!/usr/bin/env python3
"""Bounded source prefetch only; never bypasses human visual-review decisions."""
import argparse,fcntl,importlib.util,subprocess,sys,time,os
from pathlib import Path
s=importlib.util.spec_from_file_location('images',Path(__file__).with_name('illustrated-300k-20261011.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
def main(provider,start):
 i.DATA.mkdir(parents=True,exist_ok=True)
 with (i.DATA/(provider+'-prefetch.lock')).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if Path('/usr/bin/caffeinate').exists():subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for folder in sorted((i.RUN/'batches').glob(provider+'-*')):
   number=int(folder.name.rsplit('-',1)[-1])
   if number<start or (folder/'preparation-summary.json').exists():continue
   while True:
    if (i.RUN/'stop-prefetch.json').exists():print('Requested target/inspection checkpoint; stopping source prefetch',flush=True);return
    assert not (i.RUN/'access-holds'/(i.CFG[provider]['host']+'.json')).exists(),'Source surface held'
    pending=[p for p in (i.RUN/'batches').glob(provider+'-*/preparation-summary.json') if not (p.parent/'verification.json').exists()]
    if len(pending)<4:break
    print(provider,'waiting for visual review and verification of',len(pending),'prepared batches',flush=True);time.sleep(30)
   with i.m.m.connect() as db:count=i.coverage(db)['qualifying_illustrated']
   if count>=i.TARGET:print('Illustrated-artwork target reached; stopping prefetch',flush=True);return
   print('Preparing',folder.name,'qualifying illustrated',count,flush=True)
   subprocess.run([sys.executable,str(Path(__file__).with_name('illustrated-300k-20261011.py')),'prepare','--batch',folder.name],check=True)
   summary=i.m.load(folder/'preparation-summary.json')['counts'];assert summary.get('held',0)<=max(20,sum(summary.values())//20),'More than 5% of source downloads failed; investigate before continuing'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('provider',choices=['rijks','nga']);p.add_argument('--start',type=int,default=1);a=p.parse_args();main(a.provider,a.start)
