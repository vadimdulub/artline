#!/usr/bin/env python3
"""Research orchestration and read-only quality checks for twenty batches."""
import importlib.util,sys,time,collections,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 sp=importlib.util.spec_from_file_location(name,ROOT/file);v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);return v
d=module('twenty_delivery','ops/random-ten-twenty-batches-delivery-20261010.py');b=d.b;m=d.m;s=d.s;r=d.r;q=d.q;RUN=d.RUN;BACKUP=d.BACKUP
x=module('previous_helpers','ops/run-random-200-round6-20261007.py')
x.d=d;x.s=s;x.m=m;x.r=r;x.q=q;x.RUN=RUN;x.BACKUP=BACKUP;x.PRIOR_RUNS=[ROOT/'docs/research/vyzantios-random-ten-20261010']
v=module('previous_quality','ops/review-random-200-painters-round6-20261007.py');v.x=x;v.r=r;v.RUN=RUN

def pipeline():
 while not (RUN/'indexes-summary.json').exists():time.sleep(10)
 x.index_gaps()
 while not (RUN/'translations-summary.json').exists():time.sleep(10)
 while True:
  finished=(RUN/'pages-summary.json').exists()
  if finished:x.retry_pages()
  s.select();d.prepare();d.audits();d.sheets()
  selected=len(list((RUN/'selections').glob('*.json.gz')))
  m.status('pipeline',selected_artists=selected,research_done=finished)
  if finished and selected==200:
   print('All 200 selections and image preparations complete; visual and source-quality review pending.',flush=True);return
  time.sleep(15)

def quality():v.scan(True)
def quality_progress():v.scan(False)
def gaps():x.index_gaps()
def retries():x.retry_pages()
def cross():x.cross_creator_audit()
def preflight():x.preflight()
if __name__=='__main__':globals()[sys.argv[1]]()
