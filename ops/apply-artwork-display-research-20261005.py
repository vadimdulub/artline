#!/usr/bin/env python3
"""Dated Greek National Gallery display records from exact official object pages."""
import argparse
import importlib.util
from pathlib import Path

s = importlib.util.spec_from_file_location('display', Path(__file__).with_name('apply-artwork-display-research-20261004.py'))
x = importlib.util.module_from_spec(s)
s.loader.exec_module(x)
x.WAVE = 'dated-display-03'
x.FOLDER = x.r.RUN / 'delivery' / x.WAVE
a, r = x.a, x.r


def plan():
    assert not (x.FOLDER / 'plan.json.gz').exists()
    prior, digest = a.pinned('continuation-primary-01')
    verified = r.load(r.RUN / 'delivery/continuation-primary-01/verification.json')
    assert verified['targets'] == {'local': len(prior['claims']), 'production': len(prior['claims'])}
    assert verified['plan_sha256'] == digest
    claims = [c for c in prior['claims'] if c['provider'] == 'curated-20261005' and c.get('review_state', 'accepted') == 'accepted' and c['object_evidence'].get('source_explicit_on_view_main_building')]
    targets = {}
    for target in ['local', 'production']:
        records = []
        with r.connect(target) as db:
            snapshots = a.snapshots(db, [c['target_ids'][target] for c in claims])
            for c in claims:
                tid, inst = c['target_ids'][target], c['target_institutions'][target]
                old = snapshots[tid]
                assert old['artwork']['current_institution_id'] == inst['id']
                assert not any(v['claim_type'] == 'display' and v['review_state'] == 'accepted' and not v['superseded_by'] for v in old['assertions'])
                venue = db.execute('SELECT to_jsonb(v) row FROM institution_venues v WHERE id=%s AND institution_id=%s', (a.uid('venue/greek-national-gallery-main-building'), inst['id'])).fetchone()['row']
                assert venue['slug'] == 'national-gallery-greece-main-building' and venue['visit_url']
                note = 'Official object page explicitly states “On view Main Building” for this exact inventory. Dated source observation on retrieval, independently recorded from the holding association; no guarantee of continuing display after this check.'
                records.append({'artwork_id': tid, 'local_artwork_id': c['artwork_id'], 'institution': inst, 'venue': venue, 'display_state': 'on_view', 'context': 'collection', 'source_receipt': c['source_receipt'], 'source_url': c['source_url'], 'source_updated_at': None, 'note': note, 'before': old})
        targets[target] = records
        r.save_gz(r.BACKUP / x.WAVE / (target + '-preimages.json.gz'), {v['artwork_id']: v['before'] for v in records})
    r.save_gz(x.FOLDER / 'plan.json.gz', {'at': r.now(), 'targets': targets})
    r.save(x.FOLDER / 'pin.json', {'sha256': r.sha((x.FOLDER / 'plan.json.gz').read_bytes()), 'records_per_target': len(claims), 'on_view': len(claims), 'not_on_view': 0})
    print('Pinned dated Greek display observations', len(claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['plan', 'apply', 'verify'])
    parser.add_argument('--target', choices=['local', 'production'], default='local')
    args = parser.parse_args()
    x.apply(args.target) if args.command == 'apply' else x.verify() if args.command == 'verify' else plan()
