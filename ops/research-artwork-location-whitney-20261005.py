#!/usr/bin/env python3
"""Select existing records from official metadata, then recheck exact API objects."""
import collections
import concurrent.futures
import csv
import importlib.util
import io
import json
from pathlib import Path
import re
import time

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def main():
    index = p.Index()
    museum = index.institution('wikimedia-museum-q639791')
    raw, selection_receipt = r.capture('https://raw.githubusercontent.com/whitneymuseum/open-access/main/artworks.csv', tag='whitney-20261005', timeout=90)
    assert selection_receipt['status'] == 200
    candidates = collections.defaultdict(dict)
    for obj in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        for row in index.find('whitney-object', obj['id'], [obj['title']], [obj['artists']], ['Whitney Museum of American Art']):
            basis = index.match(row, 'whitney-object', obj['id'], [obj['title']], [obj['artists']], obj['accession_number'], [obj['display_date']])
            if basis.startswith(('existing_', 'unique_')):
                candidates[row['artwork']['id']][obj['id']] = obj
    selected, holds = [], []
    for aid, group in candidates.items():
        if len(group) != 1:
            holds.append({'artwork_id': aid, 'reason': 'multiple_current_museum_objects', 'object_ids': sorted(group)})
        else:
            selected.append({'artwork_id': aid, 'metadata': next(iter(group.values()))})
    r.save_gz(r.RUN / 'whitney-selection-20261005.json.gz', {'at': r.now(), 'selection_receipt': selection_receipt, 'selected': selected, 'holds': holds})
    print('Whitney selected exact existing identities', len(selected), 'ambiguous', len(holds), flush=True)

    def one(f):
        aid, prior = f['artwork_id'], f['metadata']
        path = r.RUN / 'whitney-results-20261005' / (aid + '.json')
        if path.exists():
            return r.load(path)
        result = {'artwork_id': aid}
        try:
            raw, receipt = r.capture('https://whitney.org/api/artworks/' + prior['id'], tag='whitney-20261005', timeout=35)
            assert receipt['status'] == 200, 'source_http_' + str(receipt['status'])
            data = json.loads(raw)['data']
            obj = data['attributes']
            assert str(obj['tms_id']) == prior['id'] == str(data['id']), 'current_object_identifier_conflict'
            assert obj.get('department') == 'collection' and not obj.get('is_virtual'), 'not_a_physical_permanent_collection_record'
            basis = index.match(index.by_id[aid], 'whitney-object', prior['id'], [obj['title']], [obj['display_artist_text']], obj['accession_number'], [obj['display_date']])
            assert basis.startswith(('existing_', 'unique_')), basis
            assert p.acckey(obj['accession_number']) == p.acckey(prior['accession_number']), 'current_inventory_changed'
            assert str(obj['display_artist_text']) == prior['artists'], 'creator_display_changed'
            evidence = {k: obj.get(k) for k in ['id', 'tms_id', 'title', 'display_artist_text', 'display_date', 'accession_number', 'department', 'classification', 'credit_line', 'is_virtual', 'is_portfolio', 'portfolio_tms_id', 'on_view', 'updated_at']}
            evidence.update(selection_receipt=selection_receipt, original_selection_metadata=prior, artist_relationships=data.get('relationships', {}).get('artists'))
            c = p.claim(index.by_id[aid], 'whitney-object', prior['id'], museum, receipt, 'https://whitney.org/collection/works/' + prior['id'], evidence, basis + '; fresh official CSV identity and exact current public API ID, inventory, creator display and permanent collection department agree')
            if re.search(r'loan|lent by|deaccession|returned to', obj.get('credit_line') or '', re.I) or obj.get('is_portfolio'):
                c['review_state'] = 'review'
                c['limitation'] = 'Exact museum object candidate; credit line has custody qualifications or record represents a portfolio. Preserve in review pending precise physical-object/custody reconciliation. No display inferred.'
            result.update(claim=c, reason='primary_collection_candidate')
        except Exception as exc:
            result['reason'] = str(exc)[:350]
            if 'receipt' in locals():
                result['source_receipt'] = receipt
        r.save(path, result)
        time.sleep(0.8)
        return result

    claims = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for n, result in enumerate(pool.map(one, selected), 1):
            if result.get('claim'):
                claims.append(result['claim'])
            else:
                holds.append(result)
            if n % 100 == 0:
                print('Whitney current object records checked', n, '/', len(selected), flush=True)
    p.output('whitney-20261005', claims, holds)


if __name__ == '__main__':
    main()
