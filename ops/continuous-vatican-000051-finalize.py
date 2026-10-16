#!/usr/bin/env python3
"""Verify batch 51 evidence and checkpoint a blocked, metadata-only attempt.

Only updates the researched source row under the queue lock. Never writes to
the supervisor, its configuration, or any database.
"""
import copy
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/research/continuous-production-20261011'
E = BASE / 'batches/000051'
RUNTIME = Path.home() / 'Library/Application Support/Artline/continuous-research/batches/000051'
ZERO = dict(new_painters=0, new_artworks=0, newly_illustrated=0, alternate_images=0, museum_links=0)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, f'Immutable evidence differs: {path}'
    else:
        with path.open('xb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())


def main():
    assert not (E / 'CHECKPOINT.json').exists(), 'Batch already finalized; verify saved checkpoint, do not replay'
    inputs = load(E / 'required-input-reconciliation.json')
    at = now()
    auth = load(E / 'authentication-blocker-verification.json')
    assert auth['exit_code'] == 1 and not auth['live_production_target_verified']
    assert auth['database_connections_attempted'] == auth['database_writes_attempted'] == 0
    captures = load(E / 'source-capture-manifest.json')
    assert len(captures['records']) == 1
    first = captures['records'][0]
    assert first['status'] == 403
    path = Path(first['body_path'])
    assert path.is_file() and sha(path) == first['sha256'] and b'403 Forbidden' in path.read_bytes()
    save(E / 'independent-source-access-verification.json', dict(
        at=at, records_verified=1, requested_native_id=first['native_id'],
        request_url=first['url'], response_status=403, body_path=str(path),
        body_sha256=sha(path), bytes=path.stat().st_size,
        receipt_sha256=sha(path.with_suffix('.json')),
        blocked_response_is_not_object_evidence=True,
        no_remaining_object_requests=True, retries=0, images_requested=0,
        retry_policy='Do not retry this host until documented access conditions change; no alternate client bypass.'))

    # These are leads extracted from indexed official pages, not fresh captures,
    # accepted creator authorities, selected import records, or new catalogue rows.
    prefix = 'https://catalogo.museivaticani.va/index.php/Detail/objects/'
    browse = 'https://catalogo.museivaticani.va/index.php/Browse/objects/key/c8e7902444a22806acea7637047eefc8/facet/decade_facet/id/1560/view/list'
    bibliography = 'https://m.museivaticani.va/content/dam/museivaticani/pdf/eventi_novita/iniziative/giovedi_musei/2010/MV_2_Picturae_etruscorum_vasculis_corninicv.pdf'
    leads = [
        dict(native_id='MV.40076.0.0', title='Icona: Presentazione di Gesù al Tempio o Purificazione',
             creator_label='Maestro Giovanni (Scuola Greca-Macedone)', source_date='fine sec. XVI',
             source_medium='tempera su tavola di cirmolo', source_dimensions='cm 37,7 x 29,4',
             discovery_url=prefix+'MV.40076.0.0', evidence_level='Indexed official object page; direct response subsequently HTTP 403',
             creator_treatment='Qualified master identity; globally reconcile before any painter creation',
             provenance_summary='Vettori collection; papal gift 1756; listed in the Christian Museum inventory in 1762; museum entry date 12/02/1909 is not creation date.'),
        dict(native_id='MV.40045.0.0', title='Icona: Battesimo di Cristo',
             creator_label='Arte Russa', source_date='XVI sec.',
             source_medium='tempera su tavola di rovere', source_dimensions=None,
             discovery_url=browse, evidence_level='Indexed official browse record only; detail unrequested',
             creator_treatment='Culture label, not a named person; no invented painter'),
        dict(native_id='MV.64662.0.0', title='Icona multipla decorata sui due lati. R: Cristo in trono tra la Mad...',
             title_truncated=True, creator_label='intagliatore russo (Mosca?)', source_date='XVI sec.',
             source_medium='avorio intagliato', source_dimensions=None,
             discovery_url=browse, evidence_level='Indexed official browse record only; detail unrequested',
             creator_treatment='Qualified anonymous maker; Moscow uncertainty retained',
             version_hold='Double-sided composite; complete title, unit and both sides require exact object review; never split into inflated artwork count'),
        dict(native_id='MV.61191.0.0', source_inventory_label='61191',
             title='Icona portatile raffigurante San Teodoro Tiro', creator_label=None,
             qualified_origin='Costantinopoli (?)', source_date='XIV secolo',
             source_medium='mosaico minuto su cera; legno', source_dimensions=None,
             discovery_url=bibliography, evidence_level='Indexed official curator bibliography; inferred native identifier format remains unverified',
             creator_treatment='Unidentified creator; qualified origin is not a person',
             version_hold='Exact native record and object dimensions not checked'),
    ]
    save(E / 'discovery-leads.json', dict(
        at=at, source='vatican_museums', count=4, records=leads,
        queries=['site.museivaticani.va Byzantine icons collection Saint',
                 'site:catalogo.museivaticani.va "Icona" "Numero"',
                 'site:catalogo.museivaticani.va/index.php/Detail "Icona"',
                 'site:museivaticani.va "Icona" "inv"'],
        origin='Actual web search results transcribed into this lead ledger; not raw HTTP 200 object captures',
        recency_limit='Catalogue search results were labelled crawled 1.3 years ago; fresh object validation did not succeed',
        selected_for_import=0, prepared_images=0, accepted_holdings=0,
        production_identity_reconciliation=False, creator_global_reconciliation=False,
        date_policy='Source period text preserved; no numerical year invented',
        image_policy='No image selected or requested. Registry Vatican default does not permit automated reproductions; source-specific approval must be assessed per object without generalizing another provider approval.',
        not_current_display_evidence=True))

    # Reconcile persisted previous delivery artifacts without claiming a new live
    # production check while account authentication is blocked.
    previous = BASE / 'batches/000049'
    receipt = load(previous / 'batch-verification-receipt.json')
    verification = load(previous / 'independent-production-verification.json')
    checks = [
        (Path(verification['transaction_preimages']), verification['preimage_sha256']),
        (previous / 'batches/tepapa-direct-049/selection.json.gz', receipt['selection_sha256']),
        (previous / 'batches/tepapa-direct-049/visual-review.json', receipt['visual_review_sha256']),
    ]
    for path, digest in checks:
        assert sha(path) == digest
    prior50 = load(BASE / 'batches/000050/authentication-blocker-verification.json')
    assert prior50['database_writes_attempted'] == 0
    save(E / 'prior-receipt-reconciliation-verification.json', dict(
        at=at, previous_batch=49, receipt_sha256=sha(previous / 'batch-verification-receipt.json'),
        immutable_artifacts=[dict(path=str(p), sha256=d, verified=True) for p, d in checks],
        previous_batch_50_write_attempts=0,
        batch_51_existing_transaction_preimages=[], batch_51_existing_applied_receipts=[],
        batch_51_existing_selection_or_plan_checksums=[],
        live_production_reconciliation=False,
        no_prior_delivery_counted_in_batch_51=True,
        limitation='Live source-citation/rights checks and drift reconciliation must be completed after authentication; no ambiguous write replay attempted.'))

    prior_holds = BASE / 'batches/000050/source-access-holds.json'
    save(E / 'source-access-holds.json', dict(
        at=at, inherited_ledger=str(prior_holds.relative_to(ROOT)), inherited_sha256=sha(prior_holds),
        inherited_queue='source-queue-before.json',
        new_holds=[dict(source_id='vatican_museums', host='catalogo.museivaticani.va',
                       scope='native inventory HTTP requests', status=403,
                       observed_at=first['retrieved_at'], url=first['url'],
                       evidence='independent-source-access-verification.json',
                       retry_allowed_without_external_change=False),
                   dict(source_id='production_authentication', status='interactive_reauthentication_required',
                        evidence='authentication-blocker-verification.json', attempts=1, retries=0)],
        policy='All inherited provider holds preserved. No TLS bypass, alternate account, alternate client or private credentials inspection.'))
    save(E / 'source-register.json', dict(
        at=at, registry_path=inputs['registry_path'], registry_sha256=inputs['registry_sha256'],
        registry_entries=111, source=inputs['selected_registry_source'],
        policy_reference=['Original GLOBAL_MUSEUM_SOURCE_REGISTRY.csv vatican_museums', 'docs/ARTLINE_IMAGE_USE.md'],
        access_status='Native inventory host HTTP 403; indexed public pages yielded four leads only',
        directory_coverage='Vatican institution identity already present in complete source registry',
        artwork_coverage='Four source leads; zero verified production artwork additions',
        remaining_gaps=['Fresh exact native object captures', 'Full composite title and object units',
                        'Global creator and exact artwork reconciliation', 'Current production holdings and prior delivery state',
                        'Image identity and per-object reproduction eligibility'],
        source_cursor='First selected direct object MV.40076.0.0 access-held; other three unrequested'))

    next_task = ('After gcloud reauthentication, independently reconcile batch 49 receipts and live production state, '
                 'then research Warsaw native icon search page 3, at most 24 leads, excluding saved processed IDs '
                 'and 27 date/unit/version holds. Preserve Vatican HTTP 403 hold and batch 50 Sinebrychoff cursor.')
    save(E / 'batch-verification-receipt.json', dict(
        at=at, batch=51, outcome='blocked', verified_counts=ZERO, production_ids=[],
        discovered=4, selected_for_import=0, prepared=0, imported=0, verified=0,
        native_requests=1, native_access_failures=1, images_downloaded=0,
        images_visually_viewed=0, visual_review='No image prepared or reviewed',
        source_verification='Access receipt independently rehashed; search leads are not verified object selections',
        database_connections=0, storage_writes=0, database_writes=0,
        live_production_reconciliation_completed=False,
        attribution='No attributable production increments: target verification failed before connection; no plan, transaction or source citation was written. Previous campaigns excluded.',
        blocker_evidence='authentication-blocker-verification.json', next_task=next_task))

    qpath = BASE / 'source-queue.json'
    with (BASE / 'source-queue.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        before_bytes = qpath.read_bytes()
        queue = json.loads(before_bytes)
        assert len(queue['sources']) == 111
        save(E / 'source-queue-immediately-before-update.json', queue)
        old = copy.deepcopy(queue)
        row = next(r for r in queue['sources'] if r['source_id'] == 'vatican_museums')
        if row.get('resume_cursor'):
            row.setdefault('prior_resume_cursors', []).append(copy.deepcopy(row['resume_cursor']))
        row.update(status='native_inventory_http403_hold_four_indexed_icon_leads_unreconciled',
                   checkpoint=str((E / 'CHECKPOINT.json').relative_to(ROOT)),
                   last_checked_at=at,
                   policy_reference='Original GLOBAL_MUSEUM_SOURCE_REGISTRY.csv vatican_museums; docs/ARTLINE_IMAGE_USE.md',
                   access_status='HTTP 403 on first native object; no retry; no images requested',
                   resume_cursor=dict(route='native_inventory_manual_review',
                       attempted_native_ids=['MV.40076.0.0'],
                       unrequested_native_ids=captures['remaining_native_ids'],
                       discovered_ids=[r['native_id'] for r in leads],
                       processed_for_import_ids=[], selected_ids=[],
                       retry_allowed=False, external_state_change_required='Provider access and production authentication',
                       lead_ledger=str((E/'discovery-leads.json').relative_to(ROOT)),
                       next_step='Rotate to available sources. Revisit saved leads only after documented provider access change.'),
                   latest_batch_verified_counts=ZERO,
                   remaining_gaps=['Four indexed leads have no fresh primary-source validation or global production reconciliation',
                                   'No source-backed image selected; no accepted holdings',
                                   'Do not infer current display from old gallery or exhibition pages'])
        for name in ['independent-source-access-verification.json', 'discovery-leads.json',
                     'source-register.json', 'batch-verification-receipt.json', 'CHECKPOINT.json']:
            rel = str((E / name).relative_to(ROOT))
            if rel not in row['evidence_paths']:
                row['evidence_paths'].append(rel)
        row.setdefault('research_history', []).append(dict(at=at, batch=51,
            scope='Four indexed icon leads; one bounded native metadata request',
            finding='First object request HTTP 403; no fresh selected record, image, holding or production mutation',
            evidence_path=str((E/'independent-source-access-verification.json').relative_to(ROOT))))
        unchanged = [r['source_id'] for r in old['sources'] if r['source_id'] != 'vatican_museums']
        for source_id in unchanged:
            assert next(r for r in old['sources'] if r['source_id'] == source_id) == next(r for r in queue['sources'] if r['source_id'] == source_id)
        assert {k:v for k,v in old.items() if k != 'sources'} == {k:v for k,v in queue.items() if k != 'sources'}
        tmp = qpath.with_name('source-queue.000051.tmp')
        with tmp.open('xb') as handle:
            handle.write((json.dumps(queue, ensure_ascii=False, indent=2)+'\n').encode())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, qpath)
        assert load(qpath) == queue
        save(E / 'source-queue-update-verification.json', dict(
            at=at, before_sha256=hashlib.sha256(before_bytes).hexdigest(), after_sha256=sha(qpath),
            source_count=111, changed_source_ids=['vatican_museums'],
            unchanged_source_ids=unchanged, unrelated_entries_preserved=len(unchanged),
            all_unrelated_values_preserved=True, top_level_values_preserved=True,
            finnish_and_warsaw_cursors_preserved=True, atomic_replace=True,
            queue_lock='source-queue.lock', database_ingestion_lock_not_used_no_writes=True))

    started = auth['at']
    checkpoint = dict(
        at=now(), started_at=started, batch=51, outcome='blocked',
        stage='research_checkpointed_production_authentication_and_vatican_access_blocked',
        elapsed_seconds=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(started)).total_seconds(),
        verified_counts=ZERO, discovered_leads=4, selected_for_import=0,
        blocker='Run gcloud auth login --account=vadim@alingva.com. Production credentials cannot refresh non-interactively.',
        provider_hold='catalogo.museivaticani.va HTTP 403; no unchanged retry',
        next_task=next_task, external_state_change_required=True,
        resume=dict(source='national_museum_warsaw', native_icon_search_page=3, maximum_leads=24,
                    preserve_existing_source_cursor=True,
                    prerequisites=['Production target and proxy reverified', 'Live citation/rights/preimage reconciliation before retrying any ambiguous writes',
                                   'Shared advisory lock artline-curated-ingestion for every production transaction']),
        local_catalogue_connections=0, external_supervisor_unchanged=True,
        supervisor_state_observation='Existing master checkpoint named batch 51 attempt 1; supervisor was not launched, edited or controlled by this worker.',
        milestone_report='No hourly milestone reached within this bounded worker; batch zero increments leave prior totals unchanged. Prior cumulative totals not freshly audited.',
        evidence_paths=[str(p.relative_to(ROOT)) for p in sorted(E.glob('*.json'))])
    save(E/'CHECKPOINT.json', checkpoint)
    save(RUNTIME/'CHECKPOINT.json', checkpoint)
    assert (E/'CHECKPOINT.json').read_bytes() == (RUNTIME/'CHECKPOINT.json').read_bytes()
    save(E/'final-checkpoint-verification.json', dict(
        at=now(), evidence_files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.glob('*.json'))],
        worker_files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [ROOT/'ops/continuous-vatican-000051-research.py',ROOT/'ops/continuous-vatican-000051-finalize.py']],
        runtime_checkpoint_matches=True, source_queue_111_entries=True,
        unrelated_source_entries_preserved=110, verified_counts=ZERO,
        no_current_batch_production_mutation=True, supervisor_prompt_schema_launchagent_untouched=True))
    print(json.dumps(dict(outcome='blocked',verified_counts=ZERO,discovered_leads=4,checkpoint=str(E/'CHECKPOINT.json'))))


if __name__ == '__main__':
    main()
