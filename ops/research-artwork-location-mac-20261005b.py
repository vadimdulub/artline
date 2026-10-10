#!/usr/bin/env python3
"""Reconcile selected existing artworks with the MAC's official open-data export."""
import argparse
import collections
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
RESOURCE = 'c699f2a2-2250-4262-9555-50677f60e23a'
BASE = 'https://www.donneesquebec.ca/recherche/api/3/action/datastore_search'
MUSEUM = 'Musée d’art contemporain de Montréal'


def selected():
    return [v for v in r.load(r.RUN / 'remaining-snapshot-20261005c.json.gz') if any(c[3] == MUSEUM for c in v['supplied'] or [])]


def capture():
    creators = sorted({c[0] for row in selected() for c in row['supplied'] if c[3] == MUSEUM})
    for start in range(0, len(creators), 15):
        group = creators[start:start+15]
        path = r.RUN / 'mac-selected-creators-20261005b' / f'{start//15:04d}.json.gz'
        if path.exists():
            continue
        records, receipts, total, offset = [], [], None, 0
        while True:
            raw, receipt = r.capture(BASE, {'resource_id': RESOURCE, 'filters': json.dumps({'libelleNomsArtistes': group}, ensure_ascii=False), 'limit': 500, 'offset': offset, 'sort': '_id'}, tag='mac-creator-scoped-20261005b', timeout=45)
            assert receipt['status'] == 200
            response = json.loads(raw)
            assert response['success']
            data = response['result']
            total = data['total'] if total is None else total
            assert total == data['total'] and total < 3000
            assert all(v['libelleNomsArtistes'] in group for v in data['records'])
            records.extend(data['records'])
            receipts.append(receipt)
            offset += len(data['records'])
            if offset >= total:
                break
            assert data['records']
            time.sleep(0.4)
        assert len(records) == total
        r.save_gz(path, {'creators': group, 'records': records, 'source_receipts': receipts})
        print('MAC selected creators', min(start+15, len(creators)), '/', len(creators), 'object metadata', total, flush=True)
    r.save(r.RUN / 'mac-capture-complete-20261005b.json', {'at': r.now(), 'creators': creators})


def plan(refined=False):
    assert (r.RUN / 'mac-capture-complete-20261005b.json').exists()
    index = p.Index()
    sources = collections.defaultdict(list)
    for path in (r.RUN / 'mac-selected-creators-20261005b').glob('*.json.gz'):
        batch = r.load(path)
        # Find the exact page containing each object, never cite an unrelated page.
        for receipt in batch['source_receipts']:
            import gzip
            raw = gzip.decompress((r.ROOT / receipt['body_path']).read_bytes())
            assert r.sha(raw) == receipt['sha256']
            for obj in json.loads(raw)['result']['records']:
                sources[(p.titlekey(obj['titre']), r.namekey(obj['libelleNomsArtistes']))].append((obj, receipt))
    authority = r.load(r.RUN / 'mac-open-data-authority-20261005b.json')
    assert authority['data']['result']['author'] == MUSEUM
    resource = next(v for v in authority['data']['result']['resources'] if v['id'] == RESOURCE)
    assert resource['last_modified'].startswith('2026-09-20')
    museum = {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://macm.org/')), 'slug': 'musee-art-contemporain-montreal', 'name': MUSEUM, 'normalized_name': r.norm(MUSEUM), 'website_url': 'https://macm.org/', 'wikidata_id': None, 'kind': 'museum', 'status': 'review', 'description': 'Museum identity documented by its official MACrépertoire open-data publication on Données Québec. Distinct from the Montreal Museum of Fine Arts. No current display inferred.'}
    claims, holds = [], []
    for row in selected():
        aid = row['artwork']['id']
        candidates = {}
        for cells in row['supplied']:
            for obj, receipt in sources.get((p.titlekey(cells[1]), r.namekey(cells[0])), []):
                basis = index.match(row, 'mac-object', obj['id'], [obj['titre']], [obj['libelleNomsArtistes']], obj['numero'], [obj['dateProduction']])
                if basis.startswith(('existing_', 'unique_')):
                    candidates[obj['id']] = (obj, receipt, basis)
        if len(candidates) != 1:
            holds.append({'artwork_id': aid, 'reason': 'multiple_exact_title_creator_date_candidates' if candidates else 'no_exact_title_creator_date_candidate', 'source_object_ids': sorted(candidates)})
            continue
        obj, receipt, basis = next(iter(candidates.values()))
        flags = []
        collection_names = {'Collection ' + MUSEUM}
        if refined:
            collection_names.add('Collection Lavalin du ' + MUSEUM)
        if r.norm(obj.get('collection')) not in {r.norm(v) for v in collection_names}:
            flags.append('collection_identity_requires_review')
        if obj.get('oeuvrePrincipaleId'):
            flags.append('object_is_component_requires_review')
        if re.search(r'\b(attribu\w*|atelier|copie|apres|pret|depot|restitu\w*|vole\w*|disparu\w*)\b', r.norm(' '.join(obj.get(k) or '' for k in ['libelleNomsArtistes', 'provenance', 'description']))):
            flags.append('identity_or_custody_qualification')
        if obj.get('emplacementOeuvresDansLaVille'):
            flags.append('external_physical_location_requires_review')
        evidence = {'official_export_object': obj, 'official_publication_receipt': authority['receipt'], 'resource_last_modified': resource['last_modified'], 'qualifications': flags}
        if refined and 'Lavalin' in obj.get('collection', ''):
            evidence['collection_reconciliation'] = 'The museum-published object explicitly names Collection Lavalin du Musée d’art contemporain de Montréal; this is a named subcollection of the same museum.'
        c = p.claim(row, 'mac-object', obj['id'], museum, receipt, 'https://macrepertoire.macm.org/oeuvre/' + obj['id'] + '/', evidence, basis + '; exact inventory and explicit museum collection in official September 2026 export')
        c['limitation'] = 'Museum collection documented in its official September 2026 open-data export. Museum catalogue site was unavailable to direct access; no fresh physical presence, current display or room asserted.'
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Official museum export candidate remains in review: ' + ', '.join(flags) + '. No accepted current physical location or display asserted.'
        claims.append(c)
    p.output('mac-refined-20261005b' if refined else 'mac-20261005b', claims, holds)
    print('Claim states', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan', 'plan-refined'])
    command = parser.parse_args().command
    if command == 'plan-refined':
        plan(refined=True)
    else:
        globals()[command]()
