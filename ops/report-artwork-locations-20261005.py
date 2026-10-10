#!/usr/bin/env python3
"""Read-only cumulative audit and exports after both-catalogue delivery.

Combines overlapping review and accepted claims, and the separate local and
production final waves. Verifies actual rows, not just transaction receipts.
"""
import collections
import csv
import gzip
import importlib.util
import json
from pathlib import Path
import shutil

s = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('apply-artwork-locations-20261004.py'))
d = importlib.util.module_from_spec(s)
s.loader.exec_module(d)
r = d.r
s = importlib.util.spec_from_file_location('concurrent_images', Path(__file__).with_name('audit-artwork-location-concurrent-images-20261005d.py'))
concurrent_images = importlib.util.module_from_spec(s)
s.loader.exec_module(concurrent_images)
HOLDING_WAVES = ['primary-02', 'walters-01', 'france-03', 'followup-01', 'walters-02', 'curated-01', 'final-local-01', 'final-production-01', 'authority-review-01', 'deposit-review-01', 'continuation-primary-01', 'russian-followup-01', 'tate-review-01', 'lenbach-01', 'france-alias-01', 'vam-01', 'rijks-02', 'marseille-01', 'rijks-03', 'americas-02', 'arco-01', 'smk-02', 'smk-03', 'aberdeen-01', 'ycba-01', 'aberdeen-02']
PUBLICATION_PASS_WAVES = ['arco-02', 'whistler-01', 'hunterian-01', 'kandinsky-books-01', 'met-01', 'louvre-01', 'france-allocation-01', 'iwm-01', 'date-notation-01', 'municipal-01', 'native-museums-01', 'undated-identities-01', 'russian-title-01', 'mds-01']
PUBLICATION_PASS_WAVES += ['mds-undated-01']
MAJOR_MUSEUM_PASS_WAVES = ['major-prado-louvre-01', 'major-deposit-01', 'major-titles-ng-01', 'major-french-identities-01', 'major-date-review-01', 'major-prado-rijks-01']
PUBLICATION_PASS_WAVES += MAJOR_MUSEUM_PASS_WAVES
HOLDING_WAVES += PUBLICATION_PASS_WAVES
DISPLAY_WAVES = ['dated-display-02', 'dated-display-03', 'dated-display-04']
LEAD_WAVES = ['location-leads-review-01', 'location-leads-review-02', 'location-leads-review-03', 'location-leads-review-04']


def csv_output(path, rows, fields):
    assert not path.exists()
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fields, extrasaction='raise')
        writer.writeheader()
        writer.writerows(rows)


