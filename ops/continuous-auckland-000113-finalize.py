"""Persist verified bounded-batch result and only the researched queue route."""
import importlib.util,json,gzip,copy,fcntl,os,datetime,collections
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-auckland-images-000113.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i;E=b.E
rel=lambda p:str(p.relative_to(b.ROOT))
receipt=b.load(E/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts['newly_illustrated']==3
resume=b.load(E/'independent-resume-verification.json');assert not any(resume['replay_increments'].values())
data=b.load(E/'gap-input.json.gz');discovery=b.load(E/'native-discovery.json');vr=b.load(E/'actual-visual-review.json');holds=b.load(E/'global-identity-reconciliation.json')['holds'];delivered=receipt['production_ids'];selected=[r['artwork_id'] for r in i.selected(b.B)['rows']];dispositions=[];verified_captures=[]
native=b.mod('sourcefinal113','museum-expansion-auckland-20261006.py')
for d in discovery['rows']:
 aid=d['artwork_id'];p=E/'native'/(aid+'.json');x=b.load(p);rc=x['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256'] and native.fields(raw)==x['parsed'];verified_captures.append(dict(artwork_id=aid,url=rc['url'],sha256=rc['sha256'],rights=d['fields']['Copyright']))
 if aid in delivered:state='verified_new_primary_image';reason='Unique exact object crosswalk; actual visual review, transaction attribution, audit, storage and public checks passed'
 elif aid in selected:state='held_full_frame_uncertainty';reason=next(v['notes'] for v in vr['decisions'] if v['artwork_id']==aid)
 else:state='held';reason=next(v['reason'] for v in holds if v['artwork_id']==aid)
 dispositions.append(dict(artwork_id=aid,title=d['title'],outcome=state,reason=reason))
b.save('independent-discovery-verification.json',dict(at=h.now(),metadata_records=25,captures=verified_captures,dispositions=dispositions,selected=7,prepared=7,actually_viewed=7,accepted=3,imported=3,verified=3,coverage_complete=False))
b.save('research-holds.json',dict(at=h.now(),records=[d for d in dispositions if d['artwork_id'] not in delivered],prior_holds_preserved=True,no_unchanged_access_retry=True))
with b.connect() as db:
 fresh=h.snapshot(db,data['ids']);after=b.load(E/'independent-production-verification.json')['after'];assert all(fresh[aid]==after[aid] for aid in delivered)
 assert all(fresh[aid]==data['before'][aid] for aid in data['ids'] if aid not in delivered)
b.save('independent-existing-preservation-verification.json',dict(at=h.now(),non_delivered_unchanged=22,delivered_after_snapshot_equal=True,local_catalogue_connections=0,unrelated_metadata_mutations=0))
programme=b.load(E.parents[1]/'CHECKPOINT.json');assert programme['inflight']['batch']==113
try:os.kill(programme['supervisor_pid'],0);alive=True
except OSError:alive=False
b.save('external-supervisor-observation.json',dict(at=h.now(),pid=programme['supervisor_pid'],process_exists=alive,checkpoint_inflight_batch=113,supervisor_modified=False,supervisor_continuation_responsibility='External owner; this worker executes one bounded batch only',new_supervisors_launched=0))
end=h.now();start=programme['inflight']['started_at'];elapsed=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
next_task='Research the 23 untouched Basel image-gap UUIDs saved after batch 104 using permitted WikiArt/Commons routes. Preserve native HTTP403 and all prior version holds. Auckland retains four untouched native crosswalks after this 25-record pass; revisit those later, not the 22 resolved holds without new evidence.'
Q=E.parents[1]/'source-queue.json'
with (Q.parent/'source-queue.worker.lock').open('a+') as l1,(Q.parent/'source-queue.lock').open('a+') as l2:
 fcntl.flock(l1,fcntl.LOCK_EX);fcntl.flock(l2,fcntl.LOCK_EX)
 before=h.load(Q);b.save('source-queue-immediately-before-update.json',before);after=copy.deepcopy(before);row=next(r for r in after['sources'] if r['source_id']=='auckland_art_gallery');cur=row['resume_cursor'];row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(cur))
 assert all(aid in cur['pending_artwork_ids'] for aid in data['ids'])
 pending=[aid for aid in cur['pending_artwork_ids'] if aid not in data['ids']];assert len(pending)==4
 refs=[rel(E/p) for p in ['batch-verification-receipt.json','independent-discovery-verification.json','independent-production-verification.json','independent-public-verification.json','actual-visual-review.json','research-holds.json']]
 oldcounts=row.get('programme_verified_counts',{});row.update(status='three_further_primary_images_verified_four_untouched_crosswalks_pending',last_batch=113,last_checked_at=end,checkpoint=rel(E/'CHECKPOINT.json'),latest_batch_verified_counts=counts,programme_verified_counts={k:oldcounts.get(k,0)+v for k,v in counts.items()},programme_count_evidence=refs[0],access_status='25 exact native museum pages and seven selected source images returned HTTP200. Fifteen copying-restriction records, one missing-image record, two identity holds and four physical/pixel-proportion holds; no held provider retry.',policy_reference='Original GLOBAL_MUSEUM_SOURCE_REGISTRY.csv Auckland per-object rule; docs/ARTLINE_IMAGE_USE.md; fresh native NKCR policy with New Zealand qualification retained.')
 row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+refs));row.setdefault('research_history',[]).append(dict(batch=113,at=end,evidence=refs,verified_counts=counts));row['remaining_gaps']=['Four untouched native crosswalks from frozen batch101 input.', 'Batch113: 22 explicit rights, missing-image, identity or composition-proportion holds; prior holds preserved.', 'Earlier WikiArt holds and later keyset pages remain incomplete.']
 cur.update(pending_artwork_ids=pending,native_pending_historical_crosswalk_ids=pending,discovery_evidence=rel(E/'independent-discovery-verification.json'),hold_ledger=rel(E/'research-holds.json'),verified_evidence=rel(E/'independent-production-verification.json'),next_step=next_task)
 for key,new in [('researched_artwork_ids',data['ids']),('verified_artwork_ids',delivered),('held_artwork_ids',[a for a in data['ids'] if a not in delivered])]:cur[key]=list(dict.fromkeys(cur.get(key,[])+new))
 assert [r for r in before['sources'] if r['source_id']!='auckland_art_gallery']==[r for r in after['sources'] if r['source_id']!='auckland_art_gallery'] and len(after['sources'])==111
 tmp=Q.with_suffix('.batch113.tmp')
 with tmp.open('wb') as f:f.write(json.dumps(after,ensure_ascii=False,indent=2).encode());f.flush();os.fsync(f.fileno())
 os.replace(tmp,Q);assert h.load(Q)==after
 b.save('source-queue-after.json',after);b.save('independent-queue-verification.json',dict(at=h.now(),modified_sources=['auckland_art_gallery'],unrelated_routes_preserved=110,original_registry_routes=111,remaining_pending_ids=pending,queue_sha256=h.sha(Q.read_bytes()),atomic_replace=True))
