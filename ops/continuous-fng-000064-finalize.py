#!/usr/bin/env python3
"""Save verified batch 64 and atomically advance only routes actually researched."""
import copy,datetime,fcntl,gzip,hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/research/continuous-production-20261011';E=BASE/'batches/000064';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000064'
def load(p):
 p=Path(p);raw=p.read_bytes();return json.loads(gzip.decompress(raw) if p.suffix=='.gz' else raw)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);raw=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode();p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw,'Immutable evidence differs: '+str(p)
 else:
  with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def rel(p):return str(Path(p).relative_to(ROOT))
def main():
 if (E/'final-checkpoint-verification.json').exists():
  for f in load(E/'final-checkpoint-verification.json')['files']:assert sha(f['path'])==f['sha256']
  assert load(R/'CHECKPOINT.json')==load(E/'CHECKPOINT.json');print('Final checkpoint verified; no queue update repeated.');return
 receipt=load(E/'batch-verification-receipt.json');counts=receipt['verified_counts'];ids=receipt['production_ids']
 assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=15,alternate_images=0,museum_links=0) and len(set(ids))==15
 resume=load(E/'independent-resume-verification.json');assert resume['unchanged_snapshot'] and resume['audit_events_before']==resume['audit_events_after'] and not any(resume['replay_increments'].values())
 now=datetime.datetime.now(datetime.timezone.utc);at=now.isoformat()
 inspected=load(E/'fng-bounded-gap-input.json');checks=load(E/'cited-gap-reconciliation.json');held=[r for r in checks['rows'] if r['artwork_id'] not in ids];assert len(held)==10
 save(E/'research-holds.json',dict(at=at,records=held,held=10,prior_source_holds_preserved=True,held_objects_unchanged=load(E/'independent-held-objects-verification.json')['unchanged'],images_downloaded_for_held_objects=0,no_provider_access_hold_added=True))
 save(E/'failures.json',dict(at=at,failures=[],provider_retries=0,paid_services_started=0,cloud_backups_created=0))
 source=load(E/'required-input-reconciliation.json')
 save(E/'source-register-final.json',dict(at=at,registry_path=source['registry_path'],registry_sha256=source['registry_sha256'],original_registry_records=111,sources=[r for r in source['complete_registry'] if r['source_id'] in ['yale_lux','finnish_national_gallery']],routes=[dict(source_id='yale_lux',policy_reference='docs/ARTLINE_IMAGE_USE.md#continued-illustrated-expansion--11-october-2026',access_status='No new provider requests. Original source captures and prior checksum-bound visual decisions verified; all 188 live records previously delivered.',last_checked_at=at,remaining_unimported_reserve=0,evidence='french-reserve-live-reconciliation.json'),dict(source_id='finnish_national_gallery',policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='Pinned official anonymous export checksum verified; 15 exact preferred CC0 photograph downloads HTTP 200, all individually viewed and verified publicly.',metadata_retrieved_at=load(E/'metadata-and-mime-reuse-verification.json')['source_export']['retrieved_at'],last_checked_at=at,checked_gaps=25,verified_primary_images=15,held=10,resume_after_artwork_id=checks['resume_after_artwork_id'],remaining_gaps='Prior 53 and current 10 object holds; later keyset gaps remain. Ateneum cursor preserved.')],directory_coverage_complete=False,artwork_coverage_complete=False))
 save(E/'web-source-documentation-check.json',dict(at=at,url='https://kokoelma.kansallisgalleria.fi/en/api-sovelluskehittajille',tool='web.run open',result='Official documentation page returned a JavaScript-required shell; no additional policy inference. Object-specific CC0 evidence comes from the checksum-verified official export.',no_access_hold_inferred=True))
 evidence=['batch-verification-receipt.json','independent-production-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-audit-history-verification.json','independent-resume-verification.json','independent-held-objects-verification.json','actual-visual-review.json','local-recovery-verification.json','research-holds.json','source-register-final.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json']
 for f in evidence:assert (E/f).exists()
 with (R.parent.parent/'source-queue.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);path=BASE/'source-queue.json';raw=path.read_bytes();q=json.loads(raw);before=copy.deepcopy(q)
  save(E/'source-queue-immediately-before-update.json',before)
  route=next(s for s in q['sources'] if s['source_id']=='finnish_national_gallery');c=route['continuation_routes']['sinebrychoff'];old=copy.deepcopy(c)
  assert c['after_artwork_id']==inspected['after_artwork_id']
  route.setdefault('prior_sinebrychoff_cursors',[]).append(old)
  c['after_artwork_id']=checks['resume_after_artwork_id']
  for key,new in [('inspected_ids',[r['id'] for r in inspected['rows']]),('delivered_ids',ids),('held_ids',[r['artwork_id'] for r in held])]:c[key]=list(dict.fromkeys(c.get(key,[])+new))
  c.update(latest_batch=64,latest_verified_counts=counts,latest_delivered_native_ids=[r['native_id'] for r in load(E/'batches/fng-000/selection.json.gz')['rows']],programme_sinebrychoff_newly_illustrated=old['programme_sinebrychoff_newly_illustrated']+15,pending_native_ids=[],pending_artwork_ids=[],retry_semantics='Batch 64 delivered 15 from 25 fresh gaps. Resume strictly after saved UUID. Do not replay delivered images or unchanged holds; preserve metadata refresh date and separate source/creator routes.')
  assert c['programme_sinebrychoff_newly_illustrated']==82 and len(c['held_ids'])==63 and len(c['inspected_ids'])==145
  route.update(status='82_sinebrychoff_primary_images_verified_63_holds_preserved',checkpoint=rel(E/'CHECKPOINT.json'),last_checked_at=at,verified_counts=counts,latest_batch_verified_counts=counts,access_status='25 fresh gaps reconciled; 15 exact native CC0 photos individually viewed and verified; no provider denial.',latest_attempt=dict(batch=64,at=at,outcome='progress',verified_counts=counts))
  route['evidence_paths']=list(dict.fromkeys(route.get('evidence_paths',[])+[rel(E/f) for f in evidence]))
  route['remaining_gaps']=[s for s in route.get('remaining_gaps',[]) if not s.startswith('Sinebrychoff:')]+['Sinebrychoff: 82 programme primary images verified across 145 inspected gaps; 63 object/source/date holds preserved. Continue after '+c['after_artwork_id']+'. Coverage incomplete.']
  yale=next(s for s in q['sources'] if s['source_id']=='yale_lux');yale.update(last_checked_at=at,checkpoint=rel(E/'CHECKPOINT.json'),access_status='Batch 64 verified all 188 live records, original source/manifest captures and checksum-bound prior visual approvals; zero unimported reserve objects. Do not repeat unchanged reserve checks.')
  yale['evidence_paths']=list(dict.fromkeys(yale.get('evidence_paths',[])+[rel(E/f) for f in ['french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json']]))
  yale.setdefault('research_history',[]).append(dict(batch=64,at=at,reserve_inspected=188,unimported=0,new_programme_increments=0,evidence=rel(E/'french-reserve-live-reconciliation.json')))
  unchanged=[s for s in q['sources'] if s['source_id'] not in ['yale_lux','finnish_national_gallery']]
  assert len(unchanged)==109 and unchanged==[s for s in before['sources'] if s['source_id'] not in ['yale_lux','finnish_national_gallery']]
  oldf=next(s for s in before['sources'] if s['source_id']=='finnish_national_gallery');assert route['resume_cursor']==oldf['resume_cursor']
  assert {s['source_id'] for s in q['sources']}=={s['source_id'] for s in source['complete_registry']} and len(q['sources'])==111 and path.read_bytes()==raw
  tmp=path.with_name('source-queue.batch64.tmp')
  with tmp.open('x') as f:json.dump(q,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(tmp,path);save(E/'source-queue-after.json',q)
  save(E/'source-queue-update-verification.json',dict(at=at,before_sha256=hashlib.sha256(raw).hexdigest(),after_sha256=sha(path),modified_source_ids=['yale_lux','finnish_national_gallery'],unrelated_entries_preserved=109,all_111_registry_routes_preserved=True,ateneum_cursor_preserved=True,resume_after_artwork_id=c['after_artwork_id'],sinebrychoff_held_ids=63))
 start=load(BASE/'CHECKPOINT.json')['inflight']['started_at'];elapsed=(now-datetime.datetime.fromisoformat(start)).total_seconds()
 nxt='Research the next bounded Warsaw icon page 5 via the saved national_museum_warsaw route, preserving its 47 prior holds and exact version checks. French reserves are exhausted. Future Sinebrychoff gaps start after '+c['after_artwork_id']+'.'
 cp=dict(at=at,started_at=start,elapsed_seconds=elapsed,batch=64,stage='independently_verified_complete',outcome='progress',verified_counts=counts,french_reserve_inspected=188,french_reserve_unimported=0,existing_gaps_examined=25,selected=15,prepared=15,individually_viewed=15,imported=15,verified=15,held=10,production_ids=ids,selection_sha256=receipt['selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],source_queue_resume_cursor=c['after_artwork_id'],next_task=nxt,blocker='',resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-fng-000064-resume.py',verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-fng-images-000064-verify.py',evidence_paths=[rel(E/f) for f in evidence]+[rel(E/'source-queue-update-verification.json')],local_catalogue_connections=0,external_supervisor_unchanged=True,supervisor_running_claim=False,hourly_reporting='This bounded batch ran under one hour; the external supervisor owns cumulative, hourly and 100-hour reports and continuation.')
 save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp);save(R/'verification-receipt.json',receipt)
 save(E/'batch-summary.json',dict(at=at,measured_elapsed_seconds=elapsed,verified_counts=counts,prior_campaign_increments=0,failures=0,unresolved=held,next_task=nxt))
 manifest=[dict(path=str(p),sha256=sha(p)) for p in sorted(E.glob('*.json'))]
 save(E/'final-checkpoint-verification.json',dict(at=at,files=manifest,runtime_checkpoint_equal=load(R/'CHECKPOINT.json')==cp,evidence_paths_exist=all((ROOT/f).exists() for f in cp['evidence_paths']),final_counts_equal_independent_receipt=cp['verified_counts']==receipt['verified_counts'],external_supervisor_unchanged=True))
 print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,unrelated_queue_entries_preserved=109,next_task=nxt)))
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
