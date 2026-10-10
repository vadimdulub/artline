#!/usr/bin/env python3
"""Accession-scoped searches of public museum-supplied Museum Data Service records."""
import argparse
import collections
import importlib.util
import json
import re
import time
import uuid
from pathlib import Path
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('m', Path(__file__).with_name('research-artwork-location-met-iwm-20261005c.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
r, p, h = m.r, m.p, m.h
ds = importlib.util.spec_from_file_location('date_notation', Path(__file__).with_name('refine-artwork-location-date-notation-20261005c.py'))
dn = importlib.util.module_from_spec(ds)
ds.loader.exec_module(dn)
FOLDER = r.RUN / 'mds-selected-objects-20261005c'
# Dataset names are taken from the actual public MDS collection filter.
# Networks stay at network level; an object is not placed into a branch.
DATASETS = {
    'Q1536471': ('National Museums Liverpool', 'Q1967497'),
    'Q3547979': ('National Museums Northern Ireland', 'Q16938739'),
    'Q1800739': ('North East Museums', 'Q7860476'),
    'Q7170878': ('Culture Perth & Kinross', 'Q124561076'),
    'Q1321874': ('Amgueddfa Cymru - Museum Wales', 'Q2046319'),
    'Q18561936': ('Nottingham Museums', 'Q18561936'),
    'Q55361621': ('Norfolk Museums Service', None),
    'Q1421440': ('Fitzwilliam Museum', 'Q1421440'),
    'Q636400': ('Ashmolean Museum', 'Q636400'),
    'Q7926563': ('Victoria Art Gallery', 'Q7926563'),
    'Q731616': ('National Army Museum', 'Q731616'),
    'Q7373646': ('Royal Albert Memorial Museum & Art Gallery', 'Q7373646'),
    'Q213322': ('Victoria and Albert Museum', 'Q213322'),
    'Q109893034': ('Aberdeen Archives, Gallery and Museums', 'Q109893034'),
    'Q4968867': ('Bristol Museums', None),
}


def selected():
    groups = r.load(r.RUN / 'remaining-wikidata-groups-20261005c.json.gz')
    result = []
    for qid, (name, authority_qid) in DATASETS.items():
        for v in groups.get(qid, []):
            numbers = sorted({x for x in h.statements(v['entity'], 'P217') if isinstance(x, str) and x.strip()})
            if len(numbers) == 1:
                result.append({**v, 'selected_museum_qid': qid, 'dataset_name': name, 'authority_qid': authority_qid, 'inventory': numbers[0]})
    return result


def fields(node):
    result = collections.defaultdict(list)
    for dt in node.select('dt'):
        dd = dt.find_next_sibling('dd')
        if dd:
            name = dt.get_text(' ', strip=True).rstrip(':').strip()
            value = dd.get_text(' ', strip=True)
            if value not in result[name]:
                result[name].append(value)
    return dict(result)


def capture_one(v):
    path = FOLDER / (v['artwork_id'] + '.json.gz')
    if path.exists():
        return
    # Public human search supports literal phrases. It does not support OR;
    # do not guess an API token or harvest a complete collection.
    raw, receipt = r.capture('https://museumdata.uk/object-search/',
        {'q': '"' + v['inventory'].replace('"', '') + '"', 'collection[]': v['dataset_name']},
        tag='mds-public-selected-inventories-20261005c', timeout=45)
    assert receipt['status'] == 200, receipt
    soup = BeautifulSoup(raw, 'html.parser')
    count_node = soup.select_one('.os__results-count')
    count = int(count_node.get_text().replace(',', '')) if count_node else 0
    if not count_node:
        assert 'no object records matching your search query' in soup.get_text(), 'Unexpected response; do not retry a challenge'
    candidates = []
    nodes = soup.select('details.object-overview')
    for node in nodes:
        values = fields(node)
        if values.get('Collection') != [v['dataset_name']]:
            continue
        if p.acckey(v['inventory']) not in {p.acckey(n) for n in values.get('Object number', [])}:
            continue
        links = {a['href'] for a in node.select('a[href]') if re.fullmatch(r'https://museumdata\.uk/objects/[0-9a-f-]+', a['href'])}
        if len(links) != 1:
            continue
        url = next(iter(links))
        text = node.get_text(' ', strip=True)
        licence = re.search(r'Use licence for this record:\s*(.*?)\s*Attribution for this record:', text)
        candidates.append({'fields': values, 'url': url, 'licence': licence[1] if licence else None,
            'attribution': url + ', ' + v['dataset_name'] + (', ' + licence[1] if licence else '')})
    r.save_gz(path, {'selection': v, 'source_receipt': receipt, 'result_count': count,
        'returned_count': len(nodes), 'objects': candidates})
    time.sleep(1.1)


def capture():
    values = selected()
    for n, v in enumerate(values, 1):
        capture_one(v)
        if n % 25 == 0:
            print('MDS selected inventories', n, '/', len(values), v['dataset_name'], flush=True)
    r.save(r.RUN / 'mds-capture-complete-20261005c.json', {'at': r.now(), 'selected': len(values)})


def authorities():
    ids = sorted({q for _, q in DATASETS.values() if q})
    entities, receipt = r.wiki_entities(ids, tag='mds-collection-authorities-20261005c')
    raw, rc = r.capture('https://museumdata.uk/object-search/', tag='mds-provider-methodology-20261005c', timeout=40)
    text = BeautifulSoup(raw, 'html.parser').get_text(' ', strip=True)
    assert rc['status'] == 200 and 'exported from the databases of our contributing collections' in text
    with r.connect('local') as db:
        existing = [v['i'] for v in db.execute('SELECT to_jsonb(i) i FROM institutions i')]
    decisions = {}
    for name, qid in set(DATASETS.values()):
        matches = [v for v in existing if (qid and v.get('wikidata_id') == qid) or r.norm(v['name']) == r.norm(name)]
        assert len(matches) <= 1, (name, matches)
        slug = re.sub(r'[^a-z0-9]+', '-', r.norm(name)).strip('-')
        institution = matches[0] if matches else {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum-location/mds/' + slug)),
            'slug': 'mds-' + slug, 'name': name, 'normalized_name': r.norm(name), 'kind': 'museum', 'status': 'review', 'wikidata_id': qid,
            'website_url': 'https://museumdata.uk/object-search/?collection%5B%5D=' + r.requests.utils.quote(name),
            'description': 'Museum collection authority named by its contributed Museum Data Service records. Network-level holdings do not assign a specific branch, current physical location or display.'}
        decisions[name] = {'institution': institution, 'museum_entity': entities.get(qid) if qid else None,
            'museum_entity_receipt': receipt, 'provider_methodology_receipt': rc,
            'authority_scope': 'The contributing collection, including a museum network where explicitly named; no inferred branch assignment.'}
    r.save(r.RUN / 'mds-collection-authorities-20261005c.json', decisions)


def artist_authorities():
    ids = sorted({a['id'] for v in selected() for a in h.statements(v['entity'], 'P170') if isinstance(a, dict) and a.get('id')})
    for start in range(0, len(ids), 50):
        path = r.RUN / 'mds-artist-authorities-20261005c' / (str(start) + '.json.gz')
        if not path.exists():
            entities, receipt = r.wiki_entities(ids[start:start+50], tag='mds-artist-authorities-20261005c')
            r.save_gz(path, {'entities': entities, 'receipt': receipt})
        print('MDS artist authority identities', min(start+50, len(ids)), '/', len(ids), flush=True)


def literal_titles(values):
    result = []
    for value in values:
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError):
            parsed = None
        result.extend(parsed if isinstance(parsed, list) and all(isinstance(v, str) for v in parsed) else [value])
    return result


def creator_label(value):
    value = re.sub(r'\s*\((?:artist|painter)\)\s*$', '', value, flags=re.I)
    # Explicit honors are not identity or attribution qualifications.
    value = re.sub(r'\((?:(?:Sir|Dame|RA|R\.A\.|FRS|FSA|RI|FRGS)[,\s]*)+\)', '', value)
    value = re.sub(r'\b(?:Sir|Dame|RA|FRS|FSA|RI|FRGS)\b', '', value)
    return ' '.join(value.split())


def title_key(value, dates):
    text = value or ''
    match = re.search(r'\s*\(([^()]*)\)\s*$', text)
    if match and any(dn.equivalent(match[1], date) for date in dates):
        text = text[:match.start()]
    text = re.sub(r'^Portrait of\s+', '', text, flags=re.I)
    return m.iwm_titlekey(text, dates)


def creator_names(values, entity):
    """Remove appended lifespan only when both years match the artist authority."""
    result = list(values)
    birth = {int(v['time'][1:5]) for v in h.statements(entity, 'P569') if isinstance(v, dict) and re.match(r'\+\d{4}', v.get('time', ''))}
    death = {int(v['time'][1:5]) for v in h.statements(entity, 'P570') if isinstance(v, dict) and re.match(r'\+\d{4}', v.get('time', ''))}
    for value in values:
        value = creator_label(value)
        result.append(value)
        active = re.fullmatch(r'(.*?)\s+active\s+\d{4}\s*[-–]\s*\d{4}', value, re.I)
        if active:
            # These are explicitly activity dates, not inferred birth/death.
            result.append(active[1].strip())
        match = re.fullmatch(r'(.*?)\s+\(?\s*(?:b\.\s*)?(\d{4})\s*(?:[,;]\s*d\.\s*|[-–])\s*(\d{4})\s*\)?', value)
        if match and {int(match[2])} == birth and {int(match[3])} == death:
            result.append(match[1])
        born = re.fullmatch(r'(.*?)\s+b\.\s*(\d{4})', value)
        if born and {int(born[2])} == birth:
            result.append(born[1])
        if re.fullmatch(r'[^/]+/[^/]+', value):
            result.append(value.replace('/', ', '))
    return result


def production_fields(f):
    makers = [v for v in f.get('Object production person', []) if v.strip()]
    dates = [v for v in f.get('Object production date', []) if v.strip()]
    proofs = []
    if not makers and {r.norm(x) for x in f.get("Person's association", [])} == {'creation'} and len(f.get('Associated person', [])) == 1:
        makers = list(f['Associated person'])
        proofs.append({'field': 'Associated person', 'association': f["Person's association"], 'literal_value': makers})
    if not dates and {r.norm(x) for x in f.get('Date - association', [])} == {'creation'} and len(f.get('Associated date', [])) == 1:
        dates = list(f['Associated date'])
        proofs.append({'field': 'Associated date', 'association': f['Date - association'], 'literal_value': dates})
    return makers, dates, proofs


def lifespan_conflict(values, entity):
    years = []
    for prop in ['P569', 'P570']:
        years.append({int(v['time'][1:5]) for v in h.statements(entity, prop) if isinstance(v, dict) and re.match(r'\+\d{4}', v.get('time', ''))})
    if not all(len(v) == 1 for v in years):
        return False
    for value in values:
        value = creator_label(value)
        if re.search(r'\bactive\b', value, re.I):
            continue
        match = re.fullmatch(r'(.*?)\s+\(?\s*(?:b\.\s*)?(\d{4})\s*(?:[,;]\s*d\.\s*|[-–])\s*(\d{4})\s*\)?', value)
        if match and ({int(match[2])} != years[0] or {int(match[3])} != years[1]):
            return True
    return False


def plan(provider='mds-20261005c'):
    assert (r.RUN / 'mds-capture-complete-20261005c.json').exists()
    index = p.Index()
    authorities = r.load(r.RUN / 'mds-collection-authorities-20261005c.json')
    artist_authorities = {}
    for path in (r.RUN / 'mds-artist-authorities-20261005c').glob('*.json.gz'):
        batch = r.load(path)
        for qid, entity in batch['entities'].items():
            artist_authorities[qid] = {'entity': entity, 'names': [x['value'] for x in entity.get('labels', {}).values()] + [x['value'] for names in entity.get('aliases', {}).values() for x in names], 'source_receipt': batch['receipt']}
    claims, holds = [], []
    for v in selected():
        captured = r.load(FOLDER / (v['artwork_id'] + '.json.gz'))
        objs = captured['objects']
        if len(objs) != 1 or captured['result_count'] > captured['returned_count']:
            holds.append({'artwork_id': v['artwork_id'], 'reason': 'no_unique_exhausted_exact_inventory_match', 'capture_path': str(FOLDER / (v['artwork_id'] + '.json.gz'))})
            continue
        obj, row = objs[0], index.by_id[v['artwork_id']]
        f = obj['fields']
        titles = literal_titles(f.get('Title', []) + f.get('Object name(s)', []) + f.get('Object name', []))
        if not f.get('Title'):
            titles += [v.strip() for label in f.get('Object name', []) for v in label.split(';') if v.strip()]
        makers, dates, association_proofs = production_fields(f)
        date_note_proofs = []
        if not dates:
            for note in f.get('Object production note', []):
                if dn.date_meaning(note):
                    dates.append(note)
                    date_note_proofs.append({'Object production note': note})
        for title in [row['artwork'].get(k) for k in ['title', 'alternate_title'] if row['artwork'].get(k)]:
            if title_key(title, dates) in {title_key(t, dates) for t in titles}:
                titles.append(title)
        makers += [re.sub(r'\b(Sir|Dame|Lord)\s+', '', n) for n in makers]
        creator_proofs, authority_flags, resolved_creator_sets = [], [], []
        for artist in h.statements(v['entity'], 'P170'):
            auth = artist_authorities.get(artist.get('id')) if isinstance(artist, dict) else None
            if not auth:
                continue
            names = creator_names(makers, auth['entity'])
            if {r.namekey(n) for n in names} & {r.namekey(n) for n in auth['names']}:
                if lifespan_conflict(production_fields(f)[0], auth['entity']):
                    authority_flags.append('creator_lifespan_conflicts_with_authority')
                makers += auth['names']
                creator_proofs.append({'artist_qid': artist['id'], 'primary_labels': f.get('Object production person', []), 'compared_names': names, 'authority_names': auth['names'], 'source_receipt': auth['source_receipt']})
                if all({r.namekey(n) for n in creator_names([label], auth['entity'])} & {r.namekey(n) for n in auth['names']} for label in production_fields(f)[0]):
                    resolved_creator_sets.append(artist['id'])
        basis = index.match(row, 'wikidata', v['qid'], titles, makers, f['Object number'][0], dates)
        if not basis.startswith(('existing_', 'unique_')):
            holds.append({'artwork_id': v['artwork_id'], 'reason': basis, 'source_url': obj['url'], 'source_receipt': captured['source_receipt'], 'capture_path': str(FOLDER / (v['artwork_id'] + '.json.gz'))})
            continue
        flags = sorted(set(authority_flags))
        date = row['artwork'].get('date_display')
        if not any(dn.equivalent(date, d) for d in dates):
            flags.append('creation_date_wording_differs')
        if any(dn.date_meaning(d) and not dn.equivalent(date, d) for d in dates):
            flags.append('conflicting_explicit_production_dates')
        creator_fields = [text for k, values in f.items() if k in ['Title', 'Object production person', "Person's association", 'Brief description', 'Object production note', 'Physical description', 'Text'] for text in values]
        if len({r.namekey(n) for n in production_fields(f)[0]}) > 1 and len(set(resolved_creator_sets)) != 1:
            flags.append('multiple_named_production_people')
        if re.search(r'\b(attributed|attrib|attr|after|school|circle|workshop|follower|copy|possibly|probably|uncertain)\b', r.norm(' '.join(creator_fields))):
            flags.append('qualified_creator')
        custody = ' '.join(text for k, values in f.items() if k in ['Credit line', 'Current location', 'Acquisition method', 'Brief description', 'Object history note'] for text in values)
        if re.search(r'\b(loan|lent|deaccession\w*|restitut\w*|stolen|missing|destroyed)\b', r.norm(custody)):
            flags.append('custody_or_availability_qualification')
        auth = authorities[v['dataset_name']]
        c = p.claim(row, 'mds-object', obj['url'].rsplit('/', 1)[-1], auth['institution'], captured['source_receipt'], obj['url'],
            {'museum_supplied_record': obj, 'selection': v, 'collection_authority': auth, 'qualifications': flags,
             'creator_authority_reconciliation': creator_proofs, 'date_reconciliation': {'local_date': date, 'primary_dates': dates, 'literal_production_note_proofs': date_note_proofs, 'date_meaning': dn.date_meaning(date)},
             'multiple_labels_resolved_to_single_creator_authority': resolved_creator_sets,
             'explicit_creation_association_proofs': association_proofs,
             'limitation': 'MDS republishes museum database records; updates may lag. Facts and attribution retained. No current on-view assertion.'},
            basis + '; exact MDS contributing collection, selected accession and named creator')
        c['duplicate_source_urls'] = [url for url in f.get('Text', []) + f.get('Text reference number', []) if re.match(r'https?://', url) and re.search(r'/(?:objects?|artworks?|collection|collections|catalog|id|item)/.+', url)]
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Museum-supplied catalogue candidate retained in review: ' + ', '.join(flags) + '. Existing title/date/creator and publication status retained; no current display.'
        claims.append(c)
    p.output(provider, claims, holds)
    print('States', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'authorities', 'artist_authorities', 'plan', 'refine'])
    command = parser.parse_args().command
    plan('mds-refined-20261005c') if command == 'refine' else globals()[command]()
