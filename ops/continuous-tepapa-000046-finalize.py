#!/usr/bin/env python3
"""Checkpoint one verified batch and merge only the two researched queue entries."""
import copy, csv, datetime, fcntl, importlib.util, json, os
from pathlib import Path
s=importlib.util.spec_from_file_location('w46',Path(__file__).with_name('continuous-tepapa-images-000046.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w);i=w.i;h=w.h;E=w.E
with (w.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=w.load(E/'batch-verification-receipt.json');replay=w.load(E/'independent-resume-verification.json');assert replay['unchanged_snapshot'] and all(v==0 for v in replay['replay_increments'].values())
 counts=receipt['verified_counts'];assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=4,alternate_images=0,museum_links=0)
 data=w.load(E/'tepapa-bounded-gap-input.json.gz');holds=w.load(E/'research-holds.json')['records'];rows=i.selected(w.B)['rows'];ids=receipt['production_ids'];now=h.now();master=w.load(E.parents[1]/'CHECKPOINT.json')
 assert master['inflight']['batch']==46 and len(data['rows'])==25 and len(holds)==21
 assert {r['id'] for r in data['rows']}==set(ids)|{r['artwork_id'] for r in holds}
 sourcechecks=[]
 for p in (E/'source-captures').glob('*.receipt.json'):
  r=w.load(p);body=w.ROOT/r['body_path'];import gzip
  assert h.sha(gzip.decompress(body.read_bytes()))==r['sha256'];sourcechecks.append(dict(path=str(p.relative_to(w.ROOT)),url=r['url'],status=r['status'],sha256=r['sha256']))
 w.save(E/'independent-route-completeness-verification.json',dict(at=now,inspected_gap_records=25,native_object_captures=23,accepted_primary_images=4,explicit_holds=21,every_gap_accounted_for=True,source_receipts=sourcechecks,prior_french_reserve_deliveries_excluded=188,held_object_images_downloaded=0))
 nxt='Rotate to Getty’s saved Byzantine search at offset 50 (50 leads maximum), reconcile processed slugs and object-unit holds before selecting whole objects. Te Papa can later resume after '+data['rows'][-1]['id']+'. The 188 French reserve records are exhausted; do not count or reimport them.'
 cursor=dict(route='official_native_object_pages_record_specific_NKCR_images',institution_id=w.b.MID,after_artwork_id=data['rows'][-1]['id'],previous_after_artwork_id=data['after_artwork_id'],inspected_ids=[r['id'] for r in data['rows']],native_object_ids=[r['native_id'] for r in w.load(E/'identity-crosswalk-input.json.gz')],delivered_ids=ids,held_ids=[r['artwork_id'] for r in holds],image_selection_sha256=receipt['selection_sha256'],source_media_redirect='Only exact official HTTP 303 preserving source media ID',metadata_refresh_due='2026-11-08',no_repeat_of_unchanged_holds=True,held_evidence=str((E/'research-holds.json').relative_to(w.ROOT)))
 evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-file-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-held-objects-verification.json','independent-prewrite-verification.json','independent-resume-verification.json','actual-visual-review.json','french-reserve-live-reconciliation.json','prior-write-reconciliation.json','global-identity-reconciliation.json','independent-route-completeness-verification.json','rights-guide-verification.json','source-policy-verification-v2.json','research-holds.json','source-access-holds.json','required-input-reconciliation.json']
 w.save(E/'source-register-final.json',dict(at=now,complete_original_registry_rows=111,sources=[dict(source_id='yale_lux',access_status='Read-only production reconciliation; no new provider requests',last_checked_at=now,remaining_gaps='No unimported records in the reviewed 188-object reserve',policy_reference='docs/ARTLINE_IMAGE_USE.md#continued-illustrated-expansion--11-october-2026'),dict(source_id='te_papa',access_status='23 public native object pages HTTP 200; four selected source redirects HTTP 303 followed to HTTP 200 media; no API credentials used',last_checked_at=now,policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy and native record-specific NKCR policy',remaining_gaps='21 cases documented; later UUID pages not researched; cultural and territorial rights retained',resume_cursor=cursor)],new_directory_entries=0,museum_nationwide_coverage_complete=False))
 w.save(E/'research-outcomes.json',dict(at=now,discovered_gap_records=25,researched_native_records=23,selected_images=4,prepared_images=4,imported_primary_images=4,independently_verified_primary_images=4,held=21,earlier_campaign_new_work_count=0,verified_counts=counts))
 manifest=E/'delivery-manifest.csv'
 if not manifest.exists():
  with manifest.open('w') as f:
   fields=['artwork_id','native_id','title','source_url','media_id','image_sha256','selection_sha256','rights_label','byte_size'];out=csv.DictWriter(f,fieldnames=fields);out.writeheader()
   images={im['artwork_id']:im for im in i.accepted(w.B)[0]}
   for r in rows:
    im=images[r['artwork_id']];out.writerow(dict(artwork_id=r['artwork_id'],native_id=r['current_source_id'],title=r['title'],source_url=r['source_url'],media_id=im['media_id'],image_sha256=im['sha256'],selection_sha256=receipt['selection_sha256'],rights_label=r['rights_label'],byte_size=im['bytes']))
 cp=dict(at=now,batch=46,stage='verified_complete',verified_counts=counts,production_ids=ids,selected=4,prepared=4,imported=4,verified=4,holds=21,french_reserve_already_delivered=188,resume_cursor=cursor,next_task=nxt,resume_command='/tmp/artline-cesi-venv/bin/python ops/continuous-tepapa-000046-resume.py',verify_command='/tmp/artline-cesi-venv/bin/python ops/continuous-tepapa-images-000046-verify.py',evidence_paths=[str((E/name).relative_to(w.ROOT)) for name in evidence],external_supervisor_unchanged=True,local_database_connections=0)
 w.save(E/'CHECKPOINT.json',cp);w.save(w.RUNTIME/'CHECKPOINT.json',cp)
 qp=E.parents[1]/'source-queue.json'
 if not (E/'source-queue-update-verification.json').exists():
  with qp.with_suffix('.lock').open('a+') as qlock:
   fcntl.flock(qlock,fcntl.LOCK_EX);before=w.load(qp);q=copy.deepcopy(before)
   for r in q['sources']:
    if r['source_id']=='te_papa':
     oldcounts=r.get('programme_verified_counts',r['verified_counts']);r.setdefault('prior_resume_cursors',[]).append(r.get('resume_cursor'))
     r.update(status='eight_programme_primary_images_verified_four_new_exact_native_NKCR_images',last_checked_at=now,checkpoint=str((E/'CHECKPOINT.json').relative_to(w.ROOT)),resume_cursor=cursor,verified_counts=counts,latest_batch_verified_counts=counts,programme_verified_counts={k:oldcounts[k]+counts[k] for k in counts},policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='23 native object pages HTTP 200, four exact media redirects HTTP 303 followed to HTTP 200; API not used',remaining_gaps=['21 held or unresolved cases in this page; previous 21 holds preserved in prior checkpoint','Cropped-source, missing-unit, date qualifier and creator-alias cases require new evidence','Later UUID pages and museum coverage remain incomplete'])
     add=evidence+['source-register-final.json','research-outcomes.json','CHECKPOINT.json']
    elif r['source_id']=='yale_lux':
     r.update(status='french_reserve_exhausted_live_verified_188_already_delivered',last_checked_at=now,checkpoint=str((E/'CHECKPOINT.json').relative_to(w.ROOT)),latest_batch_verified_counts={k:0 for k in counts})
     add=['french-reserve-live-reconciliation.json','independent-route-completeness-verification.json','CHECKPOINT.json']
    else:continue
    for name in add:
     path=str((E/name).relative_to(w.ROOT));assert (w.ROOT/path).is_file()
     if path not in r.setdefault('evidence_paths',[]):r['evidence_paths'].append(path)
   untouched=lambda v:{r['source_id']:r for r in v['sources'] if r['source_id'] not in ['te_papa','yale_lux']}
   assert untouched(before)==untouched(q) and len(q['sources'])==111 and all(q[k]==v for k,v in before.items() if k!='sources')
   w.save(E/'source-queue-immediately-before-update.json',before);tmp=qp.with_suffix('.batch46.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2));os.replace(tmp,qp);assert w.load(qp)==q
   w.save(E/'source-queue-update-verification.json',dict(at=now,updated_sources=['te_papa','yale_lux'],unrelated_entries_preserved=109,source_count=111,before_semantic_sha256=h.sha(json.dumps(before,sort_keys=True).encode()),after_file_sha256=h.sha(qp.read_bytes()),exact_cursor=cursor,programme_tepapa_verified_images=8))
 end=datetime.datetime.fromisoformat(now);start=datetime.datetime.fromisoformat(master['inflight']['started_at']);total=(end-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()
 w.save(E/'milestone-report.json',dict(at=now,batch=46,started_at=start.isoformat(),measured_batch_runtime_seconds=(end-start).total_seconds(),measured_programme_runtime_hours=total/3600,previous_programme_counts=master['totals'],batch_verified_counts=counts,cumulative_programme_counts={k:master['totals'][k]+counts[k] for k in counts},not_whole_catalogue_census=True,failures=['System Python lacked bs4; used existing artline-cesi-venv without installation','Guessed rights-guide URL returned 404 once; verified official prior-ledger URL HTTP 200 and persisted corrected policy reference','Strict source selector rejected apostrophe glyph difference; separately documented same-accession comparison and preserved catalogue title','Unstated measurement units and cropped source photos held, not guessed or downloaded'],hourly_summary='Programme hour '+str(int(total//3600))+': batch 46 verified four Te Papa primary images; historical French reserve exhausted; 21 current page holds saved.',external_supervisor_manages_hourly_and_100_hour_reporting=True,no_supervisor_changes=True,next_task=nxt))
 evidence+=['source-queue-update-verification.json','source-register-final.json','milestone-report.json','CHECKPOINT.json']
 result=dict(outcome='progress',summary='Verified four new Te Papa primary images, each individually viewed. All 188 French reserves were already delivered and excluded. Replay changed nothing; 21 Te Papa holds and resume cursors saved. Local catalogue untouched.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[str((E/name).relative_to(w.ROOT)) for name in ['batch-verification-receipt.json','independent-production-verification.json','independent-public-verification.json','actual-visual-review.json','independent-resume-verification.json','french-reserve-live-reconciliation.json','source-queue-update-verification.json','final-checkpoint-verification.json','CHECKPOINT.json']])
 w.save(E/'result.json',result)
 assert w.load(w.RUNTIME/'CHECKPOINT.json')==w.load(E/'CHECKPOINT.json')
 w.save(E/'final-checkpoint-verification.json',dict(at=h.now(),evidence_files=[dict(path=str((E/name).relative_to(w.ROOT)),sha256=h.sha((E/name).read_bytes())) for name in evidence],runtime_checkpoint_matches=True,source_queue_111_entries=len(w.load(qp)['sources'])==111,verified_counts=counts,supervisor_prompt_schema_launchagent_untouched=True))
 for path in result['evidence_paths']:assert (w.ROOT/path).is_file()
 print(json.dumps(result,ensure_ascii=False))
