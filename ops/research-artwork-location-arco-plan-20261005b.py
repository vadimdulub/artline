#!/usr/bin/env python3
"""Reconcile Italian object, current catalogue location and museum/city identities."""
import argparse
import collections
import importlib.util
import re
import uuid
from pathlib import Path
from urllib.parse import unquote

s = importlib.util.spec_from_file_location('a', Path(__file__).with_name('research-artwork-location-arco-20261005b.py'))
a = importlib.util.module_from_spec(s)
s.loader.exec_module(a)
p, r = a.p, a.r
DC = 'http://purl.org/dc/elements/1.1/'
LOC = 'https://w3id.org/arco/ontology/location/'
CD = 'https://w3id.org/arco/ontology/context-description/'
CLV = 'https://w3id.org/italia/onto/CLV/'
RDF_TYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
CITY_ALIASES = {'milan': 'milano', 'florence': 'firenze', 'rome': 'roma', 'venice': 'venezia', 'turin': 'torino', 'genoa': 'genova', 'naples': 'napoli', 'padua': 'padova', 'mantua': 'mantova', 'leghorn': 'livorno'}


def citykey(value):
    value = r.norm(re.sub(r'\s*\([A-Z]{2}\)\s*$', '', value or ''))
    return CITY_ALIASES.get(value, value)


def museumkey(value):
    value = p.titlekey(value)
    return re.sub(r'[^\w]+', ' ', value).strip()


def graphs():
    result = {}
    for path in sorted((r.RUN / 'arco-object-graphs-v2-20261005b').glob('*.json.gz')):
        batch = r.load(path)
        grouped = collections.defaultdict(list)
        for triple in batch['data']:
            # Keep identity/custody metadata in plans; original response remains pinned.
            if triple['s'] == triple['root'] and triple['p'].split('/')[-1] in ['preview', 'depiction', 'bibliographicCitation', 'hasBibliography', 'hasDocumentation']:
                continue
            grouped[triple['root']].append(triple)
        for uri, data in grouped.items():
            assert uri not in result
            result[uri] = (data, batch['receipt'])
    return result


