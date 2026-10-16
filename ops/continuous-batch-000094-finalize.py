#!/usr/bin/env python3
"""Verify and persist this bounded worker's result without editing its supervisor."""
import copy,datetime,fcntl,gzip,importlib.util,json,os,subprocess
from pathlib import Path
s=importlib.util.spec_from_file_location('b94w','ops/continuous-warsaw-batch-000094.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i;W=b.E;E=W.parent;Q=E.parents[1]/'source-queue.json'
def save(name,v):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,v);return v
def ref(p):return dict(path=str(p),sha256=h.sha(p.read_bytes()))
def rel(p):return str(p.relative_to(b.ROOT))
with (b.R/'worker.lock').open('a+') as worker:
 fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (E/'CHECKPOINT.json').exists():
  checkpoint=h.load(E/'CHECKPOINT.json')
  for ep in checkpoint['evidence_paths']:assert (b.ROOT/ep).is_file()
  print('Completed batch checkpoint preserved; use dedicated resume verifier for fresh live checks.');raise SystemExit(0)
 receipt=h.load(W/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts==dict(new_painters=0,new_artworks=7,newly_illustrated=7,alternate_images=0,museum_links=7)
 assert h.load(W/'independent-resume-verification.json')['new_production_increments_on_resume']==0
 p,pin=h.pinned(b.PHASE);ids=receipt['production_ids'];selected={r['source_id'] for r in p['records']}
 with h.connect() as db:
  assert h.snapshot(db,ids)==h.load(W/'independent-production-verification.json')['rows']
  qag=h.load(E/'qagoma-before.json.gz');assert h.snapshot(db,list(qag))==qag
  reserve=h.load(E/'french-reserve-live-reconciliation.json');assert h.snapshot(db,list(reserve['live_rows']))==reserve['live_rows']
  recovery=h.load(h.BACKUP/'affected-row-recovery-before.json.gz');assert h.snapshot(db,list(recovery['preserved']))==recovery['preserved']
  museum=db.execute('SELECT to_jsonb(t) v FROM institutions t WHERE id=%s',(b.MID,)).fetchone()['v'];assert museum==recovery['institutions'][0]
 save('independent-existing-preservation-verification.json',dict(at=h.now(),qagoma_unchanged=9,french_reserve_unchanged=188,prior_warsaw_artworks_and_relationships_unchanged=len(recovery['preserved']),museum_unchanged=True,local_database_connections=0))
 discovery=h.load(E/'qagoma-discovery.json');qagrows=[]
 for row in discovery['rows']:
  rc=row['discovery']['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==404 and not row['selected']
  qagrows.append(dict(artwork_id=row['id'],title=row['title'],creator_label=row['unlinked_creator_label'],url=rc['url'],status=404,receipt=rc,outcome='researched_unresolved',reason=row['reason']))
 assert len(qagrows)==9
 save('independent-qagoma-verification.json',dict(at=h.now(),rows=qagrows,distinct_profile_routes=8,selected=0,downloads=0,verified_production_increments=0,metadata_and_primary_images_unchanged=True,native_access_hold_preserved=True,profile_404_is_not_provider_wide_hold=True,no_claim_of_exhaustive_web_search=True,source_evidence=ref(E/'qagoma-source-verification.json')))
 page=h.load(W/'warsaw-icons-page10.json')['data'];page_rc=h.load(W/'warsaw-icons-page10.receipt.json');raw=gzip.decompress(Path(page_rc['body_path']).read_bytes());assert h.sha(raw)==page_rc['sha256'] and json.loads(raw)['data']==page
 assert page['paginatorDetails']['currentPage']==10 and len(page['items'])==24
 oldq=h.load(E/'source-queue-before.json');wc=next(x for x in oldq['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor'];processed=set(wc['processed_native_ids']);dispositions=[];held=[];casts=[]
 for item in page['items']:
  oid=str(item['id'])
  if oid in processed:
   dispositions.append(dict(source_id=oid,outcome='previously_processed',reason='Prior cursor identity; no repeated detail request or count.'));continue
  rc=h.load(W/f'object-{oid}.receipt.json');raw=gzip.decompress(Path(rc['body_path']).read_bytes());o=h.load(W/f'object-{oid}.json')['data'];assert h.sha(raw)==rc['sha256'] and rc['status']==200 and json.loads(raw)['data']==o
  techniques={x['name'] for x in o['techniques']};date=o['createDates'][0]['name']
  if oid in selected:outcome='verified_new_illustrated_artwork';reason='Exact distinct painted inventory, source dates, qualified workshop, public-domain primary image and production increment verified.'
  elif 'odlew' in techniques or 'relief' in techniques:outcome='saved_other_medium';reason='Cast or carved object outside selected painted-icon batch; retained for separate medium/date/unit review, no image download.';casts.append(oid)
  elif '/a-b' in o['noEvidence']:outcome='held_compound_inventory';reason='Painting and oklad share compound inventory; exact catalogue unit and unobstructed supplied view require review.'
  elif oid in ['498393','498401']:outcome='held_same_title_versions';reason='Multiple Saint Nicholas panels in current museum catalogue; exact composition/version reconciliation remains pending.'
  elif 'XIX/XX' in date:outcome='held_date_review';reason='Source century-transition wording requires established date review; no guessed 1900 creation date or automatic eligibility.'
  else:outcome='held_other_medium';reason='Embroidery or enamel-only icon cover outside this selected painted-panel batch; no painted composition inferred.'
  if oid not in selected:held.append(oid)
  dispositions.append(dict(source_id=oid,title=o['title'],accession=o['noEvidence'],source_date=date,techniques=sorted(techniques),outcome=outcome,reason=reason,receipt=rc))
 assert len(dispositions)==24 and len(held)==16
 save('page-ten-editorial-dispositions.json',dict(at=h.now(),rows=dispositions,captured=23,previously_processed=1,selected=7,held_or_other_medium=16,all_capture_checksums_verified=True))
 save('research-holds.json',dict(at=h.now(),french_reserve='All 188 already delivered; zero new increments. Original physical-date uncertainties and prior visual decisions retained.',qagoma=qagrows,warsaw=[x for x in dispositions if x['source_id'] in held],unchanged_prior_holds_preserved=True))
 save('authorization.json',dict(at=h.now(),batch=94,user_authorization='One bounded source-backed production batch, no per-batch approval. Seven selected museum objects, images and holdings.',source_rights='Native DOMENA PUBLICZNA and explicit museum project commercial-use evidence retained separately from user authorization.',policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',local_catalogue_read_only=True,no_deletion_commit_push_deploy_or_infrastructure_changes=True))
 save('failure-ledger.json',dict(at=h.now(),provider_responses=[dict(url=x['url'],status=404,retries=0,affected_artwork_ids=[r['artwork_id'] for r in qagrows if r['url']==x['url']]) for j,x in enumerate(qagrows) if x['url'] not in [r['url'] for r in qagrows[:j]]],local_recovered_errors=[dict(error='KeyError next_page in discovery cursor check',resolution='Used established next_page_after_pending key after inspecting queue; failure occurred before source requests or writes.'),dict(error='System Python lacked bs4 for read-only policy excerpt',resolution='Used existing Artline research virtual environment; no installation or environment mutation.')],production_write_failures=0,held_provider_requests=0,spending_budget_changes=0))
 programme=h.load(E.parents[1]/'CHECKPOINT.json');start=programme['inflight']['started_at'];end=h.load(E/'batch-verification-receipt.json')['finished_at'] if (E/'batch-verification-receipt.json').exists() else h.now();elapsed=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
 save('batch-verification-receipt.json',dict(receipt,batch=94,started_at=start,finished_at=end,measured_runtime_seconds=elapsed,source_verification_receipt=rel(W/'batch-verification-receipt.json'),french_reserve_selected=0,qagoma_selected=0,prior_campaign_additions_excluded=True))
 evidence=[rel(E/x) for x in ['batch-verification-receipt.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','reserve-actual-visual-sample.json','independent-qagoma-verification.json','independent-existing-preservation-verification.json','page-ten-editorial-dispositions.json','research-holds.json','failure-ledger.json','external-continuation-verification.json']]
 evidence += [rel(W/x) for x in ['independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','local-recovery-verification.json']]
 next_task='Research the 14 untouched Art Gallery of NSW image-gap candidates via approved WikiArt using its saved UUID queue; preserve native access holds. Athens Parthenis page 5 and Warsaw icons page 11 remain queued. Skip exhausted French reserve and unchanged QAGOMA profile failures.'
 with (Q.parent/'source-queue.worker.lock').open('a+') as lock1,(Q.parent/'source-queue.lock').open('a+') as lock2:
  fcntl.flock(lock1,fcntl.LOCK_EX);fcntl.flock(lock2,fcntl.LOCK_EX)
  before=h.load(Q);save('source-queue-immediately-before-update.json',before);after=copy.deepcopy(before);touched={'yale_lux','qagoma','national_museum_warsaw'}
  for row in after['sources']:
   sid=row['source_id']
   if sid not in touched:continue
   row['last_checked_at']=end;row['checkpoint']=rel(E/'CHECKPOINT.json');row['last_batch']=94
   row.setdefault('evidence_paths',[])
   refs=[rel(E/'french-reserve-live-reconciliation.json'),rel(E/'independent-reserve-evidence-verification.json'),rel(E/'reserve-actual-visual-sample.json')] if sid=='yale_lux' else [rel(E/'independent-qagoma-verification.json'),rel(E/'qagoma-source-verification.json')] if sid=='qagoma' else [rel(W/'batch-verification-receipt.json'),rel(W/'independent-production-verification.json'),rel(W/'independent-public-verification.json'),rel(E/'page-ten-editorial-dispositions.json')]
   row['evidence_paths']=list(dict.fromkeys(row['evidence_paths']+refs));cur=row['resume_cursor'];row.setdefault('research_history',[]);entry=dict(batch=94,at=end,evidence=refs,verified_counts=counts if sid=='national_museum_warsaw' else {k:0 for k in counts})
   if not any(x.get('batch')==94 for x in row['research_history']):row['research_history'].append(entry)
   if sid=='yale_lux':
    row['status']='french_reserve_exhausted_live_verified_188_already_delivered';cur.update(inspected=188,already_imported=188,remaining_unimported=0,last_live_reconciliation=refs[0],next_action='Do not replay historical reserve plan. Zero new candidates; switch to other source queues.');row['latest_batch_verified_counts']={k:0 for k in counts}
   elif sid=='qagoma':
    row['status']='frozen_16_gap_candidates_researched_unresolved_native_access_hold_preserved';row['access_status']='Nine further gaps researched across eight candidate WikiArt profile routes; HTTP404, no retries. Native QAGOMA HTTP403 hold unchanged; zero native requests.'
    cur['researched_artwork_ids']=list(dict.fromkeys(cur['researched_artwork_ids']+[x['artwork_id'] for x in qagrows]));cur['held_artwork_ids']=list(dict.fromkeys(cur['held_artwork_ids']+[x['artwork_id'] for x in qagrows]));cur['pending_artwork_ids']=[x for x in cur['pending_artwork_ids'] if x not in {r['artwork_id'] for r in qagrows}];cur['profile_404_no_unchanged_retry']=list(dict.fromkeys(cur.get('profile_404_no_unchanged_retry',[])+[x['url'] for x in qagrows]));cur['latest_checked_batch']=94;cur['latest_discovery_ledger']=refs[0];cur['next_step']='All frozen candidates researched; revisit only with new object/profile evidence. No claim that images are absent everywhere.';row['remaining_gaps']=['Sixteen researched unresolved primary-image gaps; no untouched candidate in frozen list.','Native access hold retained; no independent WikiArt matches selected in this batch.']
   else:
    row['status']='seven_page10_painted_icons_holdings_images_verified_page11_next';row['verified_counts']=counts
    cur.update(captured_page=10,next_page_after_pending=11,next_discovery_page=11,query_url=page_rc['url'],metadata_page_sha256=page_rc['sha256'],review_ledger=rel(E/'page-ten-editorial-dispositions.json'),saved_discovery=rel(W/'warsaw-icons-page10.json'),metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],next_step='Rotate institutions, then page 11. Preserve prior holds; no unchanged retries.')
    cur['processed_native_ids']=list(dict.fromkeys(cur['processed_native_ids']+[str(x['id']) for x in page['items']]));cur['held_native_ids']=list(dict.fromkeys(cur.get('held_native_ids',[])+held));cur['delivered_native_ids']=list(dict.fromkeys(cur.get('delivered_native_ids',[])+sorted(selected)));cur['latest_cast_candidate_ids']=casts;row['access_status']='Official page 10 and 23 native details HTTP200; seven selected image assets and public delivery verified.'
  untouched=[r['source_id'] for r in before['sources'] if r['source_id'] not in touched]
  assert len(untouched)==108 and len(after['sources'])==111
  assert [r for r in before['sources'] if r['source_id'] not in touched]==[r for r in after['sources'] if r['source_id'] not in touched]
  payload=json.dumps(after,ensure_ascii=False,indent=2).encode();tmp=Q.with_suffix('.batch94.tmp')
  with tmp.open('wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
  os.replace(tmp,Q);assert h.load(Q)==after
  save('source-queue-after.json',after);save('independent-queue-verification.json',dict(at=h.now(),modified_source_ids=sorted(touched),unrelated_routes_preserved=108,original_registry_routes=111,before_sha256=h.sha(json.dumps(before,sort_keys=True).encode()),after_sha256=h.sha(Q.read_bytes()),exact_unrelated_structures_equal=True,atomic_replace=True))
 save('source-register-final.json',dict(at=end,original_registry_rows=111,registry_sha256=h.load(E/'required-input-reconciliation.json')['inputs'][1]['sha256'],researched_routes=[r for r in after['sources'] if r['source_id'] in touched],directory_coverage_changed=False,object_coverage_complete=False,rights_approvals_not_generalized=True))
 evidence += [rel(E/'independent-queue-verification.json'),rel(E/'source-register-final.json')]
 for path in evidence:assert (b.ROOT/path).is_file()
 checkpoint=dict(batch=94,status='complete',outcome='progress',started_at=start,finished_at=end,measured_runtime_seconds=elapsed,verified_counts=counts,production_ids=ids,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],stage_counts=dict(french_reserve_inspected=188,french_reserve_already_imported=188,qagoma_gaps_researched=9,qagoma_selected=0,warsaw_page_items=24,warsaw_new_details_captured=23,selected=7,prepared=7,imported=7,verified=7),next_task=next_task,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000094-resume.py',verification_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000094-verify.py',delivery_complete_do_not_count_again=True,evidence_paths=evidence,external_supervisor_unchanged=True,local_catalogue_connections=0,limitations=['Seven authentic 315-pixel museum images individually viewed; fine inscriptions and reverse sides not claimed inspected.','Recovery is full schema plus scoped exact preimages, not a full database export.','QAGOMA profile failures do not establish that no authentic image exists.','Catalogue-wide goal totals not recounted in this bounded batch.'])
 save('CHECKPOINT.json',checkpoint);h.save(b.R/'CHECKPOINT.json',checkpoint)
 save('batch-summary.json',dict(at=end,measured_runtime_seconds=elapsed,verified_counts=counts,prior_programme_totals=programme['totals'],prior_totals_source='External supervisor checkpoint; not independently re-audited by this batch.',next_task=next_task,reporting_owner='External supervisor retains hourly and 100-hour milestone reporting; no schedule changed.'))
 print(json.dumps(dict(verified_counts=counts,next_task=next_task,unrelated_routes_preserved=108,checkpoint=rel(E/'CHECKPOINT.json'))))
