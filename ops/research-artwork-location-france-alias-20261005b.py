#!/usr/bin/env python3
"""Recheck selected French object identities despite supplied museum-name variants."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path
import re
import time
import uuid
from urllib.parse import urlsplit

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r
BASE = 'https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/'


def website(value):
    value = (value or '').strip()
    u = urlsplit(value if '://' in value else 'https://' + value)
    return ((u.hostname or '').removeprefix('www.'), u.path.rstrip('/'))


def authorities():
    registry = r.load(r.RUN / 'museofile-current-20261005b.json.gz')
    by_code = {a['Identifiant']: a for a in registry['rows']}
    by_host = collections.Counter(website(a['URL'])[0] for a in registry['rows'] if a['URL'])
    institutions = r.load(r.RUN / 'local-institutions-20261005b.json')
    existing_codes = collections.defaultdict(list)
    for i in institutions:
        m = re.search(r'(?:museo/|joconde-)(m\d{4})', (i.get('website_url') or '') + ' ' + i['slug'], re.I)
        if m:
            existing_codes[m[1].upper()].append(i)
    codes = sorted({v['source_record']['Code_Museofile'].upper() for v in r.load(r.RUN / 'france-museum-alias-candidates-20261005b.json.gz')['unique']})
    decisions = {}
    for code in codes:
        authority = by_code.get(code)
        if not authority:
            decisions[code] = {'reason': 'not_in_current_museofile_registry'}
            continue
        candidates = existing_codes.get(code, [])
        basis = 'exact_existing_Museofile_code'
        if not candidates and authority['URL']:
            candidates = [i for i in institutions if website(i.get('website_url')) == website(authority['URL'])]
            basis = 'exact_official_registered_website'
        if not candidates and authority['URL'] and by_host[website(authority['URL'])[0]] == 1:
            candidates = [i for i in institutions if website(i.get('website_url'))[0] == website(authority['URL'])[0]]
            basis = 'unique_official_registered_museum_hostname'
        if len(candidates) > 1:
            decisions[code] = {'reason': 'museum_authority_collision', 'candidate_ids': [i['id'] for i in candidates], 'authority': authority, 'source_receipt': registry['receipt']}
            continue
        if candidates:
            institution = candidates[0]
        else:
            name = authority['Nom_officiel'] + ' — ' + authority['Ville']
            institution = {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum-location/joconde/' + code)),
                           'slug': 'joconde-' + code.lower(), 'name': name, 'normalized_name': r.norm(name),
                           'website_url': 'https://pop.culture.gouv.fr/notice/museo/' + code, 'kind': 'museum',
                           'status': 'review', 'wikidata_id': None,
                           'description': 'Museum authority from the current French Ministry of Culture Museofile register, ' + code + '. Holdings do not establish current display.'}
            basis = 'new_review_authority_from_exact_official_Museofile_code'
        decisions[code] = {'institution': institution, 'basis': basis, 'authority': authority, 'source_receipt': registry['receipt']}
    r.save(r.RUN / 'france-alias-authorities-20261005b.json', decisions)
    print('Museum authorities', collections.Counter(v.get('basis', v.get('reason')) for v in decisions.values()), flush=True)


def plan():
    index = p.Index()
    selected = r.load(r.RUN / 'france-museum-alias-candidates-20261005b.json.gz')
    refs = {v['source_record']['Reference'] for v in selected['unique']}
    fetched, fresh = set(), {}
    for path in sorted((r.RUN / 'france-alias-batches-20261005b').glob('*.json.gz')):
        batch = r.load(path)
        fetched.update(batch['requested'])
        for obj in batch['data']:
            assert obj['Reference'] not in fresh
            fresh[obj['Reference']] = (obj, batch['receipt'])
    assert fetched == refs, 'Wait for selected current records to finish'
    museums = r.load(r.RUN / 'france-alias-authorities-20261005b.json')
    aids = [v['artwork_id'] for v in selected['unique']]
    existing_review = set()
    with r.connect('local') as db:
        for offset in range(0, len(aids), 1000):
            for h in db.execute("SELECT artwork_id::text,source_url FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND review_state='review' AND claim_type='holding' AND superseded_by IS NULL", (aids[offset:offset+1000],)):
                existing_review.add((h['artwork_id'], h['source_url']))
    claims, holds = [], []
    for candidate in selected['unique']:
        aid, old = candidate['artwork_id'], candidate['source_record']
        row, ref = index.by_id[aid], old['Reference']
        result = {'artwork_id': aid, 'reference': ref}
        if ref not in fresh:
            holds.append(dict(result, reason='current_object_not_found'))
            continue
        obj, receipt = fresh[ref]
        result.update(object_evidence=obj, source_receipt=receipt)
        code = (obj.get('Code_Museofile') or '').upper()
        authority = museums.get(code, {})
        basis = index.match(row, 'joconde-object', ref, [obj.get('Titre')], [obj.get('Auteur')], obj.get('Numero_inventaire'), [obj.get('Millesime_de_creation'), obj.get('Periode_de_creation')])
        reason = None
        if not basis.startswith(('existing_', 'unique_')):
            reason = basis
        elif p.titlekey(old['Titre']) != p.titlekey(obj.get('Titre')) or r.namekey(old['Auteur']) != r.namekey(obj.get('Auteur')):
            reason = 'current_object_identity_changed'
        elif p.acckey(old['Numero_inventaire']) != p.acckey(obj.get('Numero_inventaire')):
            reason = 'current_inventory_changed'
        elif code != old['Code_Museofile'].upper():
            reason = 'museum_code_changed'
        elif not authority.get('institution'):
            reason = authority.get('reason', 'missing_museum_authority')
        if reason:
            holds.append(dict(result, reason=reason))
            continue
        url = 'https://pop.culture.gouv.fr/notice/joconde/' + ref
        evidence = {k: obj.get(k) for k in ['Reference', 'Titre', 'Auteur', 'Numero_inventaire', 'Millesime_de_creation', 'Periode_de_creation', 'Code_Museofile', 'Nom_officiel_musee', 'Ville', 'Localisation', 'Statut_juridique', 'Lieu_de_depot', 'Ancien_depot', 'MANQUANT', 'MANQUANT_COM', 'Date_de_mise_a_jour']}
        evidence['museum_identity_resolution'] = authority
        evidence['supplied_museum_name'] = row['supplied'][0][3]
        c = p.claim(row, 'joconde-object', ref, authority['institution'], receipt, url, evidence,
                    'globally_unique_exact_supplied_creator_title_date_in_historical_Joconde; current_reference_creator_title_date_inventory_and_Museofile_authority_rechecked')
        flags = []
        if obj.get('MANQUANT') or obj.get('MANQUANT_COM'):
            flags.append('missing_or_stolen_flag')
        if obj.get('Lieu_de_depot'):
            flags.append('deposit_destination_requires_review')
        if re.search(r'\b(?:attribue|copie|atelier|ecole|suiveur|entourage|apres|anonyme)\b', r.norm(obj.get('Auteur'))):
            flags.append('qualified_creator_attribution')
        if re.search(r'recuperation|restitution|restitue|depot|deposit|pret|collection privee|particulier', r.norm(obj.get('Statut_juridique'))):
            flags.append('qualified_legal_or_custody_status')
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Exact official object candidate remains in review: ' + ', '.join(flags) + '. No current custody, accepted museum location, ownership or display is asserted.'
            if (aid, url) in existing_review:
                holds.append(dict(result, reason='same_official_candidate_already_in_review', qualifications=flags))
                continue
        claims.append(c)
    p.output('joconde-alias-20261005b', claims, holds)
    print('Claim states', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


def capture():
    chosen = r.load(r.RUN / 'france-museum-alias-candidates-20261005b.json.gz')
    refs = sorted({v['source_record']['Reference'] for v in chosen['unique']})
    for offset in range(0, len(refs), 50):
        path = r.RUN / 'france-alias-batches-20261005b' / f'{offset//50:04d}.json.gz'
        if path.exists():
            continue
        group = refs[offset:offset+50]
        raw, receipt = r.capture(BASE, {'Reference__in': ','.join(group), 'page_size': 50}, tag='joconde-alias-20261005b', timeout=60)
        assert receipt['status'] == 200, receipt['status']
        data = json.loads(raw)
        assert data.get('meta', {}).get('total', 0) <= 50 and not data['links'].get('next')
        assert all(v['Reference'] in group for v in data['data'])
        r.save_gz(path, {'requested': group, 'receipt': receipt, 'data': data['data']})
        if offset % 500 == 0:
            print('French exact object identities rechecked', min(offset+50, len(refs)), '/', len(refs), flush=True)
        time.sleep(0.6)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs='?', default='capture', choices=['capture', 'authorities', 'plan'])
    globals()[parser.parse_args().command]()