def main():
    at = r.now()
    dest = r.RUN / ('report-' + at.replace('-', '').replace(':', ''))
    dest.mkdir()
    concurrent_media, concurrent_media_evidence = concurrent_images.load(r)
    r.save(dest / 'concurrent-image-changes-audit.json', concurrent_media_evidence)
    original = {v['artwork']['id']: v for v in r.load(r.RUN / 'missing-locations.json.gz')}
    combined, source_receipts, wave_stats = {}, {}, []
    expected = {t: collections.defaultdict(dict) for t in ['local', 'production']}
    earliest = {t: {} for t in expected}
    accepted = {t: {} for t in expected}
    citation_expectations = {t: {} for t in expected}
    outcomes, paths = collections.defaultdict(set), collections.defaultdict(set)
    candidate_names, candidate_urls = collections.defaultdict(set), collections.defaultdict(set)

    def evidence(value):
        if isinstance(value, dict):
            if {'body_path', 'sha256', 'url'} <= value.keys():
                prev = source_receipts.setdefault(value['body_path'], value)
                assert prev['sha256'] == value['sha256']
            for v in value.values():
                evidence(v)
        elif isinstance(value, list):
            for v in value:
                evidence(v)

    for wave in HOLDING_WAVES:
        data, digest = d.pinned(wave)
        folder = r.RUN / 'delivery' / wave
        verified = {}
        for path in folder.glob('verification*.json'):
            verification = r.load(path)
            assert verification['plan_sha256'] == digest and not verification.get('errors')
            verified.update(verification['targets'])
        targets = data.get('targets', ['local', 'production'])
        # The original local-only final plan predates explicit target metadata.
        if wave == 'final-local-01':
            targets = ['local']
        for target in targets:
            assert verified.get(target) == len(data['claims']), (wave, target, 'not verified')
            receipts = set()
            for path in (folder / target).glob('*.json'):
                receipt = r.load(path)
                assert receipt['plan_sha256'] == digest
                assert not receipts.intersection(receipt['artwork_ids'])
                receipts.update(receipt['artwork_ids'])
            assert receipts == {c['target_ids'][target] for c in data['claims']}
            before = r.load(data['preimages'][target]['path'])
            for aid, old in before.items():
                earliest[target].setdefault(aid, old)
        wave_stats.append({'wave': wave, 'claims': len(data['claims']), 'verified_targets': targets, 'by_review_state': dict(collections.Counter(c.get('review_state', 'accepted') for c in data['claims']))})
        for c in data['claims']:
            aid = c['artwork_id']
            state = c.get('review_state', 'accepted')
            key = (aid, c['provider'], c['source_url'], state)
            old = original[aid]
            row = combined.setdefault(key, {'local_artwork_id': aid, 'production_artwork_id': None, 'slug': old['artwork']['slug'], 'title': old['artwork']['title'], 'creators': '; '.join(v['name'] for v in old['artists']) or old['artwork'].get('unlinked_creator_label'), 'museum': c['institution']['name'], 'location_text': c['location_text'], 'claim_type': 'holding', 'review_state': state, 'source_url': c['source_url'], 'checked_at': c['checked_at'], 'identity_basis': c['identity_basis'], 'limitation': c['limitation'], 'source_body_sha256': c['source_receipt']['sha256'], 'source_body_path': c['source_receipt']['body_path'], 'provider': c['provider'], 'local_wave': None, 'production_wave': None, 'local_delivery': None, 'production_delivery': None})
            for target in targets:
                tid, inst = c['target_ids'][target], c['target_institutions'][target]
                assert row[target + '_delivery'] is None, ('Repeated actual assertion', key, target)
                row[target + '_delivery'] = 'committed_and_verified'
                row[target + '_wave'] = wave
                if target == 'production':
                    row['production_artwork_id'] = tid
                expected[target][tid][d.uid(wave + '/holding/' + tid)] = {'claim_type': 'holding', 'institution_id': inst['id'], 'review_state': state, 'source_url': c['source_url'], 'display_state': None}
                citation_expectations[target][d.uid(wave + '/citation/' + tid)] = {'entity_id': tid, 'field_name': 'museum_holding_research', 'source_url': c['source_url']}
                if state == 'accepted':
                    assert tid not in accepted[target]
                    accepted[target][tid] = {'institution_id': inst['id'], 'location_text': c['location_text']}
            evidence(c)
        for hold in data['held']:
            aid = hold['artwork_id']
            outcomes[aid].add('preflight:' + hold['reason'])
            paths[aid].add(str((folder / 'plan.json.gz').relative_to(r.ROOT)))
    for row in combined.values():
        assert row['local_delivery'] == row['production_delivery'] == 'committed_and_verified'

    display_rows = []
    for wave in DISPLAY_WAVES:
        folder = r.RUN / 'delivery' / wave
        data = r.load(folder / 'plan.json.gz')
        digest = r.sha((folder / 'plan.json.gz').read_bytes())
        assert digest == r.load(folder / 'pin.json')['sha256']
        verification = r.load(folder / 'verification.json')
        assert verification['plan_sha256'] == digest
        for target, records in data['targets'].items():
            assert verification['targets'][target] == len(records)
            for c in records:
                aid = c['artwork_id']
                earliest[target].setdefault(aid, c['before'])
                expected[target][aid][d.uid(wave + '/' + aid)] = {'claim_type': 'display', 'institution_id': c['institution']['id'], 'review_state': 'accepted', 'source_url': c['source_url'], 'display_state': c['display_state']}
                citation_expectations[target][d.uid(wave + '/citation/' + aid)] = {'entity_id': aid, 'field_name': 'dated_display_location', 'source_url': c['source_url']}
                evidence(c['source_receipt'])
                if target == 'local':
                    display_rows.append({'artwork_id': aid, 'title': c['before']['artwork']['title'], 'observed_institution': c['institution']['name'], 'venue': (c.get('venue') or {}).get('name'), 'display_state': c['display_state'], 'source_url': c['source_url'], 'checked_at': c['source_receipt']['retrieved_at'], 'source_updated_at': c['source_updated_at'], 'note': c['note'], 'local_delivery': 'committed_and_verified', 'production_delivery': 'committed_and_verified'})

    lead_rows = []
    for wave in LEAD_WAVES:
        lead_path = r.RUN / 'delivery' / wave / 'plan.json.gz'
        leads = r.load(lead_path)
        lead_digest = r.sha(lead_path.read_bytes())
        assert lead_digest == r.load(lead_path.with_name('plan-pin.json'))['sha256']
        lead_verification = r.load(lead_path.with_name('verification.json'))
        assert lead_verification['plan_sha256'] == lead_digest
        for target, info in leads['preimages'].items():
            assert r.sha(Path(info['path']).read_bytes()) == info['sha256']
            for tid, before in r.load(info['path']).items():
                earliest[target].setdefault(tid, before)
                expected[target].setdefault(tid, {})
        for aid, reason in leads.get('held', {}).items():
            outcomes[aid].add('review_citation_preflight:' + reason)
            paths[aid].add(str(lead_path.relative_to(r.ROOT)))
        for v in leads['leads']:
            aid = v['artwork_id']
            old = original[aid]
            outcomes[aid].add('review_citation:' + v['provider'])
            paths[aid].add(str(lead_path.relative_to(r.ROOT)))
            candidate_names[aid].add(v['reported_location'])
            candidate_urls[aid].add(v['source_url'])
            for target, tid in v['target_ids'].items():
                assert lead_verification['targets'][target] == len(leads['leads'])
                citation_expectations[target][d.uid(wave + '/citation/' + tid + '/' + v['source_url'])] = {'entity_id': tid, 'field_name': 'museum_location_lead_review', 'source_url': v['source_url']}
            evidence(v)
            lead_rows.append({'local_artwork_id': aid, 'production_artwork_id': v['target_ids']['production'], 'slug': old['artwork']['slug'], 'title': old['artwork']['title'], 'reported_location': v['reported_location'], 'review_state': 'review', 'source_url': v['source_url'], 'checked_at': v['source_receipt']['retrieved_at'], 'provider': v['provider'], 'limitation': v['limitation'], 'local_delivery': 'committed_and_verified', 'production_delivery': 'committed_and_verified'})

    # Audit final state against the earliest preimage, allowing the exact union
    # of this research's changes, including review followed by acceptance.
    totals, remaining_by_target, concurrent_additions = {}, {}, {}
    for target in expected:
        with r.connect(target) as db:
            ids = sorted(expected[target])
            for offset in range(0, len(ids), 500):
                group = ids[offset:offset+500]
                after = d.snapshots(db, group)
                assert len(after) == len(group)
                for aid, new in after.items():
                    old = earliest[target][aid]
                    allowed = {'current_institution_id', 'current_location_text', 'current_location_unknown_reason', 'location_checked_at', 'revision', 'updated_at', 'updated_by'} if aid in accepted[target] else set()
                    image_change = concurrent_media[target].get(aid)
                    extra_revision = 0
                    if image_change and old['artwork']['primary_media_id'] != new['artwork']['primary_media_id']:
                        assert old['artwork']['primary_media_id'] is None and new['artwork']['primary_media_id'] == image_change['primary_media_id']
                        allowed |= {'primary_media_id', 'revision', 'updated_at', 'updated_by'}
                        extra_revision = 1
                    assert {k:v for k,v in old['artwork'].items() if k not in allowed} == {k:v for k,v in new['artwork'].items() if k not in allowed}, (target, aid, 'artwork changed')
                    for k in ['identifiers', 'creators', 'creator_keys', 'media']:
                        if k == 'media' and extra_revision:
                            assert new[k] == image_change['attachments']
                            assert all(v in new[k] for v in old[k]) and len(new[k]) == len(old[k]) + 1
                            continue
                        assert old[k] == new[k], (target, aid, k)
                    assertions = {v['id']: v for v in new['assertions']}
                    prior_ids = {v['id'] for v in old['assertions']}
                    assert assertions.keys() - prior_ids == expected[target][aid].keys(), (target, aid, 'unexpected assertion')
                    assert all(assertions[v['id']] == v for v in old['assertions'])
                    for assertion_id, fields in expected[target][aid].items():
                        assert all(assertions[assertion_id][k] == val for k,val in fields.items())
                    if aid in accepted[target]:
                        assert new['artwork']['current_institution_id'] == accepted[target][aid]['institution_id']
                        assert new['artwork']['current_location_text'] == accepted[target][aid]['location_text']
                        assert new['artwork']['revision'] == old['artwork']['revision'] + 1 + extra_revision
                    elif extra_revision:
                        assert new['artwork']['revision'] == old['artwork']['revision'] + extra_revision
                if offset % 5000 == 0:
                    print('Cumulative catalogue audit', target, min(offset+500, len(ids)), '/', len(ids), flush=True)
            cids = sorted(citation_expectations[target])
            for offset in range(0, len(cids), 500):
                group = cids[offset:offset+500]
                found = db.execute("SELECT id::text,entity_id::text,entity_type,field_name,source_url FROM citations WHERE id=ANY(%s::uuid[])", (group,)).fetchall()
                assert len(found) == len(group)
                assert all(v['entity_type'] == 'artwork' and all(v[k] == val for k,val in citation_expectations[target][v['id']].items()) for v in found)
            totals[target] = db.execute('SELECT status,count(*) artworks,count(current_institution_id) with_institution FROM artworks GROUP BY status ORDER BY status').fetchall()
            remaining_by_target[target] = db.execute("SELECT count(*) n FROM artworks WHERE status<>'archived' AND current_institution_id IS NULL").fetchone()['n']
            baseline_record = r.load(r.RUN / (target + '-baseline.json'))
            baseline = baseline_record['totals']
            # Another authorized catalogue import can add records while this
            # research runs. Account for those observed rows separately; all
            # original rows and this research's exact mutations remain audited.
            added = db.execute('SELECT id::text,slug,title,status,current_institution_id::text,created_at,created_by FROM artworks WHERE created_at>%s::timestamptz ORDER BY id', (baseline_record['at'],)).fetchall()
            assert not set(v['id'] for v in added).intersection(expected[target]), (target, 'research must not create artwork records')
            concurrent_additions[target] = added
            added_counts = collections.Counter(v['status'] for v in added)
            assert {v['status']: v['artworks'] - added_counts[v['status']] for v in totals[target]} == {v['status']: v['artworks'] for v in baseline}
            assert sum(v['with_institution'] for v in totals[target]) - sum(v['with_institution'] for v in baseline) - sum(v['current_institution_id'] is not None for v in added) == len(accepted[target])
            if target == 'local':
                with (dest / 'catalogue-location-coverage-after.csv').open('wb') as f:
                    with db.cursor().copy("COPY (SELECT a.id,a.slug,a.title,a.status,a.current_institution_id,i.name institution,a.current_location_text,a.current_location_unknown_reason,a.location_checked_at FROM artworks a LEFT JOIN institutions i ON i.id=a.current_institution_id WHERE a.status<>'archived' ORDER BY a.id) TO STDOUT WITH CSV HEADER") as cp:
                        for chunk in cp:
                            f.write(chunk)
    with (dest / 'catalogue-location-coverage-after.csv').open(newline='') as f:
        current = {v['id']: v for v in csv.DictReader(f)}
    with (r.RUN / 'catalogue-location-coverage.csv').open(newline='') as f:
        before = {v['id']: v for v in csv.DictReader(f)}
    assert before.keys() <= current.keys()
    assert current.keys() - before.keys() == {v['id'] for v in concurrent_additions['local'] if v['status'] != 'archived'}
    r.save(dest / 'concurrent-catalogue-additions.json', concurrent_additions)
    for aid, old in before.items():
        assert all(current[aid][k] == old[k] for k in ['id', 'slug', 'title', 'status'])
        if aid not in accepted['local']:
            assert current[aid] == old, ('Unrelated location changed', aid)

    for path in sorted((r.RUN / 'primary-plans').glob('*.json.gz')):
        data = r.load(path)
        for c in data.get('claims', []):
            aid = c['artwork_id']
            outcomes[aid].add(path.stem + ':candidate_' + c.get('review_state', 'accepted'))
            paths[aid].add(str(path.relative_to(r.ROOT)))
            candidate_names[aid].add(c['institution']['name'])
            candidate_urls[aid].add(c['source_url'])
        for h in data.get('holds', []):
            aid = h.get('artwork_id')
            if aid in original:
                outcomes[aid].add(path.stem + ':' + h['reason'])
                paths[aid].add(str(path.relative_to(r.ROOT)))
    latest = {p.name: p for p in (r.RUN / 'wikiart-leads').glob('*.json')}
    latest.update({p.name:p for p in (r.RUN / 'wikiart-leads-retry-20261005').glob('*.json')})
    wiki_counts = collections.Counter()
    for path in latest.values():
        lead = r.load(path)
        aid = lead['artwork_id']
        wiki_counts[lead['outcome']] += 1
        outcomes[aid].add('wikiart:' + lead['outcome'])
        paths[aid].add(str(path.relative_to(r.ROOT)))
        if lead.get('fields', {}).get('Location'):
            candidate_names[aid].add(lead['fields']['Location'])
            candidate_urls[aid].add(lead['source_url'])

    accepted_rows = sorted((v for v in combined.values() if v['review_state'] == 'accepted'), key=lambda v:v['local_artwork_id'])
    review_rows = sorted((v for v in combined.values() if v['review_state'] == 'review'), key=lambda v:(v['local_artwork_id'], v['provider']))
    csv_output(dest / 'supported-museum-links.csv', accepted_rows, list(accepted_rows[0]))
    csv_output(dest / 'museum-holding-candidates-review.csv', review_rows, list(review_rows[0]))
    csv_output(dest / 'location-evidence-citations-review.csv', lead_rows, list(lead_rows[0]))
    csv_output(dest / 'dated-display-observations.csv', display_rows, list(display_rows[0]))
    review_ids = {v['local_artwork_id'] for v in review_rows}
    lead_ids = {v['local_artwork_id'] for v in lead_rows}
    ledger, counts = [], collections.Counter()
    for aid, old in sorted(original.items()):
        if aid in accepted['local']:
            state = 'accepted_museum_holding'
        elif aid in review_ids:
            state = 'museum_holding_candidate_in_review'
        elif aid in lead_ids:
            state = 'location_evidence_citation_in_review'
        elif outcomes[aid]:
            state = 'researched_candidate_unresolved'
        else:
            state = 'not_researched_this_pass'
        counts[state] += 1
        ledger.append({'artwork_id': aid, 'slug': old['artwork']['slug'], 'title': old['artwork']['title'], 'creators': '; '.join(v['name'] for v in old['artists']) or old['artwork'].get('unlinked_creator_label'), 'publication_status': current[aid]['status'], 'research_status': state, 'current_local_museum': current[aid]['institution'], 'candidate_museums_not_current_location_proof': ' | '.join(sorted(candidate_names[aid])), 'candidate_source_urls': ' | '.join(sorted(candidate_urls[aid])), 'research_outcomes': ' | '.join(sorted(outcomes[aid])), 'evidence_paths': ' | '.join(sorted(paths[aid])), 'local_delivery': 'committed_and_verified' if aid in accepted['local'] or aid in review_ids or aid in lead_ids else 'no_new_evidence', 'production_delivery': 'committed_and_verified' if aid in accepted['local'] or aid in review_ids or aid in lead_ids else 'no_new_evidence'})
    csv_output(dest / 'research-ledger.csv', ledger, list(ledger[0]))
    unresolved = [v for v in ledger if not current[v['artwork_id']]['current_institution_id']]
    csv_output(dest / 'unresolved-artworks.csv', unresolved, list(ledger[0]))
    bytes_verified = 0
    for path, receipt in source_receipts.items():
        raw = gzip.decompress((r.ROOT / path).read_bytes())
        assert r.sha(raw) == receipt['sha256'], path
        bytes_verified += len(raw)
    r.save(dest / 'source-integrity.json', {'at': r.now(), 'distinct_response_bodies_verified': len(source_receipts), 'uncompressed_bytes_verified': bytes_verified, 'all_sha256_match': True, 'scope': 'Every response receipt in the delivered holding, display and review-citation evidence, including nested identity and institution sources.'})
    summary = {'generated_at': at, 'status': 'all_prepared_research_delivered_and_verified_locally_and_in_production; whole_catalogue_research_incomplete', 'new_accepted_holdings_per_database': len(accepted_rows), 'new_review_holding_assertions_per_database': len(review_rows), 'new_review_location_citations_per_database': len(lead_rows), 'new_dated_display_observations_per_database': len(display_rows), 'catalogue_totals': totals, 'remaining_missing_museum_local': len(unresolved), 'research_ledger_counts': dict(counts), 'wikiart_final_outcomes': dict(wiki_counts), 'waves': wave_stats, 'all_original_active_local_ids_titles_slugs_and_statuses_preserved': True, 'all_touched_artwork_dates_creators_images_and_prior_assertions_preserved': True, 'all_planned_citations_verified_in_both_databases': True, 'production_pending_records': 0, 'backups': r.load(r.RUN / 'backups.json'), 'limitations': ['Museum holding associations do not establish current physical location or public display. Only the dated display observations record explicit display evidence.', 'Not every catalogue artwork has been individually researched. Previously assigned museum links were inventoried, not all freshly reverified. The ledger distinguishes unresolved and unresearched original gaps.', 'Duplicate identities, conflicting metadata, loans, deposits, inaccessible sources and secondary-source location text remain in review or unresolved. No artwork publication status was changed.', 'WikiArt initially encountered a temporary DNS outage; failed requests were retried and the original evidence retained.', 'Wall-clock interruptions occurred. No claim of continuous active research duration is made.', 'Existing scoped 500-object query plans in report-20261005T042037Z measure the real catalogue. No test fixtures were inserted. Performance at 10 million artworks still requires separate representative load testing.']}
    summary['review_citation_preflight_held'] = leads.get('held', {})
    summary['code_checks'] = r.load(r.RUN / 'major-museums-final-code-checks-v2-20261005d.json')
    summary['concurrent_image_attachments'] = {'operation': concurrent_media_evidence['operation'], 'plan_sha256': concurrent_media_evidence['plan_sha256'], 'artworks_per_database': 19, 'exact_database_audit_and_external_backup_verified': True, 'scope': 'Separate existing-image attachment operation. Its exact primary-media changes and added revisions are accounted for, not attributed to museum-link research. No edits were reverted.'}
    summary['limitations'][2] = 'Unreconciled duplicate identities, attribution or custody conflicts, inaccessible sources and unsupported secondary location text remain in review. Documented deposits and loans are holdings without ownership or display claims. No artwork publication status was changed.'
    added_missing = {target: sum(v['status'] != 'archived' and v['current_institution_id'] is None for v in rows) for target, rows in concurrent_additions.items()}
    assert remaining_by_target['local'] == len(unresolved) + added_missing['local']
    summary['remaining_missing_museum_original_local_catalogue'] = len(unresolved)
    summary['remaining_missing_museum_local'] = remaining_by_target['local']
    summary['remaining_missing_museum_production'] = remaining_by_target['production']
    summary['concurrent_catalogue_additions'] = {target: {'artworks': len(rows), 'without_accepted_museum': added_missing[target], 'created_by': dict(collections.Counter(v['created_by'] for v in rows))} for target, rows in concurrent_additions.items()}
    continuation_waves = set(HOLDING_WAVES[HOLDING_WAVES.index('france-alias-01'):])
    continuation_ids = {v['local_artwork_id'] for v in accepted_rows if v['local_wave'] in continuation_waves}
    continuation_baseline = {v['artwork']['id'] for v in r.load(r.RUN / 'remaining-snapshot-20261005b.json.gz')}
    assert len(continuation_baseline) == 85488
    assert continuation_ids <= continuation_baseline
    assert len(continuation_baseline) - len(continuation_ids) == len(unresolved)
    summary['continuation_from_85488'] = {
        'baseline_missing_accepted_museum_local': len(continuation_baseline),
        'additional_accepted_museum_links_per_database': len(continuation_ids),
        'additional_review_holding_assertions_per_database': sum(v['local_wave'] in continuation_waves for v in review_rows),
        'additional_review_location_citations_per_database': sum(len(r.load(r.RUN / 'delivery' / wave / 'plan.json.gz')['leads']) for wave in LEAD_WAVES[1:]),
        'remaining_missing_accepted_museum_local': len(unresolved),
        'new_display_assertions': 0,
        'all_prepared_updates_committed_and_verified_in_both_databases': True,
    }
    pass_baseline = set(r.load(r.RUN / 'publication-pass-baseline-20261005c.json')['ids'])
    pass_rows = [v for v in accepted_rows if v['local_wave'] in PUBLICATION_PASS_WAVES]
    pass_ids = {v['local_artwork_id'] for v in pass_rows}
    assert len(pass_baseline) == 51927 and pass_ids <= pass_baseline
    assert len(pass_baseline) - len(pass_ids) == len(unresolved)
    summary['continuation_from_51927'] = {
        'baseline_missing_accepted_museum_local': len(pass_baseline),
        'additional_accepted_museum_links_per_database': len(pass_ids),
        'additional_review_holding_assertions_per_database': sum(v['local_wave'] in PUBLICATION_PASS_WAVES for v in review_rows),
        'additional_review_location_citations_per_database': sum(len(r.load(r.RUN / 'delivery' / wave / 'plan.json.gz')['leads']) for wave in LEAD_WAVES[2:]),
        'remaining_missing_accepted_museum_local': len(unresolved),
        'whole_catalogue_remaining_missing_accepted_museum_local': remaining_by_target['local'],
        'concurrent_new_artworks_without_accepted_museum_local': added_missing['local'],
        'remaining_missing_accepted_museum_production': remaining_by_target['production'],
        'new_display_assertions': 0,
        'undated_works_keep_null_creation_years_and_review_publication': True,
        'all_prepared_updates_committed_and_verified_in_both_databases': True,
    }
    csv_output(dest / 'additional-museum-links-from-51927.csv', pass_rows, list(accepted_rows[0]))
    major_baseline = set(r.load(r.RUN / 'major-museums-baseline-20261005d.json')['ids'])
    major_rows = [v for v in accepted_rows if v['local_wave'] in MAJOR_MUSEUM_PASS_WAVES]
    major_ids = {v['local_artwork_id'] for v in major_rows}
    assert len(major_baseline) == 47386 and major_ids <= major_baseline
    assert all(bool(current[aid]['current_institution_id']) == (aid in major_ids) for aid in major_baseline)
    additional_missing = sum(not v['current_institution_id'] and aid not in major_baseline for aid, v in current.items())
    assert remaining_by_target['local'] == len(major_baseline) - len(major_ids) + additional_missing
    major_review_rows = [v for v in review_rows if v['local_wave'] in MAJOR_MUSEUM_PASS_WAVES]
    major_leads = r.load(r.RUN / 'delivery/location-leads-review-04/plan.json.gz')['leads']
    summary['continuation_from_47386'] = {
        'baseline_missing_accepted_museum_local': len(major_baseline),
        'additional_accepted_museum_links_per_database': len(major_ids),
        'additional_review_holding_assertions_per_database': len(major_review_rows),
        'additional_review_evidence_citations_per_database': len(major_leads),
        'accepted_by_museum': dict(collections.Counter(v['museum'] for v in major_rows)),
        'remaining_missing_accepted_museum_local': remaining_by_target['local'],
        'remaining_missing_accepted_museum_production': remaining_by_target['production'],
        'additional_unlinked_catalogue_records_since_baseline': additional_missing,
        'new_display_assertions': 0,
        'all_prepared_updates_committed_and_verified_in_both_databases': True,
        'prado_source_limitation': 'Selected facts from a 27 March 2026 Prado catalogue research dataset, corroborated with exact native object IDs, inventories, titles and creators. Direct Prado responses were inaccessible. No fresh physical-location or display verification.',
        'louvre_search_limitation': 'The later inventory-search endpoint returned an anti-bot challenge; it was not bypassed. Accepted Louvre links use the previously captured current public JSON object records.',
        'date_review_preserved': 'Exact museum identity can support a holding while uncertain or conflicting creation dates and publication stay in editorial review.'}
    csv_output(dest / 'additional-museum-links-from-47386.csv', major_rows, list(accepted_rows[0]))
    csv_output(dest / 'major-museum-review-holdings.csv', major_review_rows, list(review_rows[0]))
    major_unresolved = [current[aid] for aid in sorted(major_baseline - major_ids)]
    csv_output(dest / 'remaining-artworks-from-47386.csv', major_unresolved, list(major_unresolved[0]))
    (dest / 'major-museums-pass-summary.txt').write_text(
        'Major museum research, ' + at + '\n\n'
        + f'Starting artworks without an accepted museum link: {len(major_baseline):,}\n'
        + f'Additional accepted museum links committed and verified in each database: {len(major_ids):,}\n'
        + f'Additional review holding assertions in each database: {len(major_review_rows):,}\n'
        + f'Additional review evidence citations in each database: {len(major_leads):,}\n'
        + f"Still without an accepted museum link locally: {remaining_by_target['local']:,}\n"
        + f"Still without an accepted museum link in production: {remaining_by_target['production']:,}\n\n"
        + '\n'.join(f'{name}: {count:,}' for name, count in collections.Counter(v['museum'] for v in major_rows).most_common())
        + '\n\nSource URLs, identifiers, archived responses and individual identity decisions are preserved.\n'
        + 'Museum deposits and loans are distinguished from legal ownership. Holding links do not establish current physical presence or public display.\n'
        + 'Prado evidence includes a March 2026 secondary catalogue dataset; inaccessible live pages were not represented as fetched primary records.\n'
        + 'All original dates, titles, creators, images, publication states and prior evidence were preserved. Research remains incomplete.\n', encoding='utf-8')
    r.save(dest / 'summary.json', summary)
    pass_details = summary['continuation_from_51927']
    (dest / 'latest-pass-summary.txt').write_text(
        'Museum-link research, ' + at + '\n\n'
        + 'Starting artworks without an accepted museum link: 51,927\n'
        + f"Additional accepted museum links, committed and verified in each database: {len(pass_ids):,}\n"
        + f"Additional review holding assertions in each database: {pass_details['additional_review_holding_assertions_per_database']:,}\n"
        + f"Additional review evidence citations in each database: {pass_details['additional_review_location_citations_per_database']:,}\n"
        + f"Original 51,927 artworks still without an accepted museum link: {len(unresolved):,}\n"
        + f"Separately added catalogue records without a museum link: {added_missing['local']:,}\n"
        + f"Whole local catalogue still without an accepted museum link: {remaining_by_target['local']:,}\n"
        + f"Production artworks still without an accepted museum link: {remaining_by_target['production']:,}\n\n"
        + 'Museum books, current object catalogues and museum-supplied datasets are preserved with source URLs and response hashes.\n'
        + 'Historical book references and unresolved identities are review citations. Holding links do not confirm current physical presence or display.\n'
        + 'Undated works with exact museum identities keep their original unknown dates and review publication state.\n'
        + 'Artwork publication states, dates, creators, images and prior evidence were preserved. Research remains incomplete.\n', encoding='utf-8')
    details = summary['continuation_from_85488']
    (dest / 'continuation-summary.txt').write_text(
        'Museum-link research continuation, ' + at + '\n\n'
        + 'Starting artworks without an accepted museum link: 85,488\n'
        + f"Additional accepted museum links, committed and verified in each database: {len(continuation_ids):,}\n"
        + f"Additional review holding assertions in each database: {details['additional_review_holding_assertions_per_database']:,}\n"
        + f"Additional review evidence citations in each database: {details['additional_review_location_citations_per_database']:,}\n"
        + f"Original researched catalogue still without an accepted museum link: {len(unresolved):,}\n"
        + f"Whole local catalogue including concurrent additions still without an accepted museum link: {remaining_by_target['local']:,}\n\n"
        + 'Sources and object identities are included in the CSV exports and preserved response receipts.\n'
        + 'Holding links document museum collection associations, not confirmed current physical presence or display.\n'
        + 'Artwork publication states, dates, creators, images and prior evidence were preserved.\n'
        + 'Research remains incomplete; unresolved and unresearched records are listed individually.\n', encoding='utf-8')
    archive = r.BACKUP / dest.name / 'scripts'
    archive.mkdir(parents=True)
    manifest = []
    for path in sorted(set(r.ROOT.joinpath('ops').glob('*artwork*2026100[45]*.py'))):
        shutil.copy2(path, archive / path.name)
        manifest.append({'path': str(path.relative_to(r.ROOT)), 'sha256': r.sha(path.read_bytes()), 'backup_path': str(archive / path.name)})
    r.save(dest / 'script-manifest.json', manifest)
    r.save(dest / 'report-files.json', [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': r.sha(p.read_bytes())} for p in sorted(dest.iterdir()) if p.is_file()])
    print(json.dumps({'report': str(dest), 'accepted': len(accepted_rows), 'review_holdings': len(review_rows), 'review_citations': len(lead_rows), 'display_observations': len(display_rows), 'remaining_missing_museum_local': remaining_by_target['local'], 'remaining_missing_museum_original_local_catalogue': len(unresolved), 'ledger': counts, 'source_bodies_verified': len(source_receipts), 'both_databases_verified': True}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
