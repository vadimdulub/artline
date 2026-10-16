#!/usr/bin/env python3
"""Finalize only batch 153 evidence and its researched queue routes."""
import fcntl
import importlib.util
import json
import os
import subprocess
from pathlib import Path

spec = importlib.util.spec_from_file_location('batch153', Path(__file__).with_name('continuous-exhibitions-000153.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
c, E, R, B, Q, ROOT = m.c, m.E, m.R, m.B, m.Q, m.ROOT
rel = lambda n: str((E / n).relative_to(ROOT))

p = c.load(E / 'plan-v2.json')
pin = c.load(E / 'plan-pin-v2.json')['sha256']
assert c.sha((E / 'plan-v2.json').read_bytes()) == pin
verification = c.load(E / 'independent-database-verification.json')
for name in ['independent-database-verification.json', 'independent-public-verification.json', 'backup-verification.json']:
    receipt = c.load(E / name)
    assert receipt['passed'] and receipt['plan_sha256'] == pin
assert c.load(E / 'attempt-002-recovery-verification.json')['prior_attempt_no_evidence_of_committed_rows']

startup = c.load(E / 'attempt-002-startup-verification.json')
protected = []
for f in startup['protected_files']:
    assert c.sha(Path(f['path']).read_bytes()) == f['sha256']
    protected.append(f)
state = c.load(R.parents[1] / 'state.json')
assert state['inflight']['batch'] == 153 and state['inflight']['attempt'] == 2
processes = []
for key in ['supervisor_pid', 'worker_pid']:
    pid = state[key]
    command = subprocess.check_output(['ps', '-p', str(pid), '-o', 'pid=,ppid=,command='], text=True).strip()
    lines = [line for line in subprocess.run(['lsof', '-p', str(pid)], capture_output=True, text=True).stdout.splitlines()
             if str(R.parents[1] / 'supervisor.lock') in line]
    assert lines and pid in [v['pid'] for v in startup['locks']]
    processes.append(dict(pid=pid, command=command, inherited_lock_lines=lines))
commands = subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True).splitlines()
supervisors = [line for line in commands if line.rstrip().endswith('/ops/continuous-exhibition-research.py run')]
workers = [line for line in commands if 'codex exec ' in line and str(R.parents[1] / 'schema.json') in line]
assert len(supervisors) == len(workers) == 1
c.save(E / 'continuation-process-verification.json', dict(at=c.now(), processes=processes,
    supervisor_pid=state['supervisor_pid'], worker_pid=state['worker_pid'], supervisor_count=1, worker_count=1,
    protected_files_unchanged=protected, external_supervisor_owns_continuation=True,
    additional_supervisors_or_workers_launched=0, inherited_descriptors_unchanged=True, passed=True))

next_task = ('Inspect the official Prints + Printmaking reference route for exhibition 3296 '
             '(https://printsandprintmaking.gov.au/exhibitions/3296/references/) for a contemporaneous checklist, '
             'then reconcile up to 20 exact objects. Preserve the two stop-date conflicts and Hamilton/Midura '
             'identity holds. If no checklist is available, select the next undelivered historical pictorial '
             'event from the captured NGV archive; do not replay this tour or retry held NGA/Arthive routes.')
evidence_names = ['attempt-002-recovery-verification.json', 'source-capture-verification-v2.json',
                  'candidate-review-verification-v2.json', 'independent-database-verification.json',
                  'independent-public-verification.json', 'backup-verification.json']
with Q.with_suffix('.lock').open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    before = c.load(Q)
    q = m.serial(before)
    before_sha = c.sha(Q.read_bytes())
    ngv = next(s for s in q['sources'] if s['source_id'] == 'ngv')
    ngv.update(last_checked_at=c.now(), research_status='batch153_one_shared_hockney_tour_sixteen_stops_verified')
    ngv.setdefault('cursor', {})['batch153'] = dict(
        native_id='260305', production_exhibition_id=m.EID, plan_sha256=pin,
        source_url=p['sources'][0]['receipt']['url'], capture_sha256=p['sources'][0]['receipt']['sha256'],
        delivered_events=1, delivered_venue_stops=16, delivered_artist_links=1,
        complete_checklists=0, exact_artwork_links=0, next_url='https://printsandprintmaking.gov.au/exhibitions/3296/references/',
        next=next_task, evidence=rel('independent-database-verification.json'))
    for hold in ngv.get('holds', []):
        if hold.get('key') == 'ngv-hockney1976-tour':
            hold.update(status='tour_identity_resolved_batch153', resolution='One shared tour delivered; 15 NGV stops plus one Prints + Printmaking stop. Date and venue uncertainties retained.',
                        resolution_evidence=rel('independent-database-verification.json'))
    for key, reason in [
        ('hockney1976-stop-date-conflicts', 'Queensland and Tasmanian source periods conflict; both literal periods preserved and exact day fields withheld.'),
        ('hockney1976-historical-venue-identities', 'Hamilton City Art Gallery country/institution unresolved; NGV spelling Midura preserved without forcing a Mildura institution link.'),
        ('hockney1976-original-checklist', 'Original contemporary checklist uninspected; no exact artwork participation or complete-checklist claim.')]:
        ngv.setdefault('holds', []).append(dict(key=key, reason=reason, evidence=rel('candidate-review-verification-v2.json')))
    ngv.setdefault('evidence', []).extend(rel(n) for n in evidence_names)

    nga = next(s for s in q['sources'] if s['source_id'] == 'nga_australia')
    nga.update(last_checked_at=c.now(), research_status='main_host_access_held_separate_prints_catalogue_available_batch153')
    if nga.get('cursor') is None:
        nga['cursor'] = {}
    nga.setdefault('cursor', {})['batch153'] = dict(
        main_host_url='https://nga.gov.au/exhibitions/david-hockney-prints-76-78/',
        main_host_status=403, new_network_retries=0,
        independently_accessible_catalogue='https://printsandprintmaking.gov.au/exhibitions/3296/',
        next='Use the separately accessible official Prints + Printmaking catalogue; no retry of held main NGA page.',
        evidence=rel('nga-australia-access-hold-verification.json'))
    nga.setdefault('holds', []).append(c.load(E / 'nga-australia-access-hold-verification.json'))
    nga.setdefault('evidence', []).append(rel('nga-australia-access-hold-verification.json'))

    arthive = next(s for s in q['supplemental_sources'] if s['source_id'] == 'arthive_exhibitions')
    arthive.update(last_checked_at=c.now())
    arthive.setdefault('cursor', {})['batch153'] = dict(
        reviewed_at=c.now(), historical_archive_access='held_http429', new_network_requests=0,
        new_discoveries=0, next='Await a documented provider access-state change; use accessible official archives.',
        evidence=rel('arthive-attempt-002-discovery-outcome.json'))
    arthive.setdefault('evidence', []).append(rel('arthive-attempt-002-discovery-outcome.json'))

    assert not any(s['source_id'] == 'australian_prints_and_printmaking' for s in q['supplemental_sources'])
    q['supplemental_sources'].append(dict(
        source_id='australian_prints_and_printmaking', source_kind='official_institutional_catalogue',
        institution_or_network='National Gallery of Australia — Australian Prints + Printmaking',
        official_website='https://printsandprintmaking.gov.au/',
        research_status='batch153_hockney3296_shared_tour_corroboration_verified', last_checked_at=c.now(),
        cursor=dict(batch153=dict(native_id='3296', exhibition_id=m.EID, source_url=p['sources'][1]['receipt']['url'],
            capture_sha256=p['sources'][1]['receipt']['sha256'], delivered_shared_exhibitions=1,
            additional_stop='Bendigo Art Gallery', next_url='https://printsandprintmaking.gov.au/exhibitions/3296/references/',
            next=next_task)),
        holds=[dict(reason='Two stop-date conflicts and original-checklist gap; source assertions remain separate.',
                    evidence=rel('candidate-review-verification-v2.json'))],
        evidence=[rel(n) for n in evidence_names],
        counting_note='Corroboration of the same NGV tour; never a second distinct exhibition.',
        image_rights_rule='No images selected or rights assumed from metadata acceptance.'))
    changed = {'ngv', 'nga_australia'}
    assert [s for s in before['sources'] if s['source_id'] not in changed] == [s for s in q['sources'] if s['source_id'] not in changed]
    assert [s for s in before['supplemental_sources'] if s['source_id'] != 'arthive_exhibitions'] == [s for s in q['supplemental_sources'] if s['source_id'] not in {'arthive_exhibitions', 'australian_prints_and_printmaking'}]
    assert {k:v for k,v in before.items() if k not in ['sources','supplemental_sources']} == {k:v for k,v in q.items() if k not in ['sources','supplemental_sources']}
    c.save(B / 'source-queue-before.json', before)
    temp = Q.with_suffix('.batch153.tmp')
    temp.write_text(json.dumps(q, ensure_ascii=False, indent=2) + '\n')
    os.replace(temp, Q)
    assert c.load(Q) == q
    c.save(B / 'source-queue-after.json', q)
c.save(E / 'queue-update-verification.json', dict(at=c.now(), before_sha256=before_sha,
    after_sha256=c.sha(Q.read_bytes()), updated_sources=['ngv','nga_australia','arthive_exhibitions'],
    added_supplemental_sources=['australian_prints_and_printmaking'], original_registry_unchanged=True,
    all_unrelated_entries_and_cursors_preserved=True, next_task=next_task, passed=True))

counts = verification['verified_counts']
checkpoint = dict(at=c.now(), batch=153, attempt=2, stage='independently_verified_complete',
    plan_sha256=pin, discovered_selected_events=1, prepared_events=1, imported_events=1,
    independently_verified_events=1, verified_counts=counts, production_ids=[m.EID],
    checklist_state='unknown', unresolved_stop_date_conflicts=2, visual_review_claimed=False,
    recovery='Fresh production read found no prior batch153 rows or audit records; locked preimage was absent.',
    next_task=next_task, external_supervisor_owns_continuation=True,
    separate_artwork_programme_modified=False, local_catalogue_connections=0)
c.save(E / 'CHECKPOINT.json', checkpoint)
c.save(R / 'batch-checkpoint.json', checkpoint)
names = evidence_names + ['attempt-002-startup-verification.json', 'arthive-attempt-002-discovery-outcome.json',
                         'continuation-process-verification.json', 'queue-update-verification.json', 'CHECKPOINT.json']
artifacts = [dict(path=rel(n), sha256=c.sha((E/n).read_bytes()), bytes=(E/n).stat().st_size) for n in names]
assert c.load(R / 'batch-checkpoint.json') == checkpoint
c.save(E / 'completion-verification.json', dict(at=c.now(), plan_sha256=pin, artifacts=artifacts,
    verified_counts=counts, runtime_checkpoint_matches=True, passed=True))
result = dict(outcome='progress', summary='Verified one [Hockney print tour](https://www.ngv.vic.gov.au/exhibition/david-hockney-prints/) (1976–1978), 16 venue stops and one existing-artist participation link. Review state, two date conflicts and unknown checklist preserved. Existing supervisor continuation verified.',
    next_task=next_task, blocker='', verified_counts=counts,
    evidence_paths=[rel(n) for n in names + ['completion-verification.json']])
c.save(E / 'final-result.json', result)
print(json.dumps(result, ensure_ascii=False))
