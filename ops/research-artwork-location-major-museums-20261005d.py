#!/usr/bin/env python3
"""Selected Prado and Louvre identities, with source-specific review decisions."""
import argparse
import collections
import csv
import gzip
import importlib.util
import io
import json
import re
from pathlib import Path

def module(name, filename):
    s = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m

l = module('louvre', 'research-artwork-location-louvre-20261005c.py')
h = module('hunterian', 'research-artwork-location-hunterian-20261005c.py')
dn = module('dates', 'refine-artwork-location-date-notation-20261005c.py')
r, p = l.r, l.p

def remaining():
    return set(r.load(r.RUN / 'major-museums-baseline-20261005d.json')['ids'])

def titles(entity):
    return [v['value'] for v in entity.get('labels', {}).values()] + [v['value'] for vs in entity.get('aliases', {}).values() for v in vs]

def key(value):
    return re.sub(r'[^\w]', '', r.norm(value))

def inventory(value):
    match = re.fullmatch(r'([A-Z]+)0*(\d+)', (value or '').strip(), re.I)
    return match[1].upper() + str(int(match[2])) if match else p.acckey(value)

def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values(): yield from strings(v)
    elif isinstance(value, list):
        for v in value: yield from strings(v)

def prado_selection():
    ids = remaining()
    return [v for v in r.load(r.RUN / 'remaining-wikidata-groups-20261005c.json.gz')['Q160112'] if v['artwork_id'] in ids]

def louvre_selection():
    ids, mapping = remaining(), l.mapped()
    selected = []
    for old in l.selection():
        if old['artwork_id'] not in ids: continue
        matches = mapping.get(old['external_id'], [])
        if len({v['ark'] for v in matches}) != 1: continue
        match = matches[0]
        cap = r.load(l.FOLDER / (match['ark'] + '.json.gz'))
        if cap.get('object'):
            selected.append({'old': old, 'crosswalk': match, 'captured': cap})
    return selected

def authorities():
    qids = set()
    for v in prado_selection():
        qids.update(x['id'] for x in h.statements(v['entity'], 'P170') if isinstance(x, dict))
    for v in louvre_selection():
        qids.add(v['crosswalk']['item'].rsplit('/', 1)[-1])
        qids.update(x['wikidata'] for x in v['captured']['object'].get('creator', []) if re.fullmatch(r'Q\d+', x.get('wikidata', '')))
    qids = sorted(qids)
    for offset in range(0, len(qids), 50):
        path = r.RUN / 'major-museum-authorities-20261005d' / (str(offset) + '.json.gz')
        if not path.exists():
            entities, receipt = r.wiki_entities(qids[offset:offset+50], tag='major-museum-authorities-20261005d')
            r.save_gz(path, {'entities': entities, 'receipt': receipt})
        print('Major museum authority checks', min(offset+50, len(qids)), '/', len(qids), flush=True)
    r.save(r.RUN / 'major-museum-authorities-complete-20261005d.json', {'at': r.now(), 'entities': len(qids)})

def load_authorities():
    assert (r.RUN / 'major-museum-authorities-complete-20261005d.json').exists()
    result = {}
    for path in (r.RUN / 'major-museum-authorities-20261005d').glob('*.json.gz'):
        batch = r.load(path)
        result.update({qid: {'entity': e, 'receipt': batch['receipt']} for qid, e in batch['entities'].items()})
    return result

def local_names(row):
    return ({r.namekey(v['name']) for v in row['artists']} | {r.namekey(v[0]) for v in row['supplied'] or []} | {r.namekey(row['artwork'].get('unlinked_creator_label'))}) - {''}

def prado_date(value):
    text = r.norm(value).strip().rstrip('.')
    text = re.sub(r'^hacia\s+', 'circa ', text)
    text = re.sub(r'^entre\s+(\d{4})\s+y\s+(\d{4})$', r'\1-\2', text)
    return text