def resolve_institution(names, city, records, uri):
    # City comparison accepts established English/Italian names without changing places.
    keys = {museumkey(n) for n in names}
    collection_reconciled = citykey(city) == 'firenze' and 'raccolta alberto della ragione e collezioni del novecento' in keys
    if collection_reconciled:
        names = {'Museo Novecento'}
        keys = {museumkey(n) for n in names}
    aliases = {
        ('galleria degli uffizi', 'firenze'): 'uffizi',
        ('galleria palatina', 'firenze'): 'palazzo-pitti-galleria-palatina',
        ('galleria palatina e appartamenti reali', 'firenze'): 'palazzo-pitti-galleria-palatina',
        ('accademia carrara museo', 'bergamo'): 'accademia-carrara',
        ('gallerie dell accademia', 'venezia'): 'gallerie-accademia-venezia',
        ('galleria sabauda', 'torino'): 'wikimedia-museum-q2245152',
        ('galleria d arte moderna ricci oddi', 'piacenza'): 'wikimedia-museum-q3757722',
        ('museo maga', 'gallarate'): 'museo-maga-gallarate',
        ('galleria dell accademia di belle arti tadini', 'lovere'): 'accademia-tadini',
        ('museo civico giovanni fattori', 'livorno'): 'wikimedia-museum-q3867777',
        ('museo di capodimonte', 'napoli'): 'spain-research-museum-q290549',
        ('galleria nazionale d arte antica', 'roma'): 'wikimedia-museum-q2266081',
        ('museo di palazzo vecchio', 'firenze'): 'wikimedia-museum-q271928',
    }
    forced = {aliases[(n, citykey(city))] for n in keys if (n, citykey(city)) in aliases}
    if forced:
        candidates = [v['institution'] for v in records if v['institution']['slug'] in forced]
        assert len(candidates) == 1
        return candidates[0], 'explicit_collection_name_alias_and_catalogue_city', None
    candidates = [v['institution'] for v in records if museumkey(v['institution']['name']) in keys and citykey((v['place'] or {}).get('name')) == citykey(city)]
    if not candidates and any(museumkey(v['institution']['name']) in keys and not v['place'] for v in records):
        return None, None, 'existing_institution_geography_requires_review'
    if len(candidates) > 1:
        return None, None, 'multiple_existing_institutions'
    if candidates:
        return candidates[0], 'exact_distinctive_institution_name_with_compatible_catalogue_city', None
    names = sorted(names, key=lambda n: (len(n), n))
    label = names[0]
    clean = r.norm(label)
    if re.search(r'privat|sconosciut|non identifica|collezione particolare', clean):
        return None, None, 'private_or_unspecified_collection'
    if re.search(r'museo|musei|pinacoteca|galleria|gallerie|accademia', clean):
        kind = 'museum'
    elif 'fondazione' in clean:
        kind = 'foundation'
    elif re.search(r'\b(chiesa|cattedrale|basilica|abbazia|convento|palazzo|castello|certosa)\b', clean):
        kind = 'historic_site'
    else:
        return None, None, 'institution_kind_requires_review'
    key = museumkey(label) + '|' + citykey(city)
    full_name = label + ' — ' + city
    institution = {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum-location/arco/' + key)),
                   'slug': 'arco-museum-' + r.sha(key.encode())[:20], 'name': full_name,
                   'normalized_name': r.norm(full_name), 'website_url': None, 'wikidata_id': None,
                   'kind': kind, 'status': 'review',
                   'description': 'Named institution and city documented in current Italian Ministry of Culture ArCo catalogue object records. The source institution URI may group same-name sites, so identity is scoped by city. No current display asserted.'}
    basis = 'official_collection_to_current_museum_reconciliation' if collection_reconciled else 'new_review_institution_from_official_object_museum_and_city'
    return institution, basis, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--draft', action='store_true')
    args = parser.parse_args()
    if not args.draft:
        assert (r.RUN / 'arco-discovery-complete-20261005b.json').exists()
        assert (r.RUN / 'arco-objects-complete-20261005b.json').exists()
    rows, _ = a.selection()
    by_id = {row['artwork']['id']: row for row in rows}
    if args.draft:
        # Draft identity candidates never enter delivery or primary-plans.
        keys = collections.defaultdict(list)
        for row in rows:
            for cells in row['supplied']:
                if cells[4] == 'Italy':
                    for title in a.variants(cells[1]):
                        keys[(title, cells[2])].append((row, cells))
        found = collections.defaultdict(dict)
        for path in (r.RUN / 'arco-selection-batches-20261005b').glob('*.json.gz'):
            batch = r.load(path)
            for obj in batch['data']:
                for row, cells in keys.get((obj['subject'], obj['date']), []):
                    if obj.get('name') and a.name(obj['name']) in {a.name(n) for n in a.variants(cells[0])}:
                        item = found[row['artwork']['id']].setdefault(obj['work'], {'artwork_id': row['artwork']['id'], 'work': obj['work'], 'source_receipt': batch['receipt'], 'matches': []})
                        item['matches'].append(obj)
        selected = [next(iter(group.values())) for group in found.values() if len(group) == 1]
        holds = []
    else:
        selection = r.load(r.RUN / 'arco-selection-20261005b.json.gz')
        selected, holds = selection['selected'], list(selection['holds'])
    source = graphs()
    institutions = r.load(r.RUN / 'institution-geography-20261005b.json')
    claims, authorities = [], {}
    for candidate in selected:
        aid, uri = candidate['artwork_id'], candidate['work']
        row = by_id[aid]
        if uri not in source:
            holds.append({'artwork_id': aid, 'reason': 'current_object_graph_pending', 'work': uri})
            continue
        triples, receipt = source[uri]
        graph = collections.defaultdict(lambda: collections.defaultdict(set))
        for t in triples:
            graph[t['s']][t['p']].add(t['o'])
        root = graph[uri]
        matched_subjects = {v['subject'] for v in candidate['matches']}
        matched_dates = {v['date'] for v in candidate['matches']}
        flags, reason = [], None
        if not matched_subjects & root[DC + 'subject'] or not matched_dates & root[DC + 'date']:
            reason = 'object_subject_or_date_changed'
        current = [x for x in root[LOC + 'hasTimeIndexedTypedLocation'] if LOC + 'CurrentPhysicalLocation' in graph[x][LOC + 'hasLocationType']]
        museums = set().union(*(graph[x][LOC + 'hasCulturalInstituteOrSite'] for x in current)) if current else set()
        cities = root[DC + 'coverage']
        if len(current) != 1 or len(museums) != 1 or len(cities) != 1:
            reason = 'no_unique_current_catalogue_museum_and_city'
        if reason:
            holds.append({'artwork_id': aid, 'reason': reason, 'work': uri, 'source_receipt': receipt})
            continue
        museum, city = next(iter(museums)), next(iter(cities))
        names = {v['mname'] for v in candidate['matches'] if v.get('museum') == museum and v.get('mname')}
        if not names:
            holds.append({'artwork_id': aid, 'reason': 'current_museum_differs_from_identity_candidate', 'work': uri, 'source_receipt': receipt})
            continue
        # Require original supplied museum name to agree with an actual current label.
        supplied_names = {museumkey(c[3]) for c in row['supplied']}
        matched_names = {n for n in names if museumkey(n) in supplied_names}
        if not matched_names:
            flags.append('supplied_museum_name_changed')
        location_names = matched_names or names
        address_cities = set().union(*(graph[x][CLV + 'hasCity'] for x in root[LOC + 'hasCulturalPropertyAddress'])) if root[LOC + 'hasCulturalPropertyAddress'] else set()
        if not address_cities or not any(citykey(unquote(x.rsplit('/', 1)[-1]).replace('-', ' ')) == citykey(city) for x in address_cities):
            flags.append('catalogue_city_and_address_require_reconciliation')
        preferred = root[CD + 'hasPreferredAuthor']
        matched_creators = {v['creator'] for v in candidate['matches'] if v.get('creator')}
        if len(preferred) != 1 or not preferred & matched_creators:
            flags.append('preferred_creator_requires_review')
        for attribution in root[CD + 'hasAuthorshipAttribution']:
            if CD + 'PreferredAuthorshipAttribution' not in graph[attribution][RDF_TYPE]:
                continue
            wording = ' '.join(o for values in graph[attribution].values() for o in values)
            if re.search(r'\b(copia|copista|bottega|scuola|ambito|cerchia|seguace|maniera|attribuito)\b', r.norm(wording)):
                flags.append('qualified_creator_attribution')
        inventory = set().union(*(graph[x][CD + 'inventoryIdentifier'] for x in root[CD + 'hasInventorySituation'])) if root[CD + 'hasInventorySituation'] else set()
        inventory |= root['https://w3id.org/arco/ontology/arco-lite/alternativeInventoryNumber']
        accession = row['artwork'].get('accession_number')
        if accession and p.acckey(accession) not in {p.acckey(v) for v in inventory}:
            flags.append('existing_inventory_not_reconciled')
        custody = ' '.join(root[DC + 'rights'] | root[DC + 'description'])
        custody += ' ' + ' '.join(o for values in graph[current[0]].values() for o in values)
        if re.search(r'\b(deposito|prestito|rubat\w*|furt\w*|dispers\w*|restitu\w*|privat\w*)\b', r.norm(custody)):
            flags.append('custody_or_legal_qualification')
        institution, authority_basis, issue = resolve_institution(names, city, institutions, museum)
        if issue:
            holds.append({'artwork_id': aid, 'reason': issue, 'work': uri, 'museum_names': sorted(names), 'city': city, 'source_receipt': receipt})
            continue
        authority = {'institution': institution, 'source_institution_uri': museum, 'source_names': sorted(names), 'catalogue_city': city, 'address_city_uris': sorted(address_cities), 'identity_basis': authority_basis}
        if authority_basis == 'explicit_collection_name_alias_and_catalogue_city':
            authority_pages = {'uffizi': 'uffizi', 'palazzo-pitti-galleria-palatina': 'galleria-palatina', 'accademia-carrara': 'accademia-carrara',
                               'gallerie-accademia-venezia': 'gallerie-accademia-venezia', 'wikimedia-museum-q2245152': 'galleria-sabauda',
                               'wikimedia-museum-q3757722': 'ricci-oddi', 'museo-maga-gallarate': 'museo-maga', 'accademia-tadini': 'accademia-tadini',
                               'wikimedia-museum-q3867777': 'museo-fattori', 'spain-research-museum-q290549': 'capodimonte',
                               'wikimedia-museum-q2266081': 'barberini-corsini', 'wikimedia-museum-q271928': 'palazzo-vecchio'}
            page = r.load(r.RUN / 'arco-institution-pages-20261005b' / (authority_pages[institution['slug']] + '.json'))
            assert page['source_receipt']['status'] == 200
            authority['institution_alias_authority_receipt'] = page['source_receipt']
        if authority_basis == 'official_collection_to_current_museum_reconciliation':
            page = r.load(r.RUN / 'arco-institution-pages-20261005b/museo-novecento.json')
            assert page['source_receipt']['status'] == 200
            authority['institution_alias_authority_receipt'] = page['source_receipt']
            location_names = {'Museo Novecento'}
        authorities[(institution['id'], museum, city)] = authority
        source_path = uri.removeprefix('https://w3id.org/arco/resource/')
        url = 'https://catalogo.cultura.gov.it/detail/' + source_path
        evidence = {'source_identity_candidate': candidate, 'current_location': current[0], 'museum_identity_resolution': authority, 'object_graph': triples, 'qualifications': sorted(set(flags)), 'catalogue_limitation': 'CurrentPhysicalLocation means location recorded by the catalogue, not a dated public-display observation.'}
        claim = p.claim(row, 'arco-object', source_path, institution, receipt, url, evidence,
                        'unique_exact_supplied_subject_creator_date; current national catalogue object, preferred creator, inventory and museum/city location reconciled',
                        min(location_names, key=lambda n: (len(n), n)) + ' — ' + city)
        if flags:
            claim['review_state'] = 'review'
            claim['limitation'] = 'Official Italian catalogue candidate remains in review: ' + ', '.join(sorted(set(flags))) + '. No accepted present museum, legal ownership or current display asserted.'
        else:
            claim['limitation'] = 'Documented museum/site connection from the current Italian national catalogue. Its location field records cataloguing-time custody; no fresh physical presence, public display, room or legal ownership asserted.'
        claims.append(claim)
    if args.draft:
        path = r.RUN / ('arco-draft-' + r.now().replace(':', '').replace('-', '') + '.json.gz')
        r.save_gz(path, {'at': r.now(), 'draft_only': True, 'claims': claims, 'holds': holds, 'authorities': list(authorities.values())})
        print('DRAFT', path, flush=True)
    else:
        r.save(r.RUN / 'arco-institution-resolutions-20261005b.json', list(authorities.values()))
        p.output('arco-20261005b', claims, holds)
    print('Claim states', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)
    print('Holds', collections.Counter(h['reason'] for h in holds), flush=True)
    print('Institution resolution', collections.Counter(v['identity_basis'] for v in authorities.values()), flush=True)


if __name__ == '__main__':
    main()
