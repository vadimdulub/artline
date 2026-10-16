#!/usr/bin/env python3
"""Research orchestration and read-only quality checks for twenty batches."""
import importlib.util,sys,time,collections,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 sp=importlib.util.spec_from_file_location(name,ROOT/file);v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);return v
d=module('twenty_delivery','ops/random-ten-twenty-batches-round2-delivery-20261011.py');b=d.b;m=d.m;s=d.s;r=d.r;q=d.q;RUN=d.RUN;BACKUP=d.BACKUP
x=module('previous_helpers','ops/run-random-200-round6-20261007.py')
x.d=d;x.s=s;x.m=m;x.r=r;x.q=q;x.RUN=RUN;x.BACKUP=BACKUP;x.PRIOR_RUNS=[(ROOT/entry['path']).parent for entry in r.load(RUN/'sampling-frame.json.gz')['prior_cohorts']]
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
def components():
 rows=[]
 for plan,pin in d.plans():
  for row in plan['rows']:
   if row['action'] in ['create','existing'] and re.search(r'\b(wing|wings|central section|(?:central|centre|center|outside|inside)(?: (?:left|right))? panel|side panel|side panels|rear|reverse|recto|verso|predella|detail|fragment)\b',row['title'],re.I):
    rows.append(dict(artist=plan['artist']['display_name'],artwork_id=row['artwork_id'],title=row['title'],source_url=row['source_url'],action=row['action'],source_fields=row['page']['fields']))
 m.status('component-candidates',painters=len(list(d.plans())),rows=rows)
 print('Component/view title candidates:',len(rows),flush=True)
def gaps():x.index_gaps()
def retries():x.retry_pages()
def cross():
 # Two excluded low-count cohorts delivered metadata only, with no image plans.
 metadata_only={'low-count-200-painters-20261008','low-count-200-painters-round2-20261009'}
 original=x.PRIOR_RUNS
 for folder in original:
  if folder.name in metadata_only:
   assert 'no new images were uploaded or attached' in (folder/'README.md').read_text().lower() or 'no catalogue images were uploaded or attached' in (folder/'README.md').read_text().lower()
 x.PRIOR_RUNS=[folder for folder in original if folder.name not in metadata_only]
 x.cross_creator_audit()
 r.save(RUN/'cross-creator-comparison-scope.json',{'at':r.now(),'prior_cohorts_excluded_from_artist_sample':len(original),'prior_image_cohorts_compared':[str(p.relative_to(ROOT)) for p in x.PRIOR_RUNS],'metadata_only_cohorts_without_delivered_images':sorted(metadata_only)})
def preflight():module('round2_checks','ops/random-ten-twenty-batches-round2-checks-20261011.py').preflight()
if __name__=='__main__':globals()[sys.argv[1]]()
