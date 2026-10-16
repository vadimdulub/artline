import importlib.util,json,datetime,collections,fcntl,copy,os
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-staedel-images-000110.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=h.load(b.E/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts['newly_illustrated']==7
 replay=h.load(b.E/'independent-resume-verification.json');assert replay['unchanged_snapshot'] and not any(replay['replay_increments'].values())
 gap=h.load(b.E/'gap-input.json.gz');holds=h.load(b.E/'research-holds.json')['records'];ids=receipt['production_ids'];now=h.now()
 nxt='Research up to 25 pre-1971 paintings, drawings or icons through undercovered DigitaltMuseum; first review provider access and object-specific image rights. Preserve existing holds. Städel image gaps can later resume after UUID 3bbdf8f9-1e37-5114-9006-83749fbb8f31; do not repeat its 16 held objects or the exhausted French reserve.'
 files=['batch-verification-receipt.json','independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','independent-other-gaps-verification.json','independent-campaign-stop-verification.json']
 evidence=[str((b.E/f).relative_to(b.ROOT)) for f in files]
 for f in files:assert (b.E/f).is_file()
 qpath=b.E.parents[1]/'source-queue.json';q=h.load(qpath);before=copy.deepcopy(q)
 entry=next(x for x in q['sources'] if x['source_id']=='staedel')
 if entry.get('last_batch')==110:
  saved=h.load(b.E/'queue-before-finalization.json');original=next(x for x in saved['sources'] if x['source_id']=='staedel');entry.clear();entry.update(copy.deepcopy(original))
 old=copy.deepcopy(entry)
 entry.setdefault('research_history',[]).append(dict(at=now,batch=110,scope='Next10 existing image gaps by UUID, nine exact native metadata pages and seven object-specific PDM statements',verified_counts=counts,evidence_paths=evidence))
 entry.setdefault('prior_resume_cursors',[]).append(old['resume_cursor'])
 cursor=entry['resume_cursor'];cursor['last_researched_artwork_id']=gap['rows'][-1]['id'];cursor['completed_artwork_ids']=list(dict.fromkeys(cursor['completed_artwork_ids']+ids));cursor['held_artwork_ids']=list(dict.fromkeys(cursor['held_artwork_ids']+[x['artwork_id'] for x in holds]));cursor.update(next_source='digitaltmuseum',next_task=nxt)
 entry.update(status='35_existing_gaps_researched_19_primary_images_verified_16_held',checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),last_checked_at=now,last_batch=110,access_status='Nine native object pages and seven per-image Public Domain Mark download statements HTTP200; seven images delivered and independently verified.',latest_batch_verified_counts=counts)
 entry['evidence_paths']=list(dict.fromkeys(entry['evidence_paths']+evidence+[str((b.E/'research-holds.json').relative_to(b.ROOT))]))
 entry['verified_counts']={k:old['verified_counts'].get(k,0)+counts[k] for k in counts}
 entry['remaining_gaps']=dict(museum_image_rights_hold=7,identity_research_pending=9,further_objects='Not yet researched beyond saved UUID cursor')
 assert [x for x in before['sources'] if x['source_id']!='staedel']==[x for x in q['sources'] if x['source_id']!='staedel']
 b.save('queue-before-finalization.json',before)
 tmp=qpath.with_suffix('.b110.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qpath)
 after=h.load(qpath);assert after==q
 b.save('independent-source-queue-verification.json',dict(at=now,source_id='staedel',unrelated_sources_preserved=110,registry_source_count=111,before_sha256=h.sha(json.dumps(before,sort_keys=True).encode()),after_file_sha256=h.sha(qpath.read_bytes()),resume_cursor=cursor,verified_counts=counts))
 elapsed=(datetime.datetime.fromisoformat(now)-datetime.datetime.fromisoformat(h.load(b.E/'started.json')['at'])).total_seconds()
 cp=dict(at=now,batch=110,stage='verified_complete',verified_counts=counts,production_ids=ids,discovered=10,selected=7,prepared=7,imported=7,independently_verified=7,held=3,actual_visual_review=dict(derivatives_individually_viewed=7,originals_separately_viewed=0),measured_batch_runtime_seconds=elapsed,next_task=nxt,evidence_paths=evidence,source_queue=str(qpath),recovery_directory=str(i.BACKUP),local_catalogue_connections=0,supervisor_unchanged=True,cloud_translation_calls=0)
 b.save('CHECKPOINT.json',cp);h.save(b.R/'CHECKPOINT.json',cp)
 baseline=h.load(b.E/'required-input-reconciliation.json')
 b.save('source-register.json',dict(at=now,provider='staedel',registry=[x for x in baseline['complete_original_registry'] if x['source_id']=='staedel'],policy_reference='docs/ARTLINE_IMAGE_USE.md general open-image policy',access_status='HTTP200 native object and per-image PDM routes',remaining_gaps=entry['remaining_gaps'],directory_coverage_increment=0,artwork_coverage=counts))
 supervisor=h.load(b.E.parents[1]/'CHECKPOINT.json');totals=supervisor['totals'];cumulative={k:totals.get(k,0)+counts[k] for k in counts}
 b.save('milestone-report.json',dict(at=now,batch_runtime_seconds=elapsed,programme_started_at=supervisor['started_at'],programme_runtime_note='Programme wall time includes explicit stopped interval; not represented as active compute time.',prior_supervisor_verified_totals=totals,this_batch=counts,expected_totals_after_supervisor_acceptance=cumulative,totals_not_written_to_supervisor=True,new_failures=0,unresolved_cases=holds,next_task=nxt))
 manifest=[dict(path=str((b.E/f).relative_to(b.ROOT)),sha256=h.sha((b.E/f).read_bytes())) for f in files+['CHECKPOINT.json','independent-source-queue-verification.json','milestone-report.json']]
 for f in manifest:assert h.sha((b.ROOT/f['path']).read_bytes())==f['sha256']
 assert h.load(b.E/'CHECKPOINT.json')==h.load(b.R/'CHECKPOINT.json')
 b.save('independent-checkpoint-verification.json',dict(at=h.now(),manifest=manifest,runtime_checkpoint_equal=True,verified_counts=counts,unrelated_queue_entries_unchanged=True))
 print(json.dumps(dict(verified_counts=counts,next_task=nxt)))
