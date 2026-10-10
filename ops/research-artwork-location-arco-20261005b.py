#!/usr/bin/env python3
"""Bounded national Italian catalogue queries for existing unresolved artworks."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path
import re
import time

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r
ENDPOINT = 'https://dati.beniculturali.it/sparql'
PREFIX = '''PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX loc: <https://w3id.org/arco/ontology/location/>
PREFIX cd: <https://w3id.org/arco/ontology/context-description/>
PREFIX cat: <https://w3id.org/arco/ontology/catalogue/>
'''


def variants(value):
    values = {value}
    if 'Ã' in value or 'Â' in value:
        try:
            values.add(value.encode('latin1').decode('utf8'))
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return values


def name(value):
    # Date-bearing biographical suffixes are identity comparison aids only.
    value = re.sub(r'\([^)]*\d{4}[^)]*\)\s*$', '', value)
    value = re.sub(r'\s+-\s+\d{4}.*$', '', value)
    return r.namekey(value)


def query(text, tag='arco-20261005b'):
    for attempt in range(3):
        try:
            raw, receipt = r.capture(ENDPOINT, {'query': PREFIX + text, 'format': 'application/sparql-results+json'}, tag=tag + ('-retry' + str(attempt) if attempt else ''), timeout=80)
            if receipt['status'] >= 500 or receipt['status'] == 429:
                raise r.requests.exceptions.ConnectionError('SPARQL temporary HTTP ' + str(receipt['status']))
            assert receipt['status'] == 200, 'SPARQL HTTP ' + str(receipt['status'])
            data = json.loads(raw)['results']['bindings']
            return [{k: v['value'] for k, v in row.items()} for row in data], receipt
        except r.requests.exceptions.RequestException:
            if attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))


def selection():
    rows = [x for x in r.load(r.RUN / 'remaining-snapshot-20261005b.json.gz') if any(c[4] == 'Italy' for c in x['supplied'] or [])]
    pairs = set()
    for row in rows:
        for cells in row['supplied']:
            if cells[4] == 'Italy':
                for title in variants(cells[1]):
                    pairs.add((title, cells[2]))
    return rows, sorted(pairs)


def capture():
    rows, pairs = selection()

    def batch(group, key):
        dest = r.RUN / 'arco-selection-batches-20261005b' / (key + '.json.gz')
        if dest.exists():
            return
        branches = []
        for subject, date in group:
            a, b = json.dumps(subject, ensure_ascii=False), json.dumps(date, ensure_ascii=False)
            branches.append('{ ?work dc:subject ' + a + '; dc:date ' + b + '. BIND(' + a + ' AS ?subject) BIND(' + b + ' AS ?date) }')
        # Explicit constant branches avoid the endpoint's unbounded VALUES join plan.
        data, receipt = query('''SELECT DISTINCT ?work ?subject ?date ?creator ?name ?museum ?mname WHERE {
{ ''' + ' UNION '.join(branches) + ''' }
OPTIONAL { ?work dc:creator ?creator . ?creator rdfs:label ?name }
OPTIONAL { ?work loc:hasCulturalInstituteOrSite ?museum . ?museum rdfs:label ?mname }
} LIMIT 10001''')
        if len(data) >= 10001:
            assert len(group) > 1, 'Single supplied title/date exceeds bounded scope'
            half = len(group) // 2
            batch(group[:half], key + 'a')
            batch(group[half:], key + 'b')
            r.save_gz(dest, {'requested': group, 'receipt': receipt, 'split': True, 'data': []})
        else:
            assert all((v['subject'], v['date']) in group for v in data)
            r.save_gz(dest, {'requested': group, 'receipt': receipt, 'data': data})
        time.sleep(0.5)

    for offset in range(0, len(pairs), 10):
        batch(pairs[offset:offset+10], f'{offset//10:04d}')
        if offset % 200 == 0:
            print('Italian supplied title/date pairs checked', min(offset+10, len(pairs)), '/', len(pairs), flush=True)
    r.save(r.RUN / 'arco-discovery-complete-20261005b.json', {'at': r.now(), 'pairs': len(pairs)})


def objects():
    rows, _ = selection()
    index = collections.defaultdict(set)
    for row in rows:
        for cells in row['supplied']:
            if cells[4] == 'Italy':
                for title in variants(cells[1]):
                    index[(title, cells[2])].update(name(n) for n in variants(cells[0]))
    seen_files, captured, selected = set(), set(), set()
    for path in (r.RUN / 'arco-object-graphs-v2-20261005b').glob('*.json.gz'):
        captured.update(r.load(path)['requested'])
    while True:
        for path in sorted((r.RUN / 'arco-selection-batches-20261005b').glob('*.json.gz')):
            if path.name in seen_files:
                continue
            batch = r.load(path)
            for obj in batch['data']:
                if obj.get('name') and name(obj['name']) in index.get((obj['subject'], obj['date']), set()):
                    assert re.fullmatch(r'https://w3id.org/arco/resource/[A-Za-z0-9_/-]+', obj['work']), 'Unexpected source URI'
                    selected.add(obj['work'])
            seen_files.add(path.name)
        pending = sorted(selected - captured)
        if pending:
            group = pending[:30]
            ids = ' '.join('<' + u + '>' for u in group)
            data, receipt = query('''SELECT DISTINCT ?root ?s ?p ?o WHERE {
VALUES ?root { ''' + ids + ''' }
{
{ ?root ?p ?o . BIND(?root AS ?s) }
UNION { ?root ?link ?s . VALUES ?link { loc:hasTimeIndexedTypedLocation loc:hasCulturalPropertyAddress cd:hasAuthorshipAttribution cd:hasInventorySituation cd:hasLegalSituation cd:hasDating cd:hasAcquisition cat:isDescribedByCatalogueRecord } ?s ?p ?o }
}
FILTER (?p NOT IN (loc:isCulturalPropertyAddressOf, loc:isCulturalInstituteOrSiteOf))
} LIMIT 20001''')
            assert len(data) < 20001, 'Selected object graph exceeds batch bound'
            assert {v['root'] for v in data} <= set(group)
            assert {v['root'] for v in data if v['s'] == v['root']} == set(group), 'Every selected object must have its own object triples'
            key = r.sha('\n'.join(group).encode())
            r.save_gz(r.RUN / 'arco-object-graphs-v2-20261005b' / (key + '.json.gz'), {'requested': group, 'receipt': receipt, 'data': data})
            captured.update(group)
            if len(captured) // 300 > (len(captured) - len(group)) // 300:
                print('Italian selected object graphs captured', len(captured), flush=True)
            time.sleep(0.5)
            continue
        if (r.RUN / 'arco-discovery-complete-20261005b.json').exists():
            break
        time.sleep(10)
    r.save(r.RUN / 'arco-objects-complete-20261005b.json', {'at': r.now(), 'selected_source_objects': len(captured)})


def identify():
    rows, pairs = selection()
    index = collections.defaultdict(list)
    for row in rows:
        for cells in row['supplied']:
            if cells[4] == 'Italy':
                for title in variants(cells[1]):
                    index[(title, cells[2])].append((row, cells))
    checked = set()
    found = collections.defaultdict(dict)
    for path in sorted((r.RUN / 'arco-selection-batches-20261005b').glob('*.json.gz')):
        batch = r.load(path)
        if batch.get('split'):
            continue
        checked.update(tuple(v) for v in batch['requested'])
        for obj in batch['data']:
            for row, cells in index.get((obj['subject'], obj['date']), []):
                if not obj.get('name') or name(obj['name']) not in {name(n) for n in variants(cells[0])}:
                    continue
                aid = row['artwork']['id']
                entry = found[aid].setdefault(obj['work'], {'artwork_id': aid, 'work': obj['work'], 'matches': [], 'source_receipt': batch['receipt']})
                if obj not in entry['matches']:
                    entry['matches'].append(obj)
    assert checked == set(pairs), 'Source discovery incomplete'
    selected, held = [], []
    for row in rows:
        aid = row['artwork']['id']
        group = found.get(aid, {})
        if len(group) == 1:
            selected.append(next(iter(group.values())))
        else:
            held.append({'artwork_id': aid, 'reason': 'multiple_exact_creator_subject_date_candidates' if group else 'no_exact_creator_subject_date_candidate', 'work_ids': sorted(group)})
    r.save_gz(r.RUN / 'arco-selection-20261005b.json.gz', {'at': r.now(), 'selected': selected, 'holds': held})
    print('Italian exact source identities', len(selected), collections.Counter(h['reason'] for h in held), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'identify', 'objects'])
    globals()[parser.parse_args().command]()
