#!/usr/bin/env python3
"""Bounded title searches against the National Gallery's documented public API."""
import argparse
import collections
import importlib.util
import json
import re
import time
from pathlib import Path

s = importlib.util.spec_from_file_location('major', Path(__file__).with_name('research-artwork-location-major-museums-20261005d.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
r, p, dn = m.r, m.p, m.dn
FOLDER = r.RUN / 'ng-selected-current-api-20261005d'

def selected():
    rows = r.load(r.RUN / 'major-museums-remaining-original-20261005d.json.gz')
    return [v for v in rows if any(c[3] == 'National Gallery' for c in v['supplied'] or []) or any('nationalgallery.org.uk' in (e.get('canonical_url') or '') for e in v['identifiers'])]

def capture():
    rows = selected()
    for n, row in enumerate(rows, 1):
        path = FOLDER / (row['artwork']['id'] + '.json.gz')
        if path.exists(): continue
        query = '@datatype.base:object AND title.value:' + json.dumps(row['artwork']['title'])
        raw, receipt = r.capture('https://data.ng.ac.uk/es/public/_search',
            {'q': query, 'size': 30, '_source_excludes': 'multimedia,description,note,subject,archive,package,bibliography,framing,plinth,@graph'},
            tag='ng-selected-current-api-20261005d', timeout=60)
        assert receipt['status'] == 200, receipt
        result = json.loads(raw)
        assert not result.get('timed_out')
        r.save_gz(path, {'artwork_id': row['artwork']['id'], 'source_receipt': receipt, 'query': query, 'result': result})
        if n % 25 == 0: print('National Gallery selected titles', n, '/', len(rows), flush=True)
        time.sleep(.7)
    r.save(r.RUN / 'ng-current-api-complete-20261005d.json', {'at': r.now(), 'selected': len(rows)})

def date_matches(local, date):
    if dn.equivalent(local.removeprefix('Unverified date: '), date.get('value')):
        return True
    meaning = dn.date_meaning(local.removeprefix('Unverified date: '))
    if not meaning or meaning[2] > 1970: return False
    start, end = date.get('from', ''), date.get('to', '')
    if not re.fullmatch(r'\d{4}', start) or not re.fullmatch(r'\d{4}', end): return False
    # Explicit structured endpoints resolve abbreviated published ranges;
    # qualifiers must still agree and cannot be silently removed.
    value = r.norm(date.get('value', ''))
    if re.search(r'\b(before|after|probably|possibly|uncertain)\b|\?', value): return False
    circa = bool(re.match(r'^(?:about|circa|ca\.?|c\.?)\s*\d', value))
    return meaning == ('circa' if circa else 'exact', int(start), int(end))

def plan():
    assert (r.RUN / 'ng-current-api-complete-20261005d.json').exists()
    institution = next(v for v in r.load(r.RUN / 'major-museums-institutions-20261005d.json') if v['slug'] == 'national-gallery-london')
    claims, holds = [], []
    for row in selected():
        aid = row['artwork']['id']
        cap = r.load(FOLDER / (aid + '.json.gz'))
        hits = cap['result']['hits']
        if hits['total']['relation'] != 'eq' or hits['total']['value'] > len(hits['hits']):
            holds.append({'artwork_id': aid, 'reason': 'bounded_title_results_not_exhausted', 'capture_path': str(FOLDER / (aid + '.json.gz'))})
            continue
        matched = []
        for hit in hits['hits']:
            o = hit['_source']
            if o.get('@datatype', {}).get('base') != 'object': continue
            if m.key(row['artwork']['title']) not in {m.key(t.get('value')) for t in o.get('title', [])}: continue
            makers = [maker for creation in o.get('creation', []) for maker in creation.get('maker', []) if not maker.get('@link', {}).get('historical')]
            if not m.local_names(row) & {r.namekey(v.get('summary', {}).get('title')) for v in makers}: continue
            numbers = [v['value'] for v in o.get('identifier', []) if v.get('type') == 'object number']
            if len(numbers) != 1: continue
            if row['artwork'].get('accession_number') and p.acckey(row['artwork']['accession_number']) != p.acckey(numbers[0]): continue
            matched.append((o, makers, numbers[0]))
        if len(matched) != 1:
            holds.append({'artwork_id': aid, 'reason': 'no_unique_current_title_creator_inventory', 'capture_path': str(FOLDER / (aid + '.json.gz')), 'matching_objects': len(matched)})
            continue
        o, makers, number = matched[0]
        flags = []
        if o.get('legal', {}).get('status') != 'Accessioned object': flags.append('non_accessioned_collection_object')
        if re.search(r'\b(loan|lent|deposit|deaccession|restitu\w*)\b', r.norm(o.get('legal', {}).get('credit', ''))): flags.append('credit_ownership_qualification')
        attributes = [a.get('value', '') for c in o.get('creation', []) for a in c.get('attribution', []) if a.get('type') == 'attribution']
        if len(makers) != 1 or re.search(r'\b(after|attributed|workshop|studio|circle|school|follower|imitator|probably|possibly|associate)\b', r.norm(' '.join(attributes))): flags.append('qualified_or_multiple_creators')
        dates = [d for c in o.get('creation', []) for d in c.get('date', [])]
        if not any(date_matches(row['artwork'].get('date_display') or '', d) for d in dates): flags.append('creation_date_requires_review')
        uid = o['@admin']['uid']
        url = 'https://data.ng.ac.uk/' + uid + '.html'
        evidence = {'current_gallery_api_record': o, 'documented_api_source': 'https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api',
                    'qualifications': flags, 'source_inventory': number, 'source_creation_dates': dates,
                    'limitation': 'Museum collection association only. The API current-location field is retained as source evidence, not converted to a dated display claim.'}
        c = p.claim(row, 'ng-object', number, institution, cap['source_receipt'], url, evidence,
                    'Unique current National Gallery object with exact title and named creator; accessioned status and creation-date comparison')
        c['duplicate_native_ids'] = [uid, o['@admin'].get('id', '')]
        if flags: c['review_state'] = 'review'
        claims.append(c)
    p.output('ng-current-api-20261005d', claims, holds)
    print('National Gallery states', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan'])
    globals()[parser.parse_args().command]()
