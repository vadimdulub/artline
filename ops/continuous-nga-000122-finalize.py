#!/usr/bin/env python3
"""Finalize one verified bounded batch; preserve external supervisor state."""
import copy,datetime,fcntl,importlib.util,json,os
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-nga-images-000122.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=b.load(b.E/'batch-verification-receipt.json');prod=b.load(b.E/'independent-production-verification.json');resume=b.load(b.E/'independent-resume-verification.json')
 assert receipt['verified_counts']['newly_illustrated']==8 and resume['unchanged_snapshot'] and resume['unchanged_storage_generations']
 assert len(b.load(b.E/'independent-public-verification.json')['rows'])==len(b.load(b.E/'independent-storage-verification.json')['checks'])==8
 counts=receipt['verified_counts'];recon=b.load(b.E/'nga-gap-reconciliation.json');stamp=h.now()
 nxt='Resume Getty Byzantine discovery at offset 150, size 50; skip processed objects and reconcile exact identities before selection. NGA reserve resumes at1262; preserve all earlier deferred positions.'
 queue=b.P.parents[1]/'source-queue.json'
 with (queue.parent/'source-queue.lock').open('a+') as qlock:
  fcntl.flock(qlock,fcntl.LOCK_EX)
  q=b.load(queue);before=copy.deepcopy(q);source=next(x for x in q['sources'] if x['source_id']=='nga_washington');old=copy.deepcopy(source)
  assert source['resume_cursor']['position'] in [1252,1262],'Concurrent NGA cursor changed; reconcile before queue update'
  source['status']='eight_further_NGA_primary_images_verified_Nanteuil_impressions'
  source['last_checked_at']=stamp;source['checkpoint']=str((b.P/'CHECKPOINT.json').relative_to(b.ROOT))
  source['policy_reference']='Original111-source registry nga_washington; docs/ARTLINE_IMAGE_USE.md; NGA primary image openaccess=1 and CC0 source metadata'
  source['resume_cursor'].update(position=recon['resume_position'],latest_reconciliation=str((b.E/'nga-gap-reconciliation.json').relative_to(b.ROOT)))
  source['resume_cursor']['deferred_positions']=sorted(set(old['resume_cursor'].get('deferred_positions',[]))|{r['position'] for r in recon['rows'] if r['reason']=='creator_variety_deferred'})
  source['latest_batch_verified_counts']=counts
  source.setdefault('evidence_paths',[])
  for f in ['batch-verification-receipt.json','independent-production-verification.json','independent-public-verification.json','independent-resume-verification.json','source-citation-pin-verification.json']:
   p=str((b.E/f).relative_to(b.ROOT))
   if p not in source['evidence_paths']:source['evidence_paths'].append(p)
  assert [x for x in q['sources'] if x['source_id']!='nga_washington']==[x for x in before['sources'] if x['source_id']!='nga_washington']
  b.save(b.P/'source-queue-update-verification.json',dict(at=stamp,source_id='nga_washington',before=old,after=source,unrelated_entries_unchanged=True,original_registry_source_count=len(q['sources'])))
  tmp=queue.with_suffix('.000122.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,queue)
 start=b.load(b.P/'required-input-reconciliation.json')['at'];seconds=(datetime.datetime.fromisoformat(stamp)-datetime.datetime.fromisoformat(start)).total_seconds()
 evidence=[b.E/f for f in ['batch-verification-receipt.json','independent-production-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-file-verification.json','independent-source-verification.json','independent-identity-verification.json','independent-resume-verification.json','independent-campaign-stop-verification.json','source-citation-pin-verification.json','local-recovery-verification.json']]+[b.P/'actual-visual-review.json',b.P/'batch107-live-reconciliation.json',b.P/'source-queue-update-verification.json']
 b.save(b.P/'independent-final-artifact-verification.json',dict(at=stamp,files=[dict(path=str(p.relative_to(b.ROOT)),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in evidence],all_files_present_and_json_decoded=all(isinstance(b.load(p),dict) for p in evidence),verified_counts=counts))
 b.save(b.P/'batch-verification-receipt.json',dict(receipt,verification_directory=str(b.E.relative_to(b.ROOT)),batch107_reconciled_rows=12,batch107_increments=0,measured_batch_seconds=seconds))
 checkpoint=dict(at=stamp,batch=122,stage='verified_complete',verified_counts=counts,selected=8,prepared=8,imported=8,verified=8,checked_reserve_positions=10,resume_cursor=source['resume_cursor'],next_task=nxt,local_catalogue_connections=0,metadata_and_holdings_unchanged=True,external_supervisor_unchanged=True,remaining_gaps=['Two creator-variety positions1259/1260 deferred; previous1199/1205/1249 preserved.','All eight are Nanteuil prints with distinct after-model attribution labels; this batch does not imply eight different printmakers.','No complete museum or painter coverage claimed.'],evidence_paths=[str(p.relative_to(b.ROOT)) for p in evidence])
 b.save(b.P/'CHECKPOINT.json',checkpoint);b.save(b.RUNTIME/'checkpoint.json',checkpoint)
 parent=b.load(b.P.parents[1]/'CHECKPOINT.json');totals={k:parent['totals'][k]+counts[k] for k in counts}
 b.save(b.P/'milestone-report.json',dict(at=stamp,started_at=start,measured_batch_seconds=seconds,verified_counts=counts,cumulative_including_this_batch=totals,cumulative_basis='External supervisor saved totals before batch122 plus this independent verified increment; supervisor remains owner of cumulative state.',new_provider_access_failures=0,local_setup_failure='Default python lacked psycopg; established /tmp/artline-cyprus-venv reused.',current_batch_held=0,next_task=nxt))
 result=dict(outcome='progress',summary='Verified eight authentic NGA primary images on existing French prints, including two distinct Jean Fronteau impressions. All eight visually reviewed; source identities, transaction preimages, audit, storage, public delivery and safe replay verified. Batch107 reconciled without recounting; queue/checkpoints saved.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[str((b.P/'batch-verification-receipt.json').relative_to(b.ROOT)),str((b.E/'independent-production-verification.json').relative_to(b.ROOT)),str((b.E/'independent-public-verification.json').relative_to(b.ROOT)),str((b.E/'independent-resume-verification.json').relative_to(b.ROOT)),str((b.P/'independent-final-artifact-verification.json').relative_to(b.ROOT)),str((b.P/'CHECKPOINT.json').relative_to(b.ROOT))])
 b.save(b.P/'worker-result.json',result)
 print(json.dumps(result))
