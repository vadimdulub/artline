"""Persist batch109 receipts and only the researched queue routes."""
import importlib.util,json,fcntl,datetime,copy,os
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-mds-batch-000109.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (b.E/'independent-checkpoint-verification.json').exists():
  done=h.load(b.E/'independent-checkpoint-verification.json')
  for item in done['evidence']:assert h.sha((b.ROOT/item['path']).read_bytes())==item['sha256']
  assert h.sha((b.E/'CHECKPOINT.json').read_bytes())==done['checkpoint_sha256']
  assert h.load(b.R/'CHECKPOINT.json')==h.load(b.E/'CHECKPOINT.json')
  print('Completed checkpoint verified; no queue replay');raise SystemExit(0)
 rc=h.load(b.E/'batch-verification-receipt.json');counts=rc['verified_counts'];assert counts==dict(new_painters=0,new_artworks=2,newly_illustrated=0,alternate_images=0,museum_links=2)
 now=h.now();next_task='Research up to 25 pre-1971 paintings, drawings or icons through the undercovered DigitaltMuseum registry route, prioritizing undercovered institutions. Preserve all access holds; French reserve is exhausted. MDS painting search can resume at page 2.'
 b.save('mds-hold-refinement.json',dict(at=now,source_id='56aafec3-7dd9-317f-add7-5b8634fe70c9',decision='exclude_creation_1989',source='mds-discovered-page1.json',basis='Original Date - earliest/single and latest fields both1989. Refines pending date review in immutable initial hold ledger; no selected plan changes.'))
 qpath=b.E.parents[1]/'source-queue.json'
 with qpath.with_suffix('.lock').open('a+') as qlock:
  fcntl.flock(qlock,fcntl.LOCK_EX);old=h.load(qpath);q=copy.deepcopy(old)
  for x in q['sources']:
   if x['source_id']=='yale_lux':
    x.update(status='french_reserve_exhausted_live_verified_188_already_delivered',last_checked_at=now,last_batch=109,checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)))
    x['resume_cursor']=dict(route='french_reserve',inspected=188,already_imported=188,remaining_unimported=0,delivered_by_prior_campaign=True,next_action='Do not repeat unchanged reserve audit; choose another registry route unless genuinely new source objects arrive.',last_live_reconciliation=str((b.E/'french-reserve-live-reconciliation.json').relative_to(b.ROOT)))
    x['latest_batch_verified_counts']=dict.fromkeys(counts,0)
    paths=['french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','reserve-actual-visual-sample.json']
   elif x['source_id']=='museum_data_service_uk':
    x.update(status='two_new_review_paintings_and_nrm_holdings_verified_public_search_page1',last_checked_at=now,last_batch=109,checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),policy_reference='Original111-source registry museum_data_service_uk; contributor CC BY metadata; docs/ARTLINE_IMAGE_USE.md. MDS metadata permission does not license images.',access_status='Public HTML search and three object records HTTP200. Search API requires token and was not called. Native Science Museum Group object route403 held, not retried.',remaining_gaps=['Eighteen unselected page1 objects: unknown creation dates, noncommercial data, grouped physical units, existing Longridge lead and1989 exclusion; see hold ledgers.','No images attached; source metadata licence is separate.','Only20 object records reviewed; institution directory and complete artwork coverage not claimed.','Fishguard creator Smith, John S. remains unlinked; Hackworth creator and both dimensions unknown.'])
    x['resume_cursor']=dict(route='public_object_search_html',query='painting',completed_page=1,next_page=2,next_url='https://museumdata.uk/object-search/?q=painting&i=2',processed_source_ids=[r['source_id'] for r in h.load(b.E/'mds-selection-and-holds.json')['rows']],delivered_source_ids=b.PIDS,skip_research_unchanged_ids=True,api_token_requested=False,native_smg_retry_allowed=False,rotate_next='digitaltmuseum')
    x['latest_batch_verified_counts']=counts
    previous=next(v for v in h.load(b.E/'source-queue-before.json')['sources'] if v['source_id']=='museum_data_service_uk').get('verified_counts',dict.fromkeys(counts,0));x['verified_counts']={k:previous.get(k,0)+counts[k] for k in counts}
    paths=['independent-source-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-public-verification.json','independent-resume-verification.json','mds-selection-and-holds.json','mds-hold-refinement.json','source-access-holds.json','batch-verification-receipt.json']
   else:continue
   x['evidence_paths']=list(dict.fromkeys(x.get('evidence_paths',[])+[str((b.E/f).relative_to(b.ROOT)) for f in paths]))
  untouched={x['source_id']:x for x in old['sources'] if x['source_id'] not in ['yale_lux','museum_data_service_uk']};assert all(x==untouched[x['source_id']] for x in q['sources'] if x['source_id'] in untouched)
  tmp=qpath.with_suffix('.109.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qpath)
 b.save('independent-source-queue-verification.json',dict(at=now,queue_path=str(qpath),queue_sha256=h.sha(qpath.read_bytes()),changed_routes=['yale_lux','museum_data_service_uk'],unrelated_routes_preserved=len(untouched),original111_sources_preserved=len(q['sources'])==111,mds_resume_page=2,french_reserve_unimported=0))
 root=h.load(b.E.parents[1]/'CHECKPOINT.json');started=root['inflight']['started_at'];elapsed=(datetime.datetime.fromisoformat(now)-datetime.datetime.fromisoformat(started)).total_seconds();totals={k:root['totals'].get(k,0)+counts[k] for k in counts}
 b.save('milestone-report.json',dict(at=now,worker_started_at=started,measured_worker_elapsed_seconds=elapsed,verified_counts=counts,cumulative_attributable_counts_after_this_batch=totals,cumulative_baseline='Supervisor persisted totals before batch109 plus this independently verified batch; not recomputed across old campaigns.',hourly_and100hour_reporting='Owned by existing supervisor, unchanged.',next_task=next_task,failures=['System Python lacked psycopg; established venv used, no installation.','Web tool could not open MDS query; direct public HTML returned200.','Native Science Museum Group returned403; no retry, no image request.'],unresolved='Recorded creator/date/grouped-unit/rights and source-access holds.'))
 b.save('source-register.json',dict(at=now,registry_file='/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv',registry_sha256=h.sha(Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv').read_bytes()),registry_rows=111,routes=[x for x in q['sources'] if x['source_id'] in ['yale_lux','museum_data_service_uk']],directory_records_delivered=0,distinct_new_artworks_delivered=2))
 checkpoint=dict(at=now,batch=109,stage='verified_complete',verified_counts=counts,production_ids=rc['production_ids'],selected=2,imported=2,independently_verified=2,french_reserve=dict(inspected=188,unimported=0,new_counts=0),mds=dict(discovered=20,selected=2,held_or_excluded=18,next_page=2),next_task=next_task,source_queue=str(qpath),production_recovery=str(h.BACKUP),local_catalogue_connections=0,supervisor_unchanged=True)
 b.save('CHECKPOINT.json',checkpoint);h.save(b.R/'CHECKPOINT.json',checkpoint)
 evidence=['batch-verification-receipt.json','independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-public-verification.json','independent-resume-verification.json','french-reserve-live-reconciliation.json','prior-batches-live-verification.json','independent-source-queue-verification.json']
 verified=[]
 for name in evidence:
  pth=b.E/name;h.load(pth);verified.append(dict(path=str(pth.relative_to(b.ROOT)),bytes=pth.stat().st_size,sha256=h.sha(pth.read_bytes())))
 b.save('independent-checkpoint-verification.json',dict(at=h.now(),evidence=verified,checkpoint_sha256=h.sha((b.E/'CHECKPOINT.json').read_bytes()),runtime_checkpoint_equal=h.load(b.R/'CHECKPOINT.json')==checkpoint,verified_counts=counts,source_queue_unrelated_routes_preserved=True))
 (b.E/'README.md').write_text('# Batch109 — verified production metadata\n\nThe188 French reserve records were already delivered by the earlier campaign. Original source captures, derivatives and checksum-bound visual evidence were verified; one derivative was actually viewed again. None counts as new. Batches107 and108 were reconciled live without replay writes.\n\nMDS public painting search page1 supplied20 object records. Two new review paintings and two National Railway Museum holdings were delivered and independently verified through rows, original evidence, audit preimages, persisted plan hashes and public API responses. No painters or images added. John S. Smith remains unlinked; the Hackworth maker is unknown. Native Science Museum Group access403 and image permissions remain held.\n\nThe18 remaining records and1989 date refinement are retained in the hold ledgers. Resume MDS at page2; rotate first to DigitaltMuseum. The existing supervisor is unchanged. Real local catalogue untouched. See CHECKPOINT.json and batch-verification-receipt.json.\n')
 print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,next_task=next_task)))
