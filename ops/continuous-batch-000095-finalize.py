"""Persist verified bounded-batch results and only the four researched source routes."""
import copy, datetime, fcntl, gzip, importlib.util, json, os
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-norway-images-000095.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i;W=b.E;E=W.parent;Q=E.parents[1]/'source-queue.json'
def save(name,v):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,v);return v
def rel(p):return str(p.relative_to(b.ROOT))
with (b.RUNTIME/'worker.lock').open('a+') as worker:
 fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (E/'CHECKPOINT.json').exists():
  print('Completed checkpoint preserved; use resume verifier for fresh checks.');raise SystemExit(0)
 receipt=h.load(W/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=8,alternate_images=0,museum_links=0)
 assert h.load(W/'independent-resume-verification.json')['new_production_increments_on_resume']==0
 ids=receipt['production_ids'];verified=h.load(W/'independent-production-verification.json');research={r:h.load(E/('independent-'+r+'-discovery-verification.json')) for r in ['nsw','auckland','khm']}
 with b.connect() as db:
  assert h.snapshot(db,ids)==verified['after']
  preserved={}
  for route,file in [('nsw','gap-input.json.gz'),('auckland','auckland-gap-input.json.gz'),('khm','khm-gap-input.json.gz')]:
   inp=h.load(E/file);assert h.snapshot(db,list(inp['before']))==inp['before'];preserved[route]=len(inp['before'])
  prior=h.load(E/'prior-batch-live-reconciliation.json');assert h.snapshot(db,list(prior['live']))==prior['live']
  recovery=h.load(i.BACKUP/'affected-row-recovery-before.json.gz');museum=db.execute('SELECT to_jsonb(t) v FROM institutions t WHERE id=%s',(b.MID,)).fetchone()['v'];assert museum==recovery['institutions'][0]
 save('independent-existing-preservation-verification.json',dict(at=h.now(),unchanged_gap_snapshots=preserved,prior_batch_objects_unchanged=len(prior['live']),museum_unchanged=True,local_catalogue_connections=0))
 for route,v in research.items():
  for row in v['rows']:
   rc=row['receipt'];assert rc['status'] in [200,404];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256']
   assert not row.get('selected',False)
 staged=h.load(W/'oslo-bounded-gap-input.json.gz');holds=h.load(W/'research-holds.json')['records'];assert len(staged['rows'])==12 and len(holds)==4
 save('research-holds.json',dict(at=h.now(),nsw=research['nsw']['rows'],auckland=research['auckland']['rows'],khm=research['khm']['rows'],norway=holds,provider_holds_preserved=True,profile_404_not_provider_wide_hold=True,unresearched_rows_remain_queued=True))
 failures={}
 for rcfile in (E/'source-captures').glob('*.json'):
  rc=h.load(rcfile)
  if rc['status']!=200:failures[rc['url']]=dict(url=rc['url'],status=rc['status'],retry_after=rc.get('retry_after'),retries=0,evidence=rel(rcfile))
 save('failure-ledger.json',dict(at=h.now(),provider_responses=list(failures.values()),local_recovered_errors=[dict(error='Read-only prior-batch receipt path and metadata checksum key differed from copied workflow',resolution='Resolved against batch 94 Warsaw subdirectory and batch checkpoint before selection or any write.'),dict(error='Cached HTTP404 summary originally labeled two repeated-creator rows as 200',resolution='No repeated network requests; corrected from immutable HTTP receipts in independent-nsw-discovery-verification.json and added cached-status assertion. No image selection from failed pages.'),dict(error='Read-only sed command typo and tool JavaScript syntax error',resolution='Corrected commands before execution; no mutation from failed calls.')],production_write_failures=0,held_provider_requests=0,spending_budget_changes=0))
 programme=h.load(E.parents[1]/'CHECKPOINT.json');assert programme['inflight']['batch']==95;start=programme['inflight']['started_at'];end=h.now();elapsed=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
 save('batch-verification-receipt.json',dict(receipt,batch=95,started_at=start,finished_at=end,measured_runtime_seconds=elapsed,source_receipt=rel(W/'batch-verification-receipt.json'),nsw_selected=0,auckland_selected=0,khm_selected=0,previous_campaign_increments_excluded=True))
 next_task='Resume Greek priority at Athens Parthenis page 5 with exact object reconciliation. Preserve Warsaw page 11. Auckland and KHM saved UUID queues retain untouched candidates; do not repeat NSW frozen-list profile failures or Norwegian rights holds without new evidence.'
 touched={'art_gallery_nsw','auckland_art_gallery','khm_vienna','nasjonalmuseet_norway'}
 with (Q.parent/'source-queue.worker.lock').open('a+') as lock1,(Q.parent/'source-queue.lock').open('a+') as lock2:
  fcntl.flock(lock1,fcntl.LOCK_EX);fcntl.flock(lock2,fcntl.LOCK_EX)
  before=h.load(Q);save('source-queue-immediately-before-update.json',before);after=copy.deepcopy(before)
  for row in after['sources']:
   sid=row['source_id']
   if sid not in touched:continue
   route={'art_gallery_nsw':'nsw','auckland_art_gallery':'auckland','khm_vienna':'khm','nasjonalmuseet_norway':'norway'}[sid]
   refs=[rel(E/('independent-'+route+'-discovery-verification.json'))] if route!='norway' else [rel(W/p) for p in ['batch-verification-receipt.json','independent-production-verification.json','independent-public-verification.json','actual-visual-review.json','research-holds.json']]
   row.update(last_checked_at=end,checkpoint=rel(E/'CHECKPOINT.json'),last_batch=95)
   row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+refs));row['latest_batch_verified_counts']=counts if route=='norway' else {k:0 for k in counts}
   history=row.setdefault('research_history',[]);already=any(x.get('batch')==95 for x in history)
   if not already:history.append(dict(batch=95,at=end,evidence=refs,verified_counts=row['latest_batch_verified_counts']))
   cur=row.get('resume_cursor') or {};row['resume_cursor']=cur
   if route=='nsw':
    done=[r['artwork_id'] for r in research[route]['rows']]
    cur['processed_artwork_ids']=list(dict.fromkeys(cur.get('processed_artwork_ids',[])+done));cur['profile_unavailable_artwork_ids']=list(dict.fromkeys(cur.get('profile_unavailable_artwork_ids',[])+done));cur['pending_artwork_ids']=[x for x in cur.get('pending_artwork_ids',[]) if x not in done]
    cur['profile_404_no_unchanged_retry']=list(dict.fromkeys(cur.get('profile_404_no_unchanged_retry',[])+[r['url'] for r in research[route]['rows']]));cur['discovery_evidence']=refs[0]
    cur['next_step']='Frozen 35-record list researched: two previously illustrated, seven unmatched, 26 candidate-profile failures. New source/profile evidence required before revisiting failed routes; no claim images are absent everywhere.'
    row['status']='frozen_35_gaps_researched_2_prior_images_7_unmatched_26_profile_unavailable';row['access_status']='Twelve fresh candidate WikiArt profile URLs returned HTTP404 across fourteen records; no retries, no native NSW requests.';row['remaining_gaps']=['33 unresolved gaps in frozen list; museum access hold preserved; no untouched frozen-list entries.']
   elif route in ['auckland','khm']:
    inp=h.load(E/(route+'-gap-input.json.gz'));v=research[route]
    cur.update(route='wikiart_exact_matches_to_existing_museum_gaps',institution_id=inp['institution_id'],input_path=rel(E/(route+'-gap-input.json.gz')),staged_artwork_ids=[r['id'] for r in inp['rows']],researched_artwork_ids=[r['artwork_id'] for r in v['rows']],pending_artwork_ids=v['pending_artwork_ids'],verified_artwork_ids=[],after_artwork_id=None,next_keyset_after_frozen_input=inp['rows'][-1]['id'],ordering='Explicit pending UUIDs before later keyset pages; sparse artist selection is not a completed positional page',profile_404_no_unchanged_retry=list(dict.fromkeys(r['profile_url'] for r in v['rows'] if r['receipt']['status']==404)),discovery_evidence=refs[0],next_step='Continue untouched UUIDs using new source evidence. Reuse captured indexes; do not retry unchanged failed profiles. Native institution sources not requested in this batch.')
    row['status']=str(v['researched'])+'_of_40_frozen_gaps_researched_via_wikiart_no_exact_matches';row['access_status']='Independent WikiArt alternate route only: profile HTTP200/404 evidence saved; no native museum metadata or image requests.';row['policy_reference']='Original 111-source registry '+sid+'; separate WikiArt approval in docs/ARTLINE_IMAGE_USE.md';row['remaining_gaps']=[str(len(v['pending_artwork_ids']))+' untouched UUIDs in saved 40-record input; checked candidates remain unresolved.','Catalogue and institution coverage remain incomplete; no source-wide absence claim.']
   else:
    oldcursor=cur.get('after_artwork_id');cur.update(previous_after_artwork_id=oldcursor,after_artwork_id=staged['rows'][-1]['id'],latest_frozen_input=rel(W/'oslo-bounded-gap-input.json.gz'),selection_sha256=receipt['selection_sha256'],latest_verified_batch=95,latest_hold_ledger=rel(W/'research-holds.json'),next_step='Rotate institutions, then continue native keyset after '+staged['rows'][-1]['id']+'. Resolve Degas date interpretation separately; preserve explicit copyright holds.')
    cur['inspected_ids']=list(dict.fromkeys(cur.get('inspected_ids',[])+[r['id'] for r in staged['rows']]));cur['delivered_ids']=list(dict.fromkeys(cur.get('delivered_ids',[])+ids));cur['held_ids']=list(dict.fromkeys(cur.get('held_ids',[])+[r['artwork_id'] for r in holds]));cur['latest_rights_hold_ids']=[r['artwork_id'] for r in holds if r.get('rights_label')];cur['latest_identity_hold_ids']=[r['artwork_id'] for r in holds if not r.get('rights_label')]
    total=row.setdefault('programme_verified_counts',{k:0 for k in counts})
    if not already:
     for k,v in counts.items():total[k]+=v
    row['verified_counts']=counts;row['status']=str(total['newly_illustrated'])+'_programme_primary_images_verified_eight_further_CC_BY_images';row['access_status']='Twelve exact native object pages and copyright policy HTTP200; eight selected full-frame images and public delivery verified.';row['remaining_gaps']=['Native queue continues after saved cursor; three new restricted objects and one date interpretation held.','No catalogue facts, creator labels, holdings or historical statuses changed.']
  assert len(after['sources'])==111
  assert [r for r in before['sources'] if r['source_id'] not in touched]==[r for r in after['sources'] if r['source_id'] not in touched]
  payload=json.dumps(after,ensure_ascii=False,indent=2).encode();tmp=Q.with_suffix('.batch95.tmp')
  with tmp.open('wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
  os.replace(tmp,Q);assert h.load(Q)==after
  save('source-queue-after.json',after);save('independent-queue-verification.json',dict(at=h.now(),modified_source_ids=sorted(touched),unrelated_routes_preserved=107,original_registry_routes=111,before_sha256=h.sha(json.dumps(before,sort_keys=True).encode()),after_sha256=h.sha(Q.read_bytes()),exact_unrelated_structures_equal=True,atomic_replace=True))
 save('source-register-final.json',dict(at=end,original_registry_rows=111,registry_sha256=h.load(E/'required-input-reconciliation.json')['registry_sha256'],researched_routes=[r for r in after['sources'] if r['source_id'] in touched],directory_coverage_changed=False,object_coverage_complete=False,rights_approvals_not_generalized=True))
 evidence=[rel(E/p) for p in ['batch-verification-receipt.json','independent-nsw-discovery-verification.json','independent-auckland-discovery-verification.json','independent-khm-discovery-verification.json','independent-existing-preservation-verification.json','failure-ledger.json','research-holds.json','source-register-final.json','independent-queue-verification.json','external-continuation-verification.json']]
 evidence += [rel(W/p) for p in ['independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','local-recovery-verification.json']]
 for p in evidence:assert (b.ROOT/p).is_file()
 checkpoint=dict(batch=95,status='complete',outcome='progress',started_at=start,finished_at=end,measured_runtime_seconds=elapsed,verified_counts=counts,production_ids=ids,image_selection_sha256=receipt['selection_sha256'],stage_counts=dict(nsw_gaps_researched=14,auckland_gaps_staged=40,auckland_gaps_researched=research['auckland']['researched'],khm_gaps_staged=40,khm_gaps_researched=5,norway_gaps_researched=12,selected=8,prepared=8,actually_viewed=8,imported=8,verified=8),next_task=next_task,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-norway-000095-resume.py',verification_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-norway-images-000095-verify.py',delivery_complete_do_not_count_again=True,evidence_paths=evidence,external_supervisor_unchanged=True,local_catalogue_connections=0,limitations=['Eight prepared JPEGs individually viewed; originals technically decoded and hashed, not separately viewed.','Recovery is full schema plus scoped exact row snapshots, not full database export.','Profile failures and unmatched indexes do not establish that images are absent elsewhere.','Global catalogue target totals not recounted in this bounded batch.'])
 save('CHECKPOINT.json',checkpoint);h.save(b.RUNTIME/'CHECKPOINT.json',checkpoint)
 save('batch-summary.json',dict(at=end,measured_runtime_seconds=elapsed,verified_counts=counts,prior_programme_totals=programme['totals'],prior_totals_source='External supervisor checkpoint, not independently re-audited by this batch',next_task=next_task,reporting_owner='Existing external supervisor owns hourly and 100-hour milestone reporting. No supervisor or schedule changed.'))
 stop=h.load(E/'completed-campaign-stop-preservation.json');assert h.sha((b.ROOT/stop['path']).read_bytes())==stop['sha256']
 save('independent-final-checkpoint-verification.json',dict(at=h.now(),checkpoint_sha256=h.sha((E/'CHECKPOINT.json').read_bytes()),runtime_checkpoint_equal=h.load(b.RUNTIME/'CHECKPOINT.json')==checkpoint,evidence_files=[dict(path=p,sha256=h.sha((b.ROOT/p).read_bytes())) for p in evidence],completed_campaign_stop_unchanged=True,unrelated_queue_routes_preserved=107,verified_counts=counts))
 print(json.dumps(dict(verified_counts=counts,next_task=next_task,checkpoint=rel(E/'CHECKPOINT.json'))))
