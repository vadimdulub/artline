#!/usr/bin/env python3
"""Find supplied artwork identities offline, then recheck selected Joconde IDs."""
import argparse
import collections
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time
import uuid

spec = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
r = p.r
BASE = 'https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/'


def selection(index):
    path = r.RUN / 'france-selection.json.gz'
    if path.exists():
        return r.load(path)
    source = r.ROOT / 'content/imports/joconde-20260910/joconde.csv'
    receipt = r.load(source.with_name(source.name + '.snapshot.json'))
    with source.open('rb') as file:
        assert hashlib.file_digest(file, 'sha256').hexdigest() == receipt['sha256']
    matches = collections.defaultdict(dict)
    keys = collections.defaultdict(list)
    for row in index.rows:
        for cells in row['supplied'] or []:
            if cells[4] != 'France':
                continue
            keys[(r.namekey(cells[0]), p.titlekey(cells[1]))].append(row)
    with source.open() as file:
        for o in csv.DictReader(file, delimiter='|'):
            for row in keys.get((r.namekey(o['Auteur']), p.titlekey(o['Titre'])), []):
                cells = row['supplied'][0]
                museum = o['Nom_officiel_musee'] + ' — ' + o['Ville']
                if p.titlekey(museum) != p.titlekey(cells[3]):
                    continue
                dates = [o['Millesime_de_creation'], o['Periode_de_creation']]
                if p.datekey(cells[2]) not in {p.datekey(d) for d in dates}:
                    continue
                matches[row['artwork']['id']][o['Reference']] = {'reference': o['Reference'], 'artwork_id': row['artwork']['id'], 'title': o['Titre'], 'artist': o['Auteur'], 'inventory': o['Numero_inventaire'], 'museum_code': o['Code_Museofile'], 'original_museum': museum, 'date': cells[2]}
    unique, ambiguous = [], []
    for aid, group in matches.items():
        if len(group) == 1:
            unique.append(next(iter(group.values())))
        else:
            ambiguous.append({'artwork_id': aid, 'references': sorted(group)})
    result = {'selection_at': r.now(), 'historical_source': receipt, 'unique': unique, 'ambiguous': ambiguous, 'matched_artworks': len(matches)}
    r.save_gz(path, result)
    print('Joconde exact identity candidates', len(unique), 'ambiguous', len(ambiguous), flush=True)
    return result


def capture(index):
    selected = selection(index)
    refs = sorted({v['reference'] for v in selected['unique']})
    for offset in range(0, len(refs), 50):
        dest = r.RUN / 'france-batches' / f'{offset//50:04d}.json.gz'
        if dest.exists():
            continue
        group = refs[offset:offset+50]
        raw, rc = r.capture(BASE, {'Reference__in': ','.join(group), 'page_size': 50}, tag='joconde')
        if rc['status'] != 200:
            raise RuntimeError('Source unavailable: ' + str(rc['status']))
        data = json.loads(raw)
        assert data.get('meta', {}).get('total', 0) <= 50 and not data['links'].get('next'), 'Bounded result required'
        assert all(o['Reference'] in group for o in data['data']), 'Source filter mismatch'
        r.save_gz(dest, {'requested': group, 'receipt': rc, 'data': data['data']})
        if offset % 500 == 0:
            print('Fresh Joconde IDs checked', min(offset+50, len(refs)), '/', len(refs), flush=True)
        time.sleep(0.5)


