#!/usr/bin/env python3
"""Fresh Rijksmuseum metadata for exact existing historical identity candidates."""
import collections
import concurrent.futures
import importlib.util
import json
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def names(value):
    return [v['content'] for v in value.get('identified_by', []) if v.get('type') == 'Name' and v.get('content')]


def main():
    index = p.Index()
    museum = index.institution('rijksmuseum')
    wanted = collections.defaultdict(dict)
    for n in [7, 9, 14]:
        file = r.ROOT / f'docs/research/expanded-round{n}-20260913/new-source-matches.json'
        digest = r.sha(file.read_bytes())
        for group in r.load(file).values():
            for old in group.values():
                if old['source'] != 'rijks':
                    continue
                obj = old['object_record']
                artists = [old['painter']['name']] + names(old['artist_record'])
                titles = names(obj)
                dates = [old['date']['display']]
                span = obj.get('produced_by', {}).get('timespan', {})
                if isinstance(span, dict):
                    dates.extend(names(span))
                for row in index.find('rijks-object', old['object_id'], titles, artists, ['Rijksmuseum']):
                    basis = index.match(row, 'rijks-object', old['object_id'], titles, artists, old['accession'], dates)
                    if basis.startswith(('existing_', 'unique_')):
                        wanted[row['artwork']['id']][old['object_id']] = {'id': old['object_id'], 'accession': old['accession'], 'creator_id': old['painter']['source_id'], 'creator_names': artists, 'dates': dates, 'selection_receipt': {'path': str(file.relative_to(r.ROOT)), 'sha256': digest}}
    selected, holds = [], []
    for aid, group in wanted.items():
        if len(group) != 1:
            holds.append({'artwork_id': aid, 'reason': 'multiple_historical_objects', 'object_ids': sorted(group)})
        else:
            selected.append({'artwork_id': aid, **next(iter(group.values()))})
    r.save_gz(r.RUN / 'rijks-selection-20261005.json.gz', {'at': r.now(), 'selected': selected, 'holds': holds})
    print('Selected Rijks identities', len(selected), 'ambiguous', len(holds), flush=True)

    def one(f):
        path = r.RUN / 'rijks-results-20261005' / (f['artwork_id'] + '.json')
        if path.exists():
            return r.load(path)
        result = {'artwork_id': f['artwork_id']}
        try:
            base = 'https://data.rijksmuseum.nl/' + f['id']
            raw, receipt = r.capture(base, {'_profile': 'la-framed'}, tag='rijks-20261005', timeout=35)
            assert receipt['status'] == 200, 'source_http_' + str(receipt['status'])
            obj = json.loads(raw)
            assert obj['id'] == 'https://id.rijksmuseum.nl/' + f['id'] and obj['type'] == 'HumanMadeObject', 'object_identity_conflict'
            production = obj.get('produced_by', {})
            parts = production.get('part', [])
            assert len(parts) == 1, 'production_parts_require_review'
            creators = parts[0].get('carried_out_by', [])
            assert len(creators) == 1 and creators[0].get('id') == 'https://id.rijksmuseum.nl/' + f['creator_id'], 'current_creator_identity_conflict'
            assert not re.search(r'\b(attributed|attribution|copy|copies|after|workshop|school|follower|circle|possibly|probably|anonymous|toegeschreven|kopie|naar|atelier|anoniem)\b', json.dumps(production, ensure_ascii=False), re.I), 'qualified_attribution'
            accession = {v['content'] for v in obj.get('identified_by', []) if v.get('type') == 'Identifier' and any(c.get('id') == 'http://vocab.getty.edu/aat/300312355' for c in v.get('classified_as', []))}
            assert len(accession) == 1 and p.acckey(next(iter(accession))) == p.acckey(f['accession']), 'current_inventory_conflict'
            span = production.get('timespan', {})
            assert isinstance(span, dict), 'multiple_date_intervals'
            artists = [v['@value'] for v in creators[0].get('notation', []) if v.get('@value')]
            # Existing aliases belong to the same explicit, unchanged museum person ID.
            artists.extend(f['creator_names'])
            basis = index.match(index.by_id[f['artwork_id']], 'rijks-object', f['id'], names(obj), artists, next(iter(accession)), names(span))
            assert basis.startswith(('existing_', 'unique_')), basis
            xml, edm_receipt = r.capture(base, {'_profile': 'edm'}, tag='rijks-20261005', timeout=35)
            assert edm_receipt['status'] == 200, 'source_edm_unavailable'
            root = ET.fromstring(xml)
            rdf = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
            ns = {'ore': 'http://www.openarchives.org/ore/terms/', 'edm': 'http://www.europeana.eu/schemas/edm/'}
            aggregation = root.find('ore:Aggregation', ns)
            provider = aggregation.find('edm:dataProvider', ns) if aggregation is not None else None
            assert provider is not None and provider.get(rdf + 'resource') == 'https://id.rijksmuseum.nl/2109266', 'museum_provider_identity_conflict'
            shown = aggregation.find('edm:isShownAt', ns)
            url = shown.get(rdf + 'resource', '') if shown is not None else ''
            assert url.startswith('https://www.rijksmuseum.nl/') and f['accession'] in url, 'collection_object_page_identity_conflict'
            evidence = {k: obj.get(k) for k in ['id', 'identified_by', 'produced_by', 'referred_to_by', 'current_owner', 'current_location', 'current_custodian']}
            evidence.update(identity_selection=f, collection_provider_receipt=edm_receipt, museum_provider_id='https://id.rijksmuseum.nl/2109266')
            c = p.claim(index.by_id[f['artwork_id']], 'rijks-object', f['id'], museum, receipt, url, evidence, basis + '; current exact creator authority and inventory; current EDM museum provider and collection URL verified')
            credit = ' '.join(v.get('content', '') for v in obj.get('referred_to_by', []) if any(t.get('id') == 'http://vocab.getty.edu/aat/300026687' for t in v.get('classified_as', [])))
            if re.search(r'bruikleen|loan|lent|returned|deaccession|teruggegeven|afgestoten', credit, re.I):
                c['review_state'] = 'review'
                c['limitation'] = 'Exact museum object identified, but acquisition/credit text mentions a loan or other custody qualification. Keep in review until present custody is independently resolved. No current-display or ownership claim.'
            result.update(claim=c, reason='primary_collection_candidate')
        except Exception as exc:
            result['reason'] = str(exc)[:300]
            if 'receipt' in locals():
                result['source_receipt'] = receipt
        r.save(path, result)
        time.sleep(0.7)
        return result

    claims = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for n, result in enumerate(pool.map(one, selected), 1):
            if result.get('claim'):
                claims.append(result['claim'])
            else:
                holds.append(result)
            if n % 50 == 0:
                print('Current Rijks objects', n, '/', len(selected), flush=True)
    p.output('rijks-20261005', claims, holds)


if __name__ == '__main__':
    main()
