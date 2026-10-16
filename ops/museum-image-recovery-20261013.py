#!/usr/bin/env python3
"""Serial museum artwork image-recovery supervisor. No database access itself."""
import argparse, datetime, fcntl, hashlib, json, os, pathlib, shutil, subprocess, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/'docs/research/museum-image-recovery-20261013/runtime'
REPORT=ROOT/'docs/research/museum-image-recovery-20261013'
PROMPT=ROOT/'docs/MUSEUM_IMAGE_RECOVERY_PROMPT.md'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p, default=None): return json.loads(p.read_text()) if p.exists() else default
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def schema():
 fields={k:{'type':'integer','minimum':0} for k in ('artworks_checked','newly_illustrated','held_without_image')}
 props={'outcome':{'type':'string','enum':['progress','blocked','no_eligible_candidates']},'summary':{'type':'string'},'next_task':{'type':'string'},'blocker':{'type':'string'},'verified_counts':{'type':'object','properties':fields,'required':list(fields),'additionalProperties':False},'evidence_paths':{'type':'array','items':{'type':'string'}}}
 return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}
def result_valid(result):
 assert result['outcome'] in ('progress','blocked','no_eligible_candidates')
 assert all(type(v) is int and v>=0 for v in result['verified_counts'].values())
 if any(result['verified_counts'].values()):
  assert result['evidence_paths'],'Delivered counts require evidence'
 for name in result['evidence_paths']:
  p=pathlib.Path(name);p=p if p.is_absolute() else ROOT/p
  assert p.is_file(), 'Missing evidence: '+str(p)
 return result
def journal_result(receipt):
 # Workers occasionally persist the schema result directly in the evidence
 # directory before the supervisor writes its checksum wrapper. Accept both
 # shapes so a completed production delivery is reconciled rather than rerun.
 return receipt.get('result', receipt)
TASKS=['Museum object-page recovery']
def prompt_for(number,previous):
 return PROMPT.read_text()+f"""
Iteration {number} of 1000. Execute ONE bounded iteration, checking up to 10 distinct previously unchecked museum-held artworks without primary images. External supervisor handles continuation; do not launch other workers or modify supervisor/prompt. Evidence: {REPORT}/batches/{number:06d}/. Runtime: {DATA}/batches/{number:06d}/. Previous result: {json.dumps(previous)}. Read all prior checked-artwork IDs in this campaign receipts before selection; maintain source-queue.json with IDs, museum cursors and holds. Reconcile interrupted writes first. Save checked-artworks.json with exact internal IDs, museum URLs, object/accession evidence and per-object outcome. Include it in evidence_paths. Only count distinct actually researched records. Output the supplied JSON schema, with artworks_checked, newly_illustrated and held_without_image counts. Never count a retry or unchanged blocked search as a new iteration. When no distinct records can be checked, return blocked.
"""

