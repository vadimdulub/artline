#!/usr/bin/env python3
"""Query the official London catalogue by selected existing artwork titles."""
import collections
import importlib.util
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
    museum = index.institution('national-gallery-london')
    titles = sorted({cells[1] for row in index.rows for cells in row['supplied'] or [] if cells[3] == 'National Gallery'})
    records = {}
    for offset in range(0, len(titles), 20):
        path = r.RUN / 'london-selected-batches-20261005' / f'{offset//20:04d}.json.gz'
        if path.exists():
            data = r.load(path)
        else:
            query = {'size': 500, 'track_total_hits': True, '_source': {'includes': ['@admin', '@datatype', 'summary', 'title', 'identifier', 'creation', 'accession', 'legal', 'location', 'measurements', 'material']}, 'query': {'bool': {'filter': {'term': {'@datatype.base': 'object'}}, 'should': [{'match_phrase': {'title.value': title}} for title in titles[offset:offset+20]], 'minimum_should_match': 1}}}
            raw, receipt = r.capture('https://data.ng.ac.uk/es/public/_search', {'source': json.dumps(query, ensure_ascii=False, separators=(',', ':')), 'source_content_type': 'application/json'}, tag='london-20261005', timeout=45)
            assert receipt['status'] == 200, receipt['status']
            response = json.loads(raw)
            assert not response.get('timed_out') and response['_shards']['failed'] == 0
            assert response['hits']['total']['relation'] == 'eq' and response['hits']['total']['value'] <= 500, 'Selected title query needs explicit pagination'
            data = {'selected_titles': titles[offset:offset+20], 'receipt': receipt, 'records': response['hits']['hits']}
            r.save_gz(path, data)
            time.sleep(0.5)
        for record in data['records']:
            records[record['_id']] = (record['_source'], data['receipt'])
        if offset % 200 == 0:
            print('London title queries', min(offset+20, len(titles)), '/', len(titles), 'source identities', len(records), flush=True)
    claims, holds = [], []
    for pid, (obj, receipt) in sorted(records.items()):
        source_titles = [v['value'] for v in obj.get('title', []) if v.get('value')]
        accession = [v['value'] for v in obj.get('identifier', []) if v.get('type') == 'object number' and v.get('primary')]
        if len(accession) != 1:
            continue
        creators = [v['summary']['title'] for creation in obj.get('creation', []) for v in creation.get('maker', []) if not v.get('@link', {}).get('historical') and v.get('summary', {}).get('title')]
        dates = [v['value'] for creation in obj.get('creation', []) for v in creation.get('date', []) if v.get('value')]
        for row in index.find('ng-object', accession[0], source_titles, creators, ['National Gallery']):
            basis = index.match(row, 'ng-object', accession[0], source_titles, creators, accession[0], dates)
            if not basis.startswith(('existing_', 'unique_')):
                holds.append({'artwork_id': row['artwork']['id'], 'reason': basis, 'accession': accession[0], 'pid': pid, 'source_receipt': receipt})
                continue
            assert obj['@admin']['uid'] == pid and obj['@admin']['status'] == 'public'
            c = p.claim(row, 'ng-object', accession[0], museum, receipt, 'https://data.ng.ac.uk/' + pid + '.html', obj, basis + '; current official museum title query, public object PID, primary inventory and current creator attribution verified')
            attributions = ' '.join(v.get('value', '') for creation in obj.get('creation', []) for v in creation.get('attribution', []) if v.get('type') == 'attribution')
            legal = obj.get('legal', {})
            if len(set(creators)) != 1 or legal.get('status') != 'Accessioned object' or re.search(r'loan|lent by|deaccession|returned', legal.get('credit', ''), re.I) or re.search(r'attributed|after |workshop|follower|circle|school|possibly|probably|copy|imitator', attributions, re.I):
                c['review_state'] = 'review'
                c['limitation'] = 'Exact museum catalogue candidate, with qualified creator attribution, multiple makers, or non-accessioned/loan custody status. Retain in review; existing attribution and publication state are unchanged. No present physical location inferred.'
            claims.append(c)
    p.output('london-20261005', claims, holds)


if __name__ == '__main__':
    main()
