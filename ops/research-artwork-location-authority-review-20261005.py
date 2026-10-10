#!/usr/bin/env python3
"""Resolve secondary museum authorities without accepting their artwork claims."""
import collections
import importlib.util
from pathlib import Path
import re
import uuid
from urllib.parse import urlsplit

s = importlib.util.spec_from_file_location('secondary', Path(__file__).with_name('research-artwork-location-secondary-20261004.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
p, r = m.p, m.r


def key(value):
    return ' '.join(re.findall(r'[^\W_]+', r.norm(value)))


def host(value):
    return (urlsplit(value or '').hostname or '').removeprefix('www.')


def main():
    index = p.Index()
    with r.connect() as db:
        institutions = [v['row'] for v in db.execute("SELECT to_jsonb(i) row FROM institutions i WHERE status<>'archived'").fetchall()]
    authorities, receipts = {}, {}
    for path in sorted((r.RUN / 'institution-authorities-20261005').glob('*.json')):
        data = r.load(path)
        for qid, entity in data['entities'].items():
            authorities[qid], receipts[qid] = entity, data['receipt']
    assert len(authorities) == 941
    crosswalk, conflicts = {}, []
    for qid, entity in sorted(authorities.items()):
        labels = {key(v['value']) for v in entity.get('labels', {}).values()} | {key(v['value']) for group in entity.get('aliases', {}).values() for v in group}
        sites = [m.value(v) for v in m.current_statements(entity, 'P856') if isinstance(m.value(v), str) and m.value(v).startswith(('https://', 'http://'))]
        types = {m.value(v) for v in m.current_statements(entity, 'P31')}
        exact = [i for i in institutions if i.get('wikidata_id') == qid]
        names = [i for i in institutions if key(i['name']) in labels]
        hosts = {host(v) for v in sites}
        joined = [i for i in names if not i.get('wikidata_id') and host(i.get('website_url')) in hosts and host(i.get('website_url'))]
        institution, basis = None, None
        if len(exact) == 1:
            institution, basis = exact[0], 'existing_exact_wikidata_institution_id'
        elif len(joined) == 1:
            institution, basis = joined[0], 'existing_exact_name_or_alias_and_official_website_host; no conflicting Wikidata ID'
        else:
            label = entity.get('labels', {}).get('en', {}).get('value')
            same_site = [i for i in institutions if host(i.get('website_url')) in hosts and host(i.get('website_url'))]
            # Q33506 = museum, Q207694 = art museum. Collection services,
            # trusts, networks, and physical branches require separate research.
            if not label or not sites or not types.intersection({'Q33506', 'Q207694'}):
                reason = 'museum_type_name_or_website_requires_research'
            elif re.search(r'collections|museum service|museums service|trust|archives|network', label, re.I):
                reason = 'collection_network_or_service_not_a_specific_museum'
            elif exact or names or same_site:
                reason = 'possible_existing_authority_or_branch_identity_conflict'
            else:
                institution = {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum-location/wikidata/' + qid)), 'slug': 'museum-authority-' + qid.lower(), 'name': label, 'normalized_name': r.norm(label), 'website_url': sorted(sites, key=lambda u: (not u.startswith('https://'), len(u), u))[0], 'wikidata_id': qid, 'kind': 'museum', 'status': 'review', 'description': 'Museum authority candidate from a dated Wikidata entity naming this museum and its official website. Institution and artwork links remain in review pending independent primary-source reconciliation.'}
                basis = 'new_review_authority; exact Wikidata entity with museum/art-museum instance, English name and official website; no matching existing name or website host'
            if institution is None:
                conflicts.append({'qid': qid, 'label': label, 'reason': reason, 'existing_name_matches': [i['id'] for i in names], 'existing_website_matches': [i['id'] for i in same_site]})
        if institution:
            crosswalk[qid] = {'institution': institution, 'basis': basis, 'authority_receipt': receipts[qid], 'authority_entity': entity}
    r.save_gz(r.RUN / 'institution-review-crosswalk-20261005.json.gz', {'at': r.now(), 'crosswalk': crosswalk, 'held': conflicts})
    claims, holds = [], []
    for path in sorted((r.RUN / 'wikidata-batches').glob('*.json')):
        data = r.load(path)
        for qid, entity in data['entities'].items():
            collections_ = m.current_statements(entity, 'P195')
            locations = m.current_statements(entity, 'P276')
            cq, lq = {m.value(v) for v in collections_}, {m.value(v) for v in locations}
            if len(cq) != 1 or cq != lq or next(iter(cq)) not in crosswalk:
                continue
            museum_qid = next(iter(cq))
            authority = crosswalk[museum_qid]
            titles = [v['value'] for v in entity.get('labels', {}).values()] + [v['value'] for group in entity.get('aliases', {}).values() for v in group]
            inventories = {p.acckey(m.value(v)) for v in m.current_statements(entity, 'P217') if isinstance(m.value(v), str)}
            for row in index.external.get(('wikidata', qid), []):
                artwork = row['artwork']
                reason = None
                if not {p.titlekey(artwork[k]) for k in ['title', 'alternate_title'] if artwork.get(k)} & {p.titlekey(t) for t in titles}:
                    reason = 'entity_title_conflict'
                elif artwork['accession_number'] and inventories and p.acckey(artwork['accession_number']) not in inventories:
                    reason = 'entity_inventory_conflict'
                elif not all(v.get('references') for v in collections_):
                    reason = 'collection_statement_has_no_reference'
                elif any(set(v.get('qualifiers', {})) - {'P580', 'P585'} for v in collections_ + locations):
                    reason = 'qualified_collection_or_location_statement'
                if reason:
                    holds.append({'artwork_id': artwork['id'], 'reason': reason, 'qid': qid, 'museum_qid': museum_qid})
                    continue
                evidence = {'id': qid, 'collection_statements': collections_, 'location_statements': locations, 'inventory_statements': m.current_statements(entity, 'P217'), 'authority_qid': museum_qid, 'authority_basis': authority['basis'], 'authority_receipt': authority['authority_receipt'], 'authority_labels': authority['authority_entity'].get('labels'), 'authority_type_statements': authority['authority_entity'].get('claims', {}).get('P31'), 'authority_website_statements': authority['authority_entity'].get('claims', {}).get('P856')}
                c = p.claim(row, 'wikidata', qid, authority['institution'], data['receipt'], 'https://www.wikidata.org/wiki/' + qid, evidence, 'existing exact artwork Wikidata ID, title and available inventory; unique referenced collection agrees with location; authority reconciled by ' + authority['basis'])
                c['review_state'] = 'review'
                c['source_class'] = 'referenced_secondary_catalogue'
                c['limitation'] = 'Secondary-source artwork and museum-authority candidate only. Independent museum confirmation and current physical location remain unverified. Keep in review; do not set the artwork current institution or publish it.'
                claims.append(c)
    p.output('wikidata-authority-review-20261005', claims, holds)
    print('Authority outcomes', len(crosswalk), 'resolved candidates;', len(conflicts), 'held;', collections.Counter(v['basis'].split(';')[0] for v in crosswalk.values()), flush=True)


if __name__ == '__main__':
    main()
