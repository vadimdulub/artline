#!/usr/bin/env python3
"""Persist verified batch-33 handoff; do not modify the supervisor checkpoint."""
import datetime, fcntl, importlib.util, json
s=importlib.util.spec_from_file_location('b','ops/continuous-warsaw-batch-000033.py')
b=importlib.util.module_from_spec(s); s.loader.exec_module(b); h=b.h; E=b.E
with (b.R/'worker.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    receipt=h.load(E/'batch-verification-receipt.json'); counts=receipt['verified_counts']
    assert counts==dict(new_painters=0,new_artworks=6,newly_illustrated=6,alternate_images=0,museum_links=6)
    resume=h.load(E/'independent-resume-verification.json'); assert resume['replayed_writes']==0
    recon=h.load(E/'global-identity-reconciliation.json')
    root=h.load(E.parents[1]/'CHECKPOINT.json'); assert root['inflight']['batch']==33
    next_task='Research up to 25 existing Musée Carnavalet primary-image gaps through Paris Musées; require exact inventory matches and per-image CC0 evidence. Check its account-token requirements without exposing credentials or bypassing access. Preserve Warsaw composite/date-unit holds and all existing provider holds; rotate to another available registry source if this route is blocked.'
    evidence_names=['batch-verification-receipt.json','independent-source-verification.json','independent-image-source-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','actual-visual-review.json','independent-resume-verification.json','source-queue-update-verification.json','milestone-report.json','CHECKPOINT.json']
    evidence=[str((E/n).relative_to(b.ROOT)) for n in evidence_names]
    holds=[x for x in recon['records'] if x['outcome']!='selected_new']
    cursor=dict(route='official_selected_icons_native_object_api',processed_native_ids=recon['all_checked_native_ids'],delivered_native_ids=[str(x) for x in b.SELECTED],held_native_ids=[x['source_id'] for x in holds],additional_discovery_pending=True,query_context='Russian, Old Believer and post-Byzantine whole icon objects; school/workshop attributions retained',skip_processed_native_ids=True)
    cp=dict(at=h.now(),batch=33,stage='independently_verified_complete',verified_counts=counts,production_ids=receipt['production_ids'],plan_sha256=receipt['plan_sha256'],selection_sha256=receipt['image_selection_sha256'],discovered=9,source_records_researched=9,selected=6,metadata_imported=6,metadata_verified=6,images_selected=6,images_prepared=6,images_actually_viewed=6,images_verified=6,source_resume=cursor,remaining_holds=holds,next_task=next_task,evidence_paths=evidence,local_database_connections=0,external_supervisor_unchanged=True,resume_command='/tmp/artline-cesi-venv/bin/python ops/continuous-warsaw-batch-000033.py deliver',verify_command='/tmp/artline-cesi-venv/bin/python ops/continuous-warsaw-000033-verify.py')
    b.save('CHECKPOINT.json',cp); h.save(b.R/'CHECKPOINT.json',h.load(E/'CHECKPOINT.json'))
    qp=E.parents[1]/'source-queue.json'
    with (b.R.parent.parent/'source-queue.lock').open('a+') as qlock:
        fcntl.flock(qlock,fcntl.LOCK_EX)
        queue=h.load(qp); before=json.loads(json.dumps(queue)); oldhash=h.sha(qp.read_bytes())
        entry=next(x for x in queue['sources'] if x['source_id']=='national_museum_warsaw')
        if entry.get('checkpoint')!=str((E/'CHECKPOINT.json').relative_to(b.ROOT)):
            if entry.get('resume_cursor'): entry.setdefault('prior_resume_cursors',[]).append(entry['resume_cursor'])
            entry.update(status='six_new_whole_icons_holdings_and_primary_images_verified_three_composite_date_holds',last_checked_at=h.now(),checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),resume_cursor=cursor,verified_counts=counts,policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='Official object API and selected image CDN HTTP 200',remaining_gaps=['Three exact native objects held for composite maker/date/unit review; unchanged holds should not trigger repeated searches.','Broader Russian/Byzantine icon collection unresearched; only nine source objects checked. Museum and directory coverage incomplete.','Preserve original workshop/school labels and qualifiers; do not invent painter identities.'])
            entry['evidence_paths']=list(dict.fromkeys(entry.get('evidence_paths',[])+evidence+[str((E/'source-register.json').relative_to(b.ROOT)),str((E/'global-identity-reconciliation.json').relative_to(b.ROOT))]))
            assert [x for x in before['sources'] if x['source_id']!='national_museum_warsaw']==[x for x in queue['sources'] if x['source_id']!='national_museum_warsaw']
            tmp=qp.with_suffix('.b000033.tmp'); tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)); tmp.replace(qp)
        b.save('source-queue-update-verification.json',dict(at=h.now(),before_sha256=oldhash,after_sha256=h.sha(qp.read_bytes()),changed_source='national_museum_warsaw',unrelated_entries_preserved=True,entry=entry,registry_source_count=len(queue['sources'])))
    start=datetime.datetime.fromisoformat(root['inflight']['started_at']); end=datetime.datetime.now(datetime.timezone.utc)
    b.save('milestone-report.json',dict(at=h.now(),measured_runtime=dict(start=start.isoformat(),end=end.isoformat(),seconds=(end-start).total_seconds()),programme_elapsed_seconds=(end-datetime.datetime.fromisoformat(root['started_at'])).total_seconds(),verified_counts=counts,cumulative_attributable_counts={k:root['totals'][k]+counts[k] for k in counts},discovered=9,selected=6,prepared_images=6,metadata_verified=6,images_verified=6,failures=[],unresolved=[dict(source_id=x['source_id'],reason=x['outcome']) for x in holds],next_task=next_task,verification_limits='All six actual images individually viewed. Modest source display resolution retained. Scoped correctness checks are not a ten-million-row load test. No full institution coverage claimed.',hourly_and_100_hour_reporting='Existing external supervisor owns summaries, continuation and milestones. No supervisor, schedule, session or LaunchAgent created or edited.'))
    result=dict(outcome='progress',summary='Verified six new Warsaw icon review artworks, six documented holdings and six new primary images. Individually viewed every image; preserved workshop/school attributions and three research holds. Verified reruns make no duplicate writes. Local catalogue untouched.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=evidence)
    b.save('worker-result.json',result); h.save(b.R/'worker-result.json',h.load(E/'worker-result.json'))
    assert all((b.ROOT/x).is_file() for x in evidence)
    assert (E/'CHECKPOINT.json').read_bytes()==(b.R/'CHECKPOINT.json').read_bytes()
    assert h.load(qp)['sources'] and all(h.load(qp)[k]==v for k,v in before.items() if k!='sources')
    b.save('final-checkpoint-verification.json',dict(at=h.now(),checkpoint_sha256=h.sha((E/'CHECKPOINT.json').read_bytes()),runtime_checkpoint_sha256=h.sha((b.R/'CHECKPOINT.json').read_bytes()),checkpoints_identical=True,evidence_files=[dict(path=x,sha256=h.sha((b.ROOT/x).read_bytes())) for x in evidence],verified_counts=counts,supervisor_checkpoint_unchanged=h.load(E.parents[1]/'CHECKPOINT.json')==root))
    print(json.dumps(result,ensure_ascii=False))
