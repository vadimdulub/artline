#!/usr/bin/env python3
"""Finalize this worker only; atomically advance the researched Warsaw route."""
import copy, datetime, fcntl, gzip, importlib.util, json, os
from pathlib import Path
s=importlib.util.spec_from_file_location('b105','ops/continuous-warsaw-batch-000105.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i;W=b.E;E=W.parent;Q=E.parents[1]/'source-queue.json'
def save(name,v):
 p=E/name
 if not p.exists():h.save(p,v)
 return h.load(p)
def rel(p):return str(p.relative_to(b.ROOT))
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (E/'CHECKPOINT.json').exists():
  print('Completed checkpoint retained; use the independent resume verifier.');raise SystemExit(0)
 receipt=h.load(W/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts==dict(new_painters=0,new_artworks=3,newly_illustrated=3,alternate_images=0,museum_links=3)
 resume=h.load(W/'independent-resume-verification.json');assert resume['new_production_increments_on_resume']==0
 p,pin=h.pinned(b.PHASE);ids=receipt['production_ids'];selected={r['source_id'] for r in p['records']}
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  assert h.snapshot(db,ids)==h.load(W/'independent-production-verification.json')['rows']
  recovery=h.load(h.BACKUP/'affected-row-recovery-before.json.gz');assert h.snapshot(db,list(recovery['preserved']))==recovery['preserved']
  museum=db.execute('SELECT to_jsonb(t) v FROM institutions t WHERE id=%s',(b.MID,)).fetchone()['v'];assert museum==recovery['institutions'][0]
  existing=h.snapshot(db,['680b4ade-d9f3-5bc5-8eeb-5d316bfa4cac']);assert existing['680b4ade-d9f3-5bc5-8eeb-5d316bfa4cac']==recovery['preserved']['680b4ade-d9f3-5bc5-8eeb-5d316bfa4cac']
 save('independent-existing-preservation-verification.json',dict(at=h.now(),prior_warsaw_artworks_and_relationships_unchanged=len(recovery['preserved']),museum_unchanged=True,existing_native_454759_excluded_and_unchanged=existing,local_database_connections=0))
 page=h.load(W/'warsaw-icons-page13.json')['data'];page_rc=h.load(W/'warsaw-icons-page13.receipt.json');raw=gzip.decompress(Path(page_rc['body_path']).read_bytes());assert h.sha(raw)==page_rc['sha256'] and json.loads(raw)['data']==page and len(page['items'])==18
 assert page['paginatorDetails']['currentPage']==page['paginatorDetails']['totalPagesCount']==13
 dispositions=[];held=[];casts=[];excluded=[]
 for item in page['items']:
  oid=str(item['id']);rc=h.load(W/f'object-{oid}.receipt.json');raw=gzip.decompress(Path(rc['body_path']).read_bytes());o=h.load(W/f'object-{oid}.json')['data'];assert h.sha(raw)==rc['sha256'] and rc['status']==200 and json.loads(raw)['data']==o
  techniques={x['name'] for x in o['techniques']}
  if oid in selected:outcome='verified_new_illustrated_artwork';reason=b.REVIEWS[int(oid)]
  elif oid=='454759':outcome='existing_exact_work_excluded';reason='Exact native identifier, inventory IK 100, title and source URL already resolve to active production 680b4ade-d9f3-5bc5-8eeb-5d316bfa4cac. No update or new increment; dates and earlier source identity preserved.';excluded.append(oid)
  elif 'odlew' in techniques:outcome='saved_cast_candidate';reason='Cast object outside this pictorial selection. Preserve exact inventory, date, unit and native rights for a separate eligible-medium review; no image downloaded.';casts.append(oid);held.append(oid)
  else:outcome='held_other_medium_or_unit';reason='Carved, relief, architectural, medallion or triptych-wing object requires separate medium and physical-unit review. Not imported as a painting and no image downloaded.';held.append(oid)
  dispositions.append(dict(source_id=oid,title=o['title'],accession=o['noEvidence'],source_dates=o['createDates'],source_creators=o['authors'],techniques=sorted(techniques),outcome=outcome,reason=reason,receipt=rc))
 assert len(dispositions)==18 and len(held)==14 and len(casts)==9 and excluded==['454759']
 save('page-thirteen-editorial-dispositions.json',dict(at=h.now(),rows=dispositions,captured=18,selected_and_verified=3,existing_exact_work_excluded=1,held_or_other_medium=14,all_capture_checksums_verified=True,paginator=page['paginatorDetails'],query_exhausted=True,whole_institution_coverage_complete=False))
 save('saved-cast-candidates.json',dict(at=h.now(),native_ids=casts,records=[r for r in dispositions if r['source_id'] in casts],selected=False,downloaded_images=0))
 save('research-holds.json',dict(at=h.now(),warsaw=[r for r in dispositions if r['source_id'] in held],existing_excluded=excluded,prior_holds_preserved=True,unchanged_held_routes_requested=0,provider_denials=0,scope='Only the saved icon-phrase/department query is exhausted. Institution and nationwide coverage remain incomplete.'))
 save('failure-ledger.json',dict(at=h.now(),failures=[dict(stage='prior-delivery-read-only-reconciliation',reason='Previous image-only verification stores full snapshots under after, while rows contains media checks. Initial reader assumed the metadata-delivery shape.',resolution='Read the actual after snapshots; exact live comparison passed. No production writes before reconciliation and no extra source requests.',resolved=True),dict(stage='diagnostic-read-only-comparison',reason='Attempted dictionary access on the previous receipt media-list field.',resolution='Corrected reader schema; no mutation.',resolved=True)],provider_failures=[],spending_limit_changes=0,authentication_changes=0))
 save('web-source-check.json',dict(at=h.now(),url='https://cyfrowe.mnw.art.pl/pl/zbiory',web_tool_result='Public catalogue HTML shell accessible; object assertions rely on saved official native object API captures.',source_records_captured=18))
 save('batch-verification-receipt.json',receipt)
 end=h.now();programme=h.load(E.parents[1]/'CHECKPOINT.json');start=h.load(E/'required-input-reconciliation.json')['started_at'];elapsed=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
 next_task='Rotate to the four staged Alte Pinakothek existing-image gaps recorded in batch 104, using exact inventories and approved accessible sources. Warsaw icon search pages 1–13 are reviewed; do not request page 14. Preserve all Warsaw component/date holds, Basel native-image and Degas holds; choose a fresh Greek creator index for later metadata expansion.'
 with Q.with_suffix('.lock').open('a+') as qlock:
  fcntl.flock(qlock,fcntl.LOCK_EX)
  before=h.load(Q);after=copy.deepcopy(before);save('source-queue-immediately-before-update.json',before)
  row=next(r for r in after['sources'] if r['source_id']=='national_museum_warsaw');original=next(r for r in h.load(E/'source-queue-before.json')['sources'] if r['source_id']=='national_museum_warsaw');assert row==original,'Concurrent same-route update; reconcile before advancing'
  cur=row['resume_cursor'];row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(cur))
  evidence=[rel(E/x) for x in ['CHECKPOINT.json','batch-verification-receipt.json','page-thirteen-editorial-dispositions.json','research-holds.json','independent-existing-preservation-verification.json']]+[rel(W/x) for x in ['independent-source-verification.json','independent-production-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json']]
  row.update(status='page13_three_new_illustrated_pictorial_objects_verified_icon_query_exhausted',checkpoint=rel(E/'CHECKPOINT.json'),last_checked_at=end,verified_counts=counts,access_status='Official final search page and 18 object details HTTP 200; three selected native images, production associations, storage and public delivery verified.',evidence_paths=list(dict.fromkeys(row.get('evidence_paths',[])+evidence)))
  cur.update(captured_page=13,next_page_after_pending=None,next_discovery_page=None,pending_native_ids_current_page=[],query_url=page_rc['url'],metadata_page_sha256=page_rc['sha256'],review_ledger=rel(E/'page-thirteen-editorial-dispositions.json'),saved_discovery=rel(W/'warsaw-icons-page13.json'),metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],query_exhausted=True,source_discovery_total=306,source_total_is_not_eligible_artwork_count=True,next_step='This exact search is exhausted at page 13. Rotate institution or choose a different documented pictorial query after reconciliation. Do not request page 14 or retry held cases unchanged.',authentication_last_verified_at=end)
  cur['processed_native_ids']=list(dict.fromkeys(cur['processed_native_ids']+[str(r['id']) for r in page['items']]))
  cur['held_native_ids']=list(dict.fromkeys(cur.get('held_native_ids',[])+held));cur['delivered_native_ids']=list(dict.fromkeys(cur.get('delivered_native_ids',[])+sorted(selected)))
  cur['existing_excluded_ids']=list(dict.fromkeys(cur.get('existing_excluded_ids',[])+excluded))
  cur['saved_cast_candidate_native_ids']=list(dict.fromkeys(cur.get('saved_cast_candidate_native_ids',[])+cur.get('latest_cast_candidate_ids',[])+casts));cur['latest_cast_candidate_ids']=casts;cur['prior_cast_candidate_ledger']=cur.get('cast_candidate_ledger');cur['cast_candidate_ledger']=rel(E/'saved-cast-candidates.json')
  row['remaining_gaps']=[str(len(cur['held_native_ids']))+' preserved other-medium or editorial holds across the query.',str(len(cur['saved_cast_candidate_native_ids']))+' saved cast candidates remain outside pictorial deliveries.','Full institution coverage incomplete. Search total 306 is a source index count, not 306 new eligible works.']
  assert len(after['sources'])==111 and [r for r in before['sources'] if r['source_id']!='national_museum_warsaw']==[r for r in after['sources'] if r['source_id']!='national_museum_warsaw']
  tmp=Q.with_suffix('.batch105.tmp')
  with tmp.open('wb') as f:f.write(json.dumps(after,ensure_ascii=False,indent=2).encode());f.flush();os.fsync(f.fileno())
  os.replace(tmp,Q);assert h.load(Q)==after
  save('source-queue-after.json',after);save('independent-queue-verification.json',dict(at=h.now(),modified_source_ids=['national_museum_warsaw'],unrelated_routes_preserved=110,original_registry_routes=111,after_sha256=h.sha(Q.read_bytes()),exact_unrelated_structures_equal=True,atomic_replace=True,final_page=13,query_exhausted=True))
 save('source-register-final.json',dict(at=end,original_registry_rows=111,registry_sha256=h.load(E/'required-input-reconciliation.json')['inputs'][1]['sha256'],researched_route=row,directory_coverage_changed=False,object_coverage_complete=False,policy='Original registry per-object open-rights requirement; actual DOMENA PUBLICZNA labels and saved museum commercial-reuse project capture; no extension to other providers.'))
 evidence=[rel(E/x) for x in ['batch-verification-receipt.json','page-thirteen-editorial-dispositions.json','research-holds.json','failure-ledger.json','external-continuation-observation.json','independent-existing-preservation-verification.json','independent-queue-verification.json','source-register-final.json']]+[rel(W/x) for x in ['independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','local-recovery-verification.json']]
 assert all((b.ROOT/x).is_file() for x in evidence)
 checkpoint=dict(batch=105,status='complete',outcome='progress',started_at=start,finished_at=end,measured_runtime_seconds=elapsed,runtime_boundary='Persisted required-input checkpoint to finalization; earlier preliminary inspection excluded.',verified_counts=counts,production_ids=ids,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],stage_counts=dict(discovered=18,researched=18,pictorial_candidates=4,already_existing_excluded=1,selected=3,prepared=3,imported=3,verified=3,held_or_other_medium=14),next_task=next_task,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000105-resume.py',verification_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000105-verify.py',delivery_complete_do_not_count_again=True,evidence_paths=evidence,external_supervisor_unchanged=True,local_catalogue_connections=0,limitations=['All three 315-pixel-wide native originals and derivatives actually viewed; absent reverse sides and small inscriptions not visually inspected.','Recovery is full production schema plus exact affected-row preimages, not a full database export.','No individual named painter identified; source unknown/workshop labels retained.','Only the saved Warsaw icon query is exhausted; museum coverage remains incomplete.'])
 save('CHECKPOINT.json',checkpoint);h.save(b.R/'CHECKPOINT.json',checkpoint)
 save('batch-summary.json',dict(at=end,measured_runtime_seconds=elapsed,verified_counts=counts,prior_programme_totals=programme['totals'],recorded_cumulative_after_batch={k:programme['totals'][k]+counts[k] for k in counts},prior_totals_source='External supervisor checkpoint; prior aggregate not independently recounted in this batch.',next_task=next_task,reporting_owner='Existing external supervisor owns hourly and 100-hour reports and next-batch scheduling; unchanged.'))
 final=dict(outcome='progress',summary='Verified three new Warsaw artworks: two painted icons and one Armenian illuminated leaf, each with a primary image and documented holding. All originals and derivatives viewed; production, public delivery and idempotent replay verified. One existing work excluded. Final icon-search page checkpointed; 110 unrelated routes preserved.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(E/'batch-verification-receipt.json'),rel(W/'independent-production-verification.json'),rel(W/'independent-public-verification.json'),rel(W/'independent-resume-verification.json'),rel(E/'independent-queue-verification.json'),rel(E/'CHECKPOINT.json')])
 save('worker-result.json',final);print(json.dumps(final))