def run():
 DATA.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
 with (DATA/'supervisor.lock').open('a+') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:
   # A surviving worker retains this lock after a supervisor crash. Wait for
   # it rather than starting a duplicate or disabling durable continuation.
   fcntl.flock(lock,fcntl.LOCK_EX)
  if (DATA/'STOP').exists() or (DATA/'PAUSE').exists():return
  state=read(DATA/'state.json',{'started_at':now(),'next_batch':1,'failures':0,'totals':{k:0 for k in schema()['properties']['verified_counts']['properties']}})
  save(DATA/'schema.json',schema())
  caffeinate=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())])
  try:
   while state['next_batch'] <= 1000 and not (DATA/'STOP').exists() and not (DATA/'PAUSE').exists():
    n=state['next_batch'];folder=DATA/'batches'/f'{n:06d}';folder.mkdir(parents=True,exist_ok=True)
    # A result journal is committed before state advances. Replay it once after a crash.
    journal=REPORT/'batches'/f'{n:06d}'/'worker-result.json'
    if journal.exists():
     receipt=read(journal);result=result_valid(journal_result(receipt))
     for k,v in result['verified_counts'].items():state['totals'][k]+=v
     state['previous']=result;state['next_batch']=n+1;state.pop('inflight',None)
     state['failures']=state['failures']+1 if result['outcome']=='blocked' else 0
     state['last_error']=result['blocker']
     if state['failures']>=3:save(DATA/'PAUSE',{'at':now(),'reason':result['blocker']})
     save(DATA/'state.json',state);save(REPORT/'CHECKPOINT.json',state);continue
    attempt=len(list(folder.glob('attempt-*.jsonl')))+1
    result_path=folder/f'result-{attempt:03d}.json'
    previous=state.get('previous',{})
    if state.get('inflight'):previous=dict(previous,recovery_required=state['inflight'])
    text=prompt_for(n,previous);(folder/f'prompt-{attempt:03d}.txt').write_text(text)
    state['inflight']={'batch':n,'attempt':attempt,'started_at':now(),'result_path':str(result_path)}
    state.update(status='running',supervisor_pid=os.getpid(),heartbeat_at=now())
    save(DATA/'state.json',state);save(REPORT/'CHECKPOINT.json',state)
    command=[shutil.which('codex') or '/opt/homebrew/bin/codex','exec','--json','--color','never','-s','danger-full-access','-c','approval_policy="never"','-C',str(ROOT),'--output-schema',str(DATA/'schema.json'),'-o',str(result_path),'-']
    with (folder/f'attempt-{attempt:03d}.jsonl').open('w') as log:
     child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=log,text=True,cwd=ROOT,pass_fds=(lock.fileno(),))
     child.stdin.write(text);child.stdin.close()
     state['worker_pid']=child.pid
     save(DATA/'state.json',state);save(REPORT/'CHECKPOINT.json',state)
     while child.poll() is None:
      state['heartbeat_at']=now();save(DATA/'state.json',state);save(REPORT/'CHECKPOINT.json',state)
      elapsed=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(state['started_at'])).total_seconds()
      hour=int(elapsed//3600)
      if hour>state.get('last_hourly_report',0):
       save(REPORT/'hourly'/f'{hour:06d}.json',dict(at=now(),elapsed_hours=elapsed/3600,verified_totals=state['totals'],inflight=state['inflight'],milestone_100h=hour>=100,source_queue=read(REPORT/'source-queue.json',{}),previous_result=state.get('previous',{})))
       state['last_hourly_report']=hour;save(DATA/'state.json',state)
      time.sleep(15)
     code=child.returncode
    try:
     assert code==0, f'Worker exit {code}; see attempt log'
     result=result_valid(read(result_path));assert result is not None
     if result['outcome'] != 'blocked':
      checked=read(REPORT/'batches'/f'{n:06d}'/'checked-artworks.json')
      assert isinstance(checked,list) and checked, 'Missing actually checked objects'
      ids=[r['artwork_id'] for r in checked]
      prior=set()
      for old in (REPORT/'batches').glob('*/worker-result.json'):
       if old.parent == REPORT/'batches'/f'{n:06d}':continue
       for row in read(old.parent/'checked-artworks.json',[]):prior.add(row['artwork_id'])
      assert len(ids)==len(set(ids)) and not prior.intersection(ids), 'Repeated coverage rejected'
      assert result['verified_counts']['artworks_checked']==len(ids), 'Coverage mismatch'
     else:
      raise RuntimeError('Blocked iteration is checkpointed but does not count toward 1000: '+result['blocker'])
     receipt={'batch':n,'attempt':attempt,'finished_at':now(),'result':result,'result_sha256':digest(result_path),'prompt_sha256':digest(folder/f'prompt-{attempt:03d}.txt')}
     save(REPORT/'batches'/f'{n:06d}'/'worker-result.json',receipt)
     state['previous']=result;state.pop('inflight',None);state.pop('worker_pid',None)
     for k,v in result['verified_counts'].items():state['totals'][k]+=v
     state['next_batch']=n+1
     state['failures']=state['failures']+1 if result['outcome']=='blocked' else 0
     state['last_error']=result['blocker']
    except Exception as exc:
     state['failures']+=1;state['last_error']=str(exc);state['status']='retry_pending'
    if state['failures']>=3:
     state['status']='paused';save(DATA/'PAUSE',{'at':now(),'reason':state['last_error'],'consecutive_failures':state['failures']})
    state['heartbeat_at']=now();save(DATA/'state.json',state);save(REPORT/'CHECKPOINT.json',state)
    if state['failures']==0 and not any(state.get('previous',{}).get('verified_counts',{}).values()):
     for _ in range(4):
      if (DATA/'STOP').exists() or (DATA/'PAUSE').exists():break
      time.sleep(15)
    if state['failures'] and state['failures']<3:
     for _ in range(20*state['failures']):
      if (DATA/'STOP').exists() or (DATA/'PAUSE').exists():break
      time.sleep(15)
   state['status']='complete' if state['next_batch'] > 1000 else ('paused' if (DATA/'PAUSE').exists() else 'stopped');save(DATA/'state.json',state);save(REPORT/'CHECKPOINT.json',state)
  finally:caffeinate.terminate()
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['run','status','stop','resume','self-test']);a=p.parse_args()
 if a.action=='run':run()
 elif a.action=='status':print(json.dumps(read(DATA/'state.json',{'status':'not_started'}),indent=2))
 elif a.action=='stop':save(DATA/'STOP',{'at':now(),'reason':'User requested graceful stop after current batch'})
 elif a.action=='resume':
  for name in ('STOP','PAUSE'):(DATA/name).unlink(missing_ok=True)
  state=read(DATA/'state.json')
  if state:state['failures']=0;save(DATA/'state.json',state)
 elif a.action=='self-test':
  import tempfile
  with tempfile.TemporaryDirectory(prefix='artline-supervisor-') as tmp:
   f=pathlib.Path(tmp)/'checkpoint.json';save(f,{'inflight':{'batch':1}});assert read(f)['inflight']['batch']==1
   save(f,{'next_batch':2});assert read(f)=={'next_batch':2} and not f.with_suffix('.json.tmp').exists()
   zero={k:0 for k in schema()['properties']['verified_counts']['properties']}
   result_valid({'outcome':'progress','verified_counts':zero,'evidence_paths':[]})
   try:result_valid({'outcome':'progress','summary':'','next_task':'','blocker':'','verified_counts':dict(zero,newly_illustrated=1),'evidence_paths':[]})
   except AssertionError:pass
   else:raise AssertionError('Missing delivery evidence accepted')
   assert len(TASKS)==1 and 'ONE bounded iteration' in prompt_for(1,{})
   assert journal_result({'result':{'outcome':'progress'}})['outcome']=='progress'
   assert journal_result({'outcome':'progress'})['outcome']=='progress'
  print('PASS: atomic checkpoint/recovery, evidence gate, serial task rotation and bounded worker prompt; no database or network writes')
if __name__=='__main__':main()
