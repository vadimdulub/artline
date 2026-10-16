#!/usr/bin/env python3
"""Continue reviewed museum metadata after the running Rijks source pass.

Plans are generated against fresh production state immediately before each
source is applied. Any identity, source or verification failure stops the chain.
"""
import fcntl,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
s=importlib.util.spec_from_file_location('controller',Path(__file__).with_name('million-rijks-continue-20261010.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c);m=c.m

def main():
 with (m.DATA/'rijks/continuation.lock').open('a+') as lock:
  while True:
   try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
   except BlockingIOError:print('Waiting for the active Rijks controller to finish its verified windows.',flush=True);time.sleep(30)
  if Path('/usr/bin/caffeinate').exists():subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  count=c.active_count()
  if count>=m.TARGET:
   assert (m.RUN/'target-reached.json').exists(),'Verify the final running source before declaring success'
   return
  pending=[(first,last) for first,last in c.source_windows() if not c.complete(m.RUN/'rijks'/(str(first).zfill(5)+'-'+str(last).zfill(5)))]
  assert not pending,'Rijks controller stopped before all source windows verified: '+str(pending)
  for provider in ['moma','aic']:
   count=c.active_count();print(json.dumps(dict(at=m.now(),next_source=provider,qualifying_active_artworks=count,remaining=max(0,m.TARGET-count))),flush=True)
   if count>=m.TARGET:c.record_target(count);return
   # Earlier read-only phase 001 estimates remain audit evidence. Reconcile
   # phase 002 only after previous source mutations have finished.
   phase='002';folder=m.RUN/provider/phase
   if c.complete(folder):continue
   c.run('million-bulk-import-20261010.py','plan',provider,'--phase',phase)
   plan=m.load(folder/'plan.json.gz')
   assert all(r['last']<=1970 and not (r['last']==1970 and 'circa' in r['precision']) and not c.b.source_chronology_conflicts(r) for r in plan['new_artworks'])
   c.run('million-bulk-import-20261010.py','apply',provider,'--phase',phase)
   c.run('million-verify-20261010.py',provider,'--phase',phase);assert c.complete(folder)
  count=c.active_count()
  if count>=m.TARGET:c.record_target(count)
  else:print('Reviewed museum sources exhausted; additional source selection required. Qualifying artworks:',count,flush=True)

if __name__=='__main__':main()
