#!/usr/bin/env python3
"""Serial, checkpointed Codex research supervisor. No database access itself."""
import argparse, datetime, fcntl, hashlib, json, os, pathlib, shutil, subprocess, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=pathlib.Path.home()/'Library/Application Support/Artline/continuous-research'
REPORT=ROOT/'docs/research/continuous-production-20261011'
PROMPT=ROOT/'docs/INFINITE_RESEARCH_PROMPT.txt'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p, default=None): return json.loads(p.read_text()) if p.exists() else default
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def schema():
 fields={k:{'type':'integer','minimum':0} for k in ('new_painters','new_artworks','newly_illustrated','alternate_images','museum_links')}
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
TASKS=[
 'Inspect the 188 remaining prepared French printmaking reserve records. Select up to 25 genuinely unimported eligible objects, reconcile them against current production, verify the original source and checksum-bound visual decisions, and deliver and independently verify a new supplement using the existing production workflow. Do not alter immutable historical plans. If a reserve object is held, skip it. Reuse existing source IDs and artwork UUIDs. If reserve cannot proceed, switch to another registry-backed task.',
 'Select a bounded batch of existing primary-image gaps from a permitted registry museum or WikiArt. Reconcile exact identities, perform required actual visual review, and attach and verify up to 100 authentic primary images. Respect completed campaign stop files: use a separate continuation campaign, not a restarted target-complete job.',
 'Select and research up to 50 distinct eligible artworks and their creators from an undercovered registry institution, preferably Greek, Russian icon, Byzantine or post-Byzantine collections. Add verified production metadata, images where supported, and documented holdings. Directory entries are not artworks.'
]
def prompt_for(number,previous):
 task=TASKS[(number-1)%len(TASKS)]
 return PROMPT.read_text()+f'''\n\nBOUND SUPERVISOR WORKER INSTRUCTIONS (override indefinite execution within this individual batch):
An external supervisor already owns persistence and continuation. Execute ONE bounded batch, then return the required structured result. Do not create or launch another supervisor, schedule, Codex session or subagent. Do not edit this supervisor, its prompt, schema or LaunchAgent. Do not stop merely at a plan: perform the selected work when possible.
Batch: {number}. Evidence directory: {REPORT}/batches/{number:06d}/
Runtime directory: {DATA}/batches/{number:06d}/
Selected task: {task}
Previous result: {json.dumps(previous,ensure_ascii=False)}
Read {REPORT}/CHECKPOINT.json and {REPORT}/source-queue.json if present. Update the source queue for routes actually researched with exact evidence and resume cursors; preserve all unrelated entries. Select available undercovered routes rather than repeatedly revisiting exhausted or held sources. Treat previous next_task as recovery context; reconcile any uncertain earlier writes before new work. A previous in-flight attempt can have committed writes even without a final result.
Shared production ingestion lock: artline-curated-ingestion. Verify the Cloud SQL proxy target is artline-508319:europe-west1:artline-postgres (confirm the actual established configuration); inspect the existing proxy command and connection helper before writes. Use the production helper in ops/india-300-delivery-20261011.py or an equally verified established helper. Do not print secrets, tokens, connection strings or private account files.
Save a batch checkpoint and verification receipts before returning. Report only independently verified production increments attributable to this programme; do not count previous campaigns. Evidence paths must refer to actual verification files, not plans alone. Establish delivery attribution from persisted source citation/rights plan checksums and transaction preimages; a COMMITTED message or applied receipt can describe replay of another plan and does not prove new programme additions. Distinguish selected rows already inserted by other jobs and exclude them from increments. If no additions are possible, record the exact holds and a different next task. If account/authentication/budget or all available routes prevent work, return blocked. Do not repeatedly retry access-held providers.
For visual review use the available image viewing tools on actual prepared images/contact sheets; do not substitute file checks for looking at the image. Preserve existing immutable visual evidence when reusing already reviewed reserves, and explicitly cite that prior review.
Your final output must conform to the supplied JSON schema.
'''
def run():
 DATA.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
 with (DATA/'supervisor.lock').open('a+') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:return
  if (DATA/'STOP').exists() or (DATA/'PAUSE').exists():return
  state=read(DATA/'state.json',{'started_at':now(),'next_batch':1,'failures':0,'totals':{k:0 for k in schema()['properties']['verified_counts']['properties']}})
  save(DATA/'schema.json',schema())
  caffeinate=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())])
  try:
   while not (DATA/'STOP').exists() and not (DATA/'PAUSE').exists():
    n=state['next_batch'];folder=DATA/'batches'/f'{n:06d}';folder.mkdir(parents=True,exist_ok=True)
    # A result journal is committed before state advances. Replay it once after a crash.
    journal=REPORT/'batches'/f'{n:06d}'/'worker-result.json'
    if journal.exists():
     receipt=read(journal);result=result_valid(receipt['result'])
     for k,v in result['verified_counts'].items():state['totals'][k]+=v
     state['previous']=result;state['next_batch']=n+1;state.pop('inflight',None)
     state['failures']=state['failures']+1 if result['outcome']=='blocked' else 0
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
     child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=log,text=True,cwd=ROOT)
     child.stdin.write(text);child.stdin.close()
     state['worker_pid']=child.pid
     while child.poll() is None:
      state['heartbeat_at']=now();save(DATA/'state.json',state)
      elapsed=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(state['started_at'])).total_seconds()
      hour=int(elapsed//3600)
      if hour>state.get('last_hourly_report',0):
       save(REPORT/'hourly'/f'{hour:06d}.json',dict(at=now(),elapsed_hours=elapsed/3600,verified_totals=state['totals'],inflight=state['inflight'],milestone_100h=hour>=100))
       state['last_hourly_report']=hour;save(DATA/'state.json',state)
      time.sleep(15)
     code=child.returncode
    try:
     assert code==0, f'Worker exit {code}; see attempt log'
     result=result_valid(read(result_path));assert result is not None
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
    if state['failures'] and state['failures']<3:
     for _ in range(20*state['failures']):
      if (DATA/'STOP').exists() or (DATA/'PAUSE').exists():break
      time.sleep(15)
   state['status']='paused' if (DATA/'PAUSE').exists() else 'stopped';save(DATA/'state.json',state);save(REPORT/'CHECKPOINT.json',state)
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
   try:result_valid({'outcome':'progress','verified_counts':dict(zero,new_artworks=1),'evidence_paths':[]})
   except AssertionError:pass
   else:raise AssertionError('Missing delivery evidence accepted')
   assert len(TASKS)==3 and 'ONE bounded batch' in prompt_for(1,{})
  print('PASS: atomic checkpoint/recovery, evidence gate, serial task rotation and bounded worker prompt; no database or network writes')
if __name__=='__main__':main()