def plan(index):
    selected = selection(index)
    fresh = {}
    for path in sorted((r.RUN / 'france-batches').glob('*.json.gz')):
        batch = r.load(path)
        for o in batch['data']:
            assert o['Reference'] not in fresh
            fresh[o['Reference']] = (o, batch['receipt'])
    museums = {}
    for i in index.institutions:
        code = re.search(r'(?:museo/|joconde-)(m\d{4})', (i.get('website_url') or '') + ' ' + i['slug'], re.I)
        if code:
            museums.setdefault(code[1].upper(), []).append(i)
    crosswalk = r.load(r.RUN / 'french-institution-crosswalk-v2.json')
    for code, decision in crosswalk.items():
        receipt = decision['source_receipt']
        body = gzip.decompress((r.ROOT / receipt['body_path']).read_bytes())
        assert receipt['status'] == 200 and r.sha(body) == receipt['sha256']
        assert receipt['final_url'] == 'https://pop.culture.gouv.fr/notice/museo/' + code
        institution = next(i for i in index.institutions if i['id'] == decision['institution_id'])
        assert not museums.get(code) or {i['id'] for i in museums[code]} == {institution['id']}
        museums[code] = [institution]
    claims, holds = [], []
    for v in selected['unique']:
        aid = v['artwork_id']
        row = index.by_id[aid]
        if v['reference'] not in fresh:
            holds.append({'artwork_id': aid, 'reason': 'current_source_not_retrieved', 'reference': v['reference']})
            continue
        o, rc = fresh[v['reference']]
        reason = None
        museum_name = (o.get('Nom_officiel_musee') or '') + ' — ' + (o.get('Ville') or '')
        code = o.get('Code_Museofile') or ''
        if p.titlekey(o.get('Titre')) != p.titlekey(v['title']) or r.namekey(o.get('Auteur')) != r.namekey(v['artist']):
            reason = 'current_source_identity_changed'
        elif p.acckey(o.get('Numero_inventaire')) != p.acckey(v['inventory']):
            reason = 'current_inventory_changed'
        elif o.get('MANQUANT') or o.get('MANQUANT_COM'):
            reason = 'missing_or_stolen_work_flag'
        elif o.get('Lieu_de_depot'):
            reason = 'deposit_requires_location_review'
        elif not re.fullmatch(r'M\d{4}', code, re.I) or not o.get('Nom_officiel_musee') or not o.get('Ville'):
            reason = 'incomplete_museum_identity'
        elif code.upper() != v['museum_code'].upper():
            reason = 'current_museum_changed_requires_review'
        candidates = museums.get(code.upper(), [])
        if len(candidates) > 1:
            reason = 'institution_identity_collision'
        if reason:
            holds.append({'artwork_id': aid, 'reason': reason, 'reference': v['reference'], 'object_evidence': o, 'source_receipt': rc})
            continue
        institution = candidates[0] if candidates else {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum-location/joconde/' + code.upper())), 'slug': 'joconde-' + code.lower(), 'name': museum_name, 'normalized_name': r.norm(museum_name), 'website_url': 'https://pop.culture.gouv.fr/notice/museo/' + code.upper(), 'kind': 'museum', 'status': 'review', 'wikidata_id': None, 'description': 'Museum identity and documented holding from the French Ministry of Culture Joconde catalogue, Museofile ' + code.upper() + '. No present display assertion.'}
        fields = ['Reference', 'Titre', 'Auteur', 'Numero_inventaire', 'Millesime_de_creation', 'Periode_de_creation', 'Code_Museofile', 'Nom_officiel_musee', 'Ville', 'Localisation', 'Statut_juridique', 'Lieu_de_depot', 'Ancien_depot', 'MANQUANT', 'MANQUANT_COM', 'Date_de_mise_a_jour']
        evidence = {k: o.get(k) for k in fields}
        if code.upper() in crosswalk:
            evidence['institution_identity_review'] = crosswalk[code.upper()]
        claims.append(p.claim(row, 'joconde-object', v['reference'], institution, rc, 'https://pop.culture.gouv.fr/notice/joconde/' + v['reference'], evidence, 'unique_exact_supplied_creator_title_museum_date_then_current_reference_and_inventory_rechecked'))
    p.output('joconde-final', claims, holds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['selection', 'capture', 'plan'])
    args = parser.parse_args()
    globals()[args.command](p.Index())
