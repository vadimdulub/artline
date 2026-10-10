#!/usr/bin/env python3
"""Trace existing Marseille artworks through Joconde catalogue renumbering."""
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
BASE = 'https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/'


def inventory_keys(value):
    keys = {p.acckey(value)} if value else set()
    # Current Marseille records prefix old numbered Beaux-Arts inventories with BA.
    # Creator, title and original supplied date are independently checked below.
    match = re.fullmatch(r'BA\s+(\d+(?:\.\d+)*)', value or '', re.I)
    if match:
        keys.add(p.acckey(match[1]))
    return keys


def capture():
    page = 1
    total = None
    count = 0
    while True:
        path = r.RUN / 'marseille-current-batches-20261005b' / f'{page:04d}.json.gz'
        if path.exists():
            batch = r.load(path)
        else:
            raw, receipt = r.capture(BASE, {'Code_Museofile__exact': 'M0913', 'page_size': 100, 'page': page}, tag='marseille-current-20261005b', timeout=50)
            assert receipt['status'] == 200
            data = json.loads(raw)
            batch = {'receipt': receipt, 'data': data['data'], 'meta': data['meta'], 'links': data['links']}
            r.save_gz(path, batch)
            time.sleep(0.5)
        assert all(o['Code_Museofile'] == 'M0913' for o in batch['data'])
        total = total or batch['meta']['total']
        assert total == batch['meta']['total'] and total < 5000
        count += len(batch['data'])
        if not batch['links'].get('next'):
            break
        page += 1
    assert count == total
    print('Scoped Marseille metadata checked', count, flush=True)


def plan():
    index = p.Index()
    old_selection = r.load(r.RUN / 'france-museum-alias-candidates-20261005b.json.gz')['unique']
    selected = [v for v in old_selection if v['source_record']['Code_Museofile'] == 'M0913']
    current = {}
    for path in (r.RUN / 'marseille-current-batches-20261005b').glob('*.json.gz'):
        batch = r.load(path)
        for obj in batch['data']:
            assert obj['Reference'] not in current
            current[obj['Reference']] = (obj, batch['receipt'])
    assert len(current) == batch['meta']['total'], 'Wait for complete bounded museum metadata'
    authority = r.load(r.RUN / 'france-alias-authorities-20261005b.json')['M0913']
    inventory = collections.defaultdict(list)
    titles = collections.defaultdict(list)
    for obj, receipt in current.values():
        if obj.get('Numero_inventaire'):
            for key in inventory_keys(obj['Numero_inventaire']):
                inventory[key].append((obj, receipt))
        titles[(p.titlekey(obj.get('Titre')), r.namekey(obj.get('Auteur')))].append((obj, receipt))
    claims, holds = [], []
    for v in selected:
        aid, old = v['artwork_id'], v['source_record']
        row = index.by_id[aid]
        pool = inventory.get(p.acckey(old.get('Numero_inventaire')), []) if old.get('Numero_inventaire') else []
        if not pool:
            pool = titles.get((p.titlekey(old.get('Titre')), r.namekey(old.get('Auteur'))), [])
        matched = []
        for obj, receipt in pool:
            if r.namekey(old.get('Auteur')) != r.namekey(obj.get('Auteur')):
                continue
            if old.get('Numero_inventaire') and not inventory_keys(old['Numero_inventaire']) & inventory_keys(obj.get('Numero_inventaire')):
                continue
            dates = {p.datekey(obj.get(k)) for k in ['Millesime_de_creation', 'Periode_de_creation']}
            supplied_dates = {p.datekey(c[2]) for c in row['supplied']}
            if not dates & supplied_dates:
                continue
            matched.append((obj, receipt))
        if len(matched) != 1:
            holds.append({'artwork_id': aid, 'reason': 'multiple_current_inventory_candidates' if matched else 'renumbered_object_identity_unresolved', 'old_reference': old['Reference']})
            continue
        obj, receipt = matched[0]
        flags = []
        if p.titlekey(obj.get('Titre')) != p.titlekey(old.get('Titre')):
            flags.append('title_changed_requires_review')
        if obj.get('MANQUANT') or obj.get('MANQUANT_COM'):
            flags.append('missing_or_stolen_work_flag')
        if obj.get('Lieu_de_depot'):
            flags.append('deposit_destination_requires_review')
        if re.search(r'recuperation|restitution|restitue|depot|deposit|pret|collection privee|particulier', r.norm(obj.get('Statut_juridique'))):
            flags.append('qualified_legal_or_custody_status')
        if re.search(r'\b(?:attribue|copie|atelier|ecole|suiveur|entourage|apres|anonyme)\b', r.norm(obj.get('Auteur'))):
            flags.append('qualified_creator_attribution')
        evidence = {'old_identity': old, 'current_object': obj, 'museum_identity_resolution': authority, 'qualifications': flags}
        c = p.claim(row, 'joconde-object', obj['Reference'], authority['institution'], receipt,
                    'https://pop.culture.gouv.fr/notice/joconde/' + obj['Reference'], evidence,
                    'historical_exact_creator_title_date_identity_reconciled_with_unique_current_museum_inventory_including_BA_prefix_creator_date_and_title; old_Joconde_reference_retained_for_duplicate_checks')
        c['duplicate_native_ids'] = [old['Reference']]
        c['duplicate_source_urls'] = ['https://pop.culture.gouv.fr/notice/joconde/' + old['Reference']]
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Renumbered official Marseille object candidate remains in review: ' + ', '.join(flags) + '. No accepted current museum, ownership or display asserted.'
        claims.append(c)
    p.output('marseille-renumbered-v2-20261005b', claims, holds)
    print('Claim states', collections.Counter(c.get('review_state', 'accepted') for c in claims))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan'])
    globals()[parser.parse_args().command]()
