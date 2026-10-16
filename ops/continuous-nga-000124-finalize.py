"""Persist verified batch124 and update only researched registry routes."""
import importlib.util,json,copy,datetime,fcntl,os
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-nga-images-000124.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
receipt=b.load(b.E/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts['newly_illustrated']==8
assert b.load(b.E/'independent-resume-verification.json')['unchanged_snapshot']
assert len(b.load(b.E/'independent-public-verification.json')['rows'])==len(b.load(b.E/'independent-storage-verification.json')['checks'])==8
recon=b.load(b.E/'nga-gap-reconciliation.json');stamp=h.now()
nxt='Research National Gallery of Ireland official painting index page39 (saved registry cursor); select eligible exact native objects and reconcile production before preparation. Respect nationalgalleryimages.ie HTTP403 hold. NGA resumes at1271 with all deferred positions preserved; French reserve exhausted, do not reselect without a documented state change.'
queue=b.P.parents[1]/'source-queue.json'
with (queue.parent/'source-queue.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);q=b.load(queue);before=copy.deepcopy(q)
 nga=next(x for x in q['sources'] if x['source_id']=='nga_washington');assert nga['resume_cursor']['position'] in [1262,1271]
 nga.update(status='eight_further_NGA_primary_images_verified_batch124',last_checked_at=stamp,checkpoint=str((b.P/'CHECKPOINT.json').relative_to(b.ROOT)),latest_batch_verified_counts=counts)
 nga['resume_cursor'].update(position=recon['resume_position'],latest_reconciliation=str((b.E/'nga-gap-reconciliation.json').relative_to(b.ROOT)))
 nga['resume_cursor']['deferred_positions']=sorted(set(nga['resume_cursor'].get('deferred_positions',[]))|{r['position'] for r in recon['rows'] if r['reason']=='creator_variety_deferred'})
 for name in ['batch-verification-receipt.json','independent-production-verification.json','independent-public-verification.json','independent-resume-verification.json']:
  p=str((b.E/name).relative_to(b.ROOT));nga.setdefault('evidence_paths',[])
  if p not in nga['evidence_paths']:nga['evidence_paths'].append(p)
 yale=next(x for x in q['sources'] if x['source_id']=='yale_lux');yale.update(last_checked_at=stamp,status='french_reserve_exhausted_188_already_imported_illustrated_live_verified')
 yale['resume_cursor'].update(remaining_prepared_french_reserve=0,recheck_only_on_new_reserve_or_production_change=True,last_live_reconciliation=str((b.P/'french-reserve-live-reconciliation.json').relative_to(b.ROOT)))
 for name in ['french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json']:
  p=str((b.P/name).relative_to(b.ROOT));yale.setdefault('evidence_paths',[])
  if p not in yale['evidence_paths']:yale['evidence_paths'].append(p)
 others=lambda x:[r for r in x['sources'] if r['source_id'] not in ['nga_washington','yale_lux']]
 assert others(q)==others(before) and len(q['sources'])==111
 b.save(b.P/'source-queue-update-verification.json',dict(at=stamp,changed_source_ids=['nga_washington','yale_lux'],unrelated_entries_preserved=109,before=[x for x in before['sources'] if x['source_id'] in ['nga_washington','yale_lux']],after=[nga,yale]))
 tmp=queue.with_suffix('.000124.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,queue)
start=b.load(b.P/'required-input-reconciliation.json')['at'];seconds=(datetime.datetime.fromisoformat(stamp)-datetime.datetime.fromisoformat(start)).total_seconds()
b.save(b.P/'batch-verification-receipt.json',dict(receipt,batch=124,reserve_inspected=188,reserve_unimported=0,reserve_increment=0,batch107_reconciled=12,batch107_increment=0,measured_runtime_seconds=seconds))
evidence=[b.E/n for n in ['batch-verification-receipt.json','independent-production-verification.json','independent-source-verification.json','independent-file-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','source-citation-pin-verification.json','local-recovery-verification.json']]+[b.P/n for n in ['batch-verification-receipt.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','batch107-live-reconciliation.json','actual-visual-review.json','source-queue-update-verification.json']]
for p in evidence:assert isinstance(b.load(p),dict)
b.save(b.P/'independent-final-artifact-verification.json',dict(at=stamp,files=[dict(path=str(p.relative_to(b.ROOT)),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in evidence],verified_counts=counts,all_files_present_and_json_decoded=True))
cp=dict(at=stamp,batch=124,stage='verified_complete',outcome='progress',verified_counts=counts,selected=8,prepared=8,imported=8,verified=8,reserve_inspected=188,reserve_unimported=0,measured_runtime_seconds=seconds,next_task=nxt,resume_cursor=nga['resume_cursor'],local_catalogue_connections=0,external_supervisor_unchanged=True,limitations=['Eight Nanteuil prints with different after-model labels are not eight different printmakers.','Contact-sheet review of all eight; no individual full-resolution visual inspection claimed.','Scoped schema and affected-row recovery; no full database export.','Prior French reserve visual decisions reused and checksum-verified; no new reserve visual review.'])
b.save(b.P/'CHECKPOINT.json',cp);b.save(b.RUNTIME/'checkpoint.json',cp)
parent=b.load(b.P.parents[1]/'CHECKPOINT.json');b.save(b.P/'milestone-report.json',dict(at=stamp,started_at=start,measured_runtime_seconds=seconds,verified_counts=counts,cumulative_including_this_batch={k:parent['totals'][k]+counts[k] for k in counts},cumulative_basis='Supervisor checkpoint totals plus independently verified batch124; supervisor owns cumulative state.',failures=[],next_task=nxt))
result=dict(outcome='progress',summary='Attached and independently verified eight authentic NGA images on existing prints. All188 French reserve objects were already delivered; batch107 reconciled without recounting. Source identities, visual review, transaction attribution, audit, storage, public delivery and idempotent replay verified.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[str(p.relative_to(b.ROOT)) for p in [b.P/'batch-verification-receipt.json',b.E/'independent-production-verification.json',b.E/'independent-public-verification.json',b.E/'independent-resume-verification.json',b.P/'independent-final-artifact-verification.json',b.P/'CHECKPOINT.json']])
b.save(b.P/'worker-result.json',result);print(json.dumps(result))