def prado():
    index, auth = p.Index(), load_authorities()
    museum = next(v for v in r.load(r.RUN / 'major-museums-institutions-20261005d.json') if v['slug'] == 'museo-del-prado')
    receipt = r.load(r.RUN / 'prado-dataset-receipt-20261005d.json')
    raw = gzip.decompress((r.ROOT / receipt['body_path']).read_bytes())
    assert r.sha(raw) == receipt['sha256']
    by_id, by_inventory = collections.defaultdict(list), collections.defaultdict(list)
    for obj in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        by_id[obj['url'].rsplit('/', 1)[-1]].append(obj)
        by_inventory[inventory(obj['Número de catálogo'])].append(obj)
    claims, holds = [], []
    for v in prado_selection():
        row = index.by_id[v['artwork_id']]
        numbers = {inventory(x) for x in h.statements(v['entity'], 'P217') if isinstance(x, str)}
        native = set(h.statements(v['entity'], 'P8905'))
        native.update(s.rsplit('/', 1)[-1].split('?')[0] for s in strings(v['entity']) if re.match(r'https?://(?:www\.)?museodelprado.es/(?:en/the-collection/art-work|coleccion/obra-de-arte)/', s))
        objects = {o['url']: o for oid in native for o in by_id.get(oid, [])}
        if not objects:
            objects = {o['url']: o for number in numbers for o in by_inventory.get(number, [])}
        if len(objects) != 1:
            holds.append({'artwork_id': v['artwork_id'], 'reason': 'no_unique_dataset_native_id_or_inventory', 'native_ids': sorted(native), 'inventories': sorted(numbers)})
            continue
        o = next(iter(objects.values()))
        oid = o['url'].rsplit('/', 1)[-1]
        flags, proofs = [], []
        if inventory(o['Número de catálogo']) not in numbers or (row['artwork'].get('accession_number') and inventory(row['artwork']['accession_number']) != inventory(o['Número de catálogo'])):
            flags.append('inventory_not_reconciled')
        aliases = {key(t) for t in titles(v['entity'])}
        if key(row['artwork']['title']) not in aliases:
            flags.append('local_title_not_reconciled')
        if key(o['Título']) not in aliases:
            flags.append('spanish_catalogue_title_requires_review')
        if native and oid not in native:
            flags.append('native_object_id_conflict')
        creator_ok = False
        for value in h.statements(v['entity'], 'P170'):
            authority = auth.get(value.get('id')) if isinstance(value, dict) else None
            if not authority: continue
            names = {r.namekey(t) for t in titles(authority['entity'])}
            if r.namekey(o['Autor']) in names and local_names(row) & names:
                creator_ok = True
                proofs.append({'qid': value['id'], 'primary_artist_name': o['Autor'], 'authority_names': titles(authority['entity']), 'source_receipt': authority['receipt']})
        if not creator_ok: flags.append('creator_not_reconciled')
        if o['Autores'].strip(): flags.append('multiple_or_qualified_creators')
        if not dn.equivalent(row['artwork'].get('date_display'), prado_date(o['Fecha'])):
            flags.append('creation_date_requires_review')
        if re.search(r'\b(deposito|depositado|depositada|prestamo|prestada|restituid\w*|desaparecid\w*|robado|destruid\w*)\b', r.norm(o['Procedencia'])):
            flags.append('custody_qualification_in_provenance')
        # Retain selected facts, not the dataset's descriptive prose. This is
        # an independently published 2026 snapshot, not a live Prado response.
        facts = {k: o[k] for k in ['Número de catálogo', 'Autor', 'Autores', 'Título', 'Fecha', 'Técnica', 'Soporte', 'Dimensión', 'url']}
        e = {'catalogue_facts_from_2026_dataset': facts, 'qualifications': flags, 'wikidata_identity': v,
             'creator_authorities': proofs, 'dataset_publication': r.load(r.RUN / 'prado-zenodo-record-20261005d.json'),
             'dataset_attribution': 'Toni Gonzalez Cifuentes and David Torrejon Vazquez, Dataset de obras del Museo Nacional del Prado, 27 March 2026, doi:10.5281/zenodo.19261880. Underlying catalogue: Museo Nacional del Prado.',
             'limitation': 'Secondary 2026 catalogue snapshot corroborated against existing object ID, inventory, multilingual title and creator authority. The current Prado page is inaccessible. No present physical location or display claim.'}
        c = p.claim(row, 'prado-object', oid, museum, receipt, o['url'], e, 'Exact Prado native object or inventory, multilingual object identity, named creator and explicit creation-date comparison')
        c['source_class'] = 'corroborated_secondary_museum_catalogue_dataset'
        c['duplicate_native_ids'] = [o['Número de catálogo'], inventory(o['Número de catálogo'])]
        c['duplicate_source_urls'] = sorted({s for s in strings(v['entity']) if s.startswith('https://www.museodelprado.es/') and oid in s})
        c['limitation'] = e['limitation']
        if flags: c['review_state'] = 'review'
        claims.append(c)
    p.output('prado-dataset-20261005d', claims, holds)
    print('Prado states', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)

