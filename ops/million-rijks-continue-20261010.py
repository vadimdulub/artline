#!/usr/bin/env python3
"""Continue authorized Rijks metadata expansion in verified, resumable windows.

No images are downloaded here. Source holds and failed integrity checks stop work.
"""
import argparse,fcntl,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
b=module('bulk','million-bulk-import-20261010.py');r=module('rijks','million-rijks-20261010.py');m=b.m
def run(script,*args):
 command=[sys.executable,str(Path(__file__).with_name(script)),*args]
 subprocess.run(command,check=True)
def source_windows():
 token=r.ET.parse(m.DATA/'rijks/ListRecords.xml').find('.//o:resumptionToken',r.NS)
 pages=(int(token.get('completeListSize'))+49)//50
 windows=[(0,1000),(1000,2000)]+[(i,min(i+500,pages)) for i in range(2000,pages,500)]
 # completeListSize can change during a long harvest. Preserve every pinned
 # window and append the captured tail only when the final token confirms EOF.
 captured=sorted((m.DATA/'rijks/pages').glob('*.xml'))
 if captured:
  last=int(captured[-1].stem)+1
  end=r.ET.parse(captured[-1]).find('.//o:resumptionToken',r.NS)
  if last>pages and (end is None or not (end.text or '').strip()):
   assert all((m.DATA/'rijks/pages'/(str(i).zfill(5)+'.xml')).exists() for i in range(pages,last))
   windows.extend((i,min(i+500,last)) for i in range(pages,last,500))
 return windows
def record_target(count):
 path=m.RUN/'target-reached.json'
 if not path.exists():m.save(path,dict(at=m.now(),qualifying_active_artworks=count,method='Read-only production count of non-archived artwork records after completed, independently verified source windows, minus explicit Rijksmuseum verso views and visually confirmed NGA duplicate pairs while both records remain active. Review records remain preserved and do not inflate this target.'))
def active_count():
 for attempt in range(20):
  try:return active_count_once()
  except b.OperationalError as error:
   state=error.sqlstate
   if attempt==19 or state and not (state.startswith('08') or state in ('57P01','57P02','57P03')):raise
   print('Progress count connection interrupted; retrying read-only query.',flush=True);time.sleep(5)
def active_count_once():
 with m.m.connect() as db:
  raw=db.execute("SELECT count(*) n FROM artworks WHERE status<>'archived'").fetchone()['n']
  views=db.execute("SELECT count(*) n FROM artworks WHERE status<>'archived' AND current_institution_id=%s AND accession_number ~* '\\((V|VERSO)\\)[[:space:]]*$'",(r.MID,)).fetchone()['n']
  review=m.RUN/'nga/duplicate-followup-visual-review.json';duplicates=0
  if review.exists():
   pairs=[v for v in m.load(review)['decisions'] if v['decision']=='same_painting'];assert len({v['new_id'] for v in pairs})==len(pairs)
   duplicates=db.execute("SELECT count(*) n FROM unnest(%s::uuid[],%s::uuid[]) p(new_id,existing_id) JOIN artworks a ON a.id=p.new_id JOIN artworks old ON old.id=p.existing_id WHERE a.status<>'archived' AND old.status<>'archived'",([v['new_id'] for v in pairs],[v['existing_id'] for v in pairs])).fetchone()['n']
  return raw-views-duplicates
def complete(folder):
 p=folder/'full-verification.json'
 if not p.exists():return False
 v=m.load(p);assert not v['failures']
 assert all(v['checks'][key]==v['expected_artworks'] for key in ['artworks','citations','artwork_location_assertions','matching_search_documents','native_identity_checks'])
 return True
def main(start):
 lockpath=m.DATA/'rijks/continuation.lock';lockpath.parent.mkdir(parents=True,exist_ok=True)
 with lockpath.open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  # Keep this explicitly requested long-running job awake; the assertion ends
  # automatically when this controller exits, without changing system settings.
  if Path('/usr/bin/caffeinate').exists():subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  windows=source_windows()
  for first,last in windows:
   if first<start:continue
   phase=str(first).zfill(5)+'-'+str(last).zfill(5);folder=m.RUN/'rijks'/phase
   if complete(folder):continue
   count=active_count();print(json.dumps(dict(at=m.now(),phase=phase,active_artworks=count,remaining=max(0,m.TARGET-count))),flush=True)
   if count>=m.TARGET:
    record_target(count)
    return
   end_receipt=m.RUN/'sources/rijks/pages'/(str(last-1).zfill(5)+'.xml.receipt.json')
   while not end_receipt.exists():
    hold=m.RUN/'access-holds/data.rijksmuseum.nl.json'
    assert not hold.exists(),'Rijksmuseum source access held; operator review required'
    print('Waiting for captured metadata through page',last-1,flush=True);time.sleep(30)
   run('million-rijks-20261010.py',str(first),str(last))
   run('million-bulk-import-20261010.py','plan','rijks','--phase',phase)
   plan=m.load(folder/'plan.json.gz');excluded_path=b.execution_exclusions(folder);excluded={x['artwork_id'] for x in m.load(excluded_path)['rows']} if excluded_path.exists() else set()
   for row in plan['new_artworks']:
    if row['artwork_id'] in excluded:continue
    assert row['last']<=1970 and not (row['last']==1970 and 'circa' in row['precision'])
    assert (row['first'],row['last'],row['precision'])==r.date(row['date_display'])
    assert not b.source_chronology_conflicts(row)
   run('million-bulk-import-20261010.py','apply','rijks','--phase',phase)
   run('million-verify-20261010.py','rijks','--phase',phase)
   assert complete(folder)
  count=active_count()
  if count>=m.TARGET:record_target(count)
  else:print('Available bounded harvest windows exhausted before target; additional source review required. Qualifying artworks:',count,flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--start',type=int,default=1000);a=ap.parse_args();main(a.start)
