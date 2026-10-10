"""Freeze verified wave78, source evidence and unfinished all-museum research."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    'a', Path(__file__).with_name('museum-expansion-britain-two-apply-20261008.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
m = a.m


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    dest = a.RUN / 'delivery-checkpoint-001.json'
    assert not dest.exists()
    assert sha(a.CHECKPOINT) == 'ff8a34c90c051412990227473ae0a4c3b11a1099143ef4b40722f8069a3c9a6d'
    previous = m.load(a.CHECKPOINT)
    assert len(previous['artifacts']) == 25469
    assert len(previous['external_artifacts']) == 482
    changes = m.load(a.RUN / 'readme-supersessions-001.json')['changes']
    changed = {v['path']: v for v in changes}
    assert set(changed) == {str((m.RUN / 'README.md').relative_to(m.ROOT))}
    for change in changes:
        assert sha(Path(change['backup_path'])) == change['backup_sha256']
        saved = m.load(Path(change['backup_path']))
        assert hashlib.sha256(saved['text'].encode()).hexdigest() == saved['sha256'] == change['before_sha256']
        assert sha(m.ROOT / change['path']) == change['after_sha256']
    for dep in previous['artifacts']:
        if dep['path'] in changed:
            assert dep['sha256'] == changed[dep['path']]['before_sha256']
        else:
            a.checked(dep)

    plan, digest = a.validate_plan()
    assert digest == '282e064ca8dd8a7202c8f20cfa1f689aea165c39c31b593f8e56dc1bedd11e54'
    with m.connect() as db:
        verified = a.verify(db, plan, digest)
    assert m.load(a.RUN / (a.KEY + '-applied.json'))['plan_sha256'] == digest
    report = m.load(m.RUN / 'verification-after-wave-78.json')
    assert report['verified_new_artworks'] == 10259
    assert report['verified_existing_artworks_linked'] == 1173
    assert report['institutions_with_new_records_or_reconciled_holdings'] == 217
    museum_changes = {v['institution_id']: v for v in report['britain_two_museum_changes']}
    assert {iid: v['existing_linked'] for iid, v in museum_changes.items()} == dict(zip(a.IIDS, [136, 97]))
    assert {iid: (v['linked_after'], v['eligible_after']) for iid, v in museum_changes.items()} == dict(zip(a.IIDS, [(138, 111), (106, 106)]))
    assert report['after']['museums_below_100'] == 1244
    assert report['after']['museums_below_200'] == 1389
    checks = m.load(a.RUN / 'checks-001.json')
    assert checks['new_offline_tests_passed'] == 16
    assert checks['historical_tests_passed'] == 1484
    assert checks['cumulative_verified_tests'] == 1500 and checks['replay_zero_writes']
    audit = m.load(m.RUN / 'after-wave-78.json')
    csvcounts, campaignids = {}, []
    for name, count in [
        ('added-artworks-after-wave-78.csv', 10259),
        ('reconciled-artworks-after-wave-78.csv', 1173),
        ('gac-date-enrichments-after-wave-78.csv', 6),
        ('museum-coverage-after-wave-78.csv', len(audit['institutions'])),
    ]:
        with (m.RUN / name).open(newline='') as fp:
            rows = list(csv.DictReader(fp))
        assert len(rows) == count
        csvcounts[name] = count
        if name.startswith(('added-artworks', 'reconciled-artworks')):
            campaignids.extend(v['artwork_id'] for v in rows)
    assert len(campaignids) == len(set(campaignids)) == 11432

    external = (previous['external_artifacts'] + list(checks['logs'].values())
                + [dict(path=v['backup_path'], sha256=v['backup_sha256']) for v in changes]
                + [dict(path=plan['backup_path'], sha256=plan['backup_sha256'])])
    reviewed = m.BACKUP / (a.KEY + '-reviewed-plan-001.json.gz')
    assert m.load(reviewed) == plan
    external.append(dict(path=str(reviewed), sha256=sha(reviewed)))
    proof = m.BACKUP / (a.KEY + '-transaction-identity-001.json.gz')
    proof_data = m.load(proof)
    assert proof_data['comparisons_equal'] and len(proof_data['comparisons']) == 242
    external.append(dict(path=str(proof), sha256=sha(proof)))
    correction = m.load(a.RUN / 'report-correction-001.json')
    original_report = correction['original_script_backup']
    external.append(original_report)
    saved_report = m.load(Path(original_report['path']))
    assert hashlib.sha256(saved_report['text'].encode()).hexdigest() == saved_report['sha256']
    a.checked(correction['corrected_script'])
    log = Path('/Users/vadimdulub/Library/Logs/artline-britain-two-delivery-20261009.log')
    assert '"documented_existing_links": 233' in log.read_text()
    external.append(dict(path=str(log), sha256=sha(log)))
    unique = {}
    for dep in external:
        assert dep['path'] not in unique or unique[dep['path']] == dep
        unique[dep['path']] = dep
        assert sha(Path(dep['path'])) == dep['sha256']

    a.checked(previous['other_job_status_reference'])
    src = m.load(a.RUN / 'source-context-001.json.gz')
    context = m.load(a.RUN / 'comparison-source-context-001.json.gz')
    refs = src['body_references'] + context['body_references']
    assert len(src['body_references']) == 146 and len(context['body_references']) == 51
    assert len({v['path'] for v in refs}) == 189
    native = [row for name in ['native-probes-001.json', 'native-probes-002.json']
              for row in m.load(a.RUN / name)['rows']]
    assert len(native) == 7 and all(v['capture']['receipt']['status'] == 200 for v in native)
    paths = {m.ROOT / v['path'] for v in previous['artifacts']}
    paths |= {a.CHECKPOINT, Path(__file__).resolve()}
    paths |= {v for v in a.RUN.rglob('*') if v.is_file()}
    paths |= {v for pattern in ['*britain-two*20261008.py', '*britain_two*20261008.py']
              for v in (m.ROOT / 'ops').glob(pattern)}
    paths |= {v for v in m.RUN.glob('*after-wave-78*')}
    paths |= {a.checked(v) for v in refs}
    artifacts = [a.reference(v) for v in sorted(paths)]

    queue = m.load(a.RUN / 'remaining-research-001.json.gz')
    assert len(queue['rows']) == 9
    a.checked(queue['previous_remaining_research_reference'])
    nextq = m.load(a.RUN / 'next-museum-pass-001.json')
    assert len(nextq['italian_museums']) == 225
    assert len(nextq['existing_holding_review_targets']) == 3
    assert not set(a.IIDS) & {v['id'] for v in nextq['existing_holding_review_targets']}
    runtime = m.load(a.RUN / 'environment-recovery-001.json')['runtime']
    result = dict(
        at=m.now(), goal_complete=False, local_only=True, new_additions=0,
        new_existing_links=233, campaign_new_artworks=10259,
        campaign_existing_links=1173, distinct_campaign_artwork_ids=11432,
        institutions_with_new_records_or_reconciled_holdings=217,
        verification=verified, museum_changes=report['britain_two_museum_changes'],
        museums_below_100=report['after']['museums_below_100'],
        museums_below_200=report['after']['museums_below_200'],
        global_coverage_snapshot_at=report['global_coverage_snapshot_at'],
        external_registry_growth_reference=report['external_registry_growth_reference'],
        new_tests_passed=16, historical_tests_passed=1484, cumulative_verified_tests=1500,
        plan_sha256=digest, csv_counts_verified=csvcounts, artifacts=artifacts,
        external_artifacts=list(unique.values()), prior_checkpoint_reference=a.reference(a.CHECKPOINT),
        prior_artifacts_verified=len(previous['artifacts']), intentional_supersessions=changes,
        other_job_status_reference=previous['other_job_status_reference'], other_job_totals_separate=True,
        editorial_holds=9, unknown_dates_preserved=27, review_reference=a.reference(a.REVIEW),
        remaining_research_reference=a.reference(a.RUN / 'remaining-research-001.json.gz'),
        next_museum_pass_reference=a.reference(a.RUN / 'next-museum-pass-001.json'),
        preserved_source_access_hold_reference=previous['new_source_access_hold_reference'],
        runtime=runtime,
        next_work='233 existing holdings verified:136 Laing,97 National Army Museum;0 new artworks. Laing138 linked/111 eligible,27 unknown dates preserved;National Army106/106. Nine unresolved attribution/version cases remain pending. Campaign10259 new+1173 reconciled=11432 distinct protected records. Continue with Cardiff, Bristol and Museo Nazionale della Scienza e della Tecnologia Leonardo da Vinci, subject to fresh saved-object, authority and duplicate/version review. Previous225 underfilled Italian museum queue,6 Verbania holds,352 earlier Italian notices and515 unapproved source leads preserved. All access holds persist, including Art UK403,three ArCo connect timeouts,regional TLS failure and Musei Reali403. Do not restart failed request loops. Use the dedicated persistent runtime. Concrete233-link progress; no repeated global blocking condition. The all-museum100 minimum/200 preferred goal remains active.')
    m.save(dest, result)
    print(json.dumps(dict(checkpoint=str(dest.relative_to(m.ROOT)), sha256=sha(dest),
                          artifacts=len(artifacts), external_artifacts=len(unique), new=0,
                          existing_links=233, campaign_new=10259, campaign_links=1173,
                          below100=result['museums_below_100'])), flush=True)


if __name__ == '__main__':
    main()
