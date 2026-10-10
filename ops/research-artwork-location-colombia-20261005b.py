#!/usr/bin/env python3
"""Query only existing Colombian artwork identities in the museum's public API."""
import argparse
import collections
import concurrent.futures
import importlib.util
import json
from pathlib import Path
import re
import time
import uuid

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r
BASE = 'https://colecciones.museonacional.gov.co/'


def selected():
    return [v for v in r.load(r.RUN / 'remaining-snapshot-20261005c.json.gz') if any(c[3] == 'Museo Nacional de Colombia' and c[4] == 'Colombia' for c in v['supplied'] or [])]


def identity(row):
    c = next(c for c in row['supplied'] if c[4] == 'Colombia')
    return c[1], c[0]


def fetch(url, params, tag):
    for attempt in range(3):
        try:
            raw, receipt = r.capture(url, params, tag=tag + (('-retry' + str(attempt)) if attempt else ''), timeout=40)
            assert receipt['status'] == 200, receipt['status']
            data = json.loads(raw)
            assert data['success']
            return data, receipt
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def key(pair):
    return r.sha(json.dumps(pair, ensure_ascii=False).encode())


def capture_one(pair):
    path = r.RUN / 'colombia-identities-20261005b' / (key(pair) + '.json.gz')
    if path.exists():
        return
    title, creator = pair
    items, receipts, total = [], [], None
    for page in range(1, 7):
        data, receipt = fetch(BASE + 'search-object.php', {'titulo': title, 'autor': creator, 'size': 48, 'page': page}, 'colombia-search-20261005b')
        receipts.append(receipt)
        total = data['total'] if total is None else total
        assert total == data['total']
        if total > 240:
            r.save_gz(path, {'identity': pair, 'search_receipts': receipts, 'reason': 'search_exceeds_identity_bound', 'total': total, 'objects': []})
            return
        items.extend(data['items'])
        if page >= data['total_pages']:
            break
        time.sleep(0.35)
    assert len(items) == total
    candidates = [v for v in items if p.titlekey(v['titulo']) == p.titlekey(title) and r.namekey(v['autor']) == r.namekey(creator)]
    objects = []
    for candidate in candidates:
        data, receipt = fetch(BASE + 'detail-object.php', {'id': candidate['id_objeto']}, 'colombia-object-json-20261005b')
        obj = data['item']
        assert obj['id_objeto'] == candidate['id_objeto']
        objects.append({'object': obj, 'source_receipt': receipt})
        time.sleep(0.35)
    r.save_gz(path, {'identity': pair, 'search_receipts': receipts, 'total': total, 'objects': objects})


def capture():
    jobs = sorted({identity(v) for v in selected()})
    # Two bounded requests at a time; never enumerate the complete museum.
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, _ in enumerate(pool.map(capture_one, jobs), 1):
            if n % 25 == 0:
                print('Colombia artwork identity groups', n, '/', len(jobs), flush=True)
    r.save(r.RUN / 'colombia-capture-complete-20261005b.json', {'at': r.now(), 'identity_groups': len(jobs)})


def plan():
    assert (r.RUN / 'colombia-capture-complete-20261005b.json').exists()
    index = p.Index()
    museum = {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://www.museonacional.gov.co/')), 'slug': 'museo-nacional-colombia', 'name': 'Museo Nacional de Colombia', 'normalized_name': r.norm('Museo Nacional de Colombia'), 'website_url': 'https://www.museonacional.gov.co/', 'wikidata_id': None, 'kind': 'museum', 'status': 'review', 'description': 'Museum identity confirmed by its official current collection catalogue, Bogotá. Artwork display is recorded separately.'}
    authority = r.load(r.RUN / 'americas-colombia-homepage-20261005b.json')['receipt']
    claims, holds = [], []
    for row in selected():
        aid = row['artwork']['id']
        captured = r.load(r.RUN / 'colombia-identities-20261005b' / (key(identity(row)) + '.json.gz'))
        found = []
        for v in captured['objects']:
            obj = v['object']
            basis = index.match(row, 'colombia-object', obj['id_objeto'], [obj['titulo']], [obj['autor']], obj['numero_registro'], [obj['fecha']])
            if basis.startswith(('existing_', 'unique_')):
                found.append((obj, v['source_receipt'], basis))
        if len(found) != 1:
            holds.append({'artwork_id': aid, 'reason': 'multiple_exact_object_candidates' if found else captured.get('reason', 'no_exact_title_creator_date_candidate'), 'search_receipts': captured['search_receipts']})
            continue
        obj, receipt, basis = found[0]
        flags = []
        if obj.get('en_investigacion'):
            flags.append('museum_marks_record_under_research')
        if r.norm(obj.get('ubicacion_actual')) != r.norm('Museo Nacional de Colombia'):
            flags.append('current_institution_requires_reconciliation')
        if re.search(r'atribuid|taller|escuela|copia|desconocido', r.norm(obj.get('autor'))):
            flags.append('creator_qualification')
        if re.search(r'prestamo|comodato|deposito|restitui|devuelt|perdid|robado', r.norm(' '.join(obj.get(k) or '' for k in ['ubicacion_actual', 'ubicacion_estado', 'procedencia']))):
            flags.append('custody_qualification')
        evidence = {'current_object': {k:v for k,v in obj.items() if k not in ['imagenes', 'imagen_principal', 'thumb']}, 'search_receipts': captured['search_receipts'], 'institution_authority_receipt': authority, 'qualifications': flags}
        c = p.claim(row, 'colombia-object', obj['id_objeto'], museum, receipt, BASE + 'objeto/' + obj['id_objeto'], evidence, basis + '; official object current museum location and inventory checked')
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Official museum object candidate retained in review: ' + ', '.join(flags) + '. No accepted physical presence, display or attribution asserted.'
        claims.append(c)
    p.output('colombia-20261005b', claims, holds)
    print('Claim states', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan'])
    globals()[parser.parse_args().command]()
