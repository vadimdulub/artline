"""Persist verified single-batch results and precise source cursors; no supervisor edits."""
import copy,csv,datetime,fcntl,gzip,importlib.util,json,os,subprocess
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-khm-images-000103.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
E=b.E.parent;R=b.R.parent;Q=E.parent.parent/'source-queue.json'
def rel(p):return str(p.relative_to(b.ROOT))
def save(name,v):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,v);return v
def ref(p):return dict(path=str(p),sha256=h.sha(p.read_bytes()))
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (E/'CHECKPOINT.json').exists():
  assert h.load(E/'CHECKPOINT.json')==h.load(R/'CHECKPOINT.json');print('Completed checkpoint exists; no new queue mutations.');raise SystemExit(0)
 receipt=h.load(b.E/'batch-verification-receipt.json');counts=receipt['verified_counts'];ids=receipt['production_ids'];assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=1,alternate_images=0,museum_links=0)
 assert not any(h.load(b.E/'independent-resume-verification.json')['replay_increments'].values())
 programme=h.load(E.parent.parent/'CHECKPOINT.json');assert programme['inflight']['batch']==103
 start=programme['inflight']['started_at'];end=h.now();elapsed=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
 # Fresh preservation: reserve and prior batch were already delivered, never counted here.
 with b.connect() as db:
  reserve=h.load(b.E/'french-reserve-live-reconciliation.json');assert h.snapshot(db,list(reserve['live_rows']))==reserve['live_rows']
  prev=h.load(E.parent/'000102/independent-production-verification.json');assert h.snapshot(db,list(prev['rows']))==prev['rows']
  rec=h.load(i.BACKUP/'affected-row-recovery-before.json.gz');nowinst=[r['v'] for r in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,))];assert nowinst==rec['institutions']
 save('independent-existing-preservation-verification.json',dict(at=h.now(),french_reserve_artworks_unchanged=188,prior_walters_artworks_unchanged=9,institution_unchanged=True,local_catalogue_connections=0))
 captures=[]
 for p in sorted((b.E/'source-captures').glob('*.json')):
  rc=h.load(p);raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'];captures.append(dict(receipt=rel(p),**rc))
 source_by_url={x['url']:x for x in captures};profiles={'Lucas Cranach the Younger':'lucas-cranach-the-younger','Hieronymus Bosch':'hieronymus-bosch','Giovanni Girolamo Savoldo':'giovanni-girolamo-savoldo','Pieter Claesz':'pieter-claesz','Francesco Bassano the Younger':'francesco-bassano','Palma il Giovane':'palma-il-giovane','Salomon van Ruysdael':'salomon-van-ruysdael','Jacopo Bassano':'jacopo-bassano'}
 dispositions=[];inp=h.load(b.E/'gap-input.json.gz')
 reasons={
 'Lucas Cranach the Younger':('profile_404','Queried profile URL returned404. No alternative artist attribution or work identity invented.'),
 'Giovanni Girolamo Savoldo':('profile_404','Queried profile URL returned404; source profile identity remains unresolved.'),
 'Francesco Bassano the Younger':('profile_404','Queried profile URL returned404; this does not establish lack of available images elsewhere.'),
 'Hieronymus Bosch':('further_review','WikiArt Vienna cross-bearing recto has useful location and dimensions, but the double-sided panel and existing illustrated reverse record need explicit physical-unit review. Prior direct official route403 not retried. No image downloaded.'),
 'Pieter Claesz':('identity_unresolved','Captured vanitas page gives1660, no museum or dimensions; catalogue has1656. Other vanitas titles exist. Same physical object not established; no download.'),
 'Palma il Giovane':('identity_unresolved','No Salome result in captured index. Two Lamentation pages: one explicitly drawing (wrong medium), one oil painting without museum/date/dimensions. Exact Vienna canvas not established.'),
 'Jacopo Bassano':('identity_unresolved','Captured index offers1544 Kings and1569 Magi, not a secure match for1555 Vienna inventory361. Date/title differences require object-level comparison.'),
 'Salomon van Ruysdael':('verified_primary_image','Exact GG6210 filename, dated museum source and original citation reconciled; selected original/derivative viewed and production/public image verified. Unknown WikiArt date preserved.')}
 for row in inp['rows']:
  if row['creator'] not in profiles:continue
  slug=profiles[row['creator']];url='https://www.wikiart.org/en/'+slug+'/all-works/text-list';rc=source_by_url[url];outcome,reason=reasons[row['creator']]
  dispositions.append(dict(artwork_id=row['id'],title=row['title'],creator=row['creator'],outcome=outcome,reason=reason,profile_url=url,receipt=rc['receipt'],source_status=rc['status']))
 assert len(dispositions)==11;processed={r['artwork_id'] for r in dispositions};pending=[r['id'] for r in inp['rows'] if r['id'] not in processed];assert len(pending)==13
 save('independent-discovery-verification.json',dict(at=h.now(),rows=dispositions,source_captures=captures,all_capture_hashes_verified=True,staged_gaps=24,researched_gaps=11,untouched_gap_ids=pending,selected=1,prepared=1,verified=1,scope='Five successful creator indexes, three404 profiles, six artwork pages and one current official museum metadata page. Search engines were discovery only; product/store results not accepted.'))
 save('research-holds.json',dict(at=end,rows=[r for r in dispositions if r['artwork_id'] not in ids],prior_holds_preserved=True,unknown_source_year_not_rewritten=True,french_reserve='188 already delivered; original physical-date holds80082,80437,81054 unchanged',native_images_downloaded=0))
 save('failure-ledger.json',dict(at=end,provider_failures=[r for r in captures if r['status']!=200],retry_policy='No unchanged404 or held endpoint retries.',local_failures=[dict(kind='worker_lock_contention',resolved='Research command refused while stage held batch lock; rerun only after stage completion. No overlapping work.'),dict(kind='read_only_sql_order_by',resolved='Scoped DISTINCT query ORDER BY a.id mismatched text projection; corrected to ORDER BY1. Failed transaction read-only; no mutation.')],remaining_blockers=[]))
 save('batch-verification-receipt.json',dict(receipt,batch=103,started_at=start,finished_at=end,measured_runtime_seconds=elapsed,french_reserve_selected=0,prior_campaign_additions_excluded=True))
 next_task='Research Warsaw painted-icon search page13, the final saved search-page cursor, preserving all editorial and image access holds. KHM retains13 untouched UUIDs plus10 explicit research holds/leads from this batch; do not repeat failed profiles or the exhausted French reserve without new evidence.'
 with (Q.parent/'source-queue.worker.lock').open('a+') as l1,(Q.parent/'source-queue.lock').open('a+') as l2:
  fcntl.flock(l1,fcntl.LOCK_EX);fcntl.flock(l2,fcntl.LOCK_EX)
  before=h.load(Q);save('source-queue-immediately-before-update.json',before);after=copy.deepcopy(before);touched={'yale_lux','khm_vienna'}
  for row in after['sources']:
   sid=row['source_id']
   if sid not in touched:continue
   cur=row['resume_cursor'];row.update(last_checked_at=end,last_batch=103,checkpoint=rel(E/'CHECKPOINT.json'))
   refs=[rel(b.E/'french-reserve-live-reconciliation.json'),rel(b.E/'independent-reserve-evidence-verification.json'),rel(b.E/'reserve-actual-visual-sample.json')] if sid=='yale_lux' else [rel(E/'independent-discovery-verification.json'),rel(b.E/'batch-verification-receipt.json'),rel(b.E/'independent-production-verification.json'),rel(b.E/'independent-public-verification.json'),rel(b.E/'actual-visual-review.json'),rel(b.E/'independent-resume-verification.json')]
   row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+refs));entry=dict(batch=103,at=end,evidence=refs,verified_counts=counts if sid=='khm_vienna' else {k:0 for k in counts})
   row.setdefault('research_history',[]).append(entry);row['latest_batch_verified_counts']=entry['verified_counts']
   if sid=='yale_lux':
    row['status']='french_reserve_exhausted_live_verified_188_already_delivered';cur.update(inspected=188,already_imported=188,remaining_unimported=0,last_live_reconciliation=refs[0],next_action='No new reserve objects. Do not replay historical plans or repeat this audit without new evidence; rotate registry routes.')
    row['access_status']='No Yale network requests. All188 original source captures, checksum-bound visual decisions and current production identities reconciled; already delivered by prior campaign.'
   else:
    row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(cur));assert set(cur['pending_artwork_ids'])=={r['id'] for r in inp['rows']}
    cur['researched_artwork_ids']=list(dict.fromkeys(cur['researched_artwork_ids']+sorted(processed)));cur['pending_artwork_ids']=pending
    cur['verified_artwork_ids']=list(dict.fromkeys(cur['verified_artwork_ids']+ids));cur['held_artwork_ids']=list(dict.fromkeys(cur.get('held_artwork_ids',[])+sorted(processed-set(ids))))
    cur['profile_404_no_unchanged_retry']=list(dict.fromkeys(cur.get('profile_404_no_unchanged_retry',[])+[r['url'] for r in captures if r['status']==404]))
    cur.update(hold_ledger=rel(E/'research-holds.json'),prior_hold_ledger=rel(E.parent/'000098/research-holds.json'),discovery_evidence=rel(E/'independent-discovery-verification.json'),verified_evidence=rel(b.E/'independent-production-verification.json'),selection_sha256=receipt['selection_sha256'],next_step='13 untouched UUIDs remain. Reuse successful indexes and preserve10 new holds/leads plus all earlier holds. Rotate to Warsaw page13 before next KHM batch.')
    row['status']='one_additional_primary_image_verified_13_untouched_frozen_ids_remain';row['access_status']='Five WikiArt indexes, six object pages and official KHM GG6210 metadata HTTP200. Three profile URLs404, no unchanged retry. Only one selected WikiArt source image downloaded; native museum images not downloaded.'
    row['remaining_gaps']=['13 untouched frozen gaps;10 newly researched holds/leads plus prior holds preserved.','Bosch recto/verso physical-unit review remains pending; no forced merge.','Unknown WikiArt Ruysdael year preserved, signed1627 official source establishes image scope.','Native KHM image reuse remains separately restricted; WikiArt approval not generalized.']
    baseline=row.get('programme_verified_counts',{k:0 for k in counts});row['programme_verified_counts']={k:baseline[k]+counts[k] for k in counts};row['programme_count_evidence']=rel(E/'batch-verification-receipt.json')
  assert len(after['sources'])==111 and [r for r in before['sources'] if r['source_id'] not in touched]==[r for r in after['sources'] if r['source_id'] not in touched]
  tmp=Q.with_suffix('.batch103.tmp')
  with tmp.open('wb') as f:f.write(json.dumps(after,ensure_ascii=False,indent=2).encode());f.flush();os.fsync(f.fileno())
  os.replace(tmp,Q);assert h.load(Q)==after
  save('source-queue-after.json',after);save('independent-queue-verification.json',dict(at=h.now(),modified_source_ids=sorted(touched),unrelated_routes_preserved=109,original_registry_routes=111,exact_unrelated_structures_equal=True,atomic_replace=True,queue_sha256=h.sha(Q.read_bytes())))
 regpath=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry=list(csv.DictReader(regpath.open()));assert len(registry)==111
 save('source-register-final.json',dict(at=end,original_registry=ref(regpath),original_registry_rows=111,researched_routes=[r for r in after['sources'] if r['source_id'] in touched],directory_coverage_changed=False,artwork_coverage_complete=False))
 pid=programme['supervisor_pid'];ps=subprocess.check_output(['ps','-p',str(pid),'-o','pid=,etime=,comm='],text=True).strip();assert ps.startswith(str(pid))
 save('external-continuation-verification.json',dict(at=h.now(),supervisor_pid=pid,live_process=ps,current_checkpoint_inflight_batch=programme['inflight']['batch'],prior_completed_batch=programme['previous']['verified_counts'],existing_process_verified=True,supervisor_schedule_prompt_and_schema_unchanged=True,new_processes_or_schedules_created=0,scope='Existing supervisor observed alive with batch103 in flight after completed102; this worker executed one batch. Future scheduler behavior not guaranteed.'))
 evidence=[rel(E/x) for x in ['batch-verification-receipt.json','independent-existing-preservation-verification.json','independent-discovery-verification.json','research-holds.json','failure-ledger.json','independent-queue-verification.json','source-register-final.json','external-continuation-verification.json']]+[rel(b.E/x) for x in ['french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','reserve-actual-visual-sample.json','independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','local-recovery-verification.json','prior-batch-live-reconciliation.json']]
 assert all((b.ROOT/p).is_file() for p in evidence)
 cp=dict(batch=103,status='complete',outcome='progress',started_at=start,finished_at=end,measured_runtime_seconds=elapsed,verified_counts=counts,production_ids=ids,selection_sha256=receipt['selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],stage_counts=dict(french_reserve_inspected=188,french_reserve_already_delivered=188,french_selected=0,khm_staged=24,khm_researched=11,khm_untouched=13,selected=1,prepared=1,imported=1,verified=1),next_task=next_task,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-khm-000103-verify.py',delivery_complete_do_not_count_again=True,local_catalogue_connections=0,evidence_paths=evidence,limitations=['One selected WikiArt original and derivative viewed; one reserve derivative sampled, other187 reuse immutable prior reviews.','Full schema plus scoped production preimages preserved; not a full database backup.','Only this batch increment independently counted; earlier supervisor cumulative totals not re-audited.','No catalogue metadata, creators, holdings, editorial states, publication gates or application deployment changed.'])
 save('CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
 save('batch-summary.json',dict(at=end,measured_runtime_seconds=elapsed,verified_counts=counts,prior_programme_totals=programme['totals'],recorded_cumulative_after_batch={k:programme['totals'][k]+counts[k] for k in counts},prior_totals_scope='Inherited external supervisor figures; only present batch independently counted.',next_task=next_task,hourly_and_100_hour_reporting_owner='Existing supervisor; no stopping threshold introduced.'))
 result=dict(outcome='progress',summary='Verified one authentic primary image on an existing KHM painting. French reserve: all188 already delivered, zero new additions. Production attribution, public delivery and unchanged replay verified;109 unrelated source routes preserved.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(E/'batch-verification-receipt.json'),rel(b.E/'french-reserve-live-reconciliation.json'),rel(b.E/'independent-production-verification.json'),rel(b.E/'independent-public-verification.json'),rel(b.E/'actual-visual-review.json'),rel(b.E/'independent-resume-verification.json'),rel(E/'independent-queue-verification.json'),rel(E/'CHECKPOINT.json')])
 save('worker-result.json',result);print(json.dumps(result))