b.save('source-register-final.json',dict(at=end,source=row,original_registry_routes=111,directory_coverage_changed=False,object_coverage_complete=False))
b.save('failure-ledger.json',dict(at=end,provider_failures=0,production_write_failures=0,local_preparation_errors=[dict(error='Initial helper copy broadly replaced a date substring',resolution='Corrected references to established 20261011 helpers before any production operation')],automatic_retries=0,spending_limit_changes=0,cloud_backups_created=0))
b.save('milestone-report.json',dict(at=end,measured_batch_runtime_seconds=elapsed,prior_programme_totals=programme['totals'],recorded_cumulative_after_batch={k:programme['totals'][k]+counts[k] for k in counts},prior_totals_scope='Inherited verified checkpoint totals, not an independent entire-catalogue recount',verified_counts=counts,next_task=next_task,report_owner='External supervisor',stop_at_100_hours=False))
evidence=[rel(E/p) for p in ['batch-verification-receipt.json','batch107-live-reconciliation.json','independent-discovery-verification.json','independent-source-verification.json','independent-file-verification.json','actual-visual-review.json','independent-production-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','independent-existing-preservation-verification.json','independent-queue-verification.json','local-recovery-verification.json','milestone-report.json']]
assert all((b.ROOT/p).is_file() for p in evidence)
checkpoint=dict(batch=113,status='complete',outcome='progress',started_at=start,finished_at=end,measured_runtime_seconds=elapsed,verified_counts=counts,production_ids=delivered,image_selection_sha256=receipt['selection_sha256'],stage_counts=dict(researched=25,selected=7,prepared=7,actually_viewed=7,accepted=3,imported=3,verified=3),next_task=next_task,evidence_paths=evidence,delivery_complete_do_not_count_again=True,external_supervisor_unchanged=True,local_catalogue_connections=0)
b.save('CHECKPOINT.json',checkpoint);h.save(b.R/'CHECKPOINT.json',checkpoint)
assert b.load(E/'CHECKPOINT.json')==b.load(b.R/'CHECKPOINT.json')
b.save('independent-checkpoint-verification.json',dict(at=h.now(),matching_evidence_and_runtime_checkpoints=True,evidence_files_exist=True,counts_match_verified_receipt=True,checkpoint_sha256=h.sha((E/'CHECKPOINT.json').read_bytes())))
result=dict(outcome='progress',summary='Verified three new Auckland primary images. Researched 25 museum objects and visually inspected seven prepared images; four composition-proportion cases held. Batch107 reconciled; 110 unrelated source routes preserved.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(E/p) for p in ['batch-verification-receipt.json','independent-production-verification.json','independent-public-verification.json','actual-visual-review.json','independent-resume-verification.json','independent-queue-verification.json','independent-checkpoint-verification.json','CHECKPOINT.json']])
b.save('worker-result.json',result);print(json.dumps(result))
