#!/usr/bin/env python3
"""Persist verified batch 100 and only the two actually researched route cursors."""
import copy,datetime,fcntl,gzip,importlib.util,json,os
from pathlib import Path
s=importlib.util.spec_from_file_location('b100','ops/continuous-warsaw-batch-000100.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i;W=b.E;E=W.parent;Q=E.parents[1]/'source-queue.json'
def save(name,v):
 p=E/name
 if not p.exists():h.save(p,v)
 return h.load(p)
def rel(p):return str(p.relative_to(b.ROOT))
def ref(p):return dict(path=rel(p) if p.is_relative_to(b.ROOT) else str(p),sha256=h.sha(p.read_bytes()))
with (b.R/'worker.lock').open('a+') as worker:
 fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (E/'CHECKPOINT.json').exists():
  print('Completed checkpoint retained. Use independent resume verifier for live reconciliation.');raise SystemExit(0)
 receipt=h.load(W/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts==dict(new_painters=0,new_artworks=10,newly_illustrated=10,alternate_images=0,museum_links=10)
 resume=h.load(W/'independent-resume-verification.json');assert resume['new_production_increments_on_resume']==0
 p,pin=h.pinned(b.PHASE);ids=receipt['production_ids'];selected={r['source_id'] for r in p['records']}
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  assert h.snapshot(db,ids)==h.load(W/'independent-production-verification.json')['rows']
  reserve=h.load(E/'french-reserve-live-reconciliation.json');assert h.snapshot(db,list(reserve['live_rows']))==reserve['live_rows']
  recovery=h.load(h.BACKUP/'affected-row-recovery-before.json.gz');assert h.snapshot(db,list(recovery['preserved']))==recovery['preserved']
  museum=db.execute('SELECT to_jsonb(t) v FROM institutions t WHERE id=%s',(b.MID,)).fetchone()['v'];assert museum==recovery['institutions'][0]
 save('independent-existing-preservation-verification.json',dict(at=h.now(),french_reserve_unchanged=188,prior_warsaw_artworks_and_relationships_unchanged=len(recovery['preserved']),museum_unchanged=True,local_database_connections=0))
 page=h.load(W/'warsaw-icons-page12.json')['data'];page_rc=h.load(W/'warsaw-icons-page12.receipt.json');raw=gzip.decompress(Path(page_rc['body_path']).read_bytes());assert h.sha(raw)==page_rc['sha256'] and json.loads(raw)['data']==page and len(page['items'])==24
 oldq=h.load(E/'source-queue-before.json');wc=next(x for x in oldq['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor'];prior=set(wc['processed_native_ids']);dispositions=[];held=[];casts=[]
 for item in page['items']:
  oid=str(item['id'])
  if oid in prior:
   dispositions.append(dict(source_id=oid,outcome='previously_processed',reason='Previously processed source identity; no repeated request or increment.'));continue
  rc=h.load(W/f'object-{oid}.receipt.json');raw=gzip.decompress(Path(rc['body_path']).read_bytes());o=h.load(W/f'object-{oid}.json')['data'];assert h.sha(raw)==rc['sha256'] and rc['status']==200 and json.loads(raw)['data']==o
  techniques={x['name'] for x in o['techniques']};date=o['createDates'][0]['name']
  if oid in selected:outcome='verified_new_illustrated_artwork';reason='Exact inventory, source dates and qualified workshop/place labels, observed composition and primary reproduction; own production insert, rights evidence and public image independently verified.'
  elif oid=='498385':outcome='held_date_review';reason='Early twentieth-century wording requires established editorial boundary interpretation; do not invent a specific end year or automatically expand to 2000.'
  elif oid=='456547':outcome='held_mixed_assembly_unit';reason='Painted hinged triptych with possibly later inserted metal cross and substantial nineteenth-century restoration; preserve one inventory and review complete component/primary-view identity separately.'
  elif 'odlew' in techniques:outcome='saved_cast_candidate';reason='Cast object retained for separate metadata, unit, image and production identity review; not selected or downloaded.';casts.append(oid)
  else:outcome='held_other_medium';reason='Carved figure, mosaic fragment or embossed gospel-cover fragments, not selected painted-panel records; medium and physical-unit review remains pending.'
  if oid not in selected:held.append(oid)
  dispositions.append(dict(source_id=oid,title=o['title'],accession=o['noEvidence'],source_dates=o['createDates'],source_creators=o['authors'],techniques=sorted(techniques),outcome=outcome,reason=reason,receipt=rc))
 assert len(dispositions)==24 and len(held)==14 and len(casts)==9
 save('page-twelve-editorial-dispositions.json',dict(at=h.now(),rows=dispositions,captured=24,previously_processed=0,selected=10,held_or_other_medium=14,all_capture_checksums_verified=True))
 save('saved-cast-candidates.json',dict(at=h.now(),native_ids=casts,records=[x for x in dispositions if x['source_id'] in casts],selected=False,downloaded_images=0,requires='Separate exact object, date, component, source-rights and production reconciliation; no implicit import approval decision.'))
 save('research-holds.json',dict(at=h.now(),french_reserve='All 188 already delivered; zero new increments. Preserve original immutable visual approvals and physical-date uncertainties for 80082, 80437 and 81054.',warsaw=[x for x in dispositions if x['source_id'] in held],prior_holds_preserved=True,no_unchanged_access_retries=True))
 save('failure-ledger.json',dict(at=h.now(),provider_failures=[dict(surface='web.run page renderer for native 440236',outcome='Internal tool access error; official metadata API and selected CDN requests HTTP200. No provider 401/403/429 or bypass.')],production_write_failures=0,held_provider_requests=0,local_recovered_errors=[dict(error='Initial read-only registry display used incorrect column; batch preflight copy accidentally changed 111-row assertion to 121; one orchestration syntax error.',resolution='Corrected display to institution_or_network, retained full 111-row registry and fixed code before any production write. No immutable historical plans altered.')],spending_budget_changes=0))
 programme=h.load(E.parents[1]/'CHECKPOINT.json');assert programme['inflight']['batch']==100
 start=programme['inflight']['started_at'];end=h.now();elapsed=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
 save('batch-verification-receipt.json',dict(receipt,batch=100,started_at=start,finished_at=end,measured_runtime_seconds=elapsed,source_verification_receipt=rel(W/'batch-verification-receipt.json'),french_reserve_selected=0,prior_campaign_additions_excluded=True))
 next_task='Continue the 25 untouched Auckland image-gap UUIDs from batch 95 using approved WikiArt and saved source evidence; preserve failed-profile and native-access holds. Warsaw page 13 (final source search page) remains queued; KHM and MNAC retain their existing independent cursors. Do not rescan the exhausted French reserve without new evidence.'
 baseline_path=E/'source-queue-before.json';baseline=next(x for x in h.load(baseline_path)['sources'] if x['source_id']=='national_museum_warsaw')['programme_verified_counts']
 rollforward={k:baseline[k]+counts[k] for k in counts}
 save('warsaw-reported-count-rollforward.json',dict(at=h.now(),recorded_baseline=baseline,baseline_reference=ref(baseline_path),additional_verified_receipts=[ref(W/'batch-verification-receipt.json')],recorded_cumulative_counts=rollforward,current_batch_verified_counts=counts,scope='Previously verified receipt rollforward; only current ten additions independently counted in this batch. Not a full catalogue recount.'))
 with (Q.parent/'source-queue.worker.lock').open('a+') as l1,(Q.parent/'source-queue.lock').open('a+') as l2:
  fcntl.flock(l1,fcntl.LOCK_EX);fcntl.flock(l2,fcntl.LOCK_EX)
  before=h.load(Q);save('source-queue-immediately-before-update.json',before);after=copy.deepcopy(before);touched={'yale_lux','national_museum_warsaw'}
  for row in after['sources']:
   sid=row['source_id']
   if sid not in touched:continue
   row.update(last_checked_at=end,checkpoint=rel(E/'CHECKPOINT.json'),last_batch=100)
   refs=[rel(E/'french-reserve-live-reconciliation.json'),rel(E/'independent-reserve-evidence-verification.json'),rel(E/'reserve-actual-visual-sample.json')] if sid=='yale_lux' else [rel(W/'batch-verification-receipt.json'),rel(W/'independent-production-verification.json'),rel(W/'independent-public-verification.json'),rel(E/'page-twelve-editorial-dispositions.json')]
   row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+refs));cur=row['resume_cursor'];entry=dict(batch=100,at=end,evidence=refs,verified_counts=counts if sid=='national_museum_warsaw' else {k:0 for k in counts})
   history=row.setdefault('research_history',[])
   if not any(x.get('batch')==100 for x in history):history.append(entry)
   if sid=='yale_lux':
    row['policy_reference']='Original 111-source yale_lux row; docs/ARTLINE_IMAGE_USE.md Continued illustrated expansion; immutable reserve per-file rights and visual evidence.'
    row['access_status']='No new Yale requests; original captures and prior visual decisions checksum verified, all 188 current production identities already illustrated.'
    row['status']='french_reserve_exhausted_live_verified_188_already_delivered';cur.update(inspected=188,already_imported=188,remaining_unimported=0,last_live_reconciliation=refs[0],next_action='Do not replay historical reserve plan or repeat unchanged reserve audit. Zero new candidates; switch to another registry source.');row['latest_batch_verified_counts']={k:0 for k in counts}
   else:
    row['policy_reference']='Original 111-source national_museum_warsaw row; docs/ARTLINE_IMAGE_USE.md general-image-use-policy; official project commercial-reuse capture and per-object DOMENA PUBLICZNA labels.'
    row['status']='ten_page12_painted_icons_holdings_images_verified_page13_next';row['verified_counts']=counts;row['latest_batch_verified_counts']=counts;row['programme_verified_counts']=rollforward;row['programme_count_evidence']=rel(E/'warsaw-reported-count-rollforward.json')
    cur.update(captured_page=12,next_page_after_pending=13,next_discovery_page=13,query_url=page_rc['url'],metadata_page_sha256=page_rc['sha256'],review_ledger=rel(E/'page-twelve-editorial-dispositions.json'),saved_discovery=rel(W/'warsaw-icons-page12.json'),metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],next_step='Rotate to untouched Auckland/KHM gaps, then final page 13. Preserve prior holds; no unchanged retries.',authentication_last_verified_at=end)
    cur['processed_native_ids']=list(dict.fromkeys(cur['processed_native_ids']+[str(x['id']) for x in page['items']]));cur['held_native_ids']=list(dict.fromkeys(cur.get('held_native_ids',[])+held));cur['delivered_native_ids']=list(dict.fromkeys(cur.get('delivered_native_ids',[])+sorted(selected)))
    cur['saved_cast_candidate_native_ids']=list(dict.fromkeys(cur.get('saved_cast_candidate_native_ids',[])+cur.get('latest_cast_candidate_ids',[])+casts));cur['latest_cast_candidate_ids']=casts;cur['prior_cast_candidate_ledger']=cur.get('cast_candidate_ledger');cur['cast_candidate_ledger']=rel(E/'saved-cast-candidates.json')
    row['access_status']='Official page 12 and 24 native details HTTP200; ten selected images, storage and public delivery verified.'
    row['remaining_gaps']=[str(len(cur['held_native_ids']))+' recorded editorial holds or other-medium candidates; all prior identities retained.',str(len(cur['saved_cast_candidate_native_ids']))+' saved cast candidates; separate physical-unit/date/identity review required.','Page 13 unreviewed; no whole-institution or directory coverage claim.']
  assert len(after['sources'])==111 and [r for r in before['sources'] if r['source_id'] not in touched]==[r for r in after['sources'] if r['source_id'] not in touched]
  tmp=Q.with_suffix('.batch100.tmp')
  with tmp.open('wb') as f:f.write(json.dumps(after,ensure_ascii=False,indent=2).encode());f.flush();os.fsync(f.fileno())
  os.replace(tmp,Q);assert h.load(Q)==after
  save('source-queue-after.json',after);save('independent-queue-verification.json',dict(at=h.now(),modified_source_ids=sorted(touched),unrelated_routes_preserved=109,original_registry_routes=111,before_sha256=h.sha(json.dumps(before,sort_keys=True).encode()),after_sha256=h.sha(Q.read_bytes()),exact_unrelated_structures_equal=True,atomic_replace=True))
 save('source-register-final.json',dict(at=end,original_registry_rows=111,registry_sha256=h.load(E/'required-input-reconciliation.json')['inputs'][1]['sha256'],researched_routes=[r for r in after['sources'] if r['source_id'] in touched],directory_coverage_changed=False,object_coverage_complete=False,rights_approvals_not_generalized=True))
 evidence=[rel(E/x) for x in ['batch-verification-receipt.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','reserve-actual-visual-sample.json','independent-existing-preservation-verification.json','page-twelve-editorial-dispositions.json','research-holds.json','failure-ledger.json','external-continuation-verification.json','independent-queue-verification.json','source-register-final.json']]
 evidence += [rel(W/x) for x in ['independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','local-recovery-verification.json']]
 assert all((b.ROOT/x).is_file() for x in evidence)
 checkpoint=dict(batch=100,status='complete',outcome='progress',started_at=start,finished_at=end,measured_runtime_seconds=elapsed,verified_counts=counts,production_ids=ids,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],stage_counts=dict(french_reserve_inspected=188,french_reserve_already_imported=188,warsaw_page_items=24,warsaw_new_details_captured=24,selected=10,prepared=10,imported=10,verified=10,held_or_other_medium=14),next_task=next_task,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000100-resume.py',verification_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000100-verify.py',delivery_complete_do_not_count_again=True,evidence_paths=evidence,external_supervisor_unchanged=True,local_catalogue_connections=0,limitations=['All ten 315-pixel originals and derivatives visually reviewed; fine inscriptions and reverse sides not inspected.','Recovery is full schema plus exact affected-row preimages, not a full catalogue export.','Programme baseline totals are inherited supervisor figures; whole-catalogue million/300000 goals not recounted.'])
 save('CHECKPOINT.json',checkpoint);h.save(b.R/'CHECKPOINT.json',checkpoint)
 save('batch-summary.json',dict(at=end,measured_runtime_seconds=elapsed,verified_counts=counts,prior_programme_totals=programme['totals'],recorded_cumulative_after_batch={k:programme['totals'][k]+counts[k] for k in counts},prior_totals_source='External supervisor checkpoint; not independently re-audited by this batch.',next_task=next_task,reporting_owner='External supervisor owns hourly and 100-hour milestone reports; no schedule edited.'))
 final=dict(outcome='progress',summary='Verified ten new Warsaw painted icons, ten primary images and ten museum links. All originals and derivatives viewed; production, storage, public delivery and idempotent replay verified. French reserve: 188 already delivered, zero new additions. Preserved 109 unrelated source routes.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(E/'batch-verification-receipt.json'),rel(W/'independent-production-verification.json'),rel(W/'independent-public-verification.json'),rel(W/'actual-visual-review.json'),rel(W/'independent-resume-verification.json'),rel(E/'independent-queue-verification.json'),rel(E/'CHECKPOINT.json')])
 save('worker-result.json',final);print(json.dumps(final))
