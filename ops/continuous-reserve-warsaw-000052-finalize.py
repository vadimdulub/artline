#!/usr/bin/env python3
"""Record batch-52 reviews and checkpoint; no production or supervisor writes."""
import copy
import datetime
import fcntl
import importlib.util
import json
import os
from pathlib import Path

spec=importlib.util.spec_from_file_location('research52',Path(__file__).with_name('continuous-reserve-warsaw-000052-research.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
E=b.E
ZERO=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)


def once(name,value):
    p=E/name
    if p.exists():return b.load(p)
    b.save(p,value);return value


def main():
    audit=b.load(E/'independent-reserve-evidence-verification.json')
    discovery=b.load(E/'warsaw-discovery.json')
    auth=b.load(E/'authentication-verification.json')
    assert not auth['live_production_target_verified']
    at=b.now()
    notes={
      '80082':'Full supplied print frame with two standing costumed figures; pale paper border retained. Image does not establish physical impression date.',
      '80437':'Full supplied print frame with two women dressing beside an oval mirror; paper border retained. Visible composition does not resolve the ca. 1935 source label.',
      '81054':'Full supplied print frame with bearded man raising one hand and holding a stick; lower printed margin retained. No physical impression date inferred from reproduction.'}
    visual=[]
    for r in audit['records']:
        if r['source_id'] in notes:
            visual.append(dict(source_id=r['source_id'],artwork_id=r['artwork_id'],
                viewed_path=r['local_path'],sha256=r['derivative_sha256'],viewed_individually=True,
                method='functions tools.view_image on actual existing prepared derivative',
                observation=notes[r['source_id']],decision='Preserve prior image approval and unresolved physical-date review',
                prior_visual_evidence=r['prior_visual_decision']))
    assert len(visual)==3
    once('actual-visual-review.json',dict(at=at,records=visual,actual_files_viewed_this_batch=3,
        remaining_185_files='Prior actual visual decisions checksum-verified; not newly viewed in this batch.',
        new_images_selected=0,metadata_changes=0))

    straightforward={'498395','498694','498539','498648','498406','498693'}
    date_review={'498307','498578','498402'}
    component_review={'498275','498516','498611','498533','498529','498614','498569'}
    reviews=[]
    for r in discovery['records']:
        sid=r['source_id'];reason=None;bounds=None
        if sid in straightforward:
            d=r['dates'];assert len(d)==1 and d[0]['name'] in ['XIX w.','XVIII w.'] and d[0]['comment'] is None
            bounds=[1801,1900] if d[0]['name']=='XIX w.' else [1701,1800]
            state='priority_for_live_global_reconciliation'
            reason='Whole painted inventory object with source closed-century date. Multiple painted scenes count as one object. Qualified workshop labels remain verbatim; no painter invention.'
        elif sid in date_review:
            state='date_interpretation_review'
            reason='Preserve literal quarter-century/century-transition or mid-century wording; final physical-date bounds need editorial review. No invented exact year.'
        elif sid in component_review:
            state='physical_unit_component_version_review'
            reason='Source describes cover, compound inventory, iconostasis fragment or assembled plaques. Reconcile physical unit and all view/component identities before selection; fragments are not categorically ineligible.'
        elif sid=='498420':
            state='creator_and_composite_version_review'
            reason='Museum inscription credits P. F. Burmistrow and 9 February 1896 on the cross; source distinguishes stylistically different side wings and reverse decoration. Do not apply one creator/date to every component without review. Reconcile creator globally before any new painter.'
        else:
            assert 'odlew' in [x['name'] for x in r['techniques']]
            state='metalwork_cast_version_review'
            reason='Cast metalwork; preserve source casting, enamel and qualified workshop evidence. Requires correct metalwork type and exact physical cast/unit reconciliation, not automatic exclusion or a painting-only importer.'
        assert r['owner']==dict(id=107515,name='Muzeum Narodowe w Warszawie')
        assert r['copyrights'] and all(x['name']=='DOMENA PUBLICZNA' and not x['restricted'] for x in r['copyrights'])
        reviews.append(dict(source_id=sid,accession=r['accession'],title=r['title'],source_url=r['source_url'],
            source_sha256=r['receipt']['sha256'],source_date=r['dates'],provisional_bounds=bounds,
            original_creators=r['creators'],decision=state,reason=reason,
            production_identity_status='Not yet live-reconciled; must check native/historical IDs, global inventory and URL identities, title/dimensions/version and creators',
            selected_for_import=False,images_downloaded=0,
            rights='Actual source DOMENA PUBLICZNA label retained; no new copyright-holder licence inferred.',
            holdings='Explicit native owner is object-level research evidence; no accepted production assertion or current-display claim.'))
    assert len(reviews)==24
    once('research-review.json',dict(at=at,records=reviews,priority_for_live_reconciliation=6,other_editorial_reviews=18,
        selected_for_import=0,metadata_ready_for_production=0,image_selection=0))
    once('failures.json',dict(at=at,failures=[
        dict(stage='production target authentication',attempts=1,retries=0,evidence='authentication-verification.json',resolution='Interactive gcloud reauthentication required'),
        dict(stage='web tool API rendering',attempts=1,error='URL not accessible via web tool',resolution='Existing documented direct public API returned HTTP 200; tool limitation is not a provider hold'),
        dict(stage='local script startup',error='System python3 lacks PIL',attempts=3,network_requests=0,production_connections=0,resolution='Used existing /tmp/artline-cyprus-venv/bin/python; no package installation or paid service')]))
    inherited=E.parent/'000051/source-access-holds.json'
    once('source-access-holds.json',dict(at=at,inherited_ledger=str(inherited.relative_to(b.ROOT)),
        inherited_sha256=b.sha(inherited.read_bytes()),all_inherited_provider_holds_preserved=True,
        new_provider_holds=[],production_authentication=dict(status='interactive_reauthentication_required',
            evidence='authentication-verification.json',retry_without_external_change=False,
            required_action='gcloud auth login --account=vadim@alingva.com'),
        researched_routes=dict(yale_lux='Archived source/visual/production evidence only; no provider requests',
            national_museum_warsaw='Page 3 and 24 object metadata responses HTTP 200; no image downloads'),
        forbidden_retries='Vatican HTTP 403 and all prior provider holds unchanged; no bypass or alternate account.'))
    registry=b.load(b.CAP/'original-111-source-registry.json')
    once('source-register.json',dict(at=at,registry_rows=111,original_registry=b.ref(b.REGISTRY),
        routes=[dict(registry=next(x for x in registry if x['source_id']==sid),
            policy_reference='docs/ARTLINE_IMAGE_USE.md#'+('continued-illustrated-expansion--11-october-2026' if sid=='yale_lux' else 'general-image-use-policy'),
            access_status='Archived evidence reverified; fresh production auth blocked' if sid=='yale_lux' else 'Public page 3 and 24 exact native object captures HTTP 200',
            last_checked_at=at,remaining_gaps='188 previously delivered reserve records excluded' if sid=='yale_lux' else '24 identities await live global reconciliation, with 18 date/unit/cast/creator reviews',
            directory_coverage_complete=False,artwork_coverage_complete=False) for sid in ['yale_lux','national_museum_warsaw']]))

    if not (E/'source-queue-update-verification.json').exists():
        with (b.R.parent.parent/'source-queue.lock').open('a+') as qlock:
            fcntl.flock(qlock,fcntl.LOCK_EX)
            raw=b.QUEUE.read_bytes();q=json.loads(raw);before=copy.deepcopy(q)
            b.save(E/'source-queue-immediately-before-update.json',before)
            by={x['source_id']:x for x in q['sources']}
            yale=by['yale_lux'];warsaw=by['national_museum_warsaw']
            for row in [yale,warsaw]:
                row['checkpoint']=str((E/'CHECKPOINT.json').relative_to(b.ROOT));row['last_checked_at']=at
                row['latest_batch_verified_counts']=ZERO
                row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+[str((E/p).relative_to(b.ROOT)) for p in ['batch-verification-receipt.json','independent-source-verification.json','independent-reserve-evidence-verification.json','research-review.json','source-register.json']]))
            yale['access_status']='188 archived source/visual/file identities reverified; batch 49 live evidence reused, fresh live authentication blocked'
            yale.setdefault('research_history',[]).append(dict(batch=52,at=at,finding='All 188 were previously delivered under another plan; zero selected',fresh_live_query=False,evidence=str((E/'independent-reserve-evidence-verification.json').relative_to(b.ROOT))))
            old=copy.deepcopy(warsaw['resume_cursor']);warsaw.setdefault('prior_resume_cursors',[]).append(old)
            cursor=copy.deepcopy(old)
            cursor.update(query_url=discovery['page_receipt']['url'],captured_page=3,
                pending_native_ids_current_page=[r['source_id'] for r in discovery['records']],
                next_page_after_pending=4,metadata_page_sha256=discovery['page_receipt']['sha256'],
                saved_discovery=str((E/'warsaw-discovery.json').relative_to(b.ROOT)),
                review_ledger=str((E/'research-review.json').relative_to(b.ROOT)),
                priority_native_ids=sorted(straightforward),
                next_step='After authentication changes, reconcile prior live receipts; reuse saved page-3 objects without recapture. Globally reconcile six straightforward painted inventories first; review the other 18. Do not advance to page 4 until page-3 dispositions are persisted.',
                production_authentication_required=True)
            # Old pins identify completed batch 48, never the new unreconciled objects.
            cursor.pop('selection_sha256',None);cursor.pop('metadata_plan_sha256',None)
            warsaw['resume_cursor']=cursor
            warsaw['status']='page3_24_native_objects_captured_pending_live_reconciliation_authentication_blocked'
            warsaw['access_status']='25 native metadata HTTP 200 responses; no image requests; production auth blocked'
            warsaw['remaining_gaps']=list(dict.fromkeys(warsaw.get('remaining_gaps',[])+['Page 3 captured: six straightforward painted objects await live reconciliation; 18 require date/unit/cast/creator review. None selected or counted as new.']))
            warsaw.setdefault('research_history',[]).append(dict(batch=52,at=at,captured_objects=24,selected_for_import=0,live_reconciliation=False,evidence=str((E/'warsaw-discovery.json').relative_to(b.ROOT))))
            untouched={k:v for k,v in by.items() if k not in ['yale_lux','national_museum_warsaw']}
            assert len(untouched)==109
            assert untouched=={x['source_id']:x for x in before['sources'] if x['source_id'] not in ['yale_lux','national_museum_warsaw']}
            assert b.QUEUE.read_bytes()==raw,'Concurrent queue update; rebase first'
            temp=b.QUEUE.with_name('source-queue.batch52.tmp')
            with temp.open('x') as f:
                json.dump(q,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
            os.replace(temp,b.QUEUE)
            b.save(E/'source-queue-update-verification.json',dict(at=at,before_sha256=b.sha(raw),
                after_sha256=b.sha(b.QUEUE.read_bytes()),modified_source_ids=['yale_lux','national_museum_warsaw'],
                unrelated_entries_preserved=109,registry_entries=111,prior_processed_delivered_and_held_ids_preserved=True,
                saved_pending_ids=cursor['pending_native_ids_current_page'],next_page_after_pending=4,
                no_cumulative_delivery_counts_changed=True))

    start=datetime.datetime.fromisoformat(auth['at']);end=datetime.datetime.now(datetime.timezone.utc)
    next_task='After gcloud reauthentication, reconcile live batch-49 receipts, then reuse Warsaw page-3 captures: globally reconcile 498395, 498694, 498539, 498648, 498406 and 498693; review the other 18 before images or import. French reserve is exhausted; preserve all provider holds.'
    cp=once('CHECKPOINT.json',dict(at=end.isoformat(),started_at=auth['at'],batch=52,outcome='blocked',
        stage='reserve_exhausted_evidence_reverified_warsaw_page3_captured_production_authentication_blocked',
        elapsed_seconds=(end-start).total_seconds(),verified_counts=ZERO,
        reserve_inspected=188,previously_delivered_excluded=188,discovered_objects=24,selected_for_import=0,
        prepared_new_images=0,production_write_attempts=0,local_catalogue_connections=0,
        blocker='Run gcloud auth login --account=vadim@alingva.com. Credentials cannot refresh non-interactively.',
        retry_authentication_without_external_change=False,next_task=next_task,
        resume=dict(command='/tmp/artline-cyprus-venv/bin/python ops/continuous-reserve-warsaw-000052-research.py warsaw',
            mode='Saved checksum-bound captures; no recapture needed',source='national_museum_warsaw',captured_page=3,
            pending_native_ids=[r['source_id'] for r in discovery['records']],next_page_after_pending=4,
            production_prerequisites=['Reverify target artline-508319:europe-west1:artline-postgres and proxy helper','Reconcile live receipts and persisted plan/source/rights checksums before writes','Fresh globally reconciled pinned plan, backup and transaction preimages','Shared transaction lock artline-curated-ingestion']),
        external_supervisor_unchanged=True,supervisor_running_claim=False,
        cumulative_counts='No increments; inherited cumulative totals not freshly audited',
        hourly_milestone='This bounded worker has not reached one hour; existing external supervisor owns hourly and 100-hour continuation reporting'))
    b.save(b.R/'CHECKPOINT.json',cp)
    once('batch-verification-receipt.json',dict(at=b.now(),batch=52,outcome='blocked',verified_counts=ZERO,
        inspected_reserve=188,source_capture_checks=376,existing_derivatives_decoded=188,
        prior_visual_evidence_checks=188,new_visual_files_viewed=3,
        fallback_metadata_objects_captured=24,selected_for_import=0,prepared=0,imported=0,
        production_ids=[],production_writes_attempted=0,storage_writes_attempted=0,
        live_production_verified=False,attribution='No production writes attempted; all 188 French works belong to earlier campaign plan. Prior campaign and earlier programme deliveries excluded from batch increments.',
        limitations=['Current production/authentication unverified','Warsaw identities not globally reconciled','No new image files selected or viewed','No current-display claims'],
        next_task=next_task))
    print('Checkpoint saved; 24 metadata captures pending; production increments zero.')


if __name__=='__main__':
    with (b.R/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
