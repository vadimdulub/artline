"""Document wave78 and retain every unresolved museum research queue."""
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
    report = m.load(m.RUN / 'verification-after-wave-78.json')
    assert report['verified_new_artworks'] == 10259
    assert report['verified_existing_artworks_linked'] == 1173
    assert report['institutions_with_new_records_or_reconciled_holdings'] == 217
    plan, digest = a.validate_plan()
    with m.connect() as db:
        a.verify(db, plan, digest)

    cp = m.load(a.CHECKPOINT)
    root = m.RUN / 'README.md'
    pin = next(v for v in cp['artifacts'] if v['path'] == str(root.relative_to(m.ROOT)))
    assert sha(root) == pin['sha256']
    backup = m.BACKUP / 'britain-two-root-readme-before-001.json.gz'
    outputs = ['checks-001.json', 'remaining-research-001.json.gz',
               'next-museum-pass-001.json', 'README.md', 'readme-supersessions-001.json']
    assert not backup.exists()
    assert all(not (a.RUN / name).exists() for name in outputs)

    rootlogs = Path('/Users/vadimdulub/Library/Logs')
    test = (rootlogs / 'artline-britain-two-tests-20261009.log').read_text()
    assert 'Ran 16 tests' in test and test.rstrip().endswith('OK')
    assert (rootlogs / 'artline-britain-two-replay-20261009.log').read_text().strip() == 'Unchanged replay: zero writes'
    logs = {p.name: dict(path=str(p), sha256=sha(p))
            for day in ['20261008', '20261009']
            for p in sorted(rootlogs.glob('artline-britain-two-*-' + day + '.log'))
            if 'delivery' not in p.name and 'checkpoint' not in p.name}
    decisions = m.load(a.REVIEW)['decisions']
    held = [v for v in decisions if v['state'] == 'editorial_hold']
    assert len(decisions) == 242 and len(held) == 9
    assert {v['number'] for v in held} == {23, 33, 71, 104, 121, 176, 178, 185, 207}
    assert cp['cumulative_verified_tests'] == 1484
    m.save(a.RUN / 'checks-001.json', dict(
        at=m.now(), new_offline_tests_passed=16, historical_tests_passed=1484,
        cumulative_verified_tests=1500, historical_tests_rerun=False,
        replay_zero_writes=True, source_objects_reviewed=242, new_artworks=0,
        existing_links=233, editorial_holds=9, unknown_dates_preserved=27,
        logs=logs, other_job_totals_separate=True,
        environment_recovery_reference=a.reference(a.RUN / 'environment-recovery-001.json'),
        reporting_correction_reference=a.reference(a.RUN / 'report-correction-001.json'),
        parser_correction='Before candidate facts were saved, the reference parser was corrected to accept an exact Art UK P854 URL as well as P1679. The initial failed parser log is retained.'))

    m.save(a.RUN / 'remaining-research-001.json.gz', dict(
        at=m.now(), rows=held, review_reference=a.reference(a.REVIEW),
        previous_remaining_research_reference=a.reference(a.prior.RUN / 'remaining-research-001.json.gz'),
        previous_source_access_hold_reference=cp['new_source_access_hold_reference'],
        policy='Nine attribution/version comparisons remain pending. Preserve the previous six Verbania holds, 352 earlier Italian notices and 515 selected Pavia/Poldi/Sabauda source leads via the linked prior queue. All source access holds remain in place, including Art UK 403, three ArCo connection timeouts, the regional TLS failure and Musei Reali 403. No unknown date is inferred; no quota-based approval.'))

    previous_queue_ref = cp['next_museum_pass_reference']
    previous_queue = m.load(a.checked(previous_queue_ref))
    live = m.load(m.RUN / 'after-wave-78.json')
    by_id = {v['id']: v for v in live['institutions']}
    next_italian = [dict(v, current_linked=by_id[v['institution_id']]['works'],
                         current_eligible=by_id[v['institution_id']]['eligible_works'])
                    for v in previous_queue['italian_museums']]
    assert len(next_italian) == 225
    target_ids = ['bbde7b48-7080-46aa-9933-19c42c1fa28e',
                  '6aaf0c6c-88e1-53f2-8455-9f894164db88',
                  '07cb8446-a063-416d-9f23-bb2280532f6e']
    targets = [by_id[iid] for iid in target_ids]
    assert all(v['works'] < 100 and v['pending_associations'] > 0
               and not v['canonical_institution_id'] for v in targets)
    pending_queue = sorted(
        [v for v in live['institutions'] if v['kind'] == 'museum'
         and v['status'] != 'archived' and not v['canonical_institution_id']
         and v['works'] < 100 and v['pending_associations'] > 0],
        key=lambda v: (-v['pending_associations'], v['name']))
    m.save(a.RUN / 'next-museum-pass-001.json', dict(
        at=m.now(), previous_queue_reference=previous_queue_ref,
        coverage_reference=a.reference(m.RUN / 'after-wave-78.json'),
        italian_museums=next_italian, existing_holding_review_targets=targets,
        underfilled_museums_with_pending_associations=pending_queue,
        remaining_research_reference=a.reference(a.RUN / 'remaining-research-001.json.gz'),
        policy='Next candidates: Cardiff, Bristol and Museo Nazionale della Scienza e della Tecnologia Leonardo da Vinci. Review saved object evidence and exact collection authority, chronology, creator qualifications and duplicate/version identity before any link. These are unreviewed targets, not approved facts. Preserve all previous access holds; do not restart failed requests or bypass restrictions. Continue toward 100 minimum and 200 preferred with no quota-based approval.',
        database_writes=0))

    text = '''# Laing Art Gallery and National Army Museum — 9 October 2026

Accepted **233 museum-holding links for existing local artwork records** after reviewing all 242 pending associations at the two museums. **No new artwork records were created.** Both museums now exceed 100 works with eligible creation dates; the preferred 200 remains unfinished.

| Museum | Links accepted | Linked before → after | Eligible dates before → after |
| --- | ---: | ---: | ---: |
| Laing Art Gallery | 136 | 2 → 138 | 2 → 111 |
| National Army Museum | 97 | 9 → 106 | 9 → 106 |

Laing retains 27 accepted records with unknown dates; they count as linked catalogue works, but are not counted as dated eligible works. Nine cases remain pending because of unresolved attribution or physical-version identity. Existing review statuses, creator labels, dates, titles and images are preserved.

The source review used exact Wikidata object identifiers, collection and location claims, inventory qualifiers, creator identities, titles and source chronology from 146 hash-verified original response bodies. These saved secondary records were captured on 4 October, not freshly confirmed by Art UK. The prior Art UK 403 access hold remains in place. Correlated references are not treated as independent confirmation. Fifteen unlinked creator labels were checked against ten freshly retrieved authority entities, without creating painter links.

Seven native pages were captured: six National Army Museum object pages and Laing's collection overview. These support only the specific facts recorded in each [editorial decision](editorial-reviewed-001.json.gz). They do not provide native confirmation of every accepted link. The review distinguishes a later copy's creation date from the date of its subject or prototype, and retains qualified attributions. A native attribution to John Graham remains held because the existing unqualified creator link needs separate correction. The accepted decisions record at least 80% editorial confidence, not calibrated probabilities. Holdings do not establish ownership or current display. No images were downloaded or attached.

Fresh identity comparison covered 36,824 existing artworks and 75,933 citations. Additional comparison context contains 58 saved source entities from 51 response bodies, with source dimensions, inventory and version evidence retained. The [transaction plan](britain-two-existing-holdings-001-plan-001.json.gz) and [application receipt](britain-two-existing-holdings-001-applied.json) record 233 new citations, 233 accepted holding assertions and 233 superseded pending assertions. All previous evidence remains intact. Only the artwork museum projection and update timestamp changed. Exact readback protected 2,188 target/comparison records and 11,199 prior campaign records. Sixteen offline guard tests and a zero-write replay passed. No commits or deployment.

The [remaining research](remaining-research-001.json.gz) retains all nine decisions and references the previous six Verbania holds, 352 earlier Italian notices and 515 unapproved Pavia/Poldi/Sabauda source leads. The [next-museum queue](next-museum-pass-001.json) preserves 225 underfilled Italian museums and identifies Cardiff, Bristol and Museo Nazionale della Scienza e della Tecnologia Leonardo da Vinci as candidates for fresh review. Prior source-access holds remain in force.

Campaign totals: **10,259 new artworks plus 1,173 reconciled existing holdings across 217 institutions**, covering 11,432 distinct artwork records. **1,244 canonical museums remain below 100 linked works**, and 1,389 remain below 200. These are catalogue coverage measures, not claims about the museums' actual collection sizes. The all-museum goal remains active. Backups are in the designated Application Support directory. The next pass must protect all 11,432 campaign records.
'''
    (a.RUN / 'README.md').write_text(text)
    before = root.read_text()
    split = before.index('\n## Added works')
    intro = (before[:split].replace('940 existing', '1,173 existing')
             .replace('expand 215 institutions', 'expand 217 institutions')
             .replace('1,246', '1,244').replace('after-wave-77', 'after-wave-78')
             .replace('Detroit, Princeton and Verbania passes',
                      'Detroit, Princeton, Verbania, Laing and National Army Museum passes'))
    assert '940 existing' not in intro and 'after-wave-77' not in intro
    contents = intro + before[split:] + '''

## Laing and National Army Museum holding reconciliation

The [two-museum review](native/britain-two-holdings-20261008/README.md) accepted **233 existing-artwork museum links** after reviewing all 242 pending associations. Laing now has **138 linked works / 111 with eligible dates**; the National Army Museum has **106 / 106**. Nine attribution/version cases remain pending and 27 unknown dates are preserved. No artwork metadata, images or historical statuses changed.

The [wave78 verification](verification-after-wave-78.json) records **10,259 additions and 1,173 holding reconciliations across 217 institutions**. There are **1,244 canonical museums below 100 linked works**. The all-museum goal remains active.
'''
    oldhash = sha(root)
    m.save(backup, dict(at=m.now(), path=str(root.relative_to(m.ROOT)),
                        sha256=oldhash, text=before))
    root.write_text(contents)
    m.save(a.RUN / 'readme-supersessions-001.json', dict(at=m.now(), changes=[dict(
        path=str(root.relative_to(m.ROOT)), before_sha256=oldhash,
        after_sha256=sha(root), backup_path=str(backup), backup_sha256=sha(backup))]))
    print(json.dumps(dict(documented_existing_links=233, campaign_new=10259,
                          campaign_links=1173, institutions=217,
                          remaining_below100=1244, next_italian_museums=len(next_italian),
                          next_existing_holding_targets=[v['name'] for v in targets])), flush=True)


if __name__ == '__main__':
    main()
