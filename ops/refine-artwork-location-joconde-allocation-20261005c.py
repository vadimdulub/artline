#!/usr/bin/env python3
"""Interpret administrative DEPO entries against current LOCA and museum authority."""
import collections
import copy
import importlib.util
import re
from pathlib import Path

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def allocation_check(o):
    parts = [r.norm(v) for v in (o.get('Lieu_de_depot') or '').split(';') if v.strip()]
    admin = {'attribution', 'affectation', 'affecte', "changement d'affectation"}
    if not parts or parts[0] not in admin:
        return 'not_an_unqualified_administrative_allocation'
    if re.search(r'\b(depot|pret|prets|pretee?|loan|restitu\w*|recuperation|manquant|disparu|vole)\b|\?', ' '.join(parts)):
        return 'deposit_loan_uncertainty_or_return_in_allocation'
    if o.get('MANQUANT') or o.get('MANQUANT_COM'):
        return 'missing_flag'
    if re.search(r'\b(attribue|copie|atelier|ecole|suiveur|entourage|apres|anonyme)\b', r.norm(o.get('Auteur'))):
        return 'qualified_creator'
    legal = r.norm(o.get('Statut_juridique'))
    if not legal.startswith(("propriete de l'etat", 'propriete de la commune')):
        return 'ownership_not_unqualified_public_collection'
    if re.search(r'recuperation|restitution|restitue|depot|deposit|pret|privee|particulier', legal):
        return 'qualified_legal_status'
    name, city = r.norm(o.get('Nom_officiel_musee')), r.norm(o.get('Ville'))
    location = [r.norm(v) for v in (o.get('Localisation') or '').split(';') if v.strip()]
    if location != [city, name]:
        return 'current_conservation_place_not_exact_registered_museum_and_city'
    if o.get('Code_Museofile') == 'M5031' or 'louvre' in name:
        return 'use_current_louvre_reconciliation_instead'
    # Specific source field abbreviation within the same explicitly named city.
    # This is an institution-level holding, never a palace/building assertion.
    names = {name}
    if o.get('Code_Museofile') == 'M5077' and city == 'versailles' and name == 'musee national des chateaux de versailles et de trianon':
        names.add('musee du chateau')
    if parts[-1] not in names:
        return 'final_administrative_destination_differs'
    # A generic museum title needs an explicit matching city in DEPO as well.
    if name in {'musee des beaux-arts', 'musee municipal', 'musee du chateau'} or parts[-1] == 'musee du chateau':
        if len(parts) < 3 or parts[-2] != city:
            return 'generic_destination_requires_matching_city'
    return None


def main():
    baseline = set(r.load(r.RUN / 'publication-pass-baseline-20261005c.json')['ids'])
    by_id = {}
    for provider in ['joconde-deposit-review-20261005', 'joconde-alias-20261005b']:
        for c in r.load(r.RUN / 'primary-plans' / (provider + '.json.gz'))['claims']:
            if c['artwork_id'] in baseline and c.get('review_state') == 'review':
                by_id[c['artwork_id']] = c
    registry = r.load(r.RUN / 'museofile-current-20261005b.json.gz')
    authorities = {v['Identifiant']: v for v in registry['rows']}
    field_manual = r.load(r.RUN / 'joconde-field-standard-20261005c.json')
    claims, holds = [], []
    for old in by_id.values():
        o = old['object_evidence']
        reason = allocation_check(o)
        if reason:
            holds.append({'artwork_id': old['artwork_id'], 'reason': reason})
            continue
        authority = authorities.get(o.get('Code_Museofile'))
        if not authority or (r.norm(authority['Nom_officiel']), r.norm(authority['Ville'])) != (r.norm(o['Nom_officiel_musee']), r.norm(o['Ville'])):
            holds.append({'artwork_id': old['artwork_id'], 'reason': 'current_museum_registry_conflict'})
            continue
        c = copy.deepcopy(old)
        c.pop('review_state', None)
        c['identity_basis'] += '; DEPO administrative allocation distinguished from loan by Ministry field manual; current LOCA and Museofile museum/city agree'
        c['limitation'] = 'Documented museum holding based on the current national object catalogue and museum register. Administrative allocation is not a loan. Previous review evidence is retained; no room, current display, legal title change or new creator/date is asserted.'
        c['object_evidence'] = {'current_object_record': o, 'previous_review_candidate': old,
            'allocation_interpretation': {'field': 'DEPO', 'field_manual': field_manual,
                'manual_page': 1, 'source_allocation': o['Lieu_de_depot'],
                'source_current_conservation': o['Localisation'], 'source_legal_status': o['Statut_juridique'],
                'current_museum_authority': authority, 'museum_authority_receipt': registry['receipt']}}
        claims.append(c)
    p.output('joconde-allocation-20261005c', claims, holds)
    print('Museum totals', collections.Counter(c['institution']['name'] for c in claims), flush=True)


if __name__ == '__main__':
    main()
