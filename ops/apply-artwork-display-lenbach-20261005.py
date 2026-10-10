#!/usr/bin/env python3
"""Record an explicit negative display observation for the reconciled object."""
import importlib.util
from pathlib import Path

s = importlib.util.spec_from_file_location('display', Path(__file__).with_name('apply-artwork-display-research-20261004.py'))
x = importlib.util.module_from_spec(s)
s.loader.exec_module(x)
x.WAVE = 'dated-display-04'
x.FOLDER = x.r.RUN / 'delivery' / x.WAVE
a, r = x.a, x.r


def main():
    assert not (x.FOLDER / 'plan.json.gz').exists()
    data, digest = a.pinned('lenbach-01')
    verification = r.load(r.RUN / 'delivery/lenbach-01/verification.json')
    assert verification['plan_sha256'] == digest and verification['targets'] == {'local': 2, 'production': 2}
    c = next(v for v in data['claims'] if v['artwork_id'] == 'd4265b60-3ab3-560e-ac33-24ef9c73cf03')
    assert c['review_state'] == 'accepted' and c['object_evidence']['explicit_display_text'] == 'Ausgestellt: Nein'
    targets = {}
    for target in ['local', 'production']:
        aid, inst = c['target_ids'][target], c['target_institutions'][target]
        with r.connect(target) as db:
            old = a.snapshots(db, [aid])[aid]
        assert old['artwork']['current_institution_id'] == inst['id']
        assert not any(v['claim_type'] == 'display' and v['review_state'] == 'accepted' and not v['superseded_by'] for v in old['assertions'])
        record = {'artwork_id': aid, 'local_artwork_id': c['artwork_id'], 'institution': inst, 'venue': None, 'display_state': 'not_on_view', 'context': 'collection', 'source_receipt': c['source_receipt'], 'source_url': c['source_url'], 'source_updated_at': None, 'note': 'The exact official inventory GMS 446 page explicitly states “Ausgestellt: Nein” (not exhibited). Dated observation on retrieval; this does not identify a storage room or guarantee continuing non-display.', 'before': old}
        targets[target] = [record]
        r.save_gz(r.BACKUP / x.WAVE / (target + '-preimages.json.gz'), {aid: old})
    r.save_gz(x.FOLDER / 'plan.json.gz', {'at': r.now(), 'targets': targets})
    r.save(x.FOLDER / 'pin.json', {'sha256': r.sha((x.FOLDER / 'plan.json.gz').read_bytes()), 'records_per_target': 1, 'on_view': 0, 'not_on_view': 1})
    x.apply('local')
    x.apply('production')
    x.verify()


if __name__ == '__main__':
    main()