def louvre():
    index, auth = p.Index(), load_authorities()
    claims, holds = [], []
    for v in louvre_selection():
        old, crosswalk, cap = v['old'], v['crosswalk'], v['captured']
        obj, row = cap['object'], index.by_id[old['artwork_id']]
        qid = crosswalk['item'].rsplit('/', 1)[-1]
        entity = auth.get(qid, {}).get('entity', {})
        flags, proofs = [], []
        primary_inventory = {p.acckey(x['value']) for x in obj.get('objectNumber', [])}
        prior_inventory = {p.acckey(x.strip()) for x in (old['object_evidence'].get('Numero_inventaire') or '').split(';')}
        if not primary_inventory & prior_inventory:
            holds.append({'artwork_id': old['artwork_id'], 'reason': 'inventory_conflict', 'source_url': obj['url'], 'source_receipt': cap['source_receipt']})
            continue
        source_titles = [obj.get('title', ''), *[x['value'] for x in obj.get('denominationTitle', [])]]
        local_titles = [row['artwork'].get(k) for k in ['title', 'alternate_title'] if row['artwork'].get(k)]
        title_basis = 'literal_title_words_and_punctuation_normalization'
        if not {key(t) for t in local_titles} & {key(t) for t in source_titles}:
            if {key(t) for t in local_titles} & {key(t) for t in titles(entity)} and crosswalk['ark'] in h.statements(entity, 'P9394') and primary_inventory & {p.acckey(x) for x in h.statements(entity, 'P217') if isinstance(x, str)}:
                title_basis = 'multilingual_title_alias_with_exact_Louvre_ARK_and_inventory'
            else:
                flags.append('current_title_requires_review')
        current = []
        for creator in obj.get('creator', []):
            if creator.get('attributionLevel') != 'Attribution actuelle': continue
            authority = auth.get(creator.get('wikidata'))
            names = {r.namekey(creator['label'])}
            if authority: names.update(r.namekey(t) for t in titles(authority['entity']))
            if local_names(row) & names:
                current.append(creator)
                if authority: proofs.append({'creator': creator, 'authority': authority})
        if not current:
            flags.append('current_creator_requires_review')
        elif any(x.get(k) for x in current for k in ['linkType', 'authenticationType', 'doubt']):
            flags.append('qualified_current_attribution')
        if obj.get('heldBy') != 'Musée du Louvre, Département des Peintures': flags.append('current_keeper_changed')
        if obj.get('isMuseesNationauxRecuperation') or obj.get('longTermLoanTo') or obj.get('ownedBy') != 'Etat': flags.append('ownership_or_long_term_loan_qualification')
        if not (r.norm(obj.get('currentLocation', '')) == 'non expose' or obj.get('currentLocation', '').startswith(('Sully,', 'Denon,', 'Richelieu,', 'Louvre-Lens,'))): flags.append('external_or_unresolved_current_location')
        a = row['artwork']
        years = [int(x[k]) for x in obj.get('dateCreated', []) for k in ['startYear', 'endYear'] if str(x.get(k, '')).isdigit()]
        if not years or not a.get('creation_year_start') or not a.get('creation_year_end') or max(years) > 1970:
            flags.append('creation_date_requires_review')
        elif max(years) < a['creation_year_start'] or min(years) > a['creation_year_end']:
            flags.append('creation_date_conflict')
        e = {'current_louvre_record': obj, 'prior_joconde_candidate': old, 'external_identifier_crosswalk': crosswalk,
             'object_authority': auth.get(qid), 'creator_authorities': proofs, 'title_reconciliation': title_basis,
             'qualifications': flags, 'limitation': 'Museum collection association only. Current-location text is not a dated display confirmation. Titles, dates and creator relationships are preserved.'}
        c = p.claim(row, 'louvre-object', 'cl' + crosswalk['ark'], old['institution'], cap['source_receipt'], obj['url'], e,
                    'Exact Joconde-to-Louvre ARK and inventory; current named creator authority; ' + title_basis)
        c['duplicate_source_urls'] = [obj['url'].replace('/ark:', '/en/ark:'), old['source_url']]
        c['duplicate_native_ids'] = [crosswalk['ark']]
        if flags: c['review_state'] = 'review'
        claims.append(c)
    p.output('louvre-authorities-20261005d', claims, holds)
    print('Louvre states', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['authorities', 'prado', 'louvre'])
    globals()[parser.parse_args().command]()
