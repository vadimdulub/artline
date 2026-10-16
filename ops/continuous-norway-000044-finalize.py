#!/usr/bin/env python3
"""Persist verified batch 44 and touched route cursors, never supervisor state."""
import copy,datetime,fcntl,importlib.util,json,os,sys
s=importlib.util.spec_from_file_location('b','ops/continuous-norway-images-000044.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i;E=b.E
def ep(name):return str((E/name).relative_to(b.ROOT))
with (b.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (E/'result.json').exists():
  proof=h.load(E/'final-checkpoint-verification.json')
  for f in proof['files']:assert h.sha((b.ROOT/f['path']).read_bytes())==f['sha256']
  print(json.dumps(h.load(E/'result.json')));sys.exit(0)
 receipt=h.load(E/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts['newly_illustrated']==12
 assert h.load(E/'independent-resume-verification.json')['no_new_writes_on_resume']
 assert h.load(E/'independent-tate-no-write-verification.json')['all_artwork_fields_relationships_and_images_unchanged']
 assert h.load(E/'independent-campaign-stop-verification.json')['all_unchanged']
 selected=i.selected(b.B);stage=h.load(E/'oslo-bounded-gap-input.json.gz');held=h.load(E/'research-holds.json');tate=h.load(E/'tate-research-outcomes.json');gaps=h.load(E/'gap-reconciliation.json')
 ids=receipt['production_ids'];nid=[r['id'] for r in stage['rows']];heldids=[r['artwork_id'] for r in held['records']]
 assert len(nid)==20 and set(nid)==set(ids)|set(heldids) and not set(ids)&set(heldids)
 inspected=[r['artwork_id'] for r in tate['object_outcomes']];pending=[r['id'] for r in gaps['rows'] if r['id'] not in inspected];assert len(pending)==72
 norway_cursor=dict(route='official_native_object_pages_and_explicit_CC_BY_primary_images',institution_id=b.MID,after_artwork_id=nid[-1],inspected_ids=nid,delivered_ids=ids,held_ids=heldids,canonical_url_404_ids=['06848876-bfda-5395-9f6d-71162a7c3d91'],translation_review_ids=['08799e6b-1c04-53aa-a038-8d4f087209e7'],unchanged_rights_hold_ids=[x['artwork_id'] for x in held['records'] if x['reason']=='Object-specific copyright restriction'],selection_sha256=receipt['selection_sha256'],prior_batch_35_cursor_preserved_in_history=True,no_repeat_of_unchanged_rights_holds=True,held_record_evidence=ep('research-holds.json'),hold_clarification=ep('research-hold-clarification.json'))
 tate_cursor=dict(route='wikiart_exact_object_crossmatch_existing_Tate_gaps',input_path=ep('gap-reconciliation.json'),bounded_input_count=80,processed_artwork_ids=inspected,pending_artwork_ids=pending,after_artwork_id=None,ordering='Explicit remaining IDs; eight sparse researched objects do not establish an 80-row cursor',official_object_page_http403_hold=True,official_images_not_permitted_by_registry=True,already_illustrated_duplicate_candidate='746e1aae-d4dc-568a-b11a-66a321c6e67a',no_repeat_unchanged_searches=True)
 nxt='Inspect an undercovered Harvard Art Museums route for a bounded existing-image-gap batch, first checking configured API access and object-specific image permissions. If no configured access is available, use Te Papa after 24f5dcb9-b68d-509c-8592-d889977f871b. Preserve Tate HTTP 403 and duplicate/version holds, Norway cursor 08799e6b-1c04-53aa-a038-8d4f087209e7, Greek/Russian/Byzantine priorities and exhausted French reserve stop state.'
 evidence=['batch-verification-receipt.json','independent-production-verification.json','independent-source-verification.json','independent-file-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-held-objects-verification.json','independent-prewrite-verification.json','actual-visual-review.json','independent-resume-verification.json','independent-tate-no-write-verification.json','independent-campaign-stop-verification.json','prior-batch-live-reconciliation.json','global-identity-reconciliation.json','research-holds.json','research-hold-clarification.json','tate-research-outcomes.json','tissot-global-reconciliation.json','access-holds/www.tate.org.uk.json','source-access-holds.json']
 reg=h.load(E/'required-input-reconciliation.json')
 b.save(E/'source-register.json',dict(at=h.now(),original_registry_path=reg['registry_path'],original_registry_sha256=reg['registry_sha256'],registry_rows=111,supplementary_registry_not_used_as_replacement=True,routes=[dict(provider='tate',registry=next(x for x in reg['complete_registry'] if x['source_id']=='tate'),image_provider='WikiArt',policy_reference='docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026',access_status='Tate object page HTTP 403, no subsequent Tate requests; WikiArt selected public metadata accessible, two candidate profiles HTTP 404; no Tate or WikiArt images downloaded',last_checked_at=h.now(),remaining_gaps='80 gaps unchanged: eight bounded source investigations held/unmatched, 72 pending; duplicate candidate kept separate',evidence=[ep('tate-research-outcomes.json'),ep('independent-tate-no-write-verification.json')]),dict(provider='nasjonalmuseet_norway',registry=next(x for x in reg['complete_registry'] if x['source_id']=='nasjonalmuseet_norway'),policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',source_policy=b.POLICY,license=b.LICENSE,access_status='Policy HTTP 200, 19 object pages HTTP 200, one object HTTP 404; 12 selected full-frame images HTTP 200',last_checked_at=h.now(),remaining_gaps='Eight of this 20-row slice remain held; later keyset uninspected. Prior batch 35 holds unchanged.',evidence=[ep('norway-policy.json'),ep('independent-source-verification.json')])],directory_coverage='No new directory coverage; object-level research does not establish whole-museum coverage.',user_approval_is_not_copyright_holder_licence=True))
 b.save(E/'research-outcomes.json',dict(at=h.now(),tate=dict(existing_gaps_screened=80,individually_researched=8,selected=0,downloaded=0,verified=0,pending=72),norway=dict(existing_gaps_screened=20,source_objects_researched=20,metadata_selected=12,images_prepared=12,individually_viewed=12,imported=12,independently_verified=12,held=8),verified_counts=counts,prior_campaign_increments=0,new_museum_or_display_claims=0,local_catalogue_connections=0))
 manifest=[dict(artwork_id=r['artwork_id'],native_id=r['native_id'],accession_number=r['accession_number'],title=r['title'],creator=r['creator_label'],source_url=r['source_url'],source_page_sha256=r['image']['receipt']['sha256'],original_catalogue_plan_sha256=r['plan_sha256'],selection_sha256=receipt['selection_sha256'],image=h.load(i.folder(b.B)/'prepared'/(r['artwork_id']+'.json'))) for r in selected['rows']]
 b.save(E/'verified-delivery-manifest.json',manifest)
 evidence+=['source-register.json','research-outcomes.json','verified-delivery-manifest.json']
 cp=dict(at=h.now(),batch=44,stage='independently_verified_complete',verified_counts=counts,production_ids=ids,selected=12,prepared=12,imported=12,verified=12,individually_viewed=12,unsampled_claimed_viewed=0,selection_sha256=receipt['selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],resume_cursors=dict(tate=tate_cursor,nasjonalmuseet_norway=norway_cursor),next_task=nxt,resume_command='/tmp/artline-cesi-venv/bin/python ops/continuous-norway-000044-resume.py',verify_command='/tmp/artline-cesi-venv/bin/python ops/continuous-norway-images-000044-verify.py',evidence_paths=[ep(p) for p in evidence],local_catalogue_connections=0,external_supervisor_unchanged=True)
 b.save(E/'CHECKPOINT.json',cp);h.save(b.RUNTIME/'CHECKPOINT.json',h.load(E/'CHECKPOINT.json'))
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as qlock:
  fcntl.flock(qlock,fcntl.LOCK_EX);queue=h.load(qp);before=copy.deepcopy(queue);qsha=h.sha(qp.read_bytes())
  for row in queue['sources']:
   if row['source_id'] not in ['tate','nasjonalmuseet_norway']:continue
   row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(row.get('resume_cursor')))
   row['last_checked_at']=h.now();row['checkpoint']=ep('CHECKPOINT.json')
   if row['source_id']=='tate':
    row['status']='official_object_http403_hold_wikiart_versions_or_existing_duplicate_no_image_writes'
    row['resume_cursor']=tate_cursor;row['latest_batch_verified_counts']={k:0 for k in counts}
    row['access_status']='Official Tate selected page HTTP 403; no repeat or bypass. WikiArt metadata permitted; no image selected.'
    row['policy_reference']='Original registry tate; WikiArt approval is separate in docs/ARTLINE_IMAGE_USE.md.'
    row['remaining_gaps']=['72 untouched gaps in bounded input; eight processed cases retain exact no-match/version/duplicate reasons.','Tissot WikiArt 1877 oil already illustrated in another record; explicit object deduplication needed before further action.','Official Tate image downloads remain disallowed and webpage access held.']
    ev=['tate-research-outcomes.json','independent-tate-no-write-verification.json','tissot-global-reconciliation.json','wikiart-index-research.json','access-holds/www.tate.org.uk.json','source-register.json']
   else:
    row['status']='eighteen_programme_primary_images_verified_twelve_new_native_CC_BY_images'
    row['resume_cursor']=norway_cursor;row['latest_batch_verified_counts']=counts;row['verified_counts']=counts
    row['programme_verified_counts']=dict(counts,newly_illustrated=18)
    row['access_status']='Official public policy and native object pages accessible; 12 selected CC BY photographs delivered and publicly byte-verified.'
    row['policy_reference']='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy'
    row.setdefault('remaining_gaps',[]).append('Batch 44 adds 12 verified primary images after batch 35 cursor. Six new copyright holds, one exact native URL 404, one translated-title reconciliation. Prior holds remain; later keyset uninspected.')
    ev=evidence
   row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+[ep(p) for p in ev]))
  old={r['source_id']:r for r in before['sources']};assert len(queue['sources'])==111
  assert all(r==old[r['source_id']] for r in queue['sources'] if r['source_id'] not in ['tate','nasjonalmuseet_norway'])
  tmp=qp.with_suffix('.000044.tmp');tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
  b.save(E/'source-queue-update-verification.json',dict(at=h.now(),before_sha256=qsha,after_sha256=h.sha(qp.read_bytes()),changed_sources=['tate','nasjonalmuseet_norway'],unrelated_entries_preserved=109,registry_rows=111,resume_cursors=cp['resume_cursors']))
 master=h.load(E.parents[1]/'CHECKPOINT.json');started=h.load(E/'production-target-reconciliation.json')['at'];now=h.now()
 seconds=(datetime.datetime.fromisoformat(now)-datetime.datetime.fromisoformat(started)).total_seconds();elapsed=(datetime.datetime.fromisoformat(now)-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()
 b.save(E/'milestone-report.json',dict(at=now,batch_started_at=started,measured_batch_runtime_seconds=seconds,programme_elapsed_seconds=elapsed,prior_supervisor_totals=master['totals'],this_independently_verified_batch=counts,programme_totals_including_this_batch={k:master['totals'][k]+counts[k] for k in counts},attribution_limit='Prior cumulative totals supplied by supervisor checkpoint; this batch independently verified.',hourly_report_owner='Existing external supervisor, unchanged',hundred_hours_is_milestone_not_stop=True,failures=['Initial system Python lacked psycopg; established existing venv used without installing dependencies.','Two candidate WikiArt artist slugs HTTP 404; no repeat.','Tate official selected object HTTP 403; source held without retry.','One Norway native object URL HTTP 404; unresolved and not retried.'],unresolved=dict(tate_processed=8,tate_pending=72,norway_held=8),next_task=nxt))
 allpaths=evidence+['CHECKPOINT.json','source-queue-update-verification.json','milestone-report.json']
 b.save(E/'final-checkpoint-verification.json',dict(at=h.now(),files=[dict(path=ep(p),sha256=h.sha((E/p).read_bytes())) for p in allpaths],runtime_checkpoint=str(b.RUNTIME/'CHECKPOINT.json'),runtime_checkpoint_identical=(b.RUNTIME/'CHECKPOINT.json').read_bytes()==(E/'CHECKPOINT.json').read_bytes(),verified_counts=counts,source_queue_unrelated_entries_preserved=True,no_completed_campaign_restart=True))
 result=dict(outcome='progress',summary='Verified 12 new primary images for existing Norwegian museum artworks across eight creators; all individually viewed. Replay made no changes. Tate access/version/duplicate holds and resumable cursors saved; local catalogue untouched.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[ep(p) for p in ['batch-verification-receipt.json','independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-storage-verification.json','independent-public-verification.json','actual-visual-review.json','independent-resume-verification.json','source-queue-update-verification.json','final-checkpoint-verification.json','CHECKPOINT.json']])
 b.save(E/'result.json',result);h.save(b.RUNTIME/'verified-result.json',result)
 print(json.dumps(result))
