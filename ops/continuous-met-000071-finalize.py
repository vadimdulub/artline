#!/usr/bin/env python3
"""Save batch handoff and advance only the researched Met route."""
import collections, copy, datetime, fcntl, importlib.util, json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-met-images-000071.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i
with (b.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=b.load(b.E/'batch-verification-receipt.json');counts=receipt['verified_counts']
 resume=b.load(b.E/'independent-resume-verification.json');assert resume['unchanged_snapshot'] and not any(resume['replay_increments'].values())
 assert b.load(b.E/'independent-held-objects-verification.json')['unchanged']
 gap=b.load(b.E/'gap-reconciliation.json');inputrows={r['id']:r for r in b.load(b.E/'bounded-gap-input.json')['rows']}
 holds=[]
 for row in gap['rows']:
  if row['reason']=='eligible':continue
  source=json.loads(__import__('gzip').decompress((b.E/'source-captures'/(row['native_id']+'.body.gz')).read_bytes()))
  holds.append(dict(row,catalogue=inputrows[row['artwork_id']],source_evidence=str((b.E/'source-captures'/(row['native_id']+'.receipt.json')).relative_to(b.ROOT)),source_fields={k:source.get(k) for k in ['objectID','title','accessionNumber','objectBeginDate','objectEndDate','artistDisplayName','artistPrefix','artistSuffix','isPublicDomain','primaryImageSmall','primaryImage','classification','objectName','dimensions']},downloaded=False,retry_unchanged=False))
 b.save(b.E/'research-holds.json',dict(at=h.now(),rows=holds,counts=dict(collections.Counter(x['reason'] for x in holds)),remaining_gaps='These 43 checked objects require changed source data or explicit identity/creator research; continue after cursor without repeating unchanged requests.'))
 b.save(b.E/'failures.json',dict(at=h.now(),failures=[dict(stage='dependency_probe',error='System Python has no psycopg',resolution='Used established /tmp/artline-cyprus-venv/bin/python; no packages installed.'),dict(stage='prewrite_validation',error='Nonblocking worker lock rejected overlap while local recovery export was running',resolution='Waited for recovery to finish, then validation succeeded. No overlapping mutations and no production change from rejected invocation.')],network_failures=0,source_access_failures=0,unresolved_research_holds=len(holds)))
 evidence=['batch-verification-receipt.json','independent-production-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-audit-history-verification.json','independent-resume-verification.json','independent-held-objects-verification.json','independent-campaign-stop-verification.json','prewrite-identity-verification.json','local-recovery-verification.json','actual-visual-review.json','research-holds.json','gap-reconciliation.json','prior-batch-live-reconciliation.json']
 for name in evidence:assert (b.E/name).is_file()
 next_task='Resume Warsaw icon page 6 from its saved source queue with prior holds preserved. For the next existing-image-gap batch, rotate to an available museum route; Met priority-subject cursor now advances past '+gap['resume_after_artwork_id']+'. French reserve remains exhausted.'
 start=b.load(b.E/'production-target-reconciliation.json')['at'];runtime=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(start)).total_seconds()
 checkpoint=dict(at=h.now(),batch=71,stage='verified_complete',campaign=i.OP,verified_counts=counts,discovered_existing_gaps=50,selected=7,prepared=7,actually_visually_reviewed=7,imported=7,verified=7,held=43,measured_work_runtime_seconds=runtime,runtime_basis='Initial successful production reconciliation through final handoff; excludes earlier reading time.',resume_cursor=gap['resume_after_artwork_id'],next_task=next_task,evidence_paths=[str((b.E/n).relative_to(b.ROOT)) for n in evidence],resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-met-000071-resume.py',verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-met-images-000071-verify.py',local_catalogue_connections=0,supervisor_modified=False,production_metadata_preserved=True)
 for path in [b.E/'CHECKPOINT.json',b.RUNTIME/'CHECKPOINT.json']:
  tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(checkpoint,indent=2));tmp.replace(path)
 qpath=b.E.parents[1]/'source-queue.json'
 with (b.RUNTIME/'queue-update.lock').open('a+') as qlock:
  fcntl.flock(qlock,fcntl.LOCK_EX)
  queue=b.load(qpath);before=copy.deepcopy(queue)
  route=next(r for r in queue['sources'] if r['source_id']=='met_museum')
  # Refuse to overwrite another worker's route advancement.
  assert route['resume_cursor']['after_artwork_id'] in [gap['after_artwork_id'],gap['resume_after_artwork_id']]
  route.update(status='seven_further_existing_primary_gaps_verified_43_checked_holds_preserved',checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),last_checked_at=h.now(),verified_counts=counts)
  route['resume_cursor'].update(after_artwork_id=gap['resume_after_artwork_id'],previous_after_artwork_id=gap['after_artwork_id'],selected_native_ids=[r['native_id'] for r in i.selected(b.B)['rows']],latest_checked=50,latest_held=43,remaining_checked_unresolved=next(r for r in b.load(b.E/'source-queue-before.json')['sources'] if r['source_id']=='met_museum')['resume_cursor'].get('remaining_checked_unresolved',0)+43,hold_ledger=str((b.E/'research-holds.json').relative_to(b.ROOT)))
  for path in checkpoint['evidence_paths']:
   if path not in route.setdefault('evidence_paths',[]):route['evidence_paths'].append(path)
  note='Batch 71: 43 checked gaps remain held; see exact source/catalogue evidence and avoid unchanged repeat requests.'
  if note not in route.setdefault('remaining_gaps',[]):route['remaining_gaps'].append(note)
  assert len(queue['sources'])==111
  unchanged=[r['source_id'] for r in before['sources'] if r['source_id']!='met_museum']
  assert [r for r in before['sources'] if r['source_id']!='met_museum']==[r for r in queue['sources'] if r['source_id']!='met_museum']
  tmp=qpath.with_suffix('.tmp');tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2));tmp.replace(qpath)
  after=b.load(qpath);assert after==queue
  b.save(b.E/'independent-final-handoff-verification.json',dict(at=h.now(),registry_routes=111,unrelated_routes_preserved=len(unchanged),unchanged_source_ids=unchanged,only_researched_route_updated='met_museum',resume_after_artwork_id=gap['resume_after_artwork_id'],queue_sha256=h.sha(qpath.read_bytes()),checkpoint_sha256=h.sha((b.E/'CHECKPOINT.json').read_bytes()),runtime_checkpoint_matches=(b.E/'CHECKPOINT.json').read_bytes()==(b.RUNTIME/'CHECKPOINT.json').read_bytes(),supervisor_owned_root_checkpoint_untouched=True))
 inputs=b.load(b.E/'required-input-reconciliation.json')
 prior=b.load(b.E.parents[1]/'CHECKPOINT.json')
 b.save(b.E/'milestone-report.json',dict(at=h.now(),batch=71,measured_work_runtime_seconds=runtime,verified_counts=counts,prior_supervisor_reported_totals=prior['totals'],prior_totals_globally_reaudited=False,projected_totals={k:v+counts[k] for k,v in prior['totals'].items()},hourly_and_100h_reports_owned_by_existing_supervisor=True,failures='failures.json',unresolved_cases='research-holds.json',next_task=next_task))
 print(json.dumps(dict(verified_counts=counts,unrelated_routes_preserved=110,next_task=next_task)))
