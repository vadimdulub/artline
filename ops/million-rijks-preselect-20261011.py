#!/usr/bin/env python3
"""Prepare bounded source selections while production authentication is pending.

Offline only: reads already captured museum pages, never opens a database and
never downloads artwork images. Production reconciliation remains mandatory.
"""
import argparse,fcntl,importlib.util,os,subprocess,time
from pathlib import Path
s=importlib.util.spec_from_file_location('continuation',Path(__file__).with_name('million-rijks-continue-20261010.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c);m=c.m
def main(start):
 with (m.DATA/'rijks/preselection.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if Path('/usr/bin/caffeinate').exists():subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for first,last in c.source_windows():
   if first<start:continue
   dest=c.r.RUN/f'selection-{first:05d}-{last:05d}-v3.json.gz'
   if dest.exists():continue
   receipt=m.RUN/'sources/rijks/pages'/f'{last-1:05d}.xml.receipt.json'
   while not receipt.exists():
    if (m.RUN/'target-reached.json').exists():return
    assert not (m.RUN/'access-holds/data.rijksmuseum.nl.json').exists(),'Source access held'
    time.sleep(30)
   c.r.selection(first,last)
  print('All captured source windows selected; production reconciliation and verification still required.',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=4000);a=p.parse_args();main(a.start)
