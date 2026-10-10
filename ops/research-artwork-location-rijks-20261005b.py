#!/usr/bin/env python3
"""Resolve captured Rijksmuseum identities, retaining qualified candidates in review."""
import collections
import gzip
import importlib.util
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def names(obj):
    return [v['content'] for v in obj.get('identified_by', []) if v.get('type') == 'Name' and v.get('content')]


def main():
    index = p.Index()
    museum = index.institution('rijksmuseum')
    rows = [x for x in r.load(r.RUN / 'remaining-snapshot-20261005b.json.gz') if any(c[3] == 'Rijksmuseum' for c in x['supplied'] or [])]
    existing_review = set()
    with r.connect('local') as db:
        for h in db.execute("SELECT artwork_id::text,source_url FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND review_state='review' AND claim_type='holding' AND superseded_by IS NULL", ([x['artwork']['id'] for x in rows],)):
            existing_review.add((h['artwork_id'], h['source_url']))
    claims, holds = [], []
    for row in rows:
        aid = row['artwork']['id']
        path = r.RUN / 'rijks-discovery-20261005b' / (aid + '.json.gz')
        assert path.exists(), 'Capture incomplete: ' + aid
        captured = r.load(path)
        candidates, errors = [], []
        for record in captured.get('objects', []):
            try:
                obj, oid, receipt = record['object'], record['id'], record['source_receipt']
                assert obj['type'] == 'HumanMadeObject' and obj['id'] == 'https://id.rijksmuseum.nl/' + oid
                production = obj.get('produced_by') or {}
                parts = production.get('part') or []
                creators = [v for part in parts for v in part.get('carried_out_by', [])] + production.get('carried_out_by', [])
                artists = [v['@value'] for creator in creators for v in creator.get('notation', []) if v.get('@value')]
                span = production.get('timespan') or {}
                assert isinstance(span, dict), 'multiple_creation_intervals'
                dates = names(span)
                accessions = {v['content'] for v in obj.get('identified_by', []) if v.get('type') == 'Identifier' and any(t.get('id') == 'http://vocab.getty.edu/aat/300312355' for t in v.get('classified_as', []))}
                assert len(accessions) == 1, 'no_unique_accession'
                accession = next(iter(accessions))
                basis = index.match(row, 'rijks-object', oid, names(obj), artists, accession, dates)
                flags = []
                if not basis.startswith(('existing_', 'unique_')):
                    # A search may match a historical or qualified creator. Such evidence
                    # can only support a review candidate, never accepted attribution.
                    title_match = p.titlekey(row['artwork']['title']) in {p.titlekey(v) for v in names(obj)}
                    date_match = bool({p.datekey(c[2]) for c in row['supplied']} & {p.datekey(v) for v in dates})
                    original_inventory = row['artwork'].get('accession_number')
                    assert title_match and date_match and (not original_inventory or p.acckey(original_inventory) == p.acckey(accession)), basis
                    source_words = r.norm(json.dumps(production, ensure_ascii=False))
                    assert any(r.norm(c[0]) in source_words for c in row['supplied']), 'creator_not_documented_in_production'
                    basis = 'exact_title_date_inventory_and_source_documented_qualified_creator_candidate'
                    flags.append('creator_relationship_requires_review')
                if len(parts) != 1 or len(creators) != 1:
                    flags.append('multiple_or_qualified_production_relationships')
                if re.search(r'\b(attributed|attribution|copy|copies|after|workshop|school|follower|circle|possibly|probably|anonymous|toegeschreven|kopie|naar|atelier|anoniem|rejected|verworpen)\b', json.dumps(production, ensure_ascii=False), re.I):
                    flags.append('qualified_or_historical_attribution')
                edm = record['provider_receipt']
                assert edm['status'] == 200, 'museum_provider_unavailable'
                xml = gzip.decompress((r.ROOT / edm['body_path']).read_bytes())
                assert r.sha(xml) == edm['sha256']
                root = ET.fromstring(xml)
                ns = {'ore': 'http://www.openarchives.org/ore/terms/', 'edm': 'http://www.europeana.eu/schemas/edm/'}
                rdf = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
                aggregation = root.find('ore:Aggregation', ns)
                provider = aggregation.find('edm:dataProvider', ns) if aggregation is not None else None
                assert provider is not None and provider.get(rdf + 'resource') == 'https://id.rijksmuseum.nl/2109266', 'museum_provider_conflict'
                shown = aggregation.find('edm:isShownAt', ns)
                url = shown.get(rdf + 'resource', '') if shown is not None else ''
                assert url.startswith('https://www.rijksmuseum.nl/') and accession in url, 'museum_object_url_conflict'
                credit = ' '.join(v.get('content', '') for v in obj.get('referred_to_by', []) if any(t.get('id') == 'http://vocab.getty.edu/aat/300026687' for t in v.get('classified_as', [])))
                if re.search(r'bruikleen|loan|lent|returned|deaccession|teruggegeven|afgestoten', credit, re.I):
                    flags.append('loan_or_custody_qualification')
                evidence = {k: obj.get(k) for k in ['id', 'identified_by', 'produced_by', 'referred_to_by', 'current_owner', 'current_location', 'current_custodian']}
                evidence.update(search_receipt=captured.get('search_receipt'), collection_provider_receipt=edm, museum_provider_id='https://id.rijksmuseum.nl/2109266', qualifications=flags)
                c = p.claim(row, 'rijks-object', oid, museum, receipt, url, evidence, basis + '; current exact accession and EDM Rijksmuseum provider verified')
                if flags:
                    c['review_state'] = 'review'
                    c['limitation'] = 'Current museum object candidate retained in review: ' + ', '.join(flags) + '. No accepted museum location, ownership, creator attribution or current display asserted.'
                candidates.append(c)
            except Exception as exc:
                errors.append({'object_id': record['id'], 'reason': str(exc)[:250]})
        if len(candidates) != 1:
            holds.append({'artwork_id': aid, 'reason': 'multiple_exact_source_candidates' if candidates else captured['reason'] if not captured.get('objects') else 'no_fully_reconciled_object', 'candidate_errors': errors, 'search_receipt': captured.get('search_receipt')})
            continue
        c = candidates[0]
        if c.get('review_state') == 'review' and (aid, c['source_url']) in existing_review:
            holds.append({'artwork_id': aid, 'reason': 'same_official_candidate_already_in_review', 'source_url': c['source_url']})
            continue
        claims.append(c)
    p.output('rijks-20261005b', claims, holds)
    print('Claim states', collections.Counter(c.get('review_state', 'accepted') for c in claims))


if __name__ == '__main__':
    main()
